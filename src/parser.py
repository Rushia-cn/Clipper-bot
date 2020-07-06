import re
import random
import string
from typing import Optional

from .request import ClipRequest

from telebot.types import Message, MessageEntity
import validators

time_pattern = re.compile(r"\d*:[0-5]\d?:[0-5]\d?$")


def parse(bot, msg: Message) -> Optional[ClipRequest]:
    splitted = msg.text.split(" ")
    if splitted.__len__() < 3:
        bot.reply_to(msg, "Command usage: /add [URL] [IN] [OUT]")
        return
    url = splitted[1]
    a = verify_time(splitted[2])
    b = verify_time(splitted[3])
    if not validators.url(url) is True:
        bot.reply_to(msg, "Invalid url")
        return
    if not a:
        bot.reply_to(msg, f"{splitted[2]} is invalid")
        return
    if not b:
        bot.reply_to(msg, f"{splitted[3]} is invalid")
        return
    if cmp_time(a, b):
        bot.reply_to(msg, f"{a} is greater than {b}")
        return
    return ClipRequest(url, a, b)


def verify_time(time: str):
    num = time.count(":")
    if num > 2:
        return False
    formatted = f"{'0:' * (2 - num)}{time}"
    if time_pattern.match(formatted):
        return formatted
    else:
        return False


def cmp_time(a, b):
    sa, sb = [int(x) for x in a.split(":")], [int(x) for x in b.split(":")]
    sec_a, sec_b = 0, 0
    for i in range(3):
        sec_a += sa[i] * 60 ** (2 - i)
        sec_b += sb[i] * 60 ** (2 - i)
    return sec_a >= sec_b
