import config
import sqlite3
# import register
import functions as f
import logging
import random
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
    id INTEGER, 
    full_name STRING
    )''')
    connect.commit()

    user_id = message.from_user.id
    users_full_name = message.from_user.full_name

    cursor.execute(f'''
    INSERT OR IGNORE INTO users(id, full_name)
    SELECT {user_id}, '{users_full_name}'
    WHERE NOT EXISTS (
    SELECT * FROM users
    WHERE id = "{user_id}") ''')
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
                id INTEGER, 
                class_name STRING,
                school_name STRING,
                task_list_id STRING,
                hw_list_id STRING,
                student_list_id STRING
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
    task_list_id = 'ts-' + f.if_in_table('task_list_id', 'ts-')
    hw_list_id = 'hw-' + f.if_in_table('hw_list_id', 'hw-')
    student_list_id = 'st-' + f.if_in_table('student_list_id', 'st-')

    params = (id, class_name, school_name, task_list_id, hw_list_id, student_list_id)
    # print(params)

    cursor.execute(f'''INSERT INTO classes
            (id, class_name, school_name, task_list_id, hw_list_id, student_list_id)
            VALUES
            (?, ?, ?, ?, ?, ?)''', params)
    connect.commit()
    await state.finish()

    f.create_task_table(task_list_id)
    f.create_homework_table(hw_list_id)
    f.create_students_table(student_list_id)


# def register_handlers_food(dp: Dispatcher):
#     dp.register_message_handler(register_table, state="*")
#     dp.register_message_handler(get_class_name, state=ClassRegister.waiting_for_class_name)
#     dp.register_message_handler(class_register, state=ClassRegister.waiting_for_school_name)


if __name__ == '__main__':
    # register.setup(dp)
    executor.start_polling(dp, skip_updates=False)
