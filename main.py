import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import ReplyKeyboardRemove, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, \
    InlineKeyboardButton, CallbackQuery, Message
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from pyexpat.errors import messages
from ORM import *
import random

from config import BOT_TOKEN

dp = Dispatcher()


class TestCreating(StatesGroup):
    test_or_not = State()
    name = State()
    password = State()
    questions = State()


async def main():
    bot = Bot(token=BOT_TOKEN)
    await dp.start_polling(bot)


async def inline_keyboard_create(variants):
    keyboard = InlineKeyboardBuilder()
    for variant in variants:
        keyboard.add(InlineKeyboardButton(text=variant, callback_data=variant))
    return keyboard.adjust(2).as_markup()


@dp.message(Command('start'))
async def start_command(message: Message):
    reply_keyboard = [[KeyboardButton(text='/admin'), KeyboardButton(text='/start_test')],
                      [KeyboardButton(text='/help')]]
    keyboard = ReplyKeyboardMarkup(keyboard=reply_keyboard, resize_keyboard=True, one_time_keyboard=True)
    await message.reply(
        "Здравствуйте! Я бот для тестов/опросов. Вы можете открыть панель администратора, чтобы создать тест или "
        "посмотреть его результаты, либо же пройти тест, если с Вами уже поделились его ID. Если остались вопросы, "
        "то можете воспользоваться меню помощи, нажав на соответствующую кнопку на клавиатуре ниже.",
        reply_markup=keyboard)


@dp.message(Command('help'))
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


@dp.message(Command('admin'))
async def admin_command(message: Message):
    inline_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='Создать тест/опрос', callback_data='create_test'),
         InlineKeyboardButton(text='Посмотреть результаты', callback_data='check_res')]
    ])
    await message.answer('Выберите, что Вы хотите сделать.', reply_markup=inline_keyboard)


@dp.callback_query(F.data == 'create_test')
async def process_callback_create_test(callback: CallbackQuery, state: FSMContext):
    inline_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='Тест', callback_data='test'),
         InlineKeyboardButton(text='Опрос', callback_data='not_test')]
    ])
    await callback.answer()
    await state.clear()
    await state.set_state(TestCreating.test_or_not)
    await callback.message.answer(
        'Выберите, какой тип тестирования Вы хотите создать. Разница в том, '
        'что тест подразумевает правильный(ые) ответ(ы), а опрос нет.',
        reply_markup=inline_keyboard)


@dp.callback_query(F.data == 'test', TestCreating.test_or_not)
async def process_callback_create_test(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    test_id = random.randint(111111, 999999)
    while check_test_id(test_id):
        test_id = random.randint(111111, 999999)
    await state.update_data(test_or_not='тест', ID=test_id)
    await state.set_state(TestCreating.name)
    await callback.message.answer('Введите название для Вашего теста.', reply_markup=ReplyKeyboardRemove())


@dp.callback_query(F.data == 'not_test', TestCreating.test_or_not)
async def process_callback_create_test(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    test_id = random.randint(111111, 999999)
    while check_test_id(test_id):
        test_id = random.randint(111111, 999999)
    await state.update_data(test_or_not='опрос', ID=test_id)
    await state.set_state(TestCreating.name)
    await callback.message.answer('Введите название для Вашего опроса.')


@dp.message(TestCreating.name)
async def name_creating(message: Message, state: FSMContext):
    name = message.text
    await state.update_data(name=name)
    await state.set_state(TestCreating.password)
    await message.answer(f'Введите пароль, чтобы позже можно было посмотреть результаты.')


@dp.message(TestCreating.password)
async def password_creating(message: Message, state: FSMContext):
    reply_keyboard = [[KeyboardButton(text='Удалить вопрос'), KeyboardButton(text='Завершить добавление вопросов')]]
    keyboard = ReplyKeyboardMarkup(keyboard=reply_keyboard, resize_keyboard=True, one_time_keyboard=False)
    password = message.text
    data = await state.get_data()
    test_text = ('После того, как Вы указали все варианты ответа, опять поставьте ^^ и '
                 'начните перечислять правильные варианты ответа так же через ; .')
    await state.update_data(password=password)
    await state.set_state(TestCreating.questions)
    await message.answer(f'ID {data["test_or_not"]}а: {data["ID"]}\n'
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
                         f' добавлять вопросы, нажмите на той же клавиатуре снизу "завершить добавление вопросов".',
                         reply_markup=keyboard)
    print(await state.get_data(), await state.get_state())


@dp.message(TestCreating.questions)
async def question_add(message: Message, state: FSMContext):
    reply_keyboard = [[KeyboardButton(text='/admin'), KeyboardButton(text='/start_test')],
                      [KeyboardButton(text='/help')]]
    keyboard = ReplyKeyboardMarkup(keyboard=reply_keyboard, resize_keyboard=True, one_time_keyboard=True)
    questions = (await state.get_data())['questions'] if 'questions' in await state.get_data() else []
    if message.text == 'Удалить вопрос':
        if not questions:
            await message.answer('Вы еще не добавили вопросов.')
        else:
            await state.update_data(questions=questions[:-1])
            await message.answer('Крайний вопрос был удален.')
        print(await state.get_data(), await state.get_state())
    elif message.text == 'Завершить добавление вопросов':
        current_data = await state.get_data()
        await state.clear()
        if questions:
            await message.answer(f'Создание {current_data["test_or_not"]}а завершено, вопросы сохранены.',
                                 reply_markup=keyboard)
            create_test(current_data)
        else:
            await message.answer(f'Создание {current_data["test_or_not"]}а отменено.', reply_markup=keyboard)
    else:
        file_id = str(message.photo[-1]).split()[0].split("'")[1] if message.photo else ''
        text = message.text if message.text else message.caption if message.caption else ''
        test_or_not = (await state.get_data())['test_or_not']
        question_text, variants = text.split('^^')[0], text.split('^^')[1].split(';') if len(
            text.split('^^')) > 1 else []
        correct_variants = text.split('^^')[2].split(';') \
            if test_or_not == 'тест' and len(text.split('^^')) == 3 else []
        variants = list(filter(lambda x: x, variants))
        correct_variants = list(filter(lambda x: x, correct_variants))
        if (test_or_not == 'тест' and
                ((len(correct_variants) == 1 and (not correct_variants[0])) or not correct_variants)):
            await message.answer('В режиме создания теста необходимо указать правильный вариант ответа.')
        elif not question_text:
            await message.answer('Пожалуйста, напишите текст вопроса.')
        elif len(variants) == 1 and variants[0] != '-':
            await message.answer('Пожалуйста, укажите больше одного варианта ответа.')
        elif file_id:
            if len(variants) > 1:
                await message.answer_photo(photo=file_id, caption=question_text,
                                           reply_markup=await inline_keyboard_create(variants))
            else:
                await message.answer_photo(photo=file_id, caption=question_text)
            await state.update_data(questions=questions + [{'file_id': file_id if file_id else '',
                                                            'question': question_text, 'variants': variants,
                                                            'correct_variants': correct_variants}])
        else:
            if len(variants) > 1:
                await message.answer(question_text, reply_markup=await inline_keyboard_create(variants))
            else:
                await message.answer(question_text)
            await state.update_data(questions=questions + [{'file_id': file_id if file_id else '',
                                                            'question': question_text, 'variants': variants,
                                                            'correct_variants': correct_variants}])
        print(await state.get_data(), await state.get_state())


if __name__ == '__main__':
    asyncio.run(main())
