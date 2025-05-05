import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.enums import ParseMode
from aiogram.types import ReplyKeyboardRemove, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, \
    InlineKeyboardButton, CallbackQuery, Message
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from pyexpat.errors import messages
from sqlalchemy.util import await_fallback
from ORM import *
import random

from config import BOT_TOKEN  # Импортируем токен бота

dp = Dispatcher()


# Создание класса состояний для добавления теста/опроса
class TestCreating(StatesGroup):
    test_or_not = State()
    name = State()
    password = State()
    questions = State()


# Создание класса состояний для прохождения теста/опроса
class TestPassing(StatesGroup):
    test_id_check = State()
    name = State()
    tasks = State()
    multi_answer = State()
    finish = State()


# Создание класса состояний для проверки результатов теста/опроса
class ResultCheck(StatesGroup):
    test_id_check = State()
    password_check = State()
    res_ch = State()


# Основная функция, запускает бота
async def main():
    bot = Bot(token=BOT_TOKEN)
    await dp.start_polling(bot)


# Асинхронная функция для динамического создания inline клавиатуры. Принимает названия клавиш
async def inline_keyboard_create(variants):
    keyboard = InlineKeyboardBuilder()
    for variant in variants:
        keyboard.add(InlineKeyboardButton(text=variant, callback_data=variant))
    return keyboard.adjust(2).as_markup()


# Базовая reply клавиатура. Выкидывается при возвращении в начальное состояние
base_reply_keyboard = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text='/admin'), KeyboardButton(text='/start_test')],
                                                    [KeyboardButton(text='/help')]],
                                          resize_keyboard=True, one_time_keyboard=True)

# Базовая inline клавиатура. Кнопка возврата в начальное состояние
base_inline_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Вернуться назад', callback_data='cancel_test_start')]
])


@dp.message(Command('start'))  # Обработчик базовой команды /start
async def start_command(message: Message):
    await message.reply(
        "Здравствуйте! Я бот для тестов/опросов. Вы можете открыть панель администратора, чтобы создать тест или "
        "посмотреть его результаты, либо же пройти тест, если с Вами уже поделились его ID. Если остались вопросы, "
        "то можете воспользоваться меню помощи, нажав на соответствующую кнопку на клавиатуре ниже.",
        reply_markup=base_reply_keyboard)


@dp.message(Command('help'))  # Обработчик базовой команды /help
async def help_command(message: Message):
    await message.reply("Для начала работы, в выпадающей клавиатуре необходимо выбрать одну из двух команд: /admin или "
                        "/start_test\n1) Режим /admin:\n    В данном режиме Вы можете создать тест или посмотреть "
                        "результаты тех, кто его уже прошел. При выборе режима создания теста, его ID определится "
                        "самостоятельно, Вам нужно будет лишь придумать имя и пароль, чтобы в дальнейшем используя ID и"
                        " пароль можно было посмотреть результаты тестируемых. Далее нужно выбрать, что Вы хотите "
                        "создать: тест или опрос? Разница в том, что тест подразумевает заведомо правильный(ые) "
                        "ответ(ы) и в результатах помимо самих ответов, будет указываться количество правильных ответов"
                        " тестируемого. В опросе же не подразумевается заведомо правильных ответов и можно посмотреть"
                        " только выбранный ответ. Затем Вы сможете создавать вопросы, добавляя текст, варианты ответа"
                        " и, при желании, медиафайлы. Когда Вы закончите создавать вопросы, нужно будет написать "
                        "команду выбрать соответствующую кнопку на выпадающей клавиатуре и завершить создание теста.\n "
                        "   В режиме просмотра результатов у Вас будет "
                        "выбор из пользователей, прошедших тестирование. Нажав на конкретного, Вы получите сообщение с"
                        " его результатами.\n2) Режим /start_test:\n    Этот режим подразумевает, что кто-то уже создал"
                        " тест и поделился с Вами его ID для прохождения. Для начала нужно ввести ID теста и свое имя."
                        " Затем Вам предлагаются вопросы(медиафайлы и выбор ответов при наличии), пока они не "
                        "закончатся. Если это был тест, то в итоге выводится количество правильных ответов, если же "
                        "опрос, то данные просто сохраняются.")


