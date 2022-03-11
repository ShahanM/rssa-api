
from pymongo import MongoClient


class MovieDB(object):
	def __init__(self, conn_str=''):
		if conn_str == '':
			print('Database Connection Error: Could load Mongo Path')

		self.conn = conn_str
		self.client = MongoClient(conn_str)
	
	def get_database(self):
		return self.client['movies']

	def skiplimit(self, page_size, page_num) -> list:
		skips = page_size * (page_num - 1)
		cursor = self.get_database()['movies'].find().skip(skips).limit(page_size)

		return self.__sanitize_movie_list(cursor)

	def __sanitize_movie_list(self, cursor) -> list:
		result_lst = []
		for x in cursor:
			x['rssa_id'] = str(x['_id'])
			del x['_id']
			x['title_year'] = x['title(year)']
			del x['title(year)']
			x['rating'] = 0
			result_lst.append(x)
		
		return result_lst

	def get_movie_lst(self, idlist) -> list:
		cursor = self.get_database()['movies'].find({'movie_id': {'$in': idlist}})

		return self.__sanitize_movie_list(cursor)
		