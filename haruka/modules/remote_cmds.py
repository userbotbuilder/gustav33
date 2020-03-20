import html
from typing import Optional, List

from telegram import Message, Chat, Update, Bot, User
from telegram.error import BadRequest
from telegram.ext import run_async, CommandHandler, Filters
from telegram.utils.helpers import mention_html

from haruka import dispatcher
from haruka.modules.helper_funcs.chat_status import bot_admin, user_admin, is_user_ban_protected, can_restrict, \
    is_user_admin, is_user_in_chat, is_bot_admin
from haruka.modules.helper_funcs.extraction import extract_user_and_text
from haruka.modules.helper_funcs.string_handling import extract_time
from haruka.modules.helper_funcs.filters import CustomFilters

RBAN_ERRORS = {
    "User is an administrator of the chat",
    "Chat not found",
    "Not enough rights to restrict/unrestrict chat member",
    "User_not_participant",
    "Peer_id_invalid",
    "Group chat was deactivated",
    "Need to be inviter of a user to kick it from a basic group",
    "Chat_admin_required",
    "Only the creator of a basic group can kick group administrators",
    "Channel_private",
    "Oof, u know u suck at this",
    "Not in the chat"
}

RUNBAN_ERRORS = {
    "User is an administrator of the chat",
    "Chat not found",
    "Not enough rights to restrict/unrestrict chat member",
    "User_not_participant",
    "Peer_id_invalid",
    "Group chat was deactivated",
    "Need to be inviter of a user to kick it from a basic group",
    "Chat_admin_required",
    "Only the creator of a basic group can kick group administrators",
    "Channel_private",
    "Not in the chat"
}

RKICK_ERRORS = {
    "User is an administrator of the chat",
    "Chat not found",
    "Not enough rights to restrict/unrestrict chat member",
    "User_not_participant",
    "Peer_id_invalid",
    "Group chat was deactivated",
    "Need to be inviter of a user to kick it from a basic group",
    "Chat_admin_required",
    "Only the creator of a basic group can kick group administrators",
    "Channel_private",
    "Not in the chat"
}

RMUTE_ERRORS = {
    "User is an administrator of the chat",
    "Chat not found",
    "Not enough rights to restrict/unrestrict chat member",
    "User_not_participant",
    "Peer_id_invalid",
    "Group chat was deactivated",
    "Need to be inviter of a user to kick it from a basic group",
    "Chat_admin_required",
    "Only the creator of a basic group can kick group administrators",
    "Channel_private",
    "Not in the chat"
}

RUNMUTE_ERRORS = {
    "User is an administrator of the chat",
    "Chat not found",
    "Not enough rights to restrict/unrestrict chat member",
    "User_not_participant",
    "Peer_id_invalid",
    "Group chat was deactivated",
    "Need to be inviter of a user to kick it from a basic group",
    "Chat_admin_required",
    "Only the creator of a basic group can kick group administrators",
    "Channel_private",
    "Not in the chat"
}

@run_async
@bot_admin
def rban(bot: Bot, update: Update, args: List[str]):
    message = update.effective_message

    if not args:
        message.reply_text("Du beziehst dich auf keine Gruppe/Nutzer.")
        return

    user_id, chat_id = extract_user_and_text(message, args)

    if not user_id:
        message.reply_text("Wie bitte? Wen meinst du?")
        return
    elif not chat_id:
        message.reply_text("Du beziehst dich auf keinen Chat")
        return

    try:
        chat = bot.get_chat(chat_id.split()[0])
    except BadRequest as excp:
        if excp.message == "Chat not found":
            message.reply_text("Chat nicht gefunden! Stelle sicher, dass die angegebene Gruppen-ID richtig ist, und dass ich in der angegebenen Gruppe bin")
            return
        else:
            raise

    if chat.type == 'private':
        message.reply_text("Sorry, das ist ein privater Chat!")
        return

    if not is_bot_admin(chat, bot.id) or not chat.get_member(bot.id).can_restrict_members:
        message.reply_text("Ich kann dort keine Personen entfernen! Stelle sicher, dass ich in der Gruppe Admin bin, und Nutzer entfernen kann")
        return

    try:
        member = chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message == "User not found":
            message.reply_text("Ich kann diesen User nicht finden.")
            return
        else:
            raise

    if is_user_ban_protected(chat, user_id, member):
        message.reply_text("Ich will wirklich mal die Admins verbannen...")
        return

    if user_id == bot.id:
        message.reply_text("Ich verbanne mich nicht selbst, sehe ich so aus?")
        return

    try:
        chat.kick_member(user_id)
        message.reply_text("Verbannt im Chat!")
    except BadRequest as excp:
        if excp.message == "Reply message not found":
            # Do not reply
            message.reply_text('Verbannt!', quote=False)
        elif excp.message in RBAN_ERRORS:
            message.reply_text(excp.message)
        else:
            LOGGER.warning(update)
            LOGGER.exception("ERROR banning user %s in chat %s (%s) due to %s", user_id, chat.title, chat.id,
                             excp.message)
            message.reply_text("Shit, ich kann die olle Klette nicht entfernen...")