@dp.message(Command('admin'))  # Обработчик вызова режима admin для создания теста или просмотра результатов
async def admin_command(message: Message, state: FSMContext):
    inline_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='Создать тест/опрос', callback_data='create_test'),
         InlineKeyboardButton(text='Посмотреть результаты', callback_data='check_res')],
        [InlineKeyboardButton(text='Вернуться назад', callback_data='cancel_test_start')]
    ])
    await state.clear()  # Очищает все текущие состояния и их data
    await message.answer('Выберите, что Вы хотите сделать.', reply_markup=inline_keyboard)


@dp.callback_query(F.data == 'create_test')  # Вызывается при нажатии кнопки с callback_data == 'create_test'
async def process_callback_create_test(callback: CallbackQuery, state: FSMContext):
    inline_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='Тест', callback_data='test'),
         InlineKeyboardButton(text='Опрос', callback_data='not_test')]
    ])
    await callback.answer()  # Отжимает нажатую inline кнопку
    await state.clear()
    await state.set_state(TestCreating.test_or_not)  # Устанавливает новое состояние
    await callback.message.answer(
        'Выберите, какой тип тестирования Вы хотите создать. Разница в том, '
        'что тест подразумевает правильный(ые) ответ(ы), а опрос нет.',
        reply_markup=inline_keyboard)


