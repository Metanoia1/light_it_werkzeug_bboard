import os
from datetime import datetime

import psycopg2

from pytz import timezone
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    DateTime,
    String,
    ForeignKey,
)


Base = declarative_base()


class Announcement(Base):
    __tablename__ = "announcements"

    id = Column(Integer, primary_key=True)
    author = Column(String(length=100))
    title = Column(String(length=100))
    text = Column(String(length=1000))
    created_date = Column(DateTime)
    comments = relationship("Comment", cascade="all,delete")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.created_date = timezone("Europe/Kiev").localize(datetime.now())

    def __repr__(self):
        return f"{self.title} ({self.author})"


class Comment(Base):
    __tablename__ = "comments"

    id = Column(Integer, primary_key=True)
    author = Column(String(length=100))
    text = Column(String(length=200))
    announcement_id = Column(Integer, ForeignKey("announcements.id"))

    def __repr__(self):
        return f"{self.author}"


# DATABASE_URL = os.environ["BBOARD"]
DATABASE_URL = os.environ["DATABASE_URL"]
DATABASE_URL = f"postgresql{DATABASE_URL[len('postgres'):]}"
engine = create_engine(DATABASE_URL)
Base.metadata.create_all(engine)
Session = sessionmaker()
Session.configure(bind=engine)


def connect_db():
    return psycopg2.connect(DATABASE_URL, sslmode="require")
