import os
import psycopg2

from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    Index,
    Date,
    DateTime,
    Numeric,
    BigInteger,
    String,
    ForeignKey,
    Boolean,
)


# DATABASE_URL = os.environ["BBOARD"]
DATABASE_URL = os.environ["DATABASE_URL"]
DATABASE_URL = f"postgresql{DATABASE_URL[len('postgres'):]}"
conn = psycopg2.connect(DATABASE_URL, sslmode="require")
Base = declarative_base()


class Announcement(Base):
    __tablename__ = "announcements"

    id = Column(Integer, primary_key=True)
    author = Column(String(length=100))
    title = Column(String(length=100))
    text = Column(String(length=1000))
    comment = relationship("Comment")

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


engine = create_engine(DATABASE_URL)
Base.metadata.create_all(engine)
Session = sessionmaker()
Session.configure(bind=engine)
