import re
import json
import logging

from src.parser import parse, ClipRequest

from telebot import TeleBot
from telebot.types import ForceReply, Message, MessageEntity

logging.basicConfig(level="INFO")
lg = logging.getLogger("clipper")

bot = TeleBot("1033924480:AAGmLW2wB24wrkFZ8dfTc1LW3rI2ZkxN3BU")
with open("cert.json", "r") as f:
    certified = json.load(f)

reqs = {"abcd": ClipRequest("https://abc.cc", "1:1:1", "2:2:2")}


"""@bot.message_handler(commands=["cert"])
def cert(msg: Message):
    if msg.from_user.username not in certified:
        bot.reply_to(msg, "You are not certified")
        return
    new_certs = []
    for e in msg.entities:
        if e.type == "mention":
            mentioned = msg.text[e.offset + 1: e.offset + e.length]
            if mentioned in certified:
                bot.reply_to(msg, f"Sorry, @{mentioned} is already certified")
                return
            else:
                new_certs.append(mentioned)
    if not new_certs:
        bot.reply_to(msg, "You need to certify at least one user\n"
                          "e\.g\. \"_/cert @foo @bar_\"", parse_mode="MarkdownV2")
    else:
        certified.extend(new_certs)
        bot.reply_to(msg, f"OK, {len(new_certs)} new user(s) have been certified")


@bot.message_handler(commands=["certed"])
def certed(msg: Message):
    bot.reply_to(msg, "Certified user(s): " + ", ".join([f"@{x}" for x in certified]))
"""


@bot.message_handler(commands=["add"])
def add(msg: Message):
    req = parse(bot, msg)
    if not req:
        return
    reqs[req.id] = req
    bot.reply_to(msg, f"Request received\! Temporary id: \n\n"
                      f"*                        _{req.id}_*\n\n"
                      f"You can add more info by sending these commands:\n\n"
                      f"/setname :id  \-  change the clip's i18n name\n"
                      f"/setcat :id  \-  change the clip's category\n\n"
                      f"Then use /publish :id: to publish the clip *\(Need certified privilege\)*",
                 parse_mode="MarkdownV2")


@bot.message_handler(commands=["setname"])
def set_name(msg: Message):
    splitted = msg.text.split()
    print(splitted[1])
    if splitted.__len__() != 2:
        bot.reply_to(msg, "Usage: /setname :id")
        return
    elif (rid := splitted[1]) not in reqs.keys():
        bot.reply_to(msg, f"Cannot find {rid}")
        return
    else:
        bot.reply_to(msg, f"Ok\. Send me a list of name for your clip in different languages\. "
                          f"EN name is mandatory while others are optional\. Please use this format:\n\n"
                          f"*en FOO\_BAR\n"
                          f"zh 歪比巴伯*\n\n"
                          f"We currently support EN, ZH and JP",
                     reply_markup=ForceReply(),
                     parse_mode="MarkdownV2")
        bot.register_next_step_handler(msg, process_name)


def process_name(msg: Message):
    if not re.match(r"([a-zA-Z]{2} .*\n)*", msg.text):
        bot.reply_to(msg, "Invalid format")
        return
    else:
        lang = {(l := x.strip())[0]: l[1] for x in msg.text.split("\n")}
        print(lang)


@bot.message_handler(commands=["setcat"])
def set_cat(msg: Message):
    print(msg)


@bot.message_handler(commands=["stat"])
def stat(msg: Message):
    pass


bot.polling()