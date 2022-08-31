import datetime
import random
from collections import defaultdict
from dataclasses import asdict

from sqlalchemy import and_
from sqlalchemy.sql import func

from .models.movie import Movie, MovieEmotions


class MovieDB(object):
	def __init__(self, db):
		self.db = db
		self.parse_datetime = lambda dtstr: datetime.\
			strptime(dtstr, "%a, %d %b %Y %H:%M:%S %Z")

		self.movie_idx_dict = self._build_hash('./db_connectors/cache/movie_id_lookup.csv')
		self.iers_movie_idx_dict = self._build_hash('./db_connectors/cache/iers_movie_id_lookup.csv')

	def _build_hash(self, filepath):
		hashvar = {
			1: defaultdict(list), 2:defaultdict(list), \
			3: defaultdict(list), 4: defaultdict(list), 5: defaultdict(list), \
			6: defaultdict(list)}
		with open(filepath, 'r') as f:
			next(f)
			for line in f:
				movie_id, rank_group, year_bucket = line.split(',')
				hashvar[int(rank_group)][int(year_bucket)].append(int(movie_id))
		return hashvar

	def get_database(self):
		return self.db

	def get_movies(self, lim, page_num, seen=None, api='rssa'):
		'''
			1: {1: 0, 2: 3, 3: 3, 4: 3, 5: 3, 6: 3},
			2: {1: 1, 2: 4, 3: 4, 4: 2, 5: 2, 6: 2},
			3: {1: 3, 2: 5, 3: 5, 4: 1, 5: 1, 6: 0},
			4: {1: 4, 2: 5, 3: 6, 4: 0, 5: 0, 6: 0},
			5: {1: 4, 2: 6, 3: 5, 4: 0, 5: 0, 6: 0}
		'''

		page_dist = {
			1: (0, 3, 3, 3, 3, 3),
			2: (1, 4, 4, 2, 2, 2),
			3: (3, 5, 5, 1, 1, 0),
			4: (4, 5, 6, 0, 0, 0),
			5: (4, 6, 5, 0, 0, 0)
		}

		ers = api == 'ers'
		if seen is None:
			seen = tuple()
		else:
			seen = tuple([item.item_id for item in seen])

		items_to_send = []
		num_pages = int(lim/sum(page_dist[1]))
		for i in range(num_pages):
			page_num += i
			page_num = 5 if page_num > 5 else page_num
			items_to_send.extend(self._generate_page(lim, \
				sampling_weights=page_dist[page_num], seen=seen, \
					pagenum=page_num, ers=ers))
			
		return self.get_movie_from_list(items_to_send, ers)

	def _generate_page(self,  lim: int, sampling_weights: tuple, seen: tuple, \
		pagenum:int, ers:bool) -> list:
		page_items = set()
		seen = set(seen)
		idxmap = self.iers_movie_idx_dict if ers else self.movie_idx_dict
		
		print('Building page for user')
		for group, count in enumerate(sampling_weights, 1):
			if count == 0: continue
			random_buckets = random.choices(range(1, 7), \
				weights=[75, 65, 50, 40, 30, 25], k=count)
			for bucket in random_buckets:
				itemidx = None
				trialcount = 0
				while itemidx is None:
					if len(idxmap[group][bucket]) > 0:
						itemidx = random.choice(idxmap[group][bucket])
					if itemidx is None or trialcount > 5:
						print('Could not find movie in bucket {} with {} \
							tries. Moving to next bucket.'\
								.format(bucket, trialcount))
						bucket += 1
						continue
					if itemidx not in page_items and itemidx not in seen:
						page_items.add(itemidx)
					else:
						trialcount += 1
		else:
			if len(page_items) < lim:
				excludelst = page_items.union(seen)
				while len(page_items) < lim:
					group, bucket = random.choices(range(2, 7), k=2)
					if len(idxmap[group][bucket]) > 0:
						filleritm = random.choice(idxmap[group][bucket])
						if filleritm not in excludelst:
							page_items.add(filleritm)

		return page_items

	def get_movie_from_list(self, movieids:list, api:str='rssa') -> list:
		ers = api == 'ers'
		movies = Movie.query.filter(Movie.movie_id.in_(movieids)).all()

		return self._prep_to_send(movies, ers)

	def _prep_to_send(self, movielist, ers):
		items = []
		for page_item in movielist:
			item = asdict(page_item)
			if page_item.emotions is not None and ers:
				emotions = asdict(page_item.emotions)
				item = {**item, **emotions}
			item['rating'] = 0
			item['movie_id'] = str(item['movie_id'])
			items.append(item)
		
		return items
