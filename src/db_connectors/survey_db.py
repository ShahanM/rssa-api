from datetime import datetime
import hashlib
from pathlib import Path
from collections import defaultdict

from .models.survey import FreeResponse, SeenItem, Survey, SurveyQuestion, SurveyResponse, User, \
	Rating, Score, Condition, Demography


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
	def __init__(self, db, survey_id=1, activity_base_path=None):
		self.db = db
		self.survey_id = survey_id
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

	def create_user(self, welcome_time, consent_start_time, consent_end_time):
		survey_pages = self._get_survey_pages()

		conditionPicker = ConditionPicker()

		user = User(survey_id=self.survey_id, \
			condition=conditionPicker.get_condition_index())
		self.db.session.add(user)
		self.db.session.flush()

		user_response = []

		welcome_page = survey_pages[0]
		welcome_response = SurveyResponse(user=user.id, survey_page=welcome_page.id, \
			starttime=self.parse_datetime(welcome_time), \
			endtime=self.parse_datetime(consent_start_time))

		consent_page = survey_pages[1]
		consent_response = SurveyResponse(user=user.id, survey_page=consent_page.id, \
			starttime=self.parse_datetime(consent_start_time), \
			endtime=self.parse_datetime(consent_end_time))

		user_response.append(welcome_response)
		user_response.append(consent_response)

		user.responses = user_response

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

		survey_response = SurveyResponse(user=user_id, survey_page=survey_page.id, \
			starttime=self.parse_datetime(starttime), endtime=self.parse_datetime(endtime))
		self.db.session.add(survey_response)
		self.db.session.flush()

		if 'ratings' in response_params:
			itemsids = [item.item_id for item in survey_response.ratings]
			for itemrating in response_params['ratings']:
				itemid = itemrating['item_id']
				rating = itemrating['rating']
				location = itemrating['loc']
				level = itemrating['level']
				if itemid not in itemsids:
					survey_response.ratings.append(Rating(survey_response=survey_response.id, \
						item_id=itemid, rating=rating, location=location, \
						level=level))

		if 'pick' in response_params:
			itemid = response_params['pick']
			survey_response.ratings = [Rating(survey_response=survey_response.id, \
				item_id=itemid, rating=99)]

		if 'responses' in response_params:
			for qres in response_params['responses']:
				qtext = qres['text']
				question = self._get_question_or_create(survey_page=survey_page, \
					text=qtext)
				if qres['type'] == 'likert':
					qscore = qres['val']
					score = Score(score_point=qscore, question=question.id, \
						survey_response=survey_response.id)
					question.scores.append(score)
					survey_response.scores.append(score)
				else:
					qresTxt = qres['val']
					free_res = FreeResponse(response_text=qresTxt, question=question.id, \
						survey_response=survey_response.id)
					question.responses.append(free_res)
					survey_response.responses.append(free_res)
		
		if 'demography' in response_params:
			dem = response_params['demography']
			age = dem['age']
			edu = dem['education']
			rac = dem['race']
			gen = dem['gender']
			con = dem['country']
			print(con)
			demo = Demography(age=age, education=edu, race=rac, gender=gen, \
				country=con, user_id=user.id)
			textgen = dem['textgen']
			if len(textgen) > 1:
				question = self._get_question_or_create(survey_page=survey_page, \
					text='Self identifying gender')
				free_res = FreeResponse(response_text=qresTxt, question=question.id, \
					survey_response=survey_response.id)
			self.db.session.add(demo)
			self.db.session.flush()

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
				question_text=text, survey_page=survey_page.id)
			self.db.session.add(question)
			self.db.session.flush()

		return question

	def movies_seen(self, userid:int) -> dict:
		seen = SeenItem.query.filter_by(user_id=userid).all()

		seen_dict = defaultdict(list)
		if len(seen) > 0:
			for seenitem in seen:
				seen_dict[seenitem.gallerypagenum].append(seenitem)
			# seen_dict = {seenitem.gallerypagenum: seenitem for seenitem in seen}
		else:
			seen_dict = {0: seen}

		return seen_dict

	def update_movies_seen(self, movies:list, userid:int, page_id:int, \
		gallerypage:int) -> None:

		seenmovies = [movie['id'] for movie in movies]
		seenitems = SeenItem.query.filter(SeenItem.id.in_(seenmovies)).all()
		seenids = [seenid.item_id for seenid in seenitems]

		newitems = [SeenItem(item_id=movieid, user_id=userid, page=page_id, \
			gallerypagenum=gallerypage)
			for movieid in seenmovies if movieid not in seenids]
		
		self.db.session.add_all(newitems)
		self.db.session.flush()
		self.db.session.commit()

	def get_user_code(self, user_id:int, survey_pageid:int, requesttime:str, \
		completed=False) -> str:
		if completed == False:
			raise InvalidRequestException
		
		user = User.query.filter_by(id=user_id).first()
		if user is None:
			raise InvalidUserException

		survey_page = self._get_survey_pages()[survey_pageid-1]
		time = self.parse_datetime(requesttime)
		survey_response = SurveyResponse(user=user_id, survey_page=survey_page.id, \
			starttime=time, endtime=time)

		user.responses.append(survey_response)
		self.db.session.commit()

		userstr = str(user.id) + str(user.date_created) + str(time)
		userhash = hashlib.md5(userstr.encode('utf8'))

		return str(userhash.digest()[3]) + ' ' + str(userhash.digest()[9])

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

