import re
import json
import logging
import functools

from src.parser import parse, ClipRequest

from telebot import TeleBot, logger as telelog
from telebot.types import ForceReply, Message, InlineKeyboardMarkup, InlineKeyboardButton
from rushia_clipper import Clipper

logging.basicConfig(level="INFO")
lg = logging.getLogger("clipper")

bot = TeleBot("1033924480:AAF9_4aHpeSsVvqLvEYxbalg1Mjoemw0mSA")
clipper = Clipper()

"""
这是我写的最烂的一次代码，每新加一行我都感觉我在造屎。以后我也不用py写什么callback和闭包了，自闭。这破烂框架谁爱用谁用去吧。
我怀疑写完这些东西第二天我自己都看不懂了（
This is what we called fucking callback hell - in python with freaking named functions
"""

with open("cert.json", "r") as f:
    certified = json.load(f)

reqs = {"abcd": ClipRequest("https://youtu.be/xqsOegkgDAc", "00:01:25", "00:01:30", _id="abcd", cat="moe")}
lang_pattern = re.compile(r"([a-zA-Z]{2} .*\n?)*$")


def log(func):
    @functools.wraps(func)
    def decorator(*args, **kwargs):
        if isinstance((msg := args[0]), Message):
            user = msg.from_user.username
            lg.info(f"[{user}]: {msg.text}")
        else:
            lg.info(f"[Unknown] {func} has been called")
        func(*args, **kwargs)

    return decorator


def reply(msg: Message, text, **kwargs):
    escaped_text = text.replace("\n", r" ")
    lg.info(f"[BOT] ==(Reply)=> [{msg.from_user.username}]: {escaped_text}")
    return bot.reply_to(msg, text, **kwargs)


def edit(text, msg, **kwargs):
    lg.info(f"[BOT] ==(Edit)=> [{msg.message_id}]: {text} ")
    bot.edit_message_text(text, msg.chat.id, msg.message_id, **kwargs)


@bot.message_handler(commands=["cert"])
@log
def cert(msg: Message):
    if not is_certified(msg):
        reply(msg, "You are not certified to do this")
        return
    new_certs = []
    for e in msg.entities:
        if e.type == "mention":
            mentioned = msg.text[e.offset + 1: e.offset + e.length]
            if mentioned in certified:
                reply(msg, f"Sorry, @{mentioned} is already certified")
                return
            else:
                new_certs.append(mentioned)
    if not new_certs:
        reply(msg, "You need to certify at least one user\n"
                   "e\.g\. \"_/cert @foo @bar_\"", parse_mode="MarkdownV2")
    else:
        certified.extend(new_certs)
        reply(msg, f"OK, {len(new_certs)} new user(s) have been certified")


@bot.message_handler(commands=["certed"])
@log
def certed(msg: Message):
    reply(msg, "Certified user(s):\n" + ", ".join([f"@{x}" for x in certified]))


"""
NEW CLIP REQUEST 
"""


@bot.message_handler(commands=["add"])
@log
def add(msg: Message):
    req = parse(bot, msg)
    if not req:
        return
    reqs[req.id] = req
    lg.info(f"[BOT] New request has been added: {req.id}")
    reply(msg, f"Request received\! Temporary id: \n\n"
               f"*                        _{req.id}_*\n\n"
               f"You can add more info by sending these commands:\n\n"
               f"/setname :id  \-  change the clip's i18n name\n"
               f"/setcat :id  \-  change the clip's category\n\n"
               f"Or use /inspect :id to inspect a clip\n"
               f"Then use /publish :id: to publish the clip *\(Need certified privilege\)*",
          parse_mode="MarkdownV2")


"""
SET NAME FOR CLIP REQUEST
"""


@bot.message_handler(commands=["setname"])
@log
def set_name(msg: Message):
    splitted = msg.text.split()
    if not (rid := check_msg(msg)):
        return
    req = reqs[rid]
    reply(msg, f"Ok\. Send me a list of name for your clip in different languages\. "
               f"EN name is mandatory while others are optional\. Please use this format:\n\n"
               f"*en FOO\_BAR\n"
               f"zh 歪比巴伯*\n\n"
               f"We currently support EN, ZH and JP\n"
               f"_*Notice: Old names will be replaced*_",
          reply_markup=ForceReply(),
          parse_mode="MarkdownV2")
    bot.register_next_step_handler(msg, process_name(req))


def process_name(req: ClipRequest):
    @log
    def inner(msg: Message):
        if not lang_pattern.match(msg.text):
            reply(msg, "Invalid format")
            return
        if msg.text.count("en") == 0:
            reply(msg, "Missing EN name")
            return
        else:
            req.name = {(l := x.strip().split())[0]: l[1] for x in msg.text.split("\n")}
            reply(msg, f"Done\! You can add more info by sending these commands:\n\n"
                       f"/setcat :id  \-  change the clip's category\n\n"
                       f"Or use /inspect :id to inspect a clip\n"
                       f"Then use /publish :id: to publish the clip *\(Need certified privilege\)*",
                  parse_mode="MarkdownV2")

    return inner


"""
SET CATEGORY FOR CLIP REQUEST
"""


