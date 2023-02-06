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


class UserRegister(StatesGroup):
    waiting_for_name = State()


class JoinClass(StatesGroup):
    waiting_for_class_id = State()


class ClassList(StatesGroup):
    waiting_for_class_number = State()


# universal message handler
@dp.message_handler()
async def message_dp(message: types.Message, state: FSMContext):
    connect = sqlite3.connect('database.db')
    cursor = connect.cursor()
    if message.text == 'Создать профиль класса':
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

    if message.text == 'Присоединиться к профилю класса':
        await message.answer('Введите id класса')
        await state.set_state(JoinClass.waiting_for_class_id.state)

    if message.text == 'Мои профили классов':
        user_id = message.from_user.id
        user_classes = cursor.execute(f'''SELECT classes_list_id FROM users WHERE user_id = {user_id}''').fetchone()[0]
        user_profiles = cursor.execute(f'''SELECT class_id FROM {user_classes} ''').fetchall()
        print(user_profiles)
        if user_profiles == None:
            await message.answer("Здесь пока ничего нет :)")
        else:
            lst = []
            for i in range(len(user_profiles)):
                for k in user_profiles[i]:
                    class_name = cursor.execute(f'''SELECT class_name FROM classes WHERE class_id = {k}''').fetchone()[
                        0]
                    school_name = \
                    cursor.execute(f'''SELECT school_name FROM classes WHERE class_id = {k}''').fetchone()[0]
                    lst.append(f'{i + 1}: класс "{class_name}" школы "{school_name}"')
            await message.answer('\n'.join(lst))
            await message.answer("Введите порядковый номер профиля")
            await state.set_state(ClassList.waiting_for_class_number.state)


# /start
@dp.message_handler(commands=['start'])
async def start(message: types.Message, state: FSMContext):
    connect = sqlite3.connect('database.db')
    cursor = connect.cursor()

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users(
    user_id INTEGER, 
    full_name STRING,
    surname_name STRING,
    classes_list_id STRING
    )''')
    connect.commit()

    await message.answer('Введиет Ваши фамилию и имя')
    await state.set_state(UserRegister.waiting_for_name.state)


@dp.message_handler(state=UserRegister.waiting_for_name)
async def start_commitment(message: types.message, state: FSMContext):
    surname_name = message.text
    user_id = message.from_user.id
    users_full_name = message.from_user.full_name
    cl_list_id = 'u_cl_' + f.if_in_table('classes_list_id', 'u/cl', 'users')
    # print(type(surname_name))

    connect = sqlite3.connect('database.db')
    cursor = connect.cursor()
    cursor.execute(f'''
    INSERT OR IGNORE INTO users(user_id, full_name, surname_name, classes_list_id)
    SELECT {user_id}, '{users_full_name}', '{surname_name}', '{cl_list_id}'
    WHERE NOT EXISTS (
    SELECT * FROM users
    WHERE user_id = "{user_id}") ''')
    connect.commit()

    class_code = '''CREATE TABLE IF NOT EXISTS {}(
                    class_id INTEGER
                    )'''.format(cl_list_id)

    f.create_table(class_code)

    kb = [
        [
            types.KeyboardButton(text="Создать профиль класса"),
            types.KeyboardButton(text="Присоединиться к профилю класса"),
            types.KeyboardButton(text="Мои профили классов")
        ]
    ]
    keyboard = types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
    await message.reply('Приветствую!', reply_markup=keyboard)
    await state.finish()


# new class
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
    task_list_id = 'c_ts_' + f.if_in_table('task_list_id', 'c_ts_', 'classes')
    hw_list_id = 'c_hw_' + f.if_in_table('hw_list_id', 'c_hw_', 'classes')
    student_list_id = 'c_st_' + f.if_in_table('student_list_id', 'c_st_', 'classes')
    subscribers_list_id = 'c_sb_' + f.if_in_table('subscribers_list_id', 'c_sb_', 'classes')

    params = (id, class_name, school_name, task_list_id, hw_list_id, student_list_id, subscribers_list_id)
    # print(params)

    cursor.execute(f'''INSERT INTO classes
            (class_id, class_name, school_name, task_list_id, hw_list_id, student_list_id, subscribers_list_id)
            VALUES
            (?, ?, ?, ?, ?, ?, ?)''', params)
    connect.commit()

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
                    surname_name STRING,
                    is_admin BOOLEAN
                    )'''.format(subscribers_list_id)
    # print(task_code)
    f.create_table(task_code)
    f.create_table(hw_code)
    f.create_table(student_code)
    f.create_table(subscribers_code)

    user_id = message.from_user.id
    user_surname_name = cursor.execute(f'''SELECT surname_name FROM users WHERE user_id = "{user_id}"''').fetchone()[0]
    user_classes = cursor.execute(f'''SELECT classes_list_id FROM users WHERE user_id = "{user_id}"''').fetchone()[0]
    # print(type(user_classes))
    # print(type(user_surname_name))

    cursor.execute(f'''INSERT INTO '{subscribers_list_id}' 
    (user_id, surname_name, is_admin)
    VALUES ({user_id}, '{user_surname_name}', {True})''')
    connect.commit()

    cursor.execute('''INSERT INTO {} 
    (class_id)
    VALUES ({})'''.format(user_classes, id))
    connect.commit()

    await message.answer("Профиль класса успешно создан")
    await state.finish()


# class join
@dp.message_handler(state=JoinClass.waiting_for_class_id.state)
async def join_class(message: types.Message, state: FSMContext):
    connect = sqlite3.connect('database.db')
    cursor = connect.cursor()
    class_id = message.text
    user_id = message.from_user.id
    user_class_list = cursor.execute(f'''SELECT classes_list_id FROM users WHERE user_id = {user_id}''').fetchone()[0]
    surname_name = cursor.execute(f'''SELECT surname_name FROM users WHERE user_id = {user_id}''').fetchone()[0]

    if cursor.execute(f'''SELECT class_id FROM classes WHERE class_id = {class_id}''').fetchone() == None:
        await message.answer("Неправильный id класса, повторите попытку")
        await state.finish()
    elif cursor.execute(f'''SELECT class_id FROM {user_class_list} WHERE class_id = {class_id}''').fetchone() != None:
        await message.answer("Вы уже подписаны на этот класс")
        await state.finish()
    else:
        subscribers_list = cursor.execute(
            f'''SELECT subscribers_list_id FROM classes WHERE class_id = {class_id}''').fetchone()[0]

        cursor.execute(f'''INSERT INTO {subscribers_list}
        (user_id, surname_name, is_admin)
        VALUES ({user_id}, '{surname_name}', {False})''')
        connect.commit()
        cursor.execute(f'''INSERT INTO {user_class_list}
        (class_id) VALUES ({class_id})''')
        connect.commit()
        await message.answer("Вы успешно подписались на профиль класса")
        await state.finish()


# @dp.message_handler(state=ClassList.waiting_for_class_number.state):
#     async def 

if __name__ == '__main__':
    # register.setup(dp)
    executor.start_polling(dp, skip_updates=False)
