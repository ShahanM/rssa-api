from dataclasses import dataclass

from db_connectors.db import db


@dataclass
class RankGroup(db.Model):
	__bind_key__ = 'postgres' 
	__tablename__ = 'rank_group'

	id:int = db.Column(db.Integer, primary_key=True, autoincrement=True)
	group_label:str = db.Column(db.String(144), nullable=False)


@dataclass
class Movie(db.Model):
	__bind_key__ = 'postgres'
	__tablename__ = 'movies'

	id:int = db.Column(db.Integer, primary_key=True, autoincrement=True)

	movie_id:int = db.Column(db.Integer, nullable=False)
	imdb_id:int = db.Column(db.Integer, nullable=False)
	title_year:str = db.Column(db.String(234), nullable=False)
	title:str = db.Column(db.String(234), nullable=False)
	year:int = db.Column(db.Integer, nullable=False)
	runtime:int = db.Column(db.Integer, nullable=False)
	genre:str = db.Column(db.String(144), nullable=False)
	ave_rating:float = db.Column(db.Numeric, nullable=False)
	director:str = db.Column(db.String(144), nullable=False)
	writer:str = db.Column(db.Text, nullable=False)
	description:str = db.Column(db.Text, nullable=False)
	cast:str = db.Column(db.Text, nullable=False)
	poster:str = db.Column(db.String(234), nullable=False)
	count:int = db.Column(db.Integer, nullable=False)
	rank:int = db.Column(db.Integer, nullable=False)

	rank_group:RankGroup = db.Column('rank_group', db.ForeignKey('rank_group.id'))
	rank_group_idx = db.Index(rank_group, postgresql_using='hash') 

	year_bucket:int = db.Column(db.Integer, nullable=False)
	year_bucket_idx = db.Index(year_bucket, postgresql_using='hash')

	movie_id_idx = db.Index(movie_id, postgresql_using='tree')

	def __hash__(self):
		return hash(self.movie_id)
