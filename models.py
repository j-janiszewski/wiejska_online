"""
Module with SQLAlchemy ORM models definitions.
"""
from sqlalchemy import Column, ForeignKey, ForeignKeyConstraint, Identity
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Integer, Date, Boolean, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.oracle import VARCHAR2


Base = declarative_base()


class Member(Base):
    """Member of Polish parliament during specific term.
    Composite primary key made of term number and parliamentary ID number"""

    __tablename__ = "members"
    __table_args__ = (
        ForeignKeyConstraint(["term", "club_id"], ["clubs.term", "clubs.id"]),
    )
    id = Column(Integer, primary_key=True)
    term = Column(Integer, primary_key=True)
    is_active = Column(Boolean)
    district_name = Column(VARCHAR2(255))
    district_num = Column(Integer)
    voivodeship = Column(VARCHAR2(255))
    club_id = Column(VARCHAR2(255))
    politician_id = Column(Integer, ForeignKey("politicians.id"))
    politician = relationship("Politician", backref="member")
    club = relationship("Club", backref="members")


class Politician(Base):
    """Politician who was a member of parliamaent or is an important figure on the political scene."""

    __tablename__ = "politicians"
    id = Column(Integer, Identity(start=1), primary_key=True)
    first_name = Column(VARCHAR2(255))
    second_name = Column(VARCHAR2(255))
    last_name = Column(VARCHAR2(255))


class Club(Base):
    """Parliament club."""

    __tablename__ = "clubs"
    id = Column(VARCHAR2(255), primary_key=True)
    term = Column(Integer, primary_key=True)
    name = Column(VARCHAR2(255))
    color = Column(VARCHAR2(255))


class Transfer(Base):
    """Transfer of parliament member between two clubs."""

    __tablename__ = "transfers"
    __table_args__ = (
        ForeignKeyConstraint(["term", "card_id"], ["members.term", "members.id"]),
        ForeignKeyConstraint(["term", "left"], ["clubs.term", "clubs.id"]),
        ForeignKeyConstraint(["term", "joined"], ["clubs.term", "clubs.id"]),
    )
    id = Column(Integer, Identity(start=1), primary_key=True)
    term = Column(Integer)
    card_id = Column(Integer)
    date = Column(Date)
    left = Column(VARCHAR2(255))
    joined = Column(VARCHAR2(255))


class TwitterAccount(Base):
    """Twitter account of politician, one politician can have many accounts but only one should be marked as active."""

    __tablename__ = "twitter_accounts"
    id = Column(Integer, primary_key=True)
    is_active = Column(Boolean)
    screen_name = Column(VARCHAR2(255))
    politician_id = Column(Integer, ForeignKey("politicians.id"))
    politician = relationship("Politician", backref="twitter_account")


class FollowersNumber(Base):
    """Number of followers of a given twitter account."""

    __tablename__ = "followers_number"
    account_id = Column(Integer, ForeignKey("twitter_accounts.id"), primary_key=True)
    date = Column(Date, primary_key=True)
    number_of_followers = Column(Integer)
    account = relationship("TwitterAccount", backref="followers_number")


class Tweet(Base):
    """Single tweet created by one of the twitter accounts."""

    __tablename__ = "tweets"
    id = Column(Integer, primary_key=True)
    created_at = Column(DateTime)
    text = Column(VARCHAR2(1000))
    source = Column(VARCHAR2(255))
    reply_to_status_id = Column(Integer)
    reply_to_user_id = Column(Integer)
    quoteded_text = Column(VARCHAR2(1000))
    quoteded_status_id = Column(Integer)
    quoted_user_id = Column(Integer)
    retweeted_status_id = Column(Integer)
    retweeted_user_id = Column(Integer)
    user_id = Column(Integer, ForeignKey("twitter_accounts.id"))
    account = relationship("TwitterAccount", backref="tweets")