@dp.callback_query(F.data == 'test', TestCreating.test_or_not)  # Вызывается при состоянии test_or_not и кнопка "тест"
async def process_callback_create_test(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    test_id = random.randint(111111, 999999)  # Генерируется рандомный шестизначный test_id
    while check_test_id(test_id):  # Проверка, что test_id уникальный, и если нет, то придумывает новый
        test_id = random.randint(111111, 999999)
    await state.update_data(test_or_not='тест', ID=test_id)  # Обновляет данные состояния, добавляет test_id
    await state.set_state(TestCreating.name)  # Опять меняет состояние
    await callback.message.answer('Введите название для Вашего теста.', reply_markup=ReplyKeyboardRemove())


@dp.callback_query(F.data == 'not_test', TestCreating.test_or_not)  # Вызывается, если выбрали не тест, а опрос
async def process_callback_create_test(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    test_id = random.randint(111111, 999999)  # Аналогично предыдущей функции, но уже не для теста, а для опроса
    while check_test_id(test_id):
        test_id = random.randint(111111, 999999)
    await state.update_data(test_or_not='опрос', ID=test_id)
    await state.set_state(TestCreating.name)
    await callback.message.answer('Введите название для Вашего опроса.')


@dp.message(TestCreating.name)  # При отправке сообщения в новом состоянии: ожидание названия теста
async def name_creating(message: Message, state: FSMContext):
    name = message.text
    if not name:  # Проверка, что отправили именно текстовое сообщение, а не фотку или тд
        await message.answer('Пожалуйста, отправьте название одним текстовым сообщением.')
    else:
        await state.update_data(name=name)  # Добавление в data названия теста
        await state.set_state(TestCreating.password)  # И снова меняем состояние
        await message.answer(f'Введите пароль, чтобы позже можно было посмотреть результаты.')


@dp.message(TestCreating.password)  # При отправке сообщения в состоянии ожидания пароля
async def password_creating(message: Message, state: FSMContext):
    # Новая клавиатура добавляется
    reply_keyboard = [[KeyboardButton(text='Удалить вопрос'), KeyboardButton(text='Завершить добавление вопросов')]]
    keyboard = ReplyKeyboardMarkup(keyboard=reply_keyboard, resize_keyboard=True, one_time_keyboard=False)
    password = message.text
    data = await state.get_data()  # Получаем уже существующие данные
    # Текст, который добавляется только если это тест
    test_text = ('После того, как Вы указали все варианты ответа, опять поставьте ^^ и '
                 'начните перечислять правильные варианты ответа так же через ; .')
    # Основной текст с инструкциями к пользованию
    msg = (f'ID {data["test_or_not"]}а: {data["ID"]}\n'
           f'Название: {data["name"]}\nПароль: {password}\n\n'
           f'Теперь Вы можете добавлять вопросы. Для этого достаточно написать сообщением текст вопроса, '
           f'после этого поставить символ ^^, показывающий, что текст вопроса закончился и далее пойдут '
           f'варианты ответа. Потом перечисляете варианты ответа, разделяя их знаком ; .Если в данном '
           f'вопросе требуется вписать ответ, а не выбрать, то вместо вариантов ответа нужно поставить '
           f'-  . {test_text if data["test_or_not"] == "тест" else ""} При желании, можно добавить к '
           f'вопросу фотографию. Когда Вы закончите, просто отправьте это сообщение. Бот же отправит '
           f'то, как этот вопрос будет выглядеть у человека, проходящего этот {data["test_or_not"]}. Если'
           f' все устраивает, просто отправляйте следующий вопрос, если же нет, то можете '
           f'выбрать соответствующую кнопку на клавиатуре ниже, чтобы удалить вопрос. Когда Вы закончите'
           f' добавлять вопросы, нажмите на той же клавиатуре снизу "завершить добавление вопросов".')
    if not password:  # Та же проверка, что отправили именно текст
        await message.answer('Пожалуйста, отправьте пароль одним текстовым сообщением.')
    else:
        await state.update_data(password=password)  # Добавляет в data пароль
        await state.set_state(TestCreating.questions)  # Обновляет состояние
        await message.answer(msg, reply_markup=keyboard)
    print(await state.get_data(), await state.get_state())  # Пишет текущую дату и состояние. Удобно для тестов


@dp.message(TestCreating.questions)  # Собственно, главный блок в создании теста. Добавление вопросов
async def question_add(message: Message, state: FSMContext):
    # Сюда записывает уже существующие вопросы, если их уже добавляли
    questions = (await state.get_data())['questions'] if 'questions' in await state.get_data() else []
    if message.text == 'Удалить вопрос':  # Перехват запроса на удаление вопроса
        if not questions:  # Проверка, а вопросы-то есть, чтобы удалять?
            await message.answer('Вы еще не добавили вопросов.')
        else:
            await state.update_data(questions=questions[:-1])  # Обновляет список вопросов без последнего
            await message.answer('Крайний вопрос был удален.')
    elif message.text == 'Завершить добавление вопросов':  # Перехват запроса на завершения добавления вопросов
        current_data = await state.get_data()  # Перехватывает дату в целом, чтобы потом записать в БД
        await state.clear()  # Очищает состояния
        if questions:  # Если вопросы были, то сохраняет тест
            await message.answer(f'Создание {current_data["test_or_not"]}а завершено, вопросы сохранены.',
                                 reply_markup=base_reply_keyboard)
            create_test(current_data)  # Функция для ORM для записи в БД
        else:  # Если вопросов не было, то отменяет добавление теста/опроса
            await message.answer(f'Создание {current_data["test_or_not"]}а отменено.', reply_markup=base_reply_keyboard)
    else:
        # Если есть фото, то записывает его ID
        file_id = str(message.photo[-1]).split()[0].split("'")[1] if message.photo else ''
        text = message.text if message.text else message.caption if message.caption else ''  # Записывает текст
        test_or_not = (await state.get_data())['test_or_not']
        # Деление текста на вопрос, варианты ответа и правильные варианты ответа
        question_text, variants = text.split('^^')[0], text.split('^^')[1].split(';') if len(
            text.split('^^')) > 1 else []
        correct_variants = text.split('^^')[2].split(';') \
            if test_or_not == 'тест' and len(text.split('^^')) == 3 else []
        variants = list(filter(lambda x: x, variants))  # Выкидывает пустые варианты
        correct_variants = list(filter(lambda x: x, correct_variants))  # Выкидывает пустые корректные варианты
        # Если тест, то проверяет, указаны ли правильные варианты ответа
        if (test_or_not == 'тест' and
                ((len(correct_variants) == 1 and (not correct_variants[0])) or not correct_variants)):
            await message.answer('В режиме создания теста необходимо указать правильный вариант ответа.')
        elif not question_text:  # Проверка, а есть ли вообще текст вопроса?
            await message.answer('Пожалуйста, напишите текст вопроса.')
        elif len(variants) == 1 and variants[0] != '-':  # Проверка на количество вариантов ответа.
            await message.answer('Пожалуйста, укажите больше одного варианта ответа.')
        elif file_id:
            if len(variants) > 1:
                # Вопрос, если есть фото и несколько вариантов ответа
                await message.answer_photo(photo=file_id, caption=question_text,
                                           reply_markup=await inline_keyboard_create(variants))
            else:
                # Вопрос, если фото и нет вариантов ответа
                await message.answer_photo(photo=file_id, caption=question_text)
            # Добавляет вопрос в список вопросов
            await state.update_data(questions=questions + [{'file_id': file_id if file_id else '',
                                                            'question': question_text, 'variants': variants,
                                                            'correct_variants': correct_variants}])
        else:
            # То же самое, только без фото
            if len(variants) > 1:
                await message.answer(question_text, reply_markup=await inline_keyboard_create(variants))
            else:
                await message.answer(question_text)
            await state.update_data(questions=questions + [{'file_id': file_id if file_id else '',
                                                            'question': question_text, 'variants': variants,
                                                            'correct_variants': correct_variants}])
    print(await state.get_data(), await state.get_state())


@dp.message(Command('start_test'))  # Обработчик команды начала прохождения теста
async def start_test_command(message: Message, state: FSMContext):
    await state.clear()
    await state.set_state(TestPassing.test_id_check)
    await message.answer('Чтобы начать проходить тест, введите его ID.', reply_markup=base_inline_keyboard)
    print(await state.get_data(), await state.get_state())


@dp.message(TestPassing.test_id_check)  # Проверяет, есть ли тест с таким ID
async def test_id_check(message: Message, state: FSMContext):
    if not check_test_id(int(message.text) if message.text.isdigit() else 000000):
        await message.answer('Теста с таким ID не существует. Пожалуйста, проверьте корректность введенных данных.',
                             reply_markup=base_inline_keyboard)
    else:
        await state.set_state(TestPassing.name)
        await state.update_data(test_id=int(message.text))
        await message.answer('Введите имя, которое будет отображаться при проверке результатов тестирования.',
                             reply_markup=ReplyKeyboardRemove())
    print(await state.get_data(), await state.get_state())


@dp.message(TestPassing.name)  # Вводится имя, проходящего тест
async def name_entering(message: Message, state: FSMContext):
    inline_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='Да', callback_data='lets_start'),
         InlineKeyboardButton(text='Вернуться назад', callback_data='cancel_test_start')]
    ])
    # Берет уже имеющеюся информацию по тесту
    test_id = (await state.get_data())['test_id']
    data = get_test_information(test_id)
    already_exist_data = get_results(test_id)
    already_exist_names = list(map(lambda x: x['name'], already_exist_data))
    if not message.text:
        await message.answer('Пожалуйста, введите имя одним текстовым сообщением.')
    # Проверка, нет ли уже результатов на такое же имя. Чтобы избежать путаницы при проверке результатов
    elif message.text in already_exist_names:
        await message.answer('Введенное имя уже было использовано. Пожалуйста, введите другое имя')
    else:
        await state.update_data(name=message.text, questions=list(enumerate(get_questions(test_id), start=1)))
        await state.set_state(TestPassing.tasks)
        await message.answer(f'{message.text}, Вам предлагается пройти {"тест" if data[0] else "опрос"} "{data[1]}".'
                             f'\nВы готовы начать?', reply_markup=inline_keyboard)
    print(await state.get_data(), await state.get_state())


