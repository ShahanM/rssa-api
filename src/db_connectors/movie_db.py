import datetime
import random
from dataclasses import asdict
import functools

from sqlalchemy import and_
from sqlalchemy.sql import func

from .models.movie import Movie, MovieEmotions


class MovieDB(object):
	def __init__(self, db):
		self.db = db
		self.parse_datetime = lambda dtstr: datetime.\
			strptime(dtstr, "%a, %d %b %Y %H:%M:%S %Z")

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
		seen = Movie.query\
			.filter(Movie.id.in_([item.item_id for item in seen])).all()
		seen = tuple() if seen is None else tuple(seen)

		items_to_send = []
		num_pages = int(lim/sum(page_dist[1]))
		for i in range(num_pages):
			page_num += i
			page_num = 5 if page_num > 5 else page_num
			items_to_send.extend(self._generate_page(lim, \
				sampling_weights=page_dist[page_num], seen=seen, \
					pagenum=page_num, ers=ers))
		print(self._generate_page.cache_info())
		return items_to_send


	@functools.lru_cache(maxsize=64)
	def _generate_page(self,  lim: int, sampling_weights: tuple, seen: tuple, \
		pagenum:int, ers:bool) -> list:
		page_items = set()
		seen = set(seen)
		print('Building page for user')
		for group, count in enumerate(sampling_weights, 1):
			if count == 0: continue
			random_buckets = random.choices(range(1, 7), \
				weights=[75, 65, 50, 40, 30, 25], k=count)
			for bucket in random_buckets:
				item = None
				trialcount = 0
				while item is None:
					item = self._get_ers_item(group, bucket) \
						if ers else self._get_rssa_item(group, bucket)
					if item is None or trialcount > 5:
						print('Could not find movie in bucket {} with {} \
							tries. Moving to next bucket.'\
								.format(bucket, trialcount))
						bucket += 1
						continue
					if item not in page_items and item not in seen:
						page_items.add(item)
					else:
						trialcount += 1
		else:
			if len(page_items) < lim:
				excludelst = [itm.id for itm in page_items.union(seen)]
				items = self._get_ers_filler(excludelst, page_items, lim) \
					if not ers else self._get_rssa_fillers(excludelst, page_items, lim)
				page_items.update(items)
				
		return self._prep_to_send(page_items, ers)

	
	def get_movie_from_list(self, movieids:list, api:str='rssa') -> list:
		ers = api == 'ers'
		movies = Movie.query.filter(Movie.movie_id.in_(movieids)).all()

		return self._prep_to_send(movies, ers)

	def _get_ers_item(self, group, bucket):
		return Movie.query.filter(and_(\
					Movie.emotions != None,
					Movie.emotions.has(MovieEmotions.iers_rank_group==group), \
					Movie.year_bucket==bucket \
				))\
				.order_by(func.random()).limit(1).first()

	def _get_rssa_item(self, group, bucket):
		return Movie.query.filter_by(rank_group=group, year_bucket=bucket)\
					.order_by(func.random()).limit(1).first()

	def _get_ers_filler(self, excludelst, page_items, lim):
		return Movie.query.filter(and_(\
					Movie.id.notin_(excludelst),
					Movie.emotions != None
				))\
				.order_by(func.random())\
				.limit(lim - len(page_items)).all()

	def _get_rssa_fillers(self, excludelst, page_items, lim):
		return Movie.query.filter(Movie.id.notin_(excludelst))\
					.order_by(func.random())\
					.limit(lim - len(page_items)).all()


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