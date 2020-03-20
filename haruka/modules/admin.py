import html
from typing import Optional, List

from telegram import Message, Chat, Update, Bot, User
from telegram import ParseMode
from telegram.error import BadRequest
from telegram.ext import CommandHandler, Filters
from telegram.ext.dispatcher import run_async
from telegram.utils.helpers import escape_markdown, mention_html

from haruka import dispatcher, updater
from haruka.modules.disable import DisableAbleCommandHandler
from haruka.modules.helper_funcs.chat_status import bot_admin, can_promote, user_admin, can_pin
from haruka.modules.helper_funcs.extraction import extract_user
from haruka.modules.log_channel import loggable
from haruka.modules.sql import admin_sql as sql
from haruka.modules.translations.strings import tld

from haruka.modules.connection import connected

@run_async
@bot_admin
@user_admin
@loggable
def promote(bot: Bot, update: Update, args: List[str]) -> str:
    message = update.effective_message  # type: Optional[Message]
    user = update.effective_user  # type: Optional[User]
    chat = update.effective_chat  # type: Optional[Chat]
    conn = connected(bot, update, chat, user.id)
    if not conn == False:
        chatD = dispatcher.bot.getChat(conn)
    else:
        chatD = update.effective_chat
        if chat.type == "private":
            exit(1)

    if not chatD.get_member(bot.id).can_promote_members:
        update.effective_message.reply_text("Ich kann hier keine Rechte der Admins verändern!"
                                            "Stelle sicher, dass ich Admin bin, und neue Admins hinzufügen/entfernen kann.")
        exit(1)

    user_id = extract_user(message, args)
    if not user_id:
        message.reply_text(tld(chat.id, "Wen meinst du?"))
        return ""

    user_member = chatD.get_member(user_id)
    if user_member.status == 'administrator' or user_member.status == 'creator':
        message.reply_text(tld(chat.id, "Wie soll ich einen Admin zum Admin machen?"))
        return ""

    if user_id == bot.id:
        message.reply_text(tld(chat.id, "Ich kann mich nicht selbst zum Admin machen. Das kann nur ein Admin dieser Gruppe!"))
        return ""

    # set same perms as bot - bot can't assign higher perms than itself!
    bot_member = chatD.get_member(bot.id)

    bot.promoteChatMember(chatD.id, user_id,
                          can_change_info=bot_member.can_change_info,
                          can_post_messages=bot_member.can_post_messages,
                          can_edit_messages=bot_member.can_edit_messages,
                          can_delete_messages=bot_member.can_delete_messages,
                          #can_invite_users=bot_member.can_invite_users,
                          can_restrict_members=bot_member.can_restrict_members,
                          can_pin_messages=bot_member.can_pin_messages,
                          can_promote_members=bot_member.can_promote_members)

    message.reply_text(tld(chat.id, f"Successfully promoted in *{chatD.title}*!"), parse_mode=ParseMode.MARKDOWN)
    return f"<b>{html.escape(chatD.title)}:</b>" \
            "\n#PROMOTED" \
           f"\n<b>Admin:</b> {mention_html(user.id, user.first_name)}" \
           f"\n<b>User:</b> {mention_html(user_member.user.id, user_member.user.first_name)}"