@dp.callback_query(F.data != 'cancel_test_start', TestPassing.tasks)  # Главный обработчик ответов по inline клавишам
async def lets_start(callback: CallbackQuery, state: FSMContext):
    # Список уже имеющихся ответов
    answers = (await state.get_data())['answers'] if 'answers' in (await state.get_data()) else []
    dop_text = ''
    if len((await state.get_data())['questions']) == 0:  # Проверка на то, что вопросы закончились
        test_or_not = get_test_information((await state.get_data())["test_id"])[0]
        dop_text = 'Перейти к результатам' if test_or_not else 'Вернуться назад'
        inline_keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=dop_text, callback_data='lets_finish')]
        ])
        await callback.message.answer(f'Вы завершили прохождение {"тест" if test_or_not else "опрос"}а.',
                                      reply_markup=inline_keyboard)
        await state.set_state(TestPassing.finish)
    else:
        # Если вопросы не закончились, то выкидываем по одному из списка
        index, quest = (await state.get_data())['questions'].pop(0)
        if len(quest['cor_var']) > 1 and quest['variants'][0] != '-':  # Если больше одного ответа, то это сообщается
            await state.update_data(no_answer_for_multi_answer=len(quest['cor_var']))
            dop_text = f' (В этом вопросе больше одного ответа)'
            await state.set_state(TestPassing.multi_answer)  # Переход в состояние вопроса с множественным ответом
        # Также обработчик с файлом/без файла, с вариантами/без вариантов
        if quest['file_id']:
            if len(quest['variants']) > 1:
                await callback.message.answer_photo(photo=quest['file_id'], caption=f"{index}) {quest['question']}"
                                                                                    f"{dop_text}",
                                                    reply_markup=await inline_keyboard_create(quest['variants']))
            else:
                await callback.message.answer_photo(photo=quest['file_id'], caption=f"{index}) {quest['question']}"
                                                                                    f"{dop_text}")
        else:
            if len(quest['variants']) > 1:
                await callback.message.answer(f"{index}) {quest['question']}{dop_text}",
                                              reply_markup=await inline_keyboard_create(quest['variants']))
            else:
                await callback.message.answer(f"{index}) {quest['question']}{dop_text}")
    # Если только вернулся из мульти-ответного вопроса, то записывает крайний колбэк в тот же вопрос
    if ('no_answer_for_multi_answer' in (await state.get_data()) and
            (await state.get_data())['no_answer_for_multi_answer'] == -10):
        await state.update_data(answers=answers[:-1] + [answers[-1] + [callback.data]], no_answer_for_multi_answer=0)
    # Если переходит в мульти-ответный режим, то создает заранее ячейку ответа
    elif await state.get_state() == TestPassing.multi_answer:
        await state.update_data(answers=answers + [[callback.data]] + [[]])
    else:  # Иначе просто записывает ответ
        await state.update_data(answers=answers + [[callback.data]])
    print(await state.get_data(), await state.get_state())