@bot.message_handler(commands=["setcat"])
@log
def set_cat(msg: Message):
    if not (rid := check_msg(msg)):
        return
    lg.info(f"Setting category for {rid}")
    req = reqs[rid]
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(*[InlineKeyboardButton(x, callback_data=x) for x in clipper.categories] +
                [InlineKeyboardButton("New Category", callback_data="new")])
    reply(msg, "Select one category", reply_markup=markup)
    bot.add_callback_query_handler(bot._build_handler_dict(handle_callback_query(req), func=lambda c: True))


def handle_callback_query(req):  # callback handler - when user had chosen which category
    @log
    def inner(call):
        msg: Message = call.message
        cat = call.data
        if cat == "new":
            new_cat(req, msg)
            return
        req.cat = cat
        edit(f"Ok, clip \"*{req.id}*\" now is categorized as \"_*{call.data}*_\"", msg.chat.id,
             parse_mode="MarkdownV2")

    return inner


@log
def new_cat(req, msg):  # Create a new category
    edit(f"Ok\. Send me a list of name for your new category in different languages\. "
         f"EN name is mandatory while others are optional\. Please use this format:\n\n"
         f"*en moe\n"
         f"zh 萌*\n\n"
         f"We currently support EN, ZH and JP",
         msg.chat.id,
         reply_markup=ForceReply(),
         parse_mode="MarkdownV2")
    bot.register_next_step_handler(msg, new_cat_next_step(req))


def new_cat_next_step(req: ClipRequest):
    # 一个callback一个named function 吃屎啊？？
    # 加个多行匿名函数不行吗狗狗你了
    @log
    def inner(msg: Message):
        lang_dict = {(l := x.strip().split())[0]: l[1] for x in msg.text.split("\n")}
        en_name = lang_dict.get("en")
        if not en_name:
            reply(msg, "Need at least one name in EN")
            return
        clipper.create_category(lang_dict)
        req.cat = en_name
        reply(msg, "Done")

    return inner


@bot.message_handler(commands=["publish"])
@log
def publish(msg: Message):
    if not (rid := check_msg(msg)):
        return
    req = reqs[rid]
    if not req.name or not req.cat:
        reply(msg, "Clip is missing information. "
                   "Use /help for more information")
        return
    if not is_certified(msg):
        reply(msg, f"Nice job! Now certified users will help you finish the publish process soon!\n"
                   f"{' '.join([f'@{x}' for x in certified])}")
        return
    rep: Message = reply(msg, "Sure, generating and going to be published soon!")
    try:
        cat = clipper.check_category(req.cat)
        clip = clipper.generate_clip(req.url, req.interval[0], req.interval[1])
        cat['clips'].append({"url": clip, "name": req.name})
        clipper.set_category()
        reqs.pop(rid)
        edit("Done! Your clip is generated!", rep)
    except Exception as e:
        lg.error(e)
        edit(f"Failed: {e}", rep)


@bot.message_handler(commands=["cats"])
@log
def cats(msg: Message):
    reply(msg, "\n".join([" / ".join(x['name'].values()) for i, x in enumerate(clipper._categories)]))


@bot.message_handler(commands=["inspect"])
@log
def inspect(msg: Message):
    if not (rid := check_msg(msg)):
        return
    reply(msg, get_info(reqs[rid]))


def get_info(req):
    return "\n".join([f"{k}:  {v}" for k, v in req.json.items()])


@bot.message_handler(commands=["help"])
@log
def help(msg: Message):
    reply(msg, f"This is the clipper bot for generating and publishing clips to *Rushia Button*\n\n"
               f"*Basic workflow:*\n\n"
               f"1\)  Use /add :url :start :end to generate a clip request, "
               f"which will give you a four\-letter *temporary id*\n\n"
               f"2\)  Use these commands to add additional information:\n\n"
               f"     /setname :id  \-  change the clip's i18n name\n"
               f"     /setcat :id  \-  change the clip's category\n\n"
               f"3\)  Use /inspect :id to check a clip\n"
               f"4\)  Use /publish :id: to publish the clip *\(Need certified privilege\)*\n\n"
               f"*Additional commands:*\n\n"
               f"     /cats \- show all categories and available languages\n"
               f"     /ls \- list all clip requests \(Published clips will not be shown\)",
          parse_mode="MarkdownV2")


@bot.message_handler(commands=["ls"])
@log
def ls(msg: Message):
    reply(msg, "\n".join([f"{k} - {v.url}" for k, v in reqs.items()]), disable_web_page_preview=True)


def check_msg(msg: Message):
    splitted = msg.text.split()
    if splitted.__len__() != 2:
        reply(msg, f"Usage: {splitted[0]} :id")
        return False
    elif (rid := splitted[1]) not in reqs.keys():
        reply(msg, f"Cannot find {rid}")
        return False
    else:
        return rid


def is_admin(msg: Message):
    if msg.chat.type in ["private", "channel"]:
        return False
    return f"@{msg.from_user.username}" in bot.get_chat_administrators(msg.chat.id)


def is_certified(msg: Message):
    return msg.from_user.username in certified


bot.polling()
