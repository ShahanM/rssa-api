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

from flask import Flask, Response, abort, json, render_template, request
from flask_cors import CORS, cross_origin

from compute.community import get_discrete_continuous_coupled
from compute.rssa import RSSACompute
from db_connectors.db import db, initialize_db
from db_connectors.movie_db import MovieDB
from db_connectors.survey_db import InvalidSurveyException, SurveyDB
from models import Rating
from utils.json_utils import RssaJsonEncoder

app = Flask(__name__)
CORS(app)
app.json_encoder = RssaJsonEncoder
survey_db = None
movie_db = None

with open('config.json') as f:
    settings = json.load(f)
ACTIVITY_BASE = settings['activity_base_path']
# MOVIE_DB = settings['mongo_url']
MOVIE_DB = settings['postgres_url']
SURVEY_DB = settings['mysql_url']
SURVEY_ID = settings['survey_id']
REDIRECT_URL = settings['study_redirect_url']
SQLALCHEMY_BINDS = {
    'postgres': MOVIE_DB
}
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = SURVEY_DB
app.config['SQLALCHEMY_BINDS'] = SQLALCHEMY_BINDS
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {'encoding': 'utf-8'}

survey_db = SurveyDB(initialize_db(app), redirect_url=REDIRECT_URL, \
    activity_base_path=ACTIVITY_BASE)
movie_db = MovieDB(db)
# movie_db = MovieDB(MOVIE_DB)

rssa = RSSACompute()


@app.before_request
def before_request_callback():
    survey_db.log_request(request)


@app.route('/')
def show_readme():
    return render_template('README.html')


@app.route('/disc_cont_coupled', methods=['GET'])
@cross_origin(supports_credentials=True)
def get_discrete_cont_coupled():
    data = get_discrete_continuous_coupled()
    
    dictdata = {movie['item_id']: movie for movie in data}
    moviedata = movie_db.get_movie_from_list(movieids=list(dictdata.keys()))
    for movie in moviedata:
        dictdata[movie['movie_id']]['poster'] = movie['poster']

    data = list(dictdata.values())
    return Response(json.dumps(data), mimetype='application/json')


@app.route('/new_movies', methods=['GET'])
@cross_origin(supports_credentials=True)
def get_movies_two():
    lim = int(request.args.get('limit'))
    page = int(request.args.get('page'))
    movies = movie_db.get_movies(lim, page)

    return Response(json.dumps(movies), mimetype='application/json')


@app.route('/new_movies', methods=['POST'])
@cross_origin(supports_credentials=True)
def get_movies_for_user():
    req = json.loads(request.data)
    try:
        userid = req['userid']
        surveypageid = req['pageid']
        lim = req['limit']
        gallerypage = req['page']
        moviesubset = 'rssa'
        if 'subset' in req:
            moviesubset = req['subset']
        seen = survey_db.movies_seen(userid)
        movies: list
        loadedpages = seen.keys()
        if 0 in loadedpages or gallerypage not in loadedpages:
            print('Sending request to movie database.')
            seenflat = []
            for seenpage in seen.values():
                seenflat.extend(seenpage)
            movies = movie_db.get_movies(lim, gallerypage, seenflat, moviesubset)
            # TODO FIXME hardcoded limit
            survey_db.update_movies_seen(movies[:lim], userid, surveypageid, \
                gallerypage)
            survey_db.update_movies_seen(movies[lim:], userid, surveypageid, \
                gallerypage+1)

        else:
            print('This page was already generated, don\'t need to rebuild.')
            movies = movie_db.get_movie_from_list(\
                [seenitem.item_id for seenitem in seen[gallerypage]])
    except KeyError:
        print(req)
        abort(400)

    return Response(json.dumps(movies), mimetype='application/json')


""" TODO
    Wrap this into to a restful Recommendation resource
    POST -> return recommendations for a userid and list of movie ratings
"""
@app.route('/recommendations', methods=['POST'])
@cross_origin(supports_credentials=True)
def predict_preferences():
    req = json.loads(request.data)

    try:
        userid = req['userid']
        ratings = req['ratings']
        ratings = [Rating(**rating) for rating in ratings]

        item_count = req['count']
        moviesubset = 'rssa'
        if 'subset' in req:
            moviesubset = req['subset']

        condition = survey_db.get_condition_for_user(userid)
        left, right = rssa.get_condition_prediction(ratings, userid, \
            condition.id-1, item_count)
        leftitems = movie_db.get_movie_from_list(movieids=left, api=moviesubset)
        rightitems = movie_db.get_movie_from_list(movieids=right, api=moviesubset)

        prediction = {
            # topN
            'left': {
                'tag': 'control',
                'label': 'Movies You May Like',
                'byline': 'Among the movies in your system, we predict that \
                    you will like these 7 movies the best.',
                'items': leftitems
            },
            # Condition specific messaging
            'right': {
                'tag': condition.cond_tag,
                'label': condition.cond_act,
                'byline': condition.cond_exp,
                'items': rightitems
            }
        }
    except KeyError:
        abort(400)

    return dict(recommendations=prediction)


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
        welcome_time = req['welcomeTime']
        consent_start_time = req['consentStartTime']
        consent_end_time = req['consentEndTime']
        platform_info = req['platformInfo']
        user_id = survey_db.create_user(welcome_time, consent_start_time, \
            consent_end_time, platform_info)
    except KeyError:
        abort(400)

    return dict({'Success': True, 'user_id': str(user_id)})


@app.route('/add_survey_response', methods=['PUT'])
@cross_origin(supports_credentials=True)
def update_survey():

    req = json.loads(request.data)

    try:
        page_id = req['pageid']
        user_id = req['userid']
        page_starttime = req['starttime']
        page_endtime = req['endtime']

        response_params = req['response']

        user_id = survey_db.add_survey_reponse(user_id=user_id, \
            survey_pageid=page_id, starttime=page_starttime, \
                endtime=page_endtime, response_params=response_params)
    except KeyError as e:
        print(e)
        abort(400)


    return dict({'Success': True, 'user_id': str(user_id)})


@app.route('/sync_movement', methods=['PUT'])
@cross_origin(supports_credentials=True)
def sync_mouse_movement():

    req = json.loads(request.data)

    try:
        activity = req['mouseActivity']
        userid = req['userid']
        pageid = req['pageid']
        page_width = req['pageWidth']
        page_height = req['pageHeight']

        survey_db.sync_activity(userid, page_width, page_height, pageid, \
            activity)
    except KeyError as e:
        abort(400)

    return dict({'Success': True})


@app.route('/redirect', methods=['POST'])
@cross_origin(supports_credentials=True)
def get_completion_code():
    
    req = json.loads(request.data)

    try:
        page_id = req['pageid']
        user_id = req['userid']
        requesttime = req['requestime']
        page_starttime = req['starttime']
        response_params = req['response']
        completed = response_params['completed']
        user_id = survey_db.add_survey_reponse(user_id=user_id, \
            survey_pageid=page_id, starttime=page_starttime, \
                endtime=requesttime, response_params=response_params)
        redirect_url = survey_db.get_redirect_url(user_id=user_id, \
            survey_pageid=page_id, requesttime=requesttime, \
                completed=completed)

    except KeyError as e:
        print(e)
        abort(400)

    return dict({'redirect_url': redirect_url})


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


if __name__ == '__main__':
    app.run(port=settings['port'],
            debug=settings['debug'])
