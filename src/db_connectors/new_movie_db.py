import datetime
import random
from dataclasses import asdict
import functools

from sqlalchemy.sql import func

from .models.movie import Movie


class NewMovieDB(object):
	def __init__(self, db):
		self.db = db
		self.parse_datetime = lambda dtstr: datetime.\
			strptime(dtstr, "%a, %d %b %Y %H:%M:%S %Z")

	def get_database(self):
		return self.db

	def get_movies(self, lim, page_num, seen=None):
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
		seen = Movie.query\
			.filter(Movie.id.in_([item.item_id for item in seen])).all()
		seen = tuple() if seen is None else tuple(seen)

		items_to_send = []
		num_pages = int(lim/sum(page_dist[1]))
		for i in range(num_pages):
			page_num += i
			page_num = 5 if page_num > 5 else page_num
			items_to_send.extend(self._generate_page(lim, \
				sampling_weights=page_dist[page_num], seen=seen))
		print(self._generate_page.cache_info())
		return items_to_send


	@functools.lru_cache(maxsize=32)
	def _generate_page(self,  lim: int, sampling_weights: tuple, seen: tuple) -> list:
		page_items = set()
		seen = set(seen)

		for group, count in enumerate(sampling_weights, 1):
			if count == 0: continue
			random_buckets = random.choices(range(1, 7), \
				weights=[75, 65, 50, 40, 30, 25], k=count)
			for bucket in random_buckets:
				item = None
				while item is None:
					item = Movie.query.filter_by(rank_group=group, \
						year_bucket=bucket)\
						.order_by(func.random()).limit(1).first()
					if item is None:
						print(group, bucket)
						bucket += 1
						continue
					if item not in page_items and item not in seen:
						page_items.add(item)
		else:
			if len(page_items) < 15:
				excludelst = [itm.id for itm in page_items.union(seen)]
				item = Movie.query.filter(Movie.id.notin_(excludelst))\
					.order_by(func.random())\
						.limit(15 - len(page_items)).all()
				page_items.update(item)
				
		items = []
		for page_item in page_items:
			item = asdict(page_item)
			item['rating'] = 0
			item['movie_id'] = str(item['movie_id'])
			items.append(item)
		return items