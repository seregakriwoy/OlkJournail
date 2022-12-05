import config
import sqlite3
# import register
import functions as f
import logging
from aiogram import Bot, Dispatcher, executor, types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage

logging.basicConfig(level=logging.INFO)

bot = Bot(token=config.TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())


class ClassRegister(StatesGroup):
    waiting_for_class_name = State()
    waiting_for_school_name = State()


@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    connect = sqlite3.connect('database.db')
    cursor = connect.cursor()

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users(
    user_id INTEGER, 
    full_name STRING
    )''')
    connect.commit()

    user_id = message.from_user.id
    users_full_name = message.from_user.full_name

    cursor.execute(f'''
    INSERT OR IGNORE INTO users(user_id, full_name)
    SELECT {user_id}, '{users_full_name}'
    WHERE NOT EXISTS (
    SELECT * FROM users
    WHERE user_id = "{user_id}") ''')
    connect.commit()

    kb = [
        [
            types.KeyboardButton(text="Создать профиль класса"),
            types.KeyboardButton(text="Присоединиться к профилю класса")
        ]
    ]
    keyboard = types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
    await message.reply('Приветствую!', reply_markup=keyboard)


@dp.message_handler()
async def register_table(message: types.Message, state: FSMContext):
    if message.text == 'Создать профиль класса':
        connect = sqlite3.connect('database.db')
        cursor = connect.cursor()

        cursor.execute('''
                CREATE TABLE IF NOT EXISTS classes(
                class_id INTEGER, 
                class_name STRING,
                school_name STRING,
                task_list_id STRING,
                hw_list_id STRING,
                student_list_id STRING,
                subscribers_list_id STRING
                )''')
        connect.commit()

        await message.answer('Введите название класса')
        await state.set_state(ClassRegister.waiting_for_class_name.state)


@dp.message_handler(state=ClassRegister.waiting_for_class_name)
async def get_class_name(message: types.Message, state: FSMContext):
    await state.update_data(class_n=message.text)
    await message.answer('Введите название школы')
    await state.set_state(ClassRegister.waiting_for_school_name.state)


@dp.message_handler(state=ClassRegister.waiting_for_school_name)
async def class_register(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    class_name = user_data['class_n']
    school_name = message.text

    connect = sqlite3.connect('database.db')
    cursor = connect.cursor()
    id = f.id_check()
    task_list_id = 'ts_' + f.if_in_table('task_list_id', 'ts_')
    hw_list_id = 'hw_' + f.if_in_table('hw_list_id', 'hw_')
    student_list_id = 'st_' + f.if_in_table('student_list_id', 'st_')
    subscribers_list_id = 'sb_' + f.if_in_table('subscribers_list_id', 'sb_')

    params = (id, class_name, school_name, task_list_id, hw_list_id, student_list_id, subscribers_list_id)
    # print(params)

    cursor.execute(f'''INSERT INTO classes
            (class_id, class_name, school_name, task_list_id, hw_list_id, student_list_id, subscribers_list_id)
            VALUES
            (?, ?, ?, ?, ?, ?, ?)''', params)
    connect.commit()
    await state.finish()

    task_code = '''
                    CREATE TABLE IF NOT EXISTS {}(
                    task STRING,
                    term_date STRING,
                    term_day STRING
                    )'''.format(task_list_id)
    hw_code = '''
                    CREATE TABLE IF NOT EXISTS {}(
                    subject, STRING
                    task STRING,
                    term_date STRING,
                    term_day STRING
                    )'''.format(hw_list_id)
    student_code = '''
                    CREATE TABLE IF NOT EXISTS {}(
                    surname_name STRING,
                    birthday STRING
                    )'''.format(student_list_id)
    subscribers_code = '''
                    CREATE TABLE IF NOT EXISTS {}(
                    user_id INTEGER,
                    surname_name STRING
                    )'''.format(subscribers_list_id)
    # print(task_code)
    f.create_table(task_code)
    f.create_table(hw_code)
    f.create_table(student_code)
    f.create_table(subscribers_code)


# def register_handlers_food(dp: Dispatcher):
#     dp.register_message_handler(register_table, state="*")
#     dp.register_message_handler(get_class_name, state=ClassRegister.waiting_for_class_name)
#     dp.register_message_handler(class_register, state=ClassRegister.waiting_for_school_name)


if __name__ == '__main__':
    # register.setup(dp)
    executor.start_polling(dp, skip_updates=False)
