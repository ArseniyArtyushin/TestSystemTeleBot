import sqlalchemy
from data import db_session
from data.db_session import SqlAlchemyBase
from sqlalchemy import orm


class QuestionList(SqlAlchemyBase):
    __tablename__ = 'questions'

    test_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey("test_list.test_id"))
    question_id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    file_id = sqlalchemy.Column(sqlalchemy.Integer, nullable=True)
    question = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    variants = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    correct_variants = sqlalchemy.Column(sqlalchemy.String, nullable=False)

    test = orm.relationship('TestList')

