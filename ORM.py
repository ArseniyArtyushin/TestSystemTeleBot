from data import db_session
from data.test_list import TestList
from data.question_list import QuestionList
from data.result_list import ResultList
import os

# Создание файла БД, если вдруг отсутствует
if not os.path.exists('db/'):
    os.mkdir('./db')
db_session.global_init("db/main.db")  # Подключение к БД


def create_test(data):  # Функция добавления теста
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


def check_test_id(ID):  # Функция проверки существования такого ID
    db_sess = db_session.create_session()
    tests = db_sess.query(TestList).all()
    test_ids = list(map(lambda x: x.test_id, tests))
    return ID in test_ids


def get_test_information(ident):  # Функция получения информации теста
    db_sess = db_session.create_session()
    data = db_sess.query(TestList).filter(TestList.test_id == ident)
    return data[0].test_or_not, data[0].name, data[0].hashed_password


def get_questions(ident):  # Функция получения вопросов теста
    db_sess = db_session.create_session()
    data = db_sess.query(QuestionList).filter(QuestionList.test_id == ident)
    data_converted =list(map(lambda x: {'file_id': x.file_id, 'question': x.question, 'variants': x.variants.split(';'),
                                        'cor_var': x.correct_variants.split(';')}, data))
    return data_converted


def copy_result(data, cac=''):  # Функция сохранения результатов теста
    db_sess = db_session.create_session()
    res = ResultList()
    res.test_id = data['test_id']
    res.name = data['name']
    res.answers = "^^^^^^".join(list(map(lambda x: ";".join(x), data['answers'])))
    if cac:
        res.correct_count = cac
    db_sess.add(res)
    db_sess.commit()


def get_results(ident):  # Функция выдачи результатов
    db_sess = db_session.create_session()
    data = db_sess.query(ResultList).filter(ResultList.test_id == ident)
    data_converted = list(map(lambda x: {'name': x.name,
                                         'answers': list(map(lambda y: y.split(';'), x.answers.split('^^^^^^'))),
                                         'cor_ans_count': x.correct_count}, data))
    return data_converted
