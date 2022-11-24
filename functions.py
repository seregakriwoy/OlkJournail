# import config
import sqlite3
# import register
import logging
import random
# from aiogram import Bot, Dispatcher, executor, types
# from aiogram.dispatcher import FSMContext
# from aiogram.dispatcher.filters.state import State, StatesGroup
# from aiogram.contrib.fsm_storage.memory import MemoryStorage


def if_in_table(st, srtname):
    connect = sqlite3.connect('database.db')
    cursor = connect.cursor()
    while True:
        x = random.randint(100000, 999999)
        if cursor.execute(f'SELECT {st} FROM classes WHERE {st}=?', (srtname + str(x),)).fetchone() != None:
            continue
        else:
            return str(x)


def id_check():
    connect = sqlite3.connect('database.db')
    cursor = connect.cursor()
    while True:
        x = random.randint(100000, 999999)
        if cursor.execute('SELECT id FROM classes WHERE id=?', (x, )).fetchone() != None:
            continue
        else:
            return x


def create_task_table(id):
    connect = sqlite3.connect('database.db')
    cursor = connect.cursor()

    cursor.execute('''
                    CREATE TABLE IF NOT EXISTS ? (
                    task STRING,
                    term_date STRING,
                    term_day STRING
                    )''', (id, ))
    connect.commit()


def create_homework_table(id):
    connect = sqlite3.connect('database.db')
    cursor = connect.cursor()

    cursor.execute('''
                    CREATE TABLE IF NOT EXISTS ? (
                    subject, string
                    task STRING,
                    term_date STRING,
                    term_day STRING
                    )''', (id, ))
    connect.commit()


def create_students_table(id):
    connect = sqlite3.connect('database.db')
    cursor = connect.cursor()

    cursor.execute('''
                    CREATE TABLE IF NOT EXISTS ? (
                    full_name STRING,
                    birthday STRING
                    )''', (id, ))
    connect.commit()