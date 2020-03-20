import html
from typing import Optional, List

from telegram import Message, Chat, Update, Bot, User
from telegram.error import BadRequest
from telegram.ext import run_async, CommandHandler, Filters
from telegram.utils.helpers import mention_html

from haruka import dispatcher, BAN_STICKER, LOGGER
from haruka.modules.disable import DisableAbleCommandHandler
from haruka.modules.helper_funcs.chat_status import bot_admin, user_admin, is_user_ban_protected, can_restrict, \
    is_user_admin, is_user_in_chat
from haruka.modules.helper_funcs.extraction import extract_user_and_text
from haruka.modules.helper_funcs.string_handling import extract_time
from haruka.modules.log_channel import loggable

from haruka.modules.translations.strings import tld


@run_async
@bot_admin
@can_restrict
@user_admin
@loggable
def ban(bot: Bot, update: Update, args: List[str]) -> str:
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    message = update.effective_message  # type: Optional[Message]

    user_id, reason = extract_user_and_text(message, args)

    if not user_id:
        message.reply_text(tld(chat.id, "Wie bitte? Wen meinst du?"))
        return ""

    try:
        member = chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message == "User not found":
            message.reply_text(tld(chat.id, "Ich kann diesen Nutzer nicht finden"))
            return ""
        else:
            raise

    if user_id == bot.id:
        message.reply_text(tld(chat.id, "Ich werde mich nicht selbst verbannen.. Sehe ich so aus?"))
        return ""

    if is_user_ban_protected(chat, user_id, member):
        message.reply_text(tld(chat.id, "Wieso sollte ich die treuen Admins dieser Gruppe aus ihr verbannen? Wäre doch ziemlich dumm."))
        return ""

    log = "<b>{}:</b>" \
          "\n#BANNED" \
          "\n<b>• Admin:</b> {}" \
          "\n<b>• User:</b> {}" \
          "\n<b>• ID:</b> <code>{}</code>".format(html.escape(chat.title), mention_html(user.id, user.first_name), 
                                                  mention_html(member.user.id, member.user.first_name), user_id)

    reply = "{} has been banned!".format(mention_html(member.user.id, member.user.first_name))

    if reason:
        log += "\n<b>Grund:</b> {}".format(reason)

    try:
        chat.kick_member(user_id)
        #bot.send_sticker(chat.id, BAN_STICKER)  # banhammer marie sticker
        message.reply_text(tld(chat.id, "Verbannt!"))
        return log

    except BadRequest as excp:
        if excp.message == "Reply message not found":
            # Do not reply
            #bot.send_sticker(chat.id, BAN_STICKER)  # banhammer marie sticker
            message.reply_text(tld(chat.id, "Verbannt!"), quote=False)
            return log
        else:
            LOGGER.warning(update)
            LOGGER.exception("ERROR banning user %s in chat %s (%s) due to %s", user_id, chat.title, chat.id,
                             excp.message)
            message.reply_text(tld(chat.id, "Diese Klette kann ich leider nicht entfernen..."))

    return ""


@run_async
@bot_admin
@can_restrict
@user_admin
@loggable
def temp_ban(bot: Bot, update: Update, args: List[str]) -> str:
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    message = update.effective_message  # type: Optional[Message]

    user_id, reason = extract_user_and_text(message, args)

    if not user_id:
        message.reply_text(tld(chat.id, "Wie bitte? Wen meinst du?"))
        return ""

    try:
        member = chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message == "User not found":
            message.reply_text(tld(chat.id, "Ich kenne diesen Nutzer nicht"))
            return ""
        else:
            raise

    if is_user_ban_protected(chat, user_id, member):
        message.reply_text(tld(chat.id, "Dieser Nutzer ist mein Heiligtum!"))
        return ""

    if user_id == bot.id:
        message.reply_text(tld(chat.id, "Wieso sollte ich mich selbst verbannen? Sehe ich so aus?"))
        return ""

    if not reason:
        message.reply_text(tld(chat.id, "Wie lange soll ich diesen Nutzer verbannen? Gib' es bitte an."))
        return ""

    split_reason = reason.split(None, 1)

    time_val = split_reason[0].lower()
    if len(split_reason) > 1:
        reason = split_reason[1]
    else:
        reason = ""

    bantime = extract_time(message, time_val)

    if not bantime:
        return ""

    log = "<b>{}:</b>" \
          "\n#TEMP BANNED" \
          "\n<b>Admin:</b> {}" \
          "\n<b>User:</b> {} (<code>{}</code>)" \
          "\n<b>Time:</b> {}".format(html.escape(chat.title),
                                     mention_html(user.id, user.first_name),
                                     mention_html(member.user.id, member.user.first_name),
                                     member.user.id,
                                     time_val)
    if reason:
        log += "\n<b>Grund:</b> {}".format(reason)

    try:
        chat.kick_member(user_id, until_date=bantime)
        #bot.send_sticker(chat.id, BAN_STICKER)  # banhammer marie sticker
        message.reply_text("Verbannt! Der Nutzer ist raus für {}.".format(time_val))
        return log

    except BadRequest as excp:
        if excp.message == "Reply message not found":
            # Do not reply
            #bot.send_sticker(chat.id, BAN_STICKER)  # banhammer marie sticker
            message.reply_text(tld(chat.id, "Verbannt! Der Nutzer ist raus für {}.").format(time_val), quote=False)
            return log
        else:
            LOGGER.warning(update)
            LOGGER.exception("ERROR banning user %s in chat %s (%s) due to %s", user_id, chat.title, chat.id,
                             excp.message)
            message.reply_text(tld(chat.id, "Leider kann ich diese Klette nicht entfernen..."))

    return ""