@run_async
@bot_admin
def runban(bot: Bot, update: Update, args: List[str]):
    message = update.effective_message

    if not args:
        message.reply_text("Du beziehst dich auf keinen Chat/Nutzer.")
        return

    user_id, chat_id = extract_user_and_text(message, args)

    if not user_id:
        message.reply_text("Du beziehst dich auf keinen Nutzer.")
        return
    elif not chat_id:
        message.reply_text("Du beziehst dich auf keinen Chat.")
        return

    try:
        chat = bot.get_chat(chat_id.split()[0])
    except BadRequest as excp:
        if excp.message == "Chat not found":
            message.reply_text("Chat nicht gefunden! Stelle sicher, dass du die richtige Chat-ID angegeben hast, und dass ich in der angegebenen Gruppe bin")
            return
        else:
            raise

    if chat.type == 'private':
        message.reply_text("Sorry, das ist ein privater Chat!")
        return

    if not is_bot_admin(chat, bot.id) or not chat.get_member(bot.id).can_restrict_members:
        message.reply_text("Ich kann hier keine Sperren von Nutzern aufheben! Stelle sicher, dass ich Admin bin.")
        return

    try:
        member = chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message == "User not found":
            message.reply_text("Ich kann diesen Nutzer dort nicht sehen!")
            return
        else:
            raise
            
    if is_user_in_chat(chat, user_id):
        message.reply_text("Wieso willst du jemanden entbannen, der bereits im Chat ist?")
        return

    if user_id == bot.id:
        message.reply_text("Ich werde mich doch da nicht ENTBANNEN, ich bin doch drin!")
        return

    try:
        chat.unban_member(user_id)
        message.reply_text("Ja, dieser Nutzer kann dem Chat wieder beitreten!")
    except BadRequest as excp:
        if excp.message == "Reply message not found":
            # Do not reply
            message.reply_text('Unbanned!', quote=False)
        elif excp.message in RUNBAN_ERRORS:
            message.reply_text(excp.message)
        else:
            LOGGER.warning(update)
            LOGGER.exception("ERROR unbanning user %s in chat %s (%s) due to %s", user_id, chat.title, chat.id,
                             excp.message)
            message.reply_text("Shit, ich kann diesen Nutzer nicht entbannen.")

@run_async
@bot_admin
def rkick(bot: Bot, update: Update, args: List[str]):
    message = update.effective_message

    if not args:
        message.reply_text("Du beziehst dich auf keinen Chat/Nutzer.")
        return

    user_id, chat_id = extract_user_and_text(message, args)

    if not user_id:
        message.reply_text("Du beziehst dich auf keinen Nutzer.")
        return
    elif not chat_id:
        message.reply_text("Du beziehst dich auf keinen Chat.")
        return

    try:
        chat = bot.get_chat(chat_id.split()[0])
    except BadRequest as excp:
        if excp.message == "Chat not found":
            message.reply_text("Chat nicht gefunden! Stelle sicher, dass du die richtige Chat-ID angegeben hast, und dass ich in der angegebenen Gruppe bin.")
            return
        else:
            raise

    if chat.type == 'private':
        message.reply_text("Sorry, das ist ein privater Chat!")
        return

    if not is_bot_admin(chat, bot.id) or not chat.get_member(bot.id).can_restrict_members:
        message.reply_text("Ich kann dort keine Nutzer entfernen! Stelle sicher, dass ich dort dieses Recht besitze.")
        return

    try:
        member = chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message == "User not found":
            message.reply_text("Ich kann diesen Nutzer nicht finden")
            return
        else:
            raise

    if is_user_ban_protected(chat, user_id, member):
        message.reply_text("Ich wünschte, ich könnte Admins verbannen...")
        return

    if user_id == bot.id:
        message.reply_text("Ich werde mich nicht selbst kicken, sehe ich so aus?")
        return

    try:
        chat.unban_member(user_id)
        message.reply_text("Kicked from chat!")
    except BadRequest as excp:
        if excp.message == "Reply message not found":
            # Do not reply
            message.reply_text('Gekickt!', quote=False)
        elif excp.message in RKICK_ERRORS:
            message.reply_text(excp.message)
        else:
            LOGGER.warning(update)
            LOGGER.exception("ERROR kicking user %s in chat %s (%s) due to %s", user_id, chat.title, chat.id,
                             excp.message)
            message.reply_text("Shit, ich kann diese Klette nicht kicken.")

