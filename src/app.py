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

from compute import predict_user_topN
from compute import predict_user_controversial_items
from compute import predict_user_hate_items
from compute import predict_user_hip_items
from compute import predict_user_no_clue_items

from models import Rating

app = Flask(__name__)


@app.route('/preferences', methods=['POST'])
def predict_preferences():
    req = request.json
    ratings = None

    try:
        ratings = req['ratings']
    except KeyError:
        abort(400)

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


if __name__ == '__main__':
    config_path = Path(__file__).parent / 'config.json'
    with open(config_path) as f:
        settings = json.load(f)
    app.run(port=settings['port'],
            debug=settings['debug'])