@run_async
@bot_admin
@user_admin
@loggable
def demote(bot: Bot, update: Update, args: List[str]) -> str:
    chat = update.effective_chat  # type: Optional[Chat]
    message = update.effective_message  # type: Optional[Message]
    user = update.effective_user  # type: Optional[User]
    conn = connected(bot, update, chat, user.id)
    if not conn == False:
        chatD = dispatcher.bot.getChat(conn)
    else:
        chatD = update.effective_chat
        if chat.type == "private":
            exit(1)

    if not chatD.get_member(bot.id).can_promote_members:
        update.effective_message.reply_text("Ich kann hier keine Rechte der Admins verändern! "
                                            "Stelle sicher, dass ich Admin bin, und neue Admins hinzufügen/entfernen kann.")
        exit(1)

    user_id = extract_user(message, args)
    if not user_id:
        message.reply_text(tld(chat.id, "Wen meinst du?"))
        return ""

    user_member = chatD.get_member(user_id)
    if user_member.status == 'creator':
        message.reply_text(tld(chat.id, "Diese Person hat diesen Chat ertsellt, wie soll ich der denn den Adminstatus wegnehmen?"))
        return ""

    if not user_member.status == 'administrator':
        message.reply_text(tld(chat.id, "Ich kann keinem nicht-Admin die Adminrechte wegnehmen!"))
        return ""

    if user_id == bot.id:
        message.reply_text(tld(chat.id, "Wieso sollte ich mir selbst die Adminrechte wegnehmen? xD"))
        return ""

    try:
        bot.promoteChatMember(int(chatD.id), int(user_id),
                              can_change_info=False,
                              can_post_messages=False,
                              can_edit_messages=False,
                              can_delete_messages=False,
                              can_invite_users=False,
                              can_restrict_members=False,
                              can_pin_messages=False,
                              can_promote_members=False)
        message.reply_text(tld(chat.id, f"Successfully demoted in *{chatD.title}*!"), parse_mode=ParseMode.MARKDOWN)
        return f"<b>{html.escape(chatD.title)}:</b>" \
                "\n#DEMOTED" \
               f"\n<b>Admin:</b> {mention_html(user.id, user.first_name)}" \
               f"\n<b>User:</b> {mention_html(user_member.user.id, user_member.user.first_name)}"

    except BadRequest:
        message.reply_text(
            tld(chat.id, "Ich konnte den Nutzer nicht herabstufen. Er hat höhere Rechte als ich!")
            )
        return ""


@run_async
@bot_admin
@can_pin
@user_admin
@loggable
def pin(bot: Bot, update: Update, args: List[str]) -> str:
    user = update.effective_user  # type: Optional[User]
    chat = update.effective_chat  # type: Optional[Chat]

    is_group = chat.type != "private" and chat.type != "channel"

    prev_message = update.effective_message.reply_to_message

    is_silent = True
    if len(args) >= 1:
        is_silent = not (args[0].lower() == 'notify' or args[0].lower() == 'loud' or args[0].lower() == 'violent')

    if prev_message and is_group:
        try:
            bot.pinChatMessage(chat.id, prev_message.message_id, disable_notification=is_silent)
        except BadRequest as excp:
            if excp.message == "Chat_not_modified":
                pass
            else:
                raise
        return f"<b>{html.escape(chat.title)}:</b>" \
                "\n#PINNED" \
               f"\n<b>Admin:</b> {mention_html(user.id, user.first_name)}"

    return ""


@run_async
@bot_admin
@can_pin
@user_admin
@loggable
def unpin(bot: Bot, update: Update) -> str:
    chat = update.effective_chat
    user = update.effective_user  # type: Optional[User]

    try:
        bot.unpinChatMessage(chat.id)
    except BadRequest as excp:
        if excp.message == "Chat_not_modified":
            pass
        else:
            raise

    return f"<b>{html.escape(chat.title)}:</b>" \
           "\n#UNPINNED" \
           f"\n<b>Admin:</b> {mention_html(user.id, user.first_name)}"


@run_async
@bot_admin
@user_admin
def invite(bot: Bot, update: Update):
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    conn = connected(bot, update, chat, user.id, need_admin=False)
    if not conn == False:
        chatP = dispatcher.bot.getChat(conn)
    else:
        chatP = update.effective_chat
        if chat.type == "private":
            exit(1)

    if chatP.username:
        update.effective_message.reply_text(chatP.username)
    elif chatP.type == chatP.SUPERGROUP or chatP.type == chatP.CHANNEL:
        bot_member = chatP.get_member(bot.id)
        if bot_member.can_invite_users:
            invitelink = chatP.invite_link
            #print(invitelink)
            if not invitelink:
                invitelink = bot.exportChatInviteLink(chatP.id)

            update.effective_message.reply_text(invitelink)
        else:
            update.effective_message.reply_text(tld(chat.id, "Ich habe keinen Zugriff auf den Einladungslink!"))
    else:
        update.effective_message.reply_text(tld(chat.id, "Ich kann dir den Einladungslink nür für Supergruppen und Kanäle geben, sorry!"))


