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
from db_connectors.models import *
with app.app_context():
	print('Dropping all existing tables.')
	db.drop_all()

	print('Creating tables.')
	db.create_all()

	print('Adding new Survey(title=\'rssa\'')
	survey = Survey(title='rssa')
	db.session.add(survey)
	db.session.flush()
	pages = ['Welcome', 'Consent', 'Instruction Summary', 'Movie Rating', 'Recommendation Rating', \
		'Recommendation Pick', 'Post Survey Page 1', 'Post Survey Page 2', 'Post Survey Page 3', \
		'Post Survey Page 3', 'Post Survey Page 4', 'Post Survey Page 5', 'Post Survey Page 6', \
		'Ending']
	page_type = ['welcome', 'consent_form', 'summary', 'rating', 'rating', 'rating', 'likert_form', \
		'likert_form', 'likert_form', 'likert_form', 'likert_form', 'likert_form', 'ending']

	survey_pages = []
	for pnum, (ptitle, ptype) in enumerate(zip(pages, page_type), 1):
		print('Adding new SurveyPage(page_num={}, page_title=\'{}\', page_type=\'{}\')'.format(pnum, ptitle, ptype))
		survey_page = SurveyPage(survey_id=survey.id, page_num=pnum, page_title=ptitle, page_type=ptype)
		survey_pages.append(survey_page)

	db.session.add_all(survey_pages)
	db.session.flush()
	db.session.commit()