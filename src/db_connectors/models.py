from datetime import datetime

from .db import db


class Survey(db.Model):
	__tablename__ = 'survey'

	id = db.Column(db.Integer, primary_key=True, autoincrement=True)
	title = db.Column(db.String(50), nullable=False)

	survey_users = db.relationship('User', backref='survey', \
		lazy=True)
	survey_pages = db.relationship('SurveyPage', backref='survey', \
		lazy=True)

	def __repr__(self) -> str:
		return '<Survey %r>' % self.id


user_response = db.Table('user_response',
	db.Column('response_id', db.Integer, db.ForeignKey('survey_response.id'), \
		primary_key=True),
	db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True)
)


class User(db.Model):
	__tablename__ = 'user'
	salt = 144

	survey_id = db.Column(db.Integer, db.ForeignKey('survey.id'), \
		nullable=False)

	id = db.Column(db.Integer, primary_key=True, autoincrement=True)
	date_created = db.Column(db.DateTime, nullable=False, \
		default=datetime.utcnow)


	responses = db.relationship('SurveyResponse', secondary=user_response, lazy='subquery',
		backref=db.backref('users', lazy=True))

	def __repr__(self) -> str:
		return '<User %r>' % self.id

class SurveyPage(db.Model):
	__tablename__ = 'survey_page'

	survey_id = db.Column(db.Integer, db.ForeignKey('survey.id'), \
		nullable=False)

	id = db.Column(db.Integer, primary_key=True, autoincrement=True)
	
	# TODO add database level validation to avoid ordering conflict
	page_num = db.Column(db.Integer, nullable=False)

	page_title = db.Column(db.String(144), nullable=False)
	page_type = db.Column(db.String(36), nullable=False)

	questions = db.relationship('SurveyQuestion', backref='survey_question', \
		lazy=True)
	reponses = db.relationship('SurveyResponse', backref='survey_response', \
		lazy=True)

	def __repr__(self) -> str:
		return '<Survey %r>' % self.id

	
class SurveyQuestion(db.Model):
	__tablename__ = 'survey_question'

	id = db.Column(db.Integer, primary_key=True, autoincrement=True)
	question_type = db.Column(db.String(36), nullable=False)
	question_text = db.Column(db.String(144), nullable=False)

	responses = db.relationship('Response', backref='question_response', \
		lazy=True)
	scores = db.relationship('Score', backref='likert_score', \
		lazy=True)
	
	survey_page = db.Column(db.Integer, db.ForeignKey('survey_page.id'), \
		nullable=False)


class SurveyResponse(db.Model):
	__tablename__ = 'survey_response'

	id = db.Column(db.Integer, primary_key=True, autoincrement=True)
	starttime = db.Column(db.DateTime, nullable=False)
	endtime = db.Column(db.DateTime, nullable=False)

	responses = db.relationship('Response', backref='response')
	scores = db.relationship('Score', backref='score')
	ratings = db.relationship('Rating', backref='movie_rating', \
		lazy=True)

	user = db.Column(db.Integer, db.ForeignKey('user.id'), \
		nullable=False)
	survey_page = db.Column(db.Integer, db.ForeignKey('survey_page.id'), \
		nullable=False)


class Response(db.Model):
	__tablename__ = 'response'
	
	id = db.Column(db.Integer, primary_key=True, autoincrement=True)
	response_text = db.Column(db.String(144))

	question = db.Column(db.Integer, db.ForeignKey('survey_question.id'), \
		nullable=False)
	survey_response = db.Column(db.Integer, db.ForeignKey('survey_response.id'), \
		nullable=False)


class Score(db.Model):
	__tablename__ = 'score'

	id = db.Column(db.Integer, primary_key=True, autoincrement=True)
	score_point = db.Column(db.Integer)

	question = db.Column(db.Integer, db.ForeignKey('survey_question.id'), \
		nullable=False)
	survey_response = db.Column(db.Integer, db.ForeignKey('survey_response.id'), \
		nullable=False)


class Rating(db.Model):
	__tablename__ = 'rating'

	id = db.Column(db.Integer, primary_key=True, autoincrement=True)
	date_created = db.Column(db.DateTime, nullable=False, \
		default=datetime.utcnow)
	item_id = db.Column(db.Integer, nullable=False)
	rating = db.Column(db.Integer, nullable=False)

	survey_response = db.Column(db.Integer, db.ForeignKey('survey_response.id'), \
		nullable=False)
