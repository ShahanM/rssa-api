"""

app.py

Aru Bhoop. Algorithms by Lijie Guo.
Clemson University. 7.27.2021.

Rewritten by Shahan (Mehtab Iqbal)
Clemson University.

Server for running the recommender algorithms. See
`models.py` for information about the input and
outputs.

"""

from ast import Num
from pathlib import Path
# import json
import re

import time
from urllib import response

from flask import Flask, abort, jsonify, json
from flask import request
from flask import render_template
from flask import Response

from flask_cors import CORS, cross_origin

from compute.community import get_discrete_continuous_coupled
from compute.rssa import RSSACompute

from compute_old import predict_user_topN
from compute_old import predict_user_controversial_items
from compute_old import predict_user_hate_items
from compute_old import predict_user_hip_items
from compute_old import predict_user_no_clue_items

from models import Rating

from utils.json_utils import RssaJsonEncoder

from db_connectors.movie_db import MovieDB
from db_connectors.survey_db import InvalidSurveyException, SurveyDB
from db_connectors.new_movie_db import NewMovieDB
from db_connectors.db import initialize_db, db
# from db_connectors.db import initialize_db as initialize_surveydb
# from db_connectors.models.movie import initialize_db as initialize_moviedb

app = Flask(__name__)
CORS(app)
app.json_encoder = RssaJsonEncoder
survey_db = None
movie_db = None

with open('config.json') as f:
    settings = json.load(f)
MOVIE_DB = settings['mongo_url']
NEW_MOVIE_DB = settings['postgres_url']
SURVEY_DB = settings['mysql_url']
SURVEY_ID = settings['survey_id']
SQLALCHEMY_BINDS = {
    'postgres': NEW_MOVIE_DB
}
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = SURVEY_DB
app.config['SQLALCHEMY_BINDS'] = SQLALCHEMY_BINDS

survey_db = SurveyDB(initialize_db(app))
new_movie_db = NewMovieDB(db)
movie_db = MovieDB(MOVIE_DB)

rssa = RSSACompute()

@app.route('/')
def show_readme():
    return render_template('README.html')


@app.route('/disc_cont_coupled', methods=['GET'])
@cross_origin(supports_credentials=True)
def get_discrete_cont_coupled():
    data = get_discrete_continuous_coupled()

    return Response(json.dumps(data), mimetype='application/json')


""" TODO
    Wrap this into a restful Movie resource
    POST -> return a list of movie objects given a list of ids
    GET  -> return a paged list of movie objects
"""
@app.route('/movies', methods=['GET'])
@cross_origin(supports_credentials=True)
def get_movies():
    lim = int(request.args.get("limit"))
    page = int(request.args.get("page"))
    movies = movie_db.skiplimit(lim, page)

    return Response(json.dumps(movies), mimetype='application/json')


@app.route('/new_movies', methods=['GET'])
@cross_origin(supports_credentials=True)
def get_movies_two():
    lim = int(request.args.get('limit'))
    page = int(request.args.get('page'))
    movies = new_movie_db.get_movies(lim, page)

    return Response(json.dumps(movies), mimetype='application/json')


@app.route('/new_movies', methods=['POST'])
@cross_origin(supports_credentials=True)
def get_movies_for_user():
    req = json.loads(request.data)
    print(req)
    try:
        userid = req['userid']
        page_id = req['pageid']
        lim = req['limit']
        page = req['page']
        seen = survey_db.movies_seen(userid)
        movies = new_movie_db.get_movies(lim, page, seen)
        survey_db.update_movies_seen(movies, userid, page_id)
    except KeyError:
        print(req)
        abort(400)

    return Response(json.dumps(movies), mimetype='application/json')


@app.route('/movies', methods=['POST'])
@cross_origin(supports_credentials=True)
def get_movie_from_ids():

    req = json.loads(request.data)
    idlst = req['movie_ids']

    movies = movie_db.get_movie_lst(idlist=idlst)
    return Response(jsonify(movies), mimetype='application/json')


""" TODO
    This can be thrown out
"""
@app.route('/movie_previews', methods=['GET'])
def preview_movies():

    movies = movie_db.skiplimit(50, 1)

    return render_template('json_viewer.html', movies=movies)


