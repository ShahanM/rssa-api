from pathlib import Path
import json

from flask import Flask
from db_connectors.db import db

app = Flask(__name__)

config_path = Path(__file__).parent / 'config.json'

print('Loading database path from {}'.format(config_path))
with open(config_path) as f:
	settings = json.load(f)

SURVEY_DB = settings['mysql_url']

app.config['SQLALCHEMY_DATABASE_URI'] = SURVEY_DB
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

print('Initializing Database at {}'.format(SURVEY_DB))
db.init_app(app)
from db_connectors.models.survey import *
with app.app_context():
	print('Dropping all existing tables.')
	db.drop_all()

	print('Creating tables.')
	db.create_all()

	print('Adding new Survey(title=\'rssa\'')
	survey = Survey(title='rssa')
	db.session.add(survey)
	db.session.flush()
	pages = ['Welcome', 'Consent', 'Pre Survey Page 1', 'Pre Survey Page 2', 'Pre Survey Page 3', 
		'Pre Survey Page 4', 'Instruction Summary', 'Movie Rating', 'Recommendation Rating 1', \
		'Recommendation Rating 2', 'Recommendation Pick', 'Closing RecSys', 'Post Survey Page 1', \
		'Post Survey Page 2', 'Post Survey Page 3', 'Post Survey Page 3', 'Post Survey Page 4', \
		'Post Survey Page 5', 'Post Survey Page 6', 'Post Survey Page 7', 'Demographic Info', 'Ending']
	page_type = ['welcome', 'consent_form', 'likert_form', 'likert_form', 'likert_form', 'likert_form', \
		'info', 'rating', 'rating', 'rating', 'info', 'likert_form', 'likert_form', 'likert_form', \
			'rating_familiarity', 'likert_form', 'likert_form', 'likert_form', 'demo_form', 'ending']

	survey_pages = []
	for pnum, (ptitle, ptype) in enumerate(zip(pages, page_type), 1):
		print('Adding new SurveyPage(page_num={}, page_title=\'{}\', page_type=\'{}\')'.format(pnum, ptitle, ptype))
		survey_page = SurveyPage(survey_id=survey.id, page_num=pnum, page_title=ptitle, page_type=ptype)
		survey_pages.append(survey_page)

	db.session.add_all(survey_pages)
	db.session.flush()

	conditions = ['Top N', 'Controversial', 'Hate', 'Hip', 'No Clue']
	cond_acts = ['More movies you may like', 'Movies that are controversial', 
				'Movies you may hate', 'Movies you will be among the first to try',
				'Movies we have no idea about']
	cond_exps = [
		'Beyond the top 7 movies on the left, there are the next 7 movies we \
			think you will like best.',
		'Thes movies received mixed reviews from people who are similar to you: \
			some likes them and some didin\'t.',
		'We predict that you particularly dislike these 7 movies... but we \
			we might be wrong.',
		'These movies received very few ratings, so you would be among the \
			first to try them.',
		'These are movies you may either like or dislike; we simply weren\'t \
			able to make an accurate prediction.'
		]
	survey_conds = []
	for tag, act, exp in zip(conditions, cond_acts, cond_exps):
		print('Adding experimental condition', tag)
		condition = Condition(cond_tag=tag, cond_act=act, cond_exp=exp)
		survey_conds.append(condition)

	db.session.add_all(survey_conds)
	db.session.flush()

	db.session.commit()