@run_async
@bot_admin
def rmute(bot: Bot, update: Update, args: List[str]):
    message = update.effective_message

    if not args:
        message.reply_text("Du beziehst dich auf keinen Chat/Nutzer.")
        return

    user_id, chat_id = extract_user_and_text(message, args)

    if not user_id:
        message.reply_text("Du beziehst dich auf keinen Nutzer.")
        return
    elif not chat_id:
        message.reply_text("Du beziehst dich auf keine Gruppe.")
        return

    try:
        chat = bot.get_chat(chat_id.split()[0])
    except BadRequest as excp:
        if excp.message == "Chat not found":
            message.reply_text("Chat nicht gefunden! Stelle sicher, dass du die richtige Chat-ID angegeben hast, und dass ich in der angegebenen Gruppe bin.")
            return
        else:
            raise

    if chat.type == 'private':
        message.reply_text("Sorry, das ist ein privater Chat!")
        return

    if not is_bot_admin(chat, bot.id) or not chat.get_member(bot.id).can_restrict_members:
        message.reply_text("Ich kann hier keine Nutzer einschränken! Stelle sicher, dass ich die Rechte dazu habe")
        return

    try:
        member = chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message == "User not found":
            message.reply_text("Ich kann diesen Nutzer nicht finden")
            return
        else:
            raise

    if is_user_ban_protected(chat, user_id, member):
        message.reply_text("Schade, dass ich den Admins nicht das Maul stopfen kann...")
        return

    if user_id == bot.id:
        message.reply_text("Ich stelle mich nicht selbst stumm, sehe ich so aus?")
        return

    try:
        bot.restrict_chat_member(chat.id, user_id, can_send_messages=False)
        message.reply_text("Stummgeschalten im Chat!")
    except BadRequest as excp:
        if excp.message == "Reply message not found":
            # Do not reply
            message.reply_text('Muted!', quote=False)
        elif excp.message in RMUTE_ERRORS:
            message.reply_text(excp.message)
        else:
            LOGGER.warning(update)
            LOGGER.exception("ERROR mute user %s in chat %s (%s) due to %s", user_id, chat.title, chat.id,
                             excp.message)
            message.reply_text("Shit, ich kann diesen Nutzer nicht stummschalten.")

@run_async
@bot_admin
def runmute(bot: Bot, update: Update, args: List[str]):
    message = update.effective_message

    if not args:
        message.reply_text("Du beziehst dich auf keinen Chat/Nutzer.")
        return

    user_id, chat_id = extract_user_and_text(message, args)

    if not user_id:
        message.reply_text("Du beziehst dich auf keinen Nutzer.")
        return
    elif not chat_id:
        message.reply_text("Du beziehst dich auf keinen Chat.")
        return

    try:
        chat = bot.get_chat(chat_id.split()[0])
    except BadRequest as excp:
        if excp.message == "Chat not found":
            message.reply_text("Chat nicht gefunden! Stelle sicher, dass du die richtige Chat-ID angegeben hast, und dass ich in der angegebenen Gruppe bin.")
            return
        else:
            raise

    if chat.type == 'private':
        message.reply_text("Sorry, das ist ein privater Chat!")
        return

    if not is_bot_admin(chat, bot.id) or not chat.get_member(bot.id).can_restrict_members:
        message.reply_text("Ich kann hier keine Einschränkungen aufheben! Stelle sicher, dass ich dazu die Berechtigung besitze")
        return

    try:
        member = chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message == "User not found":
            message.reply_text("Ohje, ich sehe diesen Nutzer dort nicht")
            return
        else:
            raise
            
    if is_user_in_chat(chat, user_id):
       if member.can_send_messages and member.can_send_media_messages \
          and member.can_send_other_messages and member.can_add_web_page_previews:
        message.reply_text("This user already has the right to speak in that chat.")
        return

    if user_id == bot.id:
        message.reply_text("Wie soll ich meine nicht vorhandene Stummschaltung aufheben?")
        return

    try:
        bot.restrict_chat_member(chat.id, int(user_id),
                                     can_send_messages=True,
                                     can_send_media_messages=True,
                                     can_send_other_messages=True,
                                     can_add_web_page_previews=True)
        message.reply_text("Yeah, dieser Nutzer kann wieder Nachrichten senden!")
    except BadRequest as excp:
        if excp.message == "Reply message not found":
            # Do not reply
            message.reply_text('Stummschaltung aufgehoben!', quote=False)
        elif excp.message in RUNMUTE_ERRORS:
            message.reply_text(excp.message)
        else:
            LOGGER.warning(update)
            LOGGER.exception("ERROR unmnuting user %s in chat %s (%s) due to %s", user_id, chat.title, chat.id,
                             excp.message)
            message.reply_text("Shit, ich kann die Stummschaltung für diesen Nutzer nicht aufheben!")

__help__ = ""

__mod_name__ = "Remote-Befehle"

RBAN_HANDLER = CommandHandler("rban", rban, pass_args=True, filters=CustomFilters.sudo_filter)
RUNBAN_HANDLER = CommandHandler("runban", runban, pass_args=True, filters=CustomFilters.sudo_filter)
RKICK_HANDLER = CommandHandler("rkick", rkick, pass_args=True, filters=CustomFilters.sudo_filter)
RMUTE_HANDLER = CommandHandler("rmute", rmute, pass_args=True, filters=CustomFilters.sudo_filter)
RUNMUTE_HANDLER = CommandHandler("runmute", runmute, pass_args=True, filters=CustomFilters.sudo_filter)

dispatcher.add_handler(RBAN_HANDLER)
dispatcher.add_handler(RUNBAN_HANDLER)
dispatcher.add_handler(RKICK_HANDLER)
dispatcher.add_handler(RMUTE_HANDLER)
dispatcher.add_handler(RUNMUTE_HANDLER)
