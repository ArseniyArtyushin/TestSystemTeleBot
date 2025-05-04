from data import db_session
from data.test_list import TestList
from data.question_list import QuestionList
import os

if not os.path.exists('db/'):
    os.mkdir('./db')
db_session.global_init("db/main.db")


def create_test(data):
    db_sess = db_session.create_session()
    test = TestList()
    test.test_id = data['ID']
    test.test_or_not = True if data['test_or_not'] == 'тест' else False
    test.name = data['name']
    test.hashed_password = data['password']
    db_sess.add(test)
    for quest in data['questions']:
        question = QuestionList()
        question.test_id = data['ID']
        question.file_id = quest['file_id']
        question.question = quest['question']
        question.variants = ';'.join(quest['variants'])
        question.correct_variants = ';'.join(quest['correct_variants'])
        db_sess.add(question)
    db_sess.commit()


def check_test_id(ID):
    db_sess = db_session.create_session()
    tests = db_sess.query(TestList).all()
    test_ids = list(map(lambda x: x.test_id, tests))
    return ID in test_ids
