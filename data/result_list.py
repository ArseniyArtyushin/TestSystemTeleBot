import sqlalchemy
from data import db_session
from data.db_session import SqlAlchemyBase
from sqlalchemy import orm


class ResultList(SqlAlchemyBase):
    __tablename__ = 'results'

    test_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey("test_list.test_id"))
    user_id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    name = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    answers = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    correct_count = sqlalchemy.Column(sqlalchemy.Integer, nullable=True)

    test = orm.relationship('TestList')