@dp.callback_query(TestPassing.multi_answer)  # Обработчик мульти-ответного вопроса
async def multi_answer(callback: CallbackQuery, state: FSMContext):
    answers = (await state.get_data())['answers']
    nafma = (await state.get_data())['no_answer_for_multi_answer'] - 1  # Количество не указанных ответов
    await state.update_data(answers=answers[:-1] + [answers[-1] + [callback.data]], no_answer_for_multi_answer=nafma)
    if nafma == 1:
        await state.set_state(TestPassing.tasks)  # Возвращение в состояние базового обработчика
        await state.update_data(no_answer_for_multi_answer=-10)  # Флаг, что мы только отсюда вернулись
    print(await state.get_data(), await state.get_state())


@dp.message(TestPassing.tasks)  # В целом то же самое, что обычный обработчик, только тут ответы без вариантов выбора
async def lets_start_with_text(message: Message, state: FSMContext):
    answers = (await state.get_data())['answers'] if 'answers' in (await state.get_data()) else []
    dop_text = ''
    if len((await state.get_data())['questions']) == 0:
        test_or_not = get_test_information((await state.get_data())["test_id"])[0]
        dop_text = 'Перейти к результатам' if test_or_not else 'Вернуться назад'
        inline_keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=dop_text, callback_data='lets_finish')]
        ])
        await message.answer(f'Вы завершили прохождение {"тест" if test_or_not else "опрос"}а.',
                             reply_markup=inline_keyboard)
        await state.set_state(TestPassing.finish)
    else:
        index, quest = (await state.get_data())['questions'].pop(0)
        if len(quest['cor_var']) > 1 and quest['variants'][0] != '-':
            await state.update_data(no_answer_for_multi_answer=len(quest['cor_var']))
            dop_text = f' (В этом вопросе {len(quest["cor_var"])} ответа(ов))'
            await state.set_state(TestPassing.multi_answer)
        if quest['file_id']:
            if len(quest['variants']) > 1:
                await message.answer_photo(photo=quest['file_id'], caption=f"{index}) {quest['question']}{dop_text}",
                                           reply_markup=await inline_keyboard_create(quest['variants']))
            else:
                await message.answer_photo(photo=quest['file_id'], caption=f"{index}) {quest['question']}{dop_text}")
        else:
            if len(quest['variants']) > 1:
                await message.answer(f"{index}) {quest['question']}{dop_text}",
                                     reply_markup=await inline_keyboard_create(quest['variants']))
            else:
                await message.answer(f"{index}) {quest['question']}{dop_text}")
    if ('no_answer_for_multi_answer' in (await state.get_data()) and
            (await state.get_data())['no_answer_for_multi_answer'] == -10):
        await state.update_data(answers=answers[:-1] + [answers[-1] + [message.text]], no_answer_for_multi_answer=0)
    elif await state.get_state() == TestPassing.multi_answer:
        await state.update_data(answers=answers + [[message.text]] + [[]])
    else:
        await state.update_data(answers=answers + [[message.text]])
    print(await state.get_data(), await state.get_state())


