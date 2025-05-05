import sqlalchemy
from data.db_session import SqlAlchemyBase
from sqlalchemy import orm


class TestList(SqlAlchemyBase):  # Класс таблицы тестов
    __tablename__ = 'test_list'

    test_id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    test_or_not = sqlalchemy.Column(sqlalchemy.Boolean)
    name = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    hashed_password = sqlalchemy.Column(sqlalchemy.String, nullable=False)

    question = orm.relationship("QuestionList", back_populates='test')
