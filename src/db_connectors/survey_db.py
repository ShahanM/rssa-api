
from datetime import datetime

from .models import Survey, SurveyResponse, User, Response


class InvalidSurveyException(Exception):
	def __init__(self, message):
		super().__init__(message)


class SurveyDB(object):
	def __init__(self, db, survey_id=1):
		self.db = db
		self.survey_id = survey_id
		self.survey_pages = []

	def get_database(self):
		return self.db

	def create_user(self, welcome_time, consent_start_time, consent_end_time):
		survey = Survey.query.filter_by(id=self.survey_id).first()
		if survey is None:
			raise InvalidSurveyException
		self.survey_pages = sorted(survey.survey_pages, key=lambda page: page.page_num)

		welcome_time = datetime.strptime(welcome_time, "%a, %d %b %Y %H:%M:%S %Z")
		consent_start_time = datetime.strptime(consent_start_time, "%a, %d %b %Y %H:%M:%S %Z")
		consent_end_time = datetime.strptime(consent_end_time, "%a, %d %b %Y %H:%M:%S %Z")

		user = User(survey_id=self.survey_id)
		self.db.session.add(user)
		self.db.session.flush()

		user_response = []
		
		# FIXME
		welcome_page = self.survey_pages[0]
		welcome_response = SurveyResponse(user=user.id, survey_page=welcome_page.id, \
			starttime=welcome_time, endtime=consent_start_time)

		# FIXME
		consent_page = self.survey_pages[1]
		consent_response = SurveyResponse(user=user.id, survey_page=consent_page.id, \
			starttime=consent_start_time, endtime=consent_end_time)
		
		# # FIXME
		# consent_question = SurveyQuestion.query.filter_by(id=)
		# response = Response(survey_response=consent_response.id, question=consent_question.id)
		# response.response_text = 'ACCEPT'

		user_response.append(welcome_response)
		user_response.append(consent_response)

		user.responses = user_response

		self.db.session.commit()

		return user.id


class SurveyMeta(object):
	''' TODO
		This class allows endpoints to create Surveys, SurveyPages and Questions
	'''
	pass
