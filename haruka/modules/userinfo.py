import html
from typing import Optional, List

from telegram import Message, Update, Bot, User
from telegram import ParseMode, MAX_MESSAGE_LENGTH
from telegram.ext.dispatcher import run_async
from telegram.utils.helpers import escape_markdown

import haruka.modules.sql.userinfo_sql as sql
from haruka import dispatcher, SUDO_USERS, OWNER_ID
from haruka.modules.disable import DisableAbleCommandHandler
from haruka.modules.helper_funcs.extraction import extract_user


@run_async
def about_me(bot: Bot, update: Update, args: List[str]):
    message = update.effective_message  # type: Optional[Message]
    user_id = extract_user(message, args)

    if user_id:
        user = bot.get_chat(user_id)
    else:
        user = message.from_user

    info = sql.get_user_me_info(user.id)

    if info:
        update.effective_message.reply_text("*{}*:\n{}".format(user.first_name, escape_markdown(info)),
                                            parse_mode=ParseMode.MARKDOWN)
    elif message.reply_to_message:
        username = message.reply_to_message.from_user.first_name
        update.effective_message.reply_text(username + " hat noch keine Info über sich selbst festgelegt!")
    else:
        update.effective_message.reply_text("Du hast noch keine Info über dich selbst festgelegt!")


@run_async
def set_about_me(bot: Bot, update: Update):
    message = update.effective_message  # type: Optional[Message]
    user_id = message.from_user.id
    text = message.text
    info = text.split(None, 1)  # use python's maxsplit to only remove the cmd, hence keeping newlines.
    if len(info) == 2:
        if len(info[1]) < MAX_MESSAGE_LENGTH // 4:
            sql.set_user_me_info(user_id, info[1])
            message.reply_text("Ich hab deine Info erneuert!")
        else:
            message.reply_text(
                "Deine Info muss kürzer als {} Zeichen sein! Du hast {} gesetzt.".format(MAX_MESSAGE_LENGTH // 4, len(info[1])))


@run_async
def about_bio(bot: Bot, update: Update, args: List[str]):
    message = update.effective_message  # type: Optional[Message]

    user_id = extract_user(message, args)
    if user_id:
        user = bot.get_chat(user_id)
    else:
        user = message.from_user

    info = sql.get_user_bio(user.id)

    if info:
        update.effective_message.reply_text("*{}*:\n{}".format(user.first_name, escape_markdown(info)),
                                            parse_mode=ParseMode.MARKDOWN)
    elif message.reply_to_message:
        username = user.first_name
        update.effective_message.reply_text("{} hat noch nichts über sich festgelegt!".format(username))
    else:
        update.effective_message.reply_text("Du hast noch keine Beschreibung über dich selbst hinzugefügt!")


@run_async
def set_about_bio(bot: Bot, update: Update):
    message = update.effective_message  # type: Optional[Message]
    sender = update.effective_user  # type: Optional[User]
    if message.reply_to_message:
        repl_message = message.reply_to_message
        user_id = repl_message.from_user.id
        if user_id == message.from_user.id:
            message.reply_text("Ha! Du kannst nicht deine eigene Bio festlegen! Das können nur deine Mitmenschen")
            return
        elif user_id == bot.id and sender.id not in SUDO_USERS:
            message.reply_text("Äm.. Ja.. Ich vertraue nur meinem Inhaber, also kann nur er meine Bio setzen.")
            return
        elif user_id in SUDO_USERS and sender.id not in SUDO_USERS:
            message.reply_text("Äm.. Ja.. Ich vertraue nur meinem Inhaber, also kann nur er seine Bio setzen.")
            return
        elif user_id == OWNER_ID:
            message.reply_text("Du setzt nicht die Bio meines Meisters...haha")
            return

        text = message.text
        bio = text.split(None, 1)  # use python's maxsplit to only remove the cmd, hence keeping newlines.
        if len(bio) == 2:
            if len(bio[1]) < MAX_MESSAGE_LENGTH // 4:
                sql.set_user_bio(user_id, bio[1])
                message.reply_text("Ich habe die Bio von {}'s erneuert!".format(repl_message.from_user.first_name))
            else:
                message.reply_text(
                    "Deine Bio muss kürzer als {} Zeichen sein! Du hast {} gesetzt.".format(
                        MAX_MESSAGE_LENGTH // 4, len(bio[1])))
    else:
        message.reply_text("Antworte auf die Nachricht von jemandem, um eine Bio für ihn vorzuschlagen!")


def __user_info__(user_id, chat_id):
    bio = html.escape(sql.get_user_bio(user_id) or "")
    me = html.escape(sql.get_user_me_info(user_id) or "")
    if bio and me:
        return "<b>Über den Nutzer:</b>\n{me}\n<b>Was andere sagen:</b>\n{bio}".format(me=me, bio=bio)
    elif bio:
        return "<b>Was andere sagen:</b>\n{bio}\n".format(me=me, bio=bio)
    elif me:
        return "<b>Über den Nutzer:</b>\n{me}""".format(me=me, bio=bio)
    else:
        return ""


def __gdpr__(user_id):
    sql.clear_user_info(user_id)
    sql.clear_user_bio(user_id)


__help__ = """
 - /setbio <text>: Antworte auf eine Nachricht eines Nutzers, um deine Meinung über ihn mitzuteilen
 - /bio: Ruft die Bio eines anderen Nutzers ab.
 - /setme <text>: Setzt die angegebene Info über dich.
 - /me: Ruft die Info von dir ab.
"""

__mod_name__ = "Bios und Beschreibungen"

SET_BIO_HANDLER = DisableAbleCommandHandler("setbio", set_about_bio)
GET_BIO_HANDLER = DisableAbleCommandHandler("bio", about_bio, pass_args=True)

SET_ABOUT_HANDLER = DisableAbleCommandHandler("setme", set_about_me)
GET_ABOUT_HANDLER = DisableAbleCommandHandler("me", about_me, pass_args=True)

dispatcher.add_handler(SET_BIO_HANDLER)
dispatcher.add_handler(GET_BIO_HANDLER)
dispatcher.add_handler(SET_ABOUT_HANDLER)
dispatcher.add_handler(GET_ABOUT_HANDLER)

