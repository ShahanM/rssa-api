from datetime import datetime
import hashlib

from .models import Survey, SurveyQuestion, SurveyResponse, User, \
	Rating, Score


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
	def __init__(self, db, survey_id=1):
		self.db = db
		self.survey_id = survey_id
		self.parse_datetime = lambda dtstr: datetime.strptime(dtstr, "%a, %d %b %Y %H:%M:%S %Z")

	def get_database(self):
		return self.db

	def _get_survey_pages(self):
		survey = Survey.query.filter_by(id=self.survey_id).first()
		if survey is None:
			raise InvalidSurveyException
		return list(sorted(survey.survey_pages, key=lambda page: page.page_num))

	def create_user(self, welcome_time, consent_start_time, consent_end_time):
		survey_pages = self._get_survey_pages()

		user = User(survey_id=self.survey_id)
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
				if itemid not in itemsids:
					survey_response.ratings.append(Rating(survey_response=survey_response.id, \
						item_id=itemid, rating=rating))

		if 'pick' in response_params:
			itemid = response_params['pick']
			survey_response.ratings = [Rating(survey_response=survey_response.id, \
				item_id=itemid, rating=99)]

		if 'responses' in response_params:
			for qres in response_params['responses']:
				qtext = qres['text']
				question = self._get_question_or_create(survey_page=survey_page, \
					text=qtext)
				qscore = qres['val']
				score = Score(score_point=qscore, question=question.id, \
					survey_response=survey_response.id)
				question.scores.append(score)
				survey_response.scores.append(score)

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

	def get_user_code(self, user_id, survey_pageid, requesttime, completed=False):
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
		

class SurveyMeta(object):
	''' TODO
		This class allows endpoints to create Surveys, SurveyPages and Questions
	'''
	pass

