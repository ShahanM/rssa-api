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
	__tablename__ = 'movie'

	id:int = db.Column(db.Integer, primary_key=True, autoincrement=True)

	movie_id:int = db.Column(db.Integer, nullable=False, unique=True)
	imdb_id:str = db.Column(db.String(144), nullable=False)
	title_year:str = db.Column(db.String(234), nullable=False)
	title:str = db.Column(db.String(234), nullable=False)
	year:int = db.Column(db.Integer, nullable=False)
	runtime:int = db.Column(db.Integer, nullable=False)
	genre:str = db.Column(db.String(144), nullable=False)
	ave_rating:float = db.Column(db.Numeric, nullable=False)
	director:str = db.Column(db.Text, nullable=False)
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

	emotions = db.relationship('MovieEmotions', back_populates='movie', \
		uselist=False)

	def __hash__(self):
		return hash(self.movie_id)

@dataclass
class MovieEmotions(db.Model):
	__bind_key__ = 'postgres'
	__tablename__ = 'movie_emotions'

	id:int = db.Column(db.Integer, primary_key=True, autoincrement=True)

	movie_id = db.Column(db.Integer, db.ForeignKey('movie.id'), \
		nullable=False, unique=True)

	anger:float = db.Column(db.Numeric, nullable=False)
	anticipation:float = db.Column(db.Numeric, nullable=False)
	disgust:float = db.Column(db.Numeric, nullable=False)
	fear:float = db.Column(db.Numeric, nullable=False)
	joy:float = db.Column(db.Numeric, nullable=False)
	surprise:float = db.Column(db.Numeric, nullable=False)
	sadness:float = db.Column(db.Numeric, nullable=False)
	trust:float = db.Column(db.Numeric, nullable=False)
	iers_count:int = db.Column(db.Integer, nullable=False)
	iers_rank:int = db.Column(db.Integer, nullable=False)

	iers_rank_group:RankGroup = db.Column('rank_group', db.ForeignKey('rank_group.id'))
	iers_rank_group_idx = db.Index(iers_rank_group, postgresql_using='hash')

	movie = db.relationship('Movie', back_populates='emotions')