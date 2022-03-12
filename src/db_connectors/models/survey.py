from datetime import datetime
from enum import unique
from db_connectors.db import db


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


user_condition = db.Table('user_condition',
	db.Column('condition_id', db.Integer, db.ForeignKey('study_condition.id'), \
		primary_key=True),
	db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True)
)

class Condition(db.Model):
	__tablename__ = 'study_condition'

	id = db.Column(db.Integer, primary_key=True, autoincrement=True)
	cond_tag = db.Column(db.String(144), nullable=False)
	cond_act = db.Column(db.String(144), nullable=False)
	cond_exp = db.Column(db.Text, nullable=True)

	participant = db.relationship('User', backref='user')


class User(db.Model):
	__tablename__ = 'user'
	salt = 144

	survey_id = db.Column(db.Integer, db.ForeignKey('survey.id'), \
		nullable=False)

	id = db.Column(db.Integer, primary_key=True, autoincrement=True)
	date_created = db.Column(db.DateTime, nullable=False, \
		default=datetime.utcnow)

	condition = db.Column(db.Integer, db.ForeignKey('study_condition.id'), \
		nullable=False)

	seen_items = db.relationship('SeenItem', backref='seen_item')

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

	seen_items = db.relationship('SeenItem', backref='seen_items', \
		lazy=True)
	questions = db.relationship('SurveyQuestion', backref='survey_question', \
		lazy=True)
	reponses = db.relationship('SurveyResponse', backref='survey_response', \
		lazy=True)

	interactions = db.relationship('UserInteraction', \
		backref='user_interaction', lazy=True)

	def __repr__(self) -> str:
		return '<Survey %r>' % self.id

	
class SurveyQuestion(db.Model):
	__tablename__ = 'survey_question'

	id = db.Column(db.Integer, primary_key=True, autoincrement=True)
	question_type = db.Column(db.String(36), nullable=False)
	question_text = db.Column(db.String(144), nullable=False)

	responses = db.relationship('FreeResponse', backref='question_response', \
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

	responses = db.relationship('FreeResponse', backref='free_response')
	scores = db.relationship('Score', backref='score')
	ratings = db.relationship('Rating', backref='movie_rating', \
		lazy=True)

	user = db.Column(db.Integer, db.ForeignKey('user.id'), \
		nullable=False)
	survey_page = db.Column(db.Integer, db.ForeignKey('survey_page.id'), \
		nullable=False)


class FreeResponse(db.Model):
	__tablename__ = 'free_response'
	
	id = db.Column(db.Integer, primary_key=True, autoincrement=True)
	response_text = db.Column(db.Text)

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


class SeenItem(db.Model):
	__tablename__ = 'seen_movies'

	id = db.Column(db.Integer, primary_key=True, autoincrement=True)
	item_id = db.Column(db.Integer, nullable=False)

	user_id = db.Column(db.Integer, db.ForeignKey('user.id'), \
		nullable=False)
	page = db.Column(db.Integer, db.ForeignKey('survey_page.id'), \
		nullable=False)
	
	gallerypagenum = db.Column(db.Integer, nullable=False)


class UserInteraction(db.Model):
	__tablename__ = 'user_interaction'

	id = db.Column(db.Integer, primary_key=True, autoincrement=True)
	user_id = db.Column(db.Integer, db.ForeignKey('user.id'), \
		nullable=False)
	page_id = db.Column(db.Integer, db.ForeignKey('survey_page.id'), \
		nullable=False)
	action_type = db.Column(db.String(144), nullable=False)
	
	action_target = db.Column(db.Integer, db.ForeignKey('action_target.id'), \
		nullable=False)
	timestamp = db.Column(db.DateTime, nullable=False)


class ActionTarget(db.Model):
	__tablename__ = 'action_target'

	id = db.Column(db.Integer, primary_key=True, autoincrement=True)
	target_label = db.Column(db.String(144), nullable=False)
	target_type = db.Column(db.String(144))