@dp.callback_query(F.data == 'lets_finish', TestPassing.finish)  # Обработчик завершения прохождения теста
async def lets_finish(callback: CallbackQuery, state: FSMContext):
    answers = (await state.get_data())['answers'][1:]
    test_id = (await state.get_data())["test_id"]
    test_or_not = get_test_information(test_id)[0]
    await state.update_data(answers=answers)
    current_state = await state.get_data()  # Сохраняет дату, чтобы потов в БД закинуть
    await state.clear()
    if not test_or_not:  # Если опрос, то просто на начальный экран возвращает
        await callback.message.answer('Выберите действие на клавиатуре ниже.', reply_markup=base_reply_keyboard)
        copy_result(current_state)  # Сохранение данных в БД
    else:  # Если тест, то выводится красивая табличка с результатами.
        cor_answers = list(map(lambda x: x['cor_var'], get_questions(test_id)))
        msg = (f"`Ваш ответ{' ' * ((max(map(len, answers)) if max(map(len, answers)) > 15 else 15) - 9)}->"
               f"{' ' * ((max(map(len, cor_answers)) if max(map(len, cor_answers)) > 22 else 22) - 16)}"
               f"Правильный ответ\n\n")
        cor_ans_count = 0
        for i in range(len(cor_answers)):
            ans = ";".join(answers[i])
            cor_ans = ";".join(cor_answers[i])
            if ans == cor_ans:
                cor_ans_count += 1
            msg += (f'{ans}{" " * ((max(map(len, answers)) if max(map(len, answers)) > 15 else 15) - len(ans))}->'
                    f'{" " * ((max(map(len, cor_answers)) if max(map(len, cor_answers)) > 22 else 22) - len(cor_ans))}'
                    f'{cor_ans}\n')
        msg += f"\nКоличество правильных ответов: {cor_ans_count}/{len(answers)}`"
        await callback.message.answer(msg, parse_mode=ParseMode.MARKDOWN_V2, reply_markup=base_inline_keyboard)
        copy_result(current_state, cor_ans_count)


