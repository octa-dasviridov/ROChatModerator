# -*- coding: utf-8 -*-
# runner.py
#
# Created by Danil Sviridov, 2024
# Contact: da_sviridov@octateam.ru

import asyncio
import datetime
import configparser
from threadsmanager import ThreadsManager

config = configparser.ConfigParser()
config.read('config.ini')
time_zone = config['DEFAULT']['time_zone']
open_time = config['DEFAULT']['open_time']
close_time = config['DEFAULT']['close_time']


class Time:
    def __init__(self, hours: int, minutes: int, seconds: int = 0) -> None:
        self.hours = hours
        self.minutes = minutes
        self.seconds = seconds

    def present(self) -> str:
        return f'{self.hours}:{self.minutes}:{self.seconds}'


def convert_time(time: str) -> Time:
    hours, minutes = time.split(':')
    hours = int(hours)
    minutes = int(minutes)
    return Time(hours, minutes)


def main() -> None:
    f_open = False
    f_close = False
    while True:
        date = datetime.datetime.today().strftime('%H:%M')
        datet = convert_time(date)
        opent = convert_time(open_time)
        closet = convert_time(close_time)
        threads = ThreadsManager()
        if datet.present() == opent.present() and not f_open:
            f_open = True
            print(f'OPEN {datetime.datetime.today().strftime("%d/%m/%Y %H:%M")}')
            try:
                asyncio.run(threads.open_threads())
            except:
                pass
        elif datet.present() == closet.present() and not f_close:
            f_close = True
            print(f'CLOSE {datetime.datetime.today().strftime("%d/%m/%Y %H:%M")}')
            try:
                asyncio.run(threads.close_threads())
            except:
                pass
        else:
            f_open = False
            f_close = False
        asyncio.run(asyncio.sleep(30))


if __name__ == '__main__':
    main()