@run_async
@bot_admin
@can_restrict
@user_admin
@loggable
def kick(bot: Bot, update: Update, args: List[str]) -> str:
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    message = update.effective_message  # type: Optional[Message]

    user_id, reason = extract_user_and_text(message, args)

    if not user_id:
        return ""

    try:
        member = chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message == "User not found":
            message.reply_text("Ich kann diesen Nutzer nicht finden...")
            return ""
        else:
            raise

    if user_id == bot.id:
        message.reply_text("Ich kicke mich doch nicht selbst!")
        return ""

    if is_user_ban_protected(chat, user_id):
        message.reply_text("Wieso sollte ich einen Admin aus seiner Gruppe kicken? Klingt ziemlich dumm.")
        return ""

    res = chat.unban_member(user_id)  # unban on current user = kick
    if res:
        #bot.send_sticker(chat.id, BAN_STICKER)  # banhammer marie sticker
        message.reply_text("Rausgeschmissen!")
        log = "<b>{}:</b>" \
              "\n#KICKED" \
              "\n<b>Admin:</b> {}" \
              "\n<b>User:</b> {} (<code>{}</code>)".format(html.escape(chat.title),
                                                           mention_html(user.id, user.first_name),
                                                           mention_html(member.user.id, member.user.first_name),
                                                           member.user.id)
        if reason:
            log += "\n<b>Grund:</b> {}".format(reason)

        return log

    else:
        message.reply_text("Diese Klette ist zu schwer, ich kann sie leider Gottes nicht raus*schmeißen*.")

    return ""


@run_async
@bot_admin
@can_restrict
def kickme(bot: Bot, update: Update):
    user_id = update.effective_message.from_user.id
    if is_user_admin(update.effective_chat, user_id):
        update.effective_message.reply_text("Wieso sollte ich einen Admin aus seiner Gruppe kicken? Klingt ziemlich dumm.")
        return

    res = update.effective_chat.unban_member(user_id)  # unban on current user = kick
    if res:
        update.effective_message.reply_text("Ach, auch dir sollen Flügel wachsen? Kein Problem.")
    else:
        update.effective_message.reply_text("Huh? kann ich nicht machen :/")


@run_async
@bot_admin
@can_restrict
@loggable
def banme(bot: Bot, update: Update):
    user_id = update.effective_message.from_user.id
    chat = update.effective_chat
    user = update.effective_user
    if is_user_admin(update.effective_chat, user_id):
        update.effective_message.reply_text("Wieso sollte ich einen Admin aus seiner eigenen Gruppe verbannen? Klingt ziemlich dumm.")
        return

    res = update.effective_chat.kick_member(user_id)  
    if res:
        update.effective_message.reply_text("Kein Problem. Verbannt.")
        log = "<b>{}:</b>" \
              "\n#BANME" \
              "\n<b>User:</b> {}" \
              "\n<b>ID:</b> <code>{}</code>".format(html.escape(chat.title),
                                                    mention_html(user.id, user.first_name), user_id)
        return log

    else:
        update.effective_message.reply_text("Huh? Kann ich leider nicht :/")


