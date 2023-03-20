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


class ClassActions(StatesGroup):
    waiting_for_class_number = State()
    waiting_for_message = State()
    addition = State()


class HWAddition(StatesGroup):
    waiting_for_subject = State()
    waiting_for_task = State()
    waiting_for_term_date = State()
    waiting_for_term_day = State()


class TaskAddition(StatesGroup):
    waiting_for_task = State()
    waiting_for_term_date = State()
    waiting_for_term_day = State()


class StudentAddition(StatesGroup):
    waiting_for_surname_name = State()
    waiting_for_birthday = State()


connect = sqlite3.connect('database.db')
cursor = connect.cursor()


# universal message handler
@dp.message_handler()
async def message_dp(message: types.Message, state: FSMContext):
    if message.text == '/start':
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users(
            user_id INTEGER, 
            full_name STRING,
            surname_name STRING,
            classes_list_id STRING
            )''')
        connect.commit()

        user_id = message.from_user.id
        if not cursor.execute(f'''SELECT user_id FROM users WHERE user_id = {user_id}''').fetchall():
            await message.answer('Введиет Ваши фамилию и имя')
            await state.set_state(UserRegister.waiting_for_name.state)

        else:

            kb = [
                [
                    types.KeyboardButton(text="Создать профиль класса"),
                    types.KeyboardButton(text="Присоединиться к профилю класса"),
                    types.KeyboardButton(text="Мои профили классов")
                ]
            ]
            keyboard = types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
            await message.answer('Аккаунт уже создан', reply_markup=keyboard)
            await state.finish()

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
        # print(user_profiles)
        if user_profiles == None:
            await message.answer("Здесь пока ничего нет :)")
        else:
            lst = []
            class_list = []
            for i in range(len(user_profiles)):
                for k in user_profiles[i]:
                    class_name = cursor.execute(f'''SELECT class_name FROM classes WHERE class_id = {k}''').fetchone()[
                        0]
                    school_name = \
                        cursor.execute(f'''SELECT school_name FROM classes WHERE class_id = {k}''').fetchone()[0]
                    lst.append(f'{i + 1}) класс "{class_name}" школы "{school_name}"')
                    class_list.append(k)
            await message.answer('\n'.join(lst))
            await message.answer("Введите порядковый номер профиля")
            await state.update_data(class_list=class_list)
            await state.set_state(ClassActions.waiting_for_class_number.state)


# /start
@dp.message_handler(state=UserRegister.waiting_for_name)
async def start_commitment(message: types.message, state: FSMContext):
    surname_name = message.text
    user_id = message.from_user.id
    users_full_name = message.from_user.full_name
    cl_list_id = 'u_cl_' + f.if_in_table('classes_list_id', 'u/cl', 'users')
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
                    subject STRING,
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
    await message.answer(f"Id профиля класса: {id}")
    await state.finish()


# class join
@dp.message_handler(state=JoinClass.waiting_for_class_id.state)
async def join_class(message: types.Message, state: FSMContext):
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


@dp.message_handler(state=ClassActions.waiting_for_class_number.state)
async def class_profile_connection(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    class_list = user_data['class_list']
    class_id = class_list[int(message.text) - 1]
    await state.update_data(class_id=class_id)
    class_name = cursor.execute(f'''SELECT class_name FROM classes WHERE class_id = {class_id}''').fetchone()[0]
    kb = [
        [
            types.KeyboardButton(text="Домашнее задание"),
            types.KeyboardButton(text="Доп информация"),
            types.KeyboardButton(text="Ученики"),
            types.KeyboardButton(text="Подписчики"),
            types.KeyboardButton(text="Выход")
        ]
    ]
    keyboard = types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
    await message.answer(f'Открыт профиль {class_name}', reply_markup=keyboard)
    await state.set_state(ClassActions.waiting_for_message.state)


@dp.message_handler(state=ClassActions.waiting_for_message.state)
async def class_message_handler(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    class_id = user_data['class_id']
    user_id = message.from_user.id
    sb_table = cursor.execute(f'''SELECT subscribers_list_id FROM classes WHERE class_id = {class_id} ''').fetchone()[0]
    hw_table = cursor.execute(f'''SELECT hw_list_id FROM classes WHERE class_id = {class_id}''').fetchone()[0]
    ts_table = cursor.execute(f'''SELECT task_list_id FROM classes WHERE class_id = {class_id}''').fetchone()[0]
    st_table = cursor.execute(f'''SELECT student_list_id FROM classes WHERE class_id = {class_id}''').fetchone()[0]
    await state.update_data(sb_table=sb_table)
    await state.update_data(hw_table=hw_table)
    await state.update_data(ts_table=ts_table)
    await state.update_data(st_table=st_table)
    kb2 = [
        [
            types.KeyboardButton(text="Добавить запись"),
            types.KeyboardButton(text="Назад")
        ]
    ]

    if message.text == 'Выход':
        kb1 = [
            [
                types.KeyboardButton(text="Создать профиль класса"),
                types.KeyboardButton(text="Присоединиться к профилю класса"),
                types.KeyboardButton(text="Мои профили классов")
            ]
        ]
        keyboard1 = types.ReplyKeyboardMarkup(keyboard=kb1, resize_keyboard=True)
        await message.reply('Славненько', reply_markup=keyboard1)
        await state.finish()

    if message.text == 'Домашнее задание':
        table_date = cursor.execute(f'''SELECT * FROM {hw_table}''').fetchall()
        if not table_date:
            await message.answer('Здесь пока ничего нет :)')
        else:
            lst = []
            for i in table_date:
                i = list(i)
                string = f'{i[0]} {i[2]}({i[3]}): {i[1]}'
                lst.append(string)
            await message.answer('\n'.join(lst))
        if cursor.execute(f'''SELECT is_admin FROM {sb_table} WHERE user_id = {user_id}'''):
            keyboard2 = types.ReplyKeyboardMarkup(keyboard=kb2, resize_keyboard=True)
            await message.answer('Добавить запись?', reply_markup=keyboard2)
            add_key = 'hw'
            await state.update_data(add_key=add_key)
            await state.set_state(ClassActions.addition.state)

    if message.text == 'Доп информация':
        table_date = cursor.execute(f'''SELECT * FROM {ts_table}''').fetchall()
        if not table_date:
            await message.answer('Здесь пока ничего нет :)')
        else:
            lst = []
            for i in table_date:
                i = list(i)
                string = f'{i[1]}({i[2]}): {i[0]}'
                lst.append(string)
            await message.answer('\n'.join(lst))
        if cursor.execute(f'''SELECT is_admin FROM {sb_table} WHERE user_id = {user_id}'''):
            keyboard2 = types.ReplyKeyboardMarkup(keyboard=kb2, resize_keyboard=True)
            await message.answer('Добавить запись?', reply_markup=keyboard2)
            add_key = 'ts'
            await state.update_data(add_key=add_key)
            await state.set_state(ClassActions.addition.state)

    if message.text == 'Ученики':
        table_date = cursor.execute(f'''SELECT * FROM {st_table}''').fetchall()
        if not table_date:
            await message.answer('Здесь пока ничего нет :)')
        else:
            lst = []
            for i in table_date:
                i = list(i)
                string = f'{i[0]}: {i[1]}'
                lst.append(string)
            await message.answer('\n'.join(lst))
        if cursor.execute(f'''SELECT is_admin FROM {sb_table} WHERE user_id = {user_id}'''):
            kb3 = [
                [
                    types.KeyboardButton(text="Добавить ученика"),
                    types.KeyboardButton(text="Назад")
                ]
            ]

            keyboard2 = types.ReplyKeyboardMarkup(keyboard=kb3, resize_keyboard=True)
            await message.answer('Добавить ученика?', reply_markup=keyboard2)
            add_key = 'st'
            await state.update_data(add_key=add_key)
            await state.set_state(ClassActions.addition.state)

    if message.text == 'Подписчики':
        table_date = cursor.execute(f'''SELECT * FROM {sb_table}''').fetchall()
        if not table_date:
            await message.answer('Здесь пока ничего нет :)')
        else:
            lst = []
            for i in table_date:
                i = list(i)
                string = f'{i[1]}'
                lst.append(string)
            await message.answer('\n'.join(lst))


@dp.message_handler(state=ClassActions.addition.state)
async def addition(message: types.Message, state: FSMContext):
    if message.text == 'Назад':
        kb = [
            [
                types.KeyboardButton(text="Домашнее задание"),
                types.KeyboardButton(text="Доп информация"),
                types.KeyboardButton(text="Ученики"),
                types.KeyboardButton(text="Подписчики"),
                types.KeyboardButton(text="Выход")
            ]
        ]
        keyboard = types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
        await message.answer('Что-то еще?', reply_markup=keyboard)
        await state.set_state(ClassActions.waiting_for_message.state)
    if message.text == 'Добавить запись':
        user_data = await state.get_data()
        sb_table = user_data['sb_table']
        add_key = user_data['add_key']
        if cursor.execute(f'''SELECT is_admin FROM {sb_table} WHERE user_id = {message.from_user.id}''').fetchone()[0]:
            if add_key == 'hw':
                await message.answer('Введите название предмета')
                await state.set_state(HWAddition.waiting_for_subject.state)
            if add_key == 'ts':
                await message.answer('Введите задание')
                await state.set_state(TaskAddition.waiting_for_task.state)
    if message.text == 'Добавить ученика':
        await message.answer('Введите фамилию и имя ученика')
        await state.set_state(StudentAddition.waiting_for_surname_name.state)


# hw addition
@dp.message_handler(state=HWAddition.waiting_for_subject.state)
async def add_subject(message: types.Message, state: FSMContext):
    await state.update_data(subject=message.text)
    await message.answer('Введите задание')
    await state.set_state(HWAddition.waiting_for_task.state)


@dp.message_handler(state=HWAddition.waiting_for_task.state)
async def add_subject(message: types.Message, state: FSMContext):
    await state.update_data(task=message.text)
    await message.answer('На какое число задано задание?')
    await state.set_state(HWAddition.waiting_for_term_date.state)


@dp.message_handler(state=HWAddition.waiting_for_term_date.state)
async def add_subject(message: types.Message, state: FSMContext):
    await state.update_data(term_date=message.text)
    await message.answer('На какой день недели задано задание? ')
    await state.set_state(HWAddition.waiting_for_term_day.state)


@dp.message_handler(state=HWAddition.waiting_for_term_day.state)
async def add_subject(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    subject = user_data['subject']
    task = user_data['task']
    term_date = user_data['term_date']
    term_day = message.text
    hw_table = user_data['hw_table']

    params = (subject, task, term_date, term_day)
    # print(params)

    cursor.execute(f'''INSERT INTO {hw_table}
                (subject, task, term_date, term_day)
                VALUES
                (?, ?, ?, ?)''', params)
    connect.commit()

    kb = [
        [
            types.KeyboardButton(text="Домашнее задание"),
            types.KeyboardButton(text="Доп информация"),
            types.KeyboardButton(text="Ученики"),
            types.KeyboardButton(text="Подписчики"),
            types.KeyboardButton(text="Выход")
        ]
    ]
    keyboard = types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
    await message.answer('Запись успешно создана', reply_markup=keyboard)
    await state.set_state(ClassActions.waiting_for_message.state)


# task addition
@dp.message_handler(state=TaskAddition.waiting_for_task.state)
async def add_subject(message: types.Message, state: FSMContext):
    await state.update_data(task=message.text)
    await message.answer('На какое число задано задание?')
    await state.set_state(TaskAddition.waiting_for_term_date.state)


@dp.message_handler(state=TaskAddition.waiting_for_term_date.state)
async def add_subject(message: types.Message, state: FSMContext):
    await state.update_data(term_date=message.text)
    await message.answer('На какой день недели задано задание? ')
    await state.set_state(TaskAddition.waiting_for_term_day.state)


@dp.message_handler(state=TaskAddition.waiting_for_term_day.state)
async def add_subject(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    task = user_data['task']
    term_date = user_data['term_date']
    term_day = message.text
    ts_table = user_data['ts_table']

    params = (task, term_date, term_day)
    # print(params)

    cursor.execute(f'''INSERT INTO {ts_table}
                (task, term_date, term_day)
                VALUES
                (?, ?, ?)''', params)
    connect.commit()

    kb = [
        [
            types.KeyboardButton(text="Домашнее задание"),
            types.KeyboardButton(text="Доп информация"),
            types.KeyboardButton(text="Ученики"),
            types.KeyboardButton(text="Подписчики"),
            types.KeyboardButton(text="Выход")
        ]
    ]
    keyboard = types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
    await message.answer('Запись успешно создана', reply_markup=keyboard)
    await state.set_state(ClassActions.waiting_for_message.state)


# student addition
@dp.message_handler(state=StudentAddition.waiting_for_surname_name.state)
async def add_subject(message: types.Message, state: FSMContext):
    await state.update_data(surname_name=message.text)
    await message.answer('Введите дату рождения ')
    await state.set_state(StudentAddition.waiting_for_birthday.state)


@dp.message_handler(state=StudentAddition.waiting_for_birthday.state)
async def add_subject(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    surname_name = user_data['surname_name']
    birthday = message.text
    st_table = user_data['st_table']

    params = (surname_name, birthday)
    # print(params)

    cursor.execute(f'''INSERT INTO {st_table}
                (surname_name, birthday)
                VALUES
                (?, ?)''', params)
    connect.commit()

    kb = [
        [
            types.KeyboardButton(text="Домашнее задание"),
            types.KeyboardButton(text="Доп информация"),
            types.KeyboardButton(text="Ученики"),
            types.KeyboardButton(text="Подписчики"),
            types.KeyboardButton(text="Выход")
        ]
    ]
    keyboard = types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
    await message.answer('Ученик добавлен', reply_markup=keyboard)
    await state.set_state(ClassActions.waiting_for_message.state)


if __name__ == '__main__':
    # register.setup(dp)
    executor.start_polling(dp, skip_updates=False)
