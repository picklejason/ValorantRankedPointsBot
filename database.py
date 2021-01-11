import os

from dotenv import load_dotenv
from sqlalchemy import create_engine, Column, Integer, BigInteger, String, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.mutable import MutableList
from sqlalchemy.orm import sessionmaker, relationship
load_dotenv()
DATABASE_URL = os.getenv('DATABASE_URL')

engine = create_engine(DATABASE_URL)
Base = declarative_base()

class User(Base):
	__tablename__ = 'users'
	id = Column('id', BigInteger, primary_key=True)
	player_id = Column('player_id', String)
	track_id = Column('track_id', BigInteger)
	match_id = Column('match_id', String)

	def __init__ (self, id):
		self.id = id

Base.metadata.create_all(bind=engine)
Session = sessionmaker(bind=engine)

def get_user(session, id):
	return session.query(User).filter_by(id=id).one_or_none()

def get_attr(id, attr):
	if not attr:
		return
	session = Session()
	for id in [id]:
		if not id:
			continue
		user = get_user(session, id)
		if hasattr(user, attr) and getattr(user, attr) != None:
			return getattr(user, attr)
	session.close()

def set_attr(id, attr, val):
	if not id or not attr or not val:
		return
	session = Session()
	user = get_user(session, id)
	if not user:
		user = User(id)
	setattr(user, attr, val)
	session.add(user)
	session.commit()
	session.close()

def set_player_id(id, player_id):
	set_attr(id, 'player_id', player_id)

def get_player_id(id):
	return get_attr(id, 'player_id')

def set_track_id(id, track_id):
	set_attr(id, 'track_id', track_id)

def get_track_id(id):
	return get_attr(id, 'track_id')

def del_track_id(id):
	if not id:
		return
	session = Session()
	user = session.query(User).filter_by(id=id).one_or_none()
	if user.track_id:
		user.track_id = None
		session.add(user)
		session.commit()
	session.close()

def set_match_id(id, match_id):
	set_attr(id, 'match_id', match_id)

def get_match_id(id):
	return get_attr(id, 'match_id')

def get_all_users():

	users = []
	session = Session()
	for user in session.query(User.id):
		users.append(user.id)
	session.close()
	return users