@dp.callback_query(F.data == 'check_res')  # Обработчик вызова режима просмотра результатов
async def check_res(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await state.set_state(ResultCheck.test_id_check)
    await callback.message.answer('Введите ID теста, результаты которого Вы хотите посмотреть.',
                                  reply_markup=base_inline_keyboard)
    print(await state.get_data(), await state.get_state())


@dp.message(ResultCheck.test_id_check)  # Обработчик запроса ID
async def res_test_id_check(message: Message, state: FSMContext):
    if not message.text:
        await message.answer('Пожалуйста, отправьте ID одним текстовым сообщением.')
    elif not check_test_id(int(message.text) if message.text.isdigit() else 000000):  # Проверяет наличие такого ID
        await message.answer('Теста с таким ID не существует. Пожалуйста, проверьте корректность введенных данных.',
                             reply_markup=base_inline_keyboard)
    else:
        await state.set_state(ResultCheck.password_check)
        await state.update_data(test_id=int(message.text))
        await message.answer('Для доступа к результатам, введите пароль от теста.', reply_markup=base_inline_keyboard)
    print(await state.get_data(), await state.get_state())


@dp.message(ResultCheck.password_check)  # Обработчик запроса пароля
async def res_password_check(message: Message, state: FSMContext):
    test_id = (await state.get_data())['test_id']
    data = get_test_information(test_id)
    if not message.text:
        await message.answer('Пожалуйста, отправьте пароль одним текстовым сообщением.')
    elif data[2] != message.text:  # Проверка пароля
        await message.answer('Пароль некорректен. Проверьте правильность введенных данных.',
                             reply_markup=base_inline_keyboard)
    else:
        res_data = get_results(test_id)
        names_list = list(map(lambda x: x['name'], res_data))
        await state.set_state(ResultCheck.res_ch)
        await message.answer('Список пользователей, прошедших тестирование:',
                             reply_markup=await inline_keyboard_create(names_list))  # Выводит список прошедших
    print(await state.get_data(), await state.get_state())


@dp.callback_query(ResultCheck.res_ch)  # Вывод результатов, в зависимости от запрашиваемого имени
async def res_ch(callback: CallbackQuery, state: FSMContext):
    if callback.data == 'cancel_test_start':  # Выкидывает в меню, если нажали на соответствующую клавишу
        await state.clear()
        await callback.message.answer('Выберите действие на клавиатуре ниже.', reply_markup=base_reply_keyboard)
    else:  # Ну и собственно вывод результатов
        test_id = (await state.get_data())['test_id']
        res_data = get_results(test_id)
        results = list(filter(lambda x: x['name'] == callback.data, res_data))
        answ = results[0]['answers'] if results else []
        if results:
            msg = f"`Результаты тестируемого {callback.data}:\n"
            for i in range(len(answ)):
                msg += f"{i + 1}) {';'.join(answ[i])}\n"
        if results[0]['cor_ans_count']:
            msg += f"Количество правильных ответов: {results[0]['cor_ans_count']}/{len(answ)}`"
        else:
            msg += '`'
        await callback.message.answer(msg, parse_mode=ParseMode.MARKDOWN_V2, reply_markup=base_inline_keyboard)


@dp.callback_query(F.data == 'cancel_test_start')  # Обработчик возврата в меню
async def cancel_test_start(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.answer('Выберите действие на клавиатуре ниже.', reply_markup=base_reply_keyboard)


@dp.callback_query(F.data == 'cancel_test_start', TestPassing.tasks)  # Тот же обработчик, но во время прохождения теста
async def cancel_test_start1(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.answer('Выберите действие на клавиатуре ниже.', reply_markup=base_reply_keyboard)


if __name__ == '__main__':
    asyncio.run(main())