@run_async
@bot_admin
@can_restrict
@user_admin
@loggable
def unban(bot: Bot, update: Update, args: List[str]) -> str:
    message = update.effective_message  # type: Optional[Message]
    user = update.effective_user  # type: Optional[User]
    chat = update.effective_chat  # type: Optional[Chat]

    user_id, reason = extract_user_and_text(message, args)

    if not user_id:
        return ""

    try:
        member = chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message == "User not found":
            message.reply_text("Ich kann diesen Nutzer nicht finden")
            return ""
        else:
            raise

    if user_id == bot.id:
        message.reply_text("Wie soll ich mich bitte entbannen, wenn ich dann nicht da wäre?")
        return ""

    if is_user_in_chat(chat, user_id):
        message.reply_text("Wieso willst du jemanden entbannen, der bereits im Chat ist?")
        return ""

    chat.unban_member(user_id)
    message.reply_text("Yep, der Nutzer kann wieder zu uns!")

    log = "<b>{}:</b>" \
          "\n#UNBANNED" \
          "\n<b>Admin:</b> {}" \
          "\n<b>User:</b> {} (<code>{}</code>)".format(html.escape(chat.title),
                                                       mention_html(user.id, user.first_name),
                                                       mention_html(member.user.id, member.user.first_name),
                                                       member.user.id)
    if reason:
        log += "\n<b>Grund:</b> {}".format(reason)

    return log


@run_async
@bot_admin
@can_restrict
@user_admin
@loggable
def sban(bot: Bot, update: Update, args: List[str]) -> str:
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    message = update.effective_message  # type: Optional[Message]

    update.effective_message.delete()

    user_id, reason = extract_user_and_text(message, args)

    if not user_id:
        return ""

    try:
        member = chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message == "Nutzer nicht gefunden":
            return ""
        else:
            raise

    if is_user_ban_protected(chat, user_id, member):
        return ""

    if user_id == bot.id:
        return ""

    log = "<b>{}:</b>" \
          "\n# SILENTBAN" \
          "\n<b>• Admin:</b> {}" \
          "\n<b>• User:</b> {}" \
          "\n<b>• ID:</b> <code>{}</code>".format(html.escape(chat.title), mention_html(user.id, user.first_name), 
                                                  mention_html(member.user.id, member.user.first_name), user_id)
    if reason:
        log += "\n<b>• Grund:</b> {}".format(reason)

    try:
        chat.kick_member(user_id)
        return log

    except BadRequest as excp:
        if excp.message == "Reply message not found":
            return log
        else:
            LOGGER.warning(update)
            LOGGER.exception("ERROR banning user %s in chat %s (%s) due to %s", user_id, chat.title, chat.id, excp.message)       
    return ""


__help__ = """
Manche Leute müssen so verbannt werden, dass es alle mitbekommen. z.B. Trolls, Spammer etc..

Mit dieser Funktion ist es möglich, diese Ganoven schnell und einfach zu entfernen, und gleichzeitig an's Licht zu bringen!

Die verfügbaren Befehle:
 - /ban: Bannt den gewünschten Nutzer aus der Gruppe.
 - /banme: Dich selbst verbannen.
 - /tban: Einen Nutzer temporär verbannen. Bei der Zeitangabe <d/h/m> (Tage|Stunden|Minuten) nutzen.
 - /unban: Einen verbannten Nutzer wieder in den Chat lassen.
 - /sban: Einen Nutzer stillschweigend verbannen.
 - /mute: Einen Nutzer in dem Chat stummschalten.
 - /tmute: Einen Nutzer temporär stummschalten. Bei der Zeitangabe <d/h/m> (Tage|Stunden|Minuten) nutzen.
 - /unmute: Die Stummschaltung für einen entsprechenden Nutzer aufheben.
 - /kick: Kickt einen Nutzewr aus deinem Chat.
 - /kickme: Derjenige, wo das nutzt, wird gekickt!
"""

__mod_name__ = "Nutzer einschränken"

BAN_HANDLER = DisableAbleCommandHandler("ban", ban, pass_args=True, filters=Filters.group, admin_ok=True)
TEMPBAN_HANDLER = DisableAbleCommandHandler(["tban", "tempban"], temp_ban, pass_args=True, filters=Filters.group, admin_ok=True)
KICK_HANDLER = DisableAbleCommandHandler("kick", kick, pass_args=True, filters=Filters.group, admin_ok=True)
UNBAN_HANDLER = DisableAbleCommandHandler("unban", unban, pass_args=True, filters=Filters.group, admin_ok=True)
KICKME_HANDLER = DisableAbleCommandHandler("kickme", kickme, filters=Filters.group)
SBAN_HANDLER = DisableAbleCommandHandler("sban", sban, pass_args=True, filters=Filters.group, admin_ok=True)
BANME_HANDLER = DisableAbleCommandHandler("banme", banme, filters=Filters.group)

dispatcher.add_handler(BAN_HANDLER)
dispatcher.add_handler(TEMPBAN_HANDLER)
dispatcher.add_handler(KICK_HANDLER)
dispatcher.add_handler(UNBAN_HANDLER)
dispatcher.add_handler(KICKME_HANDLER)
dispatcher.add_handler(BANME_HANDLER)
dispatcher.add_handler(SBAN_HANDLER)
