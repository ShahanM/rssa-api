from datetime import datetime
import hashlib
from pathlib import Path
from collections import defaultdict
import re
# from MySQLdb import Timestamp
from flask import request, json
from sqlalchemy import and_
from random import randrange

from .models.survey import *


class InvalidSurveyException(Exception):
	def __init__(self, message):
		super().__init__(message)


class InvalidUserException(Exception):
	def __init__(self, message):
		super().__init__(message)


class InvalidRequestException(Exception):
	def __init__(self, message):
		super().__init__(message)


class SurveyDB(object):
	def __init__(self, db, survey_id=1, redirect_url='', activity_base_path=None):
		self.db = db
		self.survey_id = survey_id
		self.redirect_url = redirect_url
		self.parse_datetime = lambda dtstr: datetime.strptime(dtstr, "%a, %d %b %Y %H:%M:%S %Z")
		self.activity_base_path = 'user_interaction_data/' if \
			activity_base_path is None else activity_base_path

	def get_database(self):
		return self.db

	def _get_survey_pages(self):
		survey = Survey.query.filter_by(id=self.survey_id).first()
		if survey is None:
			raise InvalidSurveyException
		return list(sorted(survey.survey_pages, key=lambda page: page.page_num))

	def create_user(self, welcome_time, consent_start_time, consent_end_time, user_type, platform_info):
		survey_pages = self._get_survey_pages()
		user_type = UserType.query.filter_by(type_str=user_type).first()

		# conditionPicker = ConditionPicker()
		# condition = randrange(5)+1
		prevcond = User.query.order_by(User.id.desc()).first().condition
		condition = 1 if prevcond == 5 else prevcond + 1
		user = User(survey_id=self.survey_id, \
			condition=condition, user_type=user_type.id)
		self.db.session.add(user)
		self.db.session.flush()

		user_response = []

		welcome_page = survey_pages[0]
		welcome_response = SurveyResponse(user=user.id, survey_page=welcome_page.id, \
			starttime=self.parse_datetime(welcome_time), \
			endtime=self.parse_datetime(consent_start_time), survey_id=self.survey_id)

		consent_page = survey_pages[1]
		consent_response = SurveyResponse(user=user.id, survey_page=consent_page.id, \
			starttime=self.parse_datetime(consent_start_time), \
			endtime=self.parse_datetime(consent_end_time), survey_id=self.survey_id)

		user_response.append(welcome_response)
		user_response.append(consent_response)

		user.responses = user_response

		self.add_platform_session(platform_info, user.id)
		self.db.session.commit()

		return user.id
	
	def get_condition_for_user(self, userid:int) -> int:
		user = User.query.filter_by(id=userid).first()
		condition = Condition.query.filter_by(id=user.condition).first()
		
		return condition

	def add_survey_reponse(self, user_id, survey_pageid, starttime, endtime, \
		response_params):
		user = User.query.filter_by(id=user_id).first()
		if user is None:
			raise InvalidUserException
		survey_page = self._get_survey_pages()[survey_pageid-1] # FIXME - validate survey_page

		survey_response = SurveyResponse.query.filter(
			and_(
				SurveyResponse.user==user_id,
				SurveyResponse.survey_page==survey_pageid
			)
		).first()

		if survey_response is not None:
			print('Data for this page already exists!')
			return user_id

		survey_response = SurveyResponse(user=user_id, survey_page=survey_page.id, \
			starttime=self.parse_datetime(starttime), endtime=self.parse_datetime(endtime),
			survey_id=self.survey_id)
		self.db.session.add(survey_response)
		self.db.session.flush()
		if 'ratings' in response_params:
			itemsids = [item.item_id for item in survey_response.ratings]
			for itemrating in response_params['ratings']:
				itemid = itemrating['item_id']
				rating_date = self.parse_datetime(itemrating['rating_date'])
				rating = itemrating['rating']
				location = itemrating['loc']
				level = itemrating['level']
				if itemid not in itemsids:
					survey_response.ratings.append(Rating(survey_response=survey_response.id, \
						item_id=itemid, date_created=rating_date, rating=rating, \
						location=location, level=level, survey_id=self.survey_id, \
						user_id=user_id))
			rating_history = []
			for rating_event in response_params['rating_history']:
				rhist_item = rating_event['item_id']
				rhist_rate = rating_event['rating']
				rhist_date = self.parse_datetime(rating_event['rating_date'])
				rhist_loc = rating_event['loc']
				rhist_leve = rating_event['level']
				rhist_event = RatingHistory(user_id=user_id, page_id=survey_pageid, \
					item_id=rhist_item, rating=rhist_rate, location=rhist_loc, \
					timestamp=rhist_date, level=rhist_leve, survey_id=self.survey_id)
				rating_history.append(rhist_event)
			self.db.session.add_all(rating_history)

			hover_history = []
			hover_events = response_params['hover_history']
			for hover_event in response_params['hover_history']:
				hhist_item = hover_event['item_id']
				hhist_actn = hover_event['action']
				hhist_time = self.parse_datetime(hover_event['time'])
				hhist_loc = hover_event['loc']
				hhist_leve = hover_event['level']
				hhist_event = HoverHistory(user_id=user_id, page_id=survey_pageid, \
					item_id=hhist_item, location=hhist_loc, \
					timestamp=hhist_time, event_type=hhist_actn, \
					level=hhist_leve, survey_id=self.survey_id)
				hover_history.append(hhist_event)
			self.db.session.add_all(hover_history)

		if 'action_history' in response_params:
			action_history = []
			for action_event in response_params['action_history']:
				target_label = action_event['target_label']
				target_type = action_event['target_type']
				action_type = action_event['action_type']
				timestamp = action_event['timestamp']
				action_target = self._get_action_or_create(target_label, target_type)
				interaction = UserInteraction(user_id=user_id, survey_id=self.survey_id,\
					page_id=survey_pageid, action_type=action_type, \
					action_target=action_target.id,\
					timestamp=self.parse_datetime(timestamp))
				action_history.append(interaction)
			self.db.session.add_all(action_history)

		# if 'pick' in response_params:
		# 	itemid = response_params['pick']
		# 	survey_response.ratings = [Rating(survey_response=survey_response.id, \
		# 		item_id=itemid, rating=99, survey_id=self.survey_id, user_id=user_id)]

		if 'responses' in response_params:
			for qres in response_params['responses']:
				qtext = qres['text']
				question = self._get_question_or_create(survey_page=survey_page, \
					text=qtext)
				if qres['type'] == 'likert':
					qscore = qres['val']
					score = Score(score_point=qscore, question=question.id, \
						survey_response=survey_response.id, survey_id=self.survey_id, \
						user_id=user_id)
					question.scores.append(score)
					survey_response.scores.append(score)
				else:
					qresTxt = qres['val']
					free_res = FreeResponse(response_text=qresTxt, question=question.id, \
						survey_response=survey_response.id, survey_id=self.survey_id, \
						user_id=user_id)
					question.responses.append(free_res)
					survey_response.responses.append(free_res)
		
		if 'demography' in response_params:
			dem = response_params['demography']
			age = dem['age']
			edu = dem['education']
			rac = dem['race']
			gen = dem['gender']
			con = dem['country']
			demo = Demography(age=age, education=edu, race=':'.join(map(str, rac)), \
				gender=gen, country=con, user_id=user.id, survey_id=self.survey_id)
			textgen = dem['textgen']
			if len(textgen) > 1:
				question = self._get_question_or_create(survey_page=survey_page, \
					text='Self identifying gender.')
				free_res = FreeResponse(response_text=textgen, question=question.id, \
					survey_response=survey_response.id, survey_id=self.survey_id, \
					user_id=user.id)
			textrac = dem['textrac']
			if len(textrac) > 1:
				question = self._get_question_or_create(survey_page=survey_page, \
					text='Self identifying race.')
				free_res = FreeResponse(response_text=textrac, question=question.id, \
					survey_response=survey_response.id, survey_id=self.survey_id, \
					user_id=user.id)
			self.db.session.add(demo)
		
		if 'completed' in response_params:
			question = self._get_question_or_create(survey_page=survey_page, \
				text='Survey Completion Placeholder.')
			free_res = FreeResponse(response_text=str(response_params['completed']), \
				question=question.id, survey_response=survey_response.id, \
				survey_id=self.survey_id, user_id=user.id)

		user.responses.append(survey_response)
		self.db.session.commit()

		return user.id
	
	def _find_question_by_text(self, survey_page, text):
		all_questions = SurveyQuestion.query.filter_by(\
			survey_page=survey_page.id).all()
		for question in all_questions:
			if text.lower() == question.question_text.lower():
				return question
		
		return None

	def _get_question_or_create(self, survey_page, text):
		question = self._find_question_by_text(survey_page, text)
		if question is None:
			question = SurveyQuestion(question_type='Likert', \
				question_text=text, survey_page=survey_page.id, survey_id=self.survey_id)
			self.db.session.add(question)
			self.db.session.flush()

		return question

	def _find_action_target_by_typelabel(self, target_label, target_type):
		action = ActionTarget.query.filter(and_(\
			ActionTarget.target_label==target_label, \
			ActionTarget.target_type==target_type)).first()
		return action

	def _get_action_or_create(self, target_label, target_type):
		action = self._find_action_target_by_typelabel(target_label, target_type)
		if action is None:
			action = ActionTarget(target_label=target_label, target_type=target_type)
			self.db.session.add(action)
			self.db.session.flush()
		return action

	def movies_seen(self, userid:int) -> dict:
		seen = SeenItem.query.filter_by(user_id=userid).all()

		seen_dict = defaultdict(list)
		if len(seen) > 0:
			for seenitem in seen:
				seen_dict[seenitem.gallerypagenum].append(seenitem)
		else:
			seen_dict = {0: seen}

		return seen_dict

	def update_movies_seen(self, movies:list, userid:int, page_id:int, \
		gallerypage:int) -> None:

		seenmovies = [movie['id'] for movie in movies]
		seenitems = SeenItem.query.filter(SeenItem.id.in_(seenmovies)).all()
		seenids = [seenid.item_id for seenid in seenitems]

		newitems = [SeenItem(item_id=movieid, user_id=userid, page=page_id, \
			gallerypagenum=gallerypage, survey_id=self.survey_id)
			for movieid in seenmovies if movieid not in seenids]
		
		self.db.session.add_all(newitems)
		self.db.session.commit()

	def get_redirect_url(self, user_id:int, survey_pageid:int, requesttime:str, \
		completed=False) -> str:
		if completed == False:
			raise InvalidRequestException
		
		user = User.query.filter_by(id=user_id).first()
		if user is None:
			raise InvalidUserException

		survey_page = self._get_survey_pages()[survey_pageid-1]
		time = self.parse_datetime(requesttime)
		survey_response = SurveyResponse(user=user_id, survey_page=survey_page.id, \
			starttime=time, endtime=time, survey_id=self.survey_id)

		user.responses.append(survey_response)
		self.db.session.commit()

		return self.redirect_url

	def add_user_interaction(self, userid:int, pageid:int, action:str, \
		target:int, time) -> None:
		pass

	def sync_activity(self, userid:int, page_width:int, page_height:int, \
		page_id:int, activity_data:list) -> None:

		# activity_base_path = 'user_interaction_data/'
		Path(self.activity_base_path + str(userid)).mkdir(parents=True, exist_ok=True)
		orderedkeys = ['clientX', 'clientY', 'pageX', 'pageY', 'timestamp']
		with open(self.activity_base_path + str(userid) + '/' + str(page_id) + \
			'.csv', 'w') as f:
			f.write(','.join(orderedkeys))
			f.write('\n')
			for line in activity_data:
				f.write(','.join([str(line[key]) for key in orderedkeys]))
				f.write('\n')

	def log_request(self, req:request):
		userid = None
		print(req.headers)

		if 'userid' in str(req.get_data()):
			userid = json.loads((req.get_data()))['userid']
		rawheader = req.headers
		useragent = req.headers['User-Agent']
		# origin = req.headers['Origin']
		origin = 'deprecated'
		# referer = req.headers['Referer']
		referer = 'deprecated'
		endpoint = req.full_path
		reqlog = RequestLog(timestamp=datetime.now(), rawheader=rawheader, \
			useragent=useragent, origin=origin, referer=referer, endpoint=endpoint,\
			user_id=userid, survey_id=self.survey_id)
		
		self.db.session.add(reqlog)
		self.db.session.commit()


	def add_platform_session(self, platform_info:dict, userid:int=None):
		platform_type = 'Prolific'
		platform_id = platform_info['prolific_pid']
		study_id = platform_info['study_id']
		session_id = platform_info['session_id']
		starttime = platform_info['start_time']
		if all(map(lambda x: len(x) > 0, [platform_id, study_id, session_id])):
			platform_sess = PlatformSession(timestamp=self.parse_datetime(starttime), \
				platform_type=platform_type, platform_id=platform_id, \
				study_id=study_id, session_id=session_id, user_id=userid, \
				survey_id=self.survey_id)
			self.db.session.add(platform_sess)
		

class Borg:
    __shared_state = {}
    def __init__(self):
        self.__dict__ = self.__shared_state


class ConditionPicker(Borg):
	idx = 0
	def __init__(self):
		super().__init__()

	@classmethod
	def get_condition_index(cls):
		if cls.idx == 5: cls.idx = 0
		cls.idx += 1
		return cls.idx 


class SurveyMeta(object):
	''' TODO
		This class allows endpoints to create Surveys, SurveyPages and Questions
	'''
	pass
