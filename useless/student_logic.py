import sqlalchemy
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import declarative_base
from sqlalchemy.ext.declarative import declarative_base
from passlib.context import CryptContext


DATABASE_URL = "postgresql+psycopg2://learning_user:d1997225@localhost/learning_graph_db"