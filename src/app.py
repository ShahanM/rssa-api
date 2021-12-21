"""

app.py

Aru Bhoop. Algorithms by Lijie Guo.
Clemson University. 7.27.2021.

Server for running the recommender algorithms. See
`models.py` for information about the input and
outputs.

"""

from pathlib import Path
import json

from flask import Flask, abort
from flask import request
from flask import render_template
from flask import Response

from flask_cors import CORS, cross_origin

from compute import predict_user_topN
from compute import predict_user_controversial_items
from compute import predict_user_hate_items
from compute import predict_user_hip_items
from compute import predict_user_no_clue_items

from models import Rating

from db_connectors.movie_db import MovieDB
from db_connectors.survey_db import SurveyDB

app = Flask(__name__)
CORS(app)
MOVIE_DB = ''
USER_DB = ''

@app.route('/')
def show_readme():
    return render_template('README.html')

@app.route('/movies', methods=['GET'])
@cross_origin(supports_credentials=True)
def get_movies():
    movie_db = MovieDB(MOVIE_DB)
    print(request);
    lim = int(request.args.get("limit"))
    page = int(request.args.get("page"))
    movies = movie_db.skiplimit(lim, page)
    return Response(json.dumps(movies), mimetype='application/json')


@app.route('/movie_previews', methods=['GET'])
def preview_movies():    
    movie_db = MovieDB(MOVIE_DB)
    movies = movie_db.skiplimit(50, 1)

    return render_template('json_viewer.html', movies=movies)

@app.route('/movies', methods=['POST'])
@cross_origin(supports_credentials=True)
def get_movie_from_ids():
    movie_db = MovieDB(MOVIE_DB)
    req = json.loads(request.data)
    idlst = req['movie_ids']

    movies = movie_db.get_movie_lst(idlist=idlst)
    return Response(json.dumps(movies), mimetype='application/json')


@app.route('/preferences', methods=['POST'])
@cross_origin(supports_credentials=True)
def predict_preferences():
    req = json.loads(request.data)
    ratings = None

    try:
        ratings = req['ratings']
    except KeyError:
        abort(400)

    # HIP - Movies you would be among the first to try
    # Double check the TopN condition (Top 20? -> left 10 -> right 10) -> "More movies you may like"
    funcs = {
        'top_n': predict_user_topN,
        'controversial': predict_user_controversial_items,
        'hate': predict_user_hate_items,
        'hip': predict_user_hip_items,
        'no_clue': predict_user_no_clue_items
    }

    ratings = [Rating(**rating) for rating in ratings]
    predictions = {k: f(ratings=ratings, user_id=0) for k, f in funcs.items()}

    return dict(preferences=predictions)


@app.route('/new_user', methods=['POST'])
@cross_origin(supports_credentials=True)
def create_new_user():
    # req = json.loads(request.data)
    # user_id = None
    
    # try:
    #     user_id = req['user_id']
    # except KeyError:
    #     abort(400)

    survey_db = SurveyDB(SURVEY_DB)
    user_id = survey_db.create_user()

    return dict({'Success': True, 'user_id': str(user_id.inserted_id)})


if __name__ == '__main__':
    config_path = Path(__file__).parent / 'config.json'
    with open(config_path) as f:
        settings = json.load(f)
    MOVIE_DB = settings['mongo_url']
    SURVEY_DB = settings['mysql_url']
    
    app.run(port=settings['port'],
            debug=settings['debug'])
