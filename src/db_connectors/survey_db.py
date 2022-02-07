
from datetime import datetime

from .models import Survey, SurveyResponse, User, Response


class InvalidSurveyException(Exception):
	def __init__(self, message):
		super().__init__(message)


class InvalidUserException(Exception):
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

		# welcome_time = datetime.strptime(welcome_time, "%a, %d %b %Y %H:%M:%S %Z")
		# consent_start_time = datetime.strptime(consent_start_time, "%a, %d %b %Y %H:%M:%S %Z")
		# consent_end_time = datetime.strptime(consent_end_time, "%a, %d %b %Y %H:%M:%S %Z")

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
		**response_params):
		user = User.query.filter_by(id=user_id).first()
		if user is None:
			raise InvalidUserException

		survey_page = self._get_survey_pages()[survey_pageid-1] # FIXME - validate survey_page
		
		user_response = user.responses
		survey_response = SurveyResponse(user=user_id, survey_page=survey_page.id, \
			starttime=self.parse_datetime(starttime), endtime=self.parse_datetime(endtime))

		user_response.append(survey_response)
		user.responses = user_response

		self.db.session.commit()

		return user.id


class SurveyMeta(object):
	''' TODO
		This class allows endpoints to create Surveys, SurveyPages and Questions
	'''
	pass
