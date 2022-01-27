from models import Rating
from compute import predict_user_topN
from compute import predict_user_controversial_items
from compute import predict_user_hate_items
from compute import predict_user_hip_items
from compute import predict_user_no_clue_items

import time

with open('../tests/test_ratings.json', 'r') as f:
    data = eval(f.read())

funcs = {
	'top_n': predict_user_topN,
	'controversial': predict_user_controversial_items,
	'hate': predict_user_hate_items,
	'hip': predict_user_hip_items,
	'no_clue': predict_user_no_clue_items
}

ratings = [Rating(**rating) for rating in data['ratings']]

start_time = time.time()
predictions = {k: f(ratings=ratings, user_id=0) for k, f in funcs.items()}
print("All Methods : --- {:10f} seconds ---".format((time.time() - start_time)))


start_time = time.time()
predict_user_topN(ratings, 0)
print("TopN        : --- {:10f} seconds ---".format((time.time() - start_time)))

start_time = time.time()
predict_user_controversial_items(ratings, 0)
print("Controverial: --- {:10f} seconds ---".format((time.time() - start_time)))

start_time = time.time()
predict_user_hate_items(ratings, 0)
print("Will Hate   : --- {:10f} seconds ---".format((time.time() - start_time)))

start_time = time.time()
predict_user_hip_items(ratings, 0)
print("Hip Items   : --- {:10f} seconds ---".format((time.time() - start_time)))

start_time = time.time()
predict_user_no_clue_items(ratings, 0)
print("No Clue     : --- {:10f} seconds ---".format((time.time() - start_time)))