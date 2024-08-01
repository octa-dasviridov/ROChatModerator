# -*- coding: utf-8 -*-
# threadsmanager.py
#
# Created by Danil Sviridov, 2024
# Contact: da_sviridov@octateam.ru

import ast
import sqlite3
import requests
import configparser
from aiogram import Bot

config = configparser.ConfigParser()
config.read('config.ini')
db_path = config['DEFAULT']['db_path']


class Thread:
    @staticmethod
    def __execute(command: str = '') -> tuple:
        connection = sqlite3.connect(db_path)
        cursor = connection.cursor()
        try:
            _ = cursor.execute(command).fetchall()
            connection.commit()
        except Exception:
            connection.rollback()
            _ = ''
        finally:
            connection.close()
            return _

    def __init__(self, data: tuple, thread_id: int = -1) -> None:
        if thread_id == -1:
            self.id: int = data[0]
            self.status: bool = data[1] == 1
            self.auto_open: bool = data[2] == 1
            self.auto_close: bool = data[3] == 1
            self.set_thread()
        else:
            data = self.__execute(f'SELECT * FROM threads WHERE id = {thread_id}')
            self.id: int = data[0]
            self.status: bool = data[1]
            self.auto_open: bool = data[2]
            self.auto_close: bool = data[3]
            self.set_thread()

    def rm_thread(self, thread_id: int) -> None:
        self.__execute(f'DELETE FROM threads WHERE id = {thread_id}')

    def set_thread(self) -> None:
        exists = self.__execute(f'SELECT COUNT(*) FROM threads WHERE id = {self.id}')
        exists = int(exists[0][0]) > 0
        if exists:
            self.__execute(f'UPDATE threads SET '
                           f'status = {self.status}'
                           f'auto_open = {self.auto_open}'
                           f'auto_close = {self.auto_close} WHERE id = {self.id}')
        else:
            self.__execute(f'INSERT INTO threads (id, status, auto_open, auto_close) '
                           f'VALUES ({self.id}, {self.status}, {self.auto_open}, {self.auto_close})')

    async def toggle_status(self) -> None:
        __group_id = config['DEFAULT']['group_id']
        __token = config['DEFAULT']['token']
        bot = Bot(token=__token)
        if self.status:
            await bot.close_forum_topic(chat_id=__group_id, message_thread_id=self.id)
        else:
            url = f'https://api.telegram.org/bot{__token}/reopenForumTopic?chat_id={__group_id}&message_thread_id={self.id}'
            requests.get(url)
        self.status = not self.status
        self.__execute(f'UPDATE threads SET status = {self.status}')


class ThreadsManager:
    @staticmethod
    def __execute(command: str = '') -> tuple:
        connection = sqlite3.connect(db_path)
        cursor = connection.cursor()
        try:
            _ = cursor.execute(command).fetchall()
            connection.commit()
        except Exception:
            connection.rollback()
            _ = ''
        finally:
            connection.close()
            return _,

    @classmethod
    def __init_database(cls) -> None:
        exists = cls.__execute('SELECT COUNT(*) FROM sqlite_master WHERE type="table" AND name="threads"')
        exists = int(exists[0][0][0]) > 0
        if not exists:
            __locked_open_threads = ast.literal_eval(config['DEFAULT']['locked_open_threads'])
            __locked_close_threads = ast.literal_eval(config['DEFAULT']['locked_close_threads'])
            cls.__execute('CREATE TABLE threads (id INTEGER, status INTEGER, auto_open INTEGER, auto_close INTEGER)')
            for thread in __locked_open_threads:
                thread_exists = int(cls.__execute(f'SELECT COUNT(*) FROM threads WHERE id = {thread}')[0][0][0]) > 0
                if not thread_exists:
                    cls.__execute(f'INSERT INTO threads (id, status, auto_open, auto_close) '
                                  f'VALUES ({thread[0]}, 1, 0, -1)')
            for thread in __locked_close_threads:
                thread_exists = int(cls.__execute(f'SELECT COUNT(*) FROM threads WHERE id = {thread}')[0][0][0]) > 0
                if not thread_exists:
                    cls.__execute(f'INSERT INTO threads (id, status, auto_open, auto_close) '
                                  f'VALUES ({thread[0]}, 1, 1, 0)')
                else:
                    close_status = cls.__execute(f'SELECT auto_close FROM threads WHERE id = {thread}')[0][0][0] == -1
                    if close_status:
                        cls.__execute(f'UPDATE threads SET auto_close = 0 WHERE id = {thread}')

    def __init__(self):
        self.__init_database()

    def __get_open_threads(self) -> list[Thread]:
        db_data = self.__execute('SELECT * FROM threads')
        threads = []
        for i in db_data[0]:
            thread = Thread(i)
            if thread.auto_open and not thread.status:
                threads.append(thread)
        return threads

    def __get_close_threads(self) -> list[Thread]:
        db_data = self.__execute('SELECT * FROM threads')
        threads = []
        for i in db_data[0]:
            thread = Thread(i)
            if thread.auto_close and thread.status:
                threads.append(thread)
        return threads

    async def open_threads(self) -> None:
        threads_to_open = self.__get_open_threads()
        for thread in threads_to_open:
            await thread.toggle_status()

    async def close_threads(self) -> None:
        threads_to_close = self.__get_close_threads()
        for thread in threads_to_close:
            await thread.toggle_status()
