from datetime import datetime

from db import db


class Survey(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	title = db.Column(db.String(50), nullable=False)

	survey_users = db.relationship('User', backref='survey', \
		lazy=True)
	survey_pages = db.relationship('SurveyPage', backref='survey', \
		lazy=True)

	def __repr__(self) -> str:
		return '<Survey %r>' % self.id


pages = db.Table('pages',
	db.Column('page_id', db.Integer, db.ForeignKey('surveypage.id'), primary_key=True),
	db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True)
)


class User(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	date_created = db.Column(db.DateTime, nullable=False, \
		default=datetime.utcnow)

	survey_id = db.Column(db.Integer, db.ForeignKey('survey.id'), \
		nullable=False)

	pages_done = db.relationship('SurveyPage', secondary=pages, lazy='subquery',
		backref=db.backref('users', lazy=True))

	def __repr__(self) -> str:
		return '<User %r>' % self.id


class SurveyPage(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	page_title = db.Column(db.String(144), nullable=False)
	page_type = db.Column(db.String(36), nullable=False)

	survey_id = db.Column(db.Integer, db.ForeignKey('survey.id'), \
		nullable=False)

	ratings = db.relationship('Rating', backref='rating', \
		lazy=True)
	questions = db.relationship('SurveyQuestion', backref='surveyquestion', \
		lazy=True)

	def __repr__(self) -> str:
		return '<Survey %r>' % self.id


class Rating(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	date_created = db.Column(db.DateTime, nullable=False, \
		default=datetime.utcnow)
	movie_id = db.Column(db.Integer, nullable=False)
	rating = db.Column(db.Integer, nullable=False)

	survey_page = db.Column(db.Integer, db.ForeignKey('surveypage.id'), \
		nullable=False)


class SurveyQuestion(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	question_type = db.Column(db.String(36), nullable=False)
	question_text = db.Column(db.String(144), nullable=False)

	score = db.Column(db.Integer)
	response = db.Column(db.String(144))
	
	survey_page = db.Column(db.Integer, db.ForeignKey('surveypage.id'), \
		nullable=False)