""" TODO
    Wrap this into to a restful Recommendation resource
    POST -> return recommendations for a userid and list of movie ratings
"""
@app.route('/recommendations', methods=['POST'])
@cross_origin(supports_credentials=True)
def predict_preferences():
    req = json.loads(request.data)

    item_count = 7

    funcs = {
        0: ('top_n', predict_user_topN, 'Movies We Think You May Like'),
        1: ('controversial', predict_user_controversial_items, \
            'Movies We Think are Controversial to Your Preference'),
        2: ('hate', predict_user_hate_items, 'Movies We Think You May Hate'),
        3: ('hip', predict_user_hip_items, \
            'Movies You We Think May Be Among the First to Try '),
        4: ('no_clue', predict_user_no_clue_items, \
            'Movies We Have No Idea About')
    }

    try:
        userid = req['userid']
        ratings = req['ratings']
        ratings = [Rating(**rating) for rating in ratings]
        condition = int(userid)%5
        if condition == 0:
            topn = predict_user_topN(ratings=ratings, user_id=userid, \
                numRec=item_count*2)
            topn = movie_db.get_movie_lst(idlist=topn)
            prediction = {
                # topN
                'left': {
                    'label': 'Movies We Think You May Like', 'items': topn[:item_count]
                },
                # moreTopN
                'right': {
                    'label': 'More Movies We Think You May Like', \
                        'items': topn[item_count:]
                }
            }
        else:
            topn = predict_user_topN(ratings=ratings, user_id=userid, \
                numRec=item_count)
            topn = movie_db.get_movie_lst(idlist=topn)

            rightitems = funcs[condition][1](ratings=ratings, user_id=userid, \
                numRec=item_count)
            rightitems = movie_db.get_movie_lst(idlist=rightitems)
            prediction = {
                # topN
                'left': {
                    'label': 'Movies You May Like', 'items': topn
                },
                # Condition specific messaging
                'right': {
                    'label': funcs[condition][2],
                    'items': rightitems
                }
            }
    except KeyError:
        abort(400)

    # TODO Break this into conditionals to save compute cost
    # HIP - Movies you would be among the first to try
    # Double check the TopN condition (Top 20? -> left 10 -> right 10) -> "More movies you may like"
    # funcs = {
    #     'top_n': predict_user_topN,
    #     'controversial': predict_user_controversial_items,
    #     'hate': predict_user_hate_items,
    #     'hip': predict_user_hip_items,
    #     'no_clue': predict_user_no_clue_items
    # }

    # predictions = {k: f(ratings=ratings, user_id=0) for k, f in funcs.items()}

    return dict(recommendations=prediction)


""" TODO
    Wrap this into a restful Survey resource
    POST -> New Survey
    GET  -> return list of Survey for authenticated user
"""
@app.route('/new_survey', methods=['POST'])
@cross_origin(supports_credentials=True)
def create_new_survey():

    # TODO This should be implemented for the framework deploy

    abort(401)


""" TODO
    Wrap this into a restful SurveyPage resource
    POST -> New survey page for a given survey id
    GET  -> return a list of survey pages for a given survey id
"""
@app.route('/new_survey_page', methods=['POST'])
@cross_origin(supports_credentials=True)
def create_new_page():

    # TODO This is for the page building form in the framework deploy

    abort(401)


""" TODO
    Wrap this into a restful User resource
    POST -> create a new user at the beginning of the survey
    PUT  -> Update entries as a user progresses through the survey
"""
@app.route('/new_user', methods=['POST'])
@cross_origin()
def create_new_user():

    req = json.loads(request.data)

    try:
        # survey_id = req['survey_id']
        welcome_time = req['welcomeTime']
        consent_start_time = req['consentStartTime']
        consent_end_time = req['consentEndTime']
        user_id = survey_db.create_user(welcome_time, consent_start_time, \
            consent_end_time)
    except KeyError:
        abort(400)

    return dict({'Success': True, 'user_id': str(user_id)})


@app.route('/add_survey_response', methods=['PUT'])
@cross_origin(supports_credentials=True)
def update_survey():

    req = json.loads(request.data)

    try:
        # survey_id = req['survey_id']
        page_id = req['pageid']
        user_id = req['userid']
        page_starttime = req['starttime']
        page_endtime = req['endtime']

        response_params = req['response']

        user_id = survey_db.add_survey_reponse(user_id=user_id, \
            survey_pageid=page_id, starttime=page_starttime, \
                endtime=page_endtime, response_params=response_params)
    except KeyError as e:
        abort(400)


    return dict({'Sucess': True, 'user_id': str(user_id)})


@app.route('/completionCode', methods=['POST'])
@cross_origin(supports_credentials=True)
def get_completion_code():
    
    req = json.loads(request.data)

    try:
        page_id = req['pageid']
        user_id = req['userid']
        requesttime = req['requestime']
        completed = req['completed']

        user_code = survey_db.get_user_code(user_id=user_id, \
            survey_pageid=page_id, requesttime=requesttime, \
                completed=completed)

    except KeyError as e:
        print(e)
        abort(400)

    return dict({'user_code': str(user_code)})


if __name__ == '__main__':
    # host='0.0.0.0'
    app.run(port=settings['port'],
            debug=settings['debug'])