@run_async
def adminlist(bot, update):
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    conn = connected(bot, update, chat, user.id, need_admin=False)
    if not conn == False:
        chatP = dispatcher.bot.getChat(conn)
    else:
        chatP = update.effective_chat
        if chat.type == "private":
            exit(1)
    
    administrators = chatP.get_administrators()

    text = tld(chat.id, "Admins im Chat") + " *{}*:".format(chatP.title or tld(chat.id, "this chat"))
    for admin in administrators:
        user = admin.user
        status = admin.status
        if status == "creator":
            name = user.first_name + (user.last_name or "") + tld(chat.id, " (Ersteller)")
        else:
            name = user.first_name + (user.last_name or "")
        text += f"\n• `{name}`"

    update.effective_message.reply_text(text, parse_mode=ParseMode.MARKDOWN)


@user_admin
@run_async
def reaction(bot: Bot, update: Update, args: List[str]) -> str:
    chat = update.effective_chat  # type: Optional[Chat]
    if len(args) >= 1:
        var = args[0]
        print(var)
        if var == "False":
            sql.set_command_reaction(chat.id, False)
            update.effective_message.reply_text("Ich höre nun nur auf Admins!")
        elif var == "True":
            sql.set_command_reaction(chat.id, True)
            update.effective_message.reply_text("Nun können auch normale User die Befehle von mir nutzen.")
        else:
            update.effective_message.reply_text("Gib' bitte true oder false an!", parse_mode=ParseMode.MARKDOWN)
    else:
        status = sql.command_reaction(chat.id)
        if status == False:
            update.effective_message.reply_text("Ich reagiere nun nicht auf Nutzer, die Befehle für Admins nutzen!", parse_mode=ParseMode.MARKDOWN)
        else:
            update.effective_message.reply_text("Ich reagiere nun auf Nutzer, die Befehle für Admins nutzen!", parse_mode=ParseMode.MARKDOWN)
        

__help__ = """
 - /adminlist oder /admins: Liste der Admins in dem entsprechenden Chat

*Nur für Admins:*
 - /pin: Pinnt die gewünschte Nachricht an
 - /unpin: Pinnt die aktuell angepinnte Nachricht ab
 - /Einladungslink: Sendet den aktuellen Einladungslink
 - /promote: Macht den gewünschten Nutzer Admin
 - /demote: Nimmt dem gewüschten Nutzer die Adminrechte weg
"""

__mod_name__ = "Admins"

PIN_HANDLER = DisableAbleCommandHandler("pin", pin, pass_args=True, filters=Filters.group)
UNPIN_HANDLER = DisableAbleCommandHandler("unpin", unpin, filters=Filters.group)

INVITE_HANDLER = CommandHandler("einladungslink", invite)

PROMOTE_HANDLER = DisableAbleCommandHandler("promote", promote, pass_args=True)
DEMOTE_HANDLER = DisableAbleCommandHandler("demote", demote, pass_args=True)

REACT_HANDLER = DisableAbleCommandHandler("reaction", reaction, pass_args=True, filters=Filters.group)

ADMINLIST_HANDLER = DisableAbleCommandHandler(["adminlist", "admins"], adminlist)

dispatcher.add_handler(PIN_HANDLER)
dispatcher.add_handler(UNPIN_HANDLER)
dispatcher.add_handler(INVITE_HANDLER)
dispatcher.add_handler(PROMOTE_HANDLER)
dispatcher.add_handler(DEMOTE_HANDLER)
dispatcher.add_handler(ADMINLIST_HANDLER)
dispatcher.add_handler(REACT_HANDLER)
