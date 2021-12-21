
from datetime import datetime
from pymongo.mongo_client import MongoClient


class SurveyDB(object):
	def __init__(self, conn_str):
		if conn_str == '':
			print('Could not load database')
		self.conn_str = conn_str
		self.client = MongoClient(conn_str)

	def get_database(self):
		return self.client['survey']

	def create_user(self):
		user_id = self.get_database()['testuser'].insert_one({
			'created_time': datetime.now(),
		})

		return user_id
