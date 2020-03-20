import html
from io import BytesIO
from typing import Optional, List
import random
import uuid
import re
import json
import time
from time import sleep

from future.utils import string_types
from telegram.error import BadRequest, TelegramError, Unauthorized
from telegram import ParseMode, Update, Bot, Chat, User, MessageEntity, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import run_async, CommandHandler, MessageHandler, Filters, CallbackQueryHandler
from telegram.utils.helpers import escape_markdown, mention_html, mention_markdown

from haruka import dispatcher, OWNER_ID, SUDO_USERS, WHITELIST_USERS, MESSAGE_DUMP, LOGGER
from haruka.modules.helper_funcs.handlers import CMD_STARTERS
from haruka.modules.helper_funcs.misc import is_module_loaded, send_to_list
from haruka.modules.helper_funcs.chat_status import is_user_admin
from haruka.modules.helper_funcs.extraction import extract_user, extract_user_and_text
from haruka.modules.helper_funcs.string_handling import markdown_parser
from haruka.modules.disable import DisableAbleCommandHandler

import haruka.modules.sql.feds_sql as sql

# Hello bot owner, I spended for feds many hours of my life, Please don't remove this if you still respect MrYacha and peaktogoo and AyraHikari too
# Federation by MrYacha 2018-2019
# Federation rework by Mizukito Akito 2019
# Federation update v2 by Ayra Hikari 2019
#
# Time spended on feds = 10h by #MrYacha
# Time spended on reworking on the whole feds = 22+ hours by @RealAkito
# Time spended on updating version to v2 = 26+ hours by @AyraHikari
#
# Total spended for making this features is 68+ hours

LOGGER.info("Föderationen- NEU!")


FBAN_ERRORS = {
	"Der Nutzer ist Admin",
	"Chat nicht gefunden",
	"Ich besitze nicht genug Rechte, Nutzer zu verbannen/entbannen",
	"User_not_participant",
	"Peer_id_invalid",
	"Gruppe wurde deaktiviert",
	"Need to be inviter of a user to kick it from a basic group",
	"Chat_admin_required",
	"Only the creator of a basic group can kick group administrators",
	"Channel_private",
	"Ich bin nicht mehr in dem gewünschten Chat",
	"Ich kann dort keine Nachrichten senden"
}

UNFBAN_ERRORS = {
	"Nutzer ist ein Admin des Chats",
	"Chat nicht gefunden",
	"Ich besitze nicht genug Rechte, Nutzer zu verbannen/entbannen",
	"User_not_participant",
	"Method is available for supergroup and channel chats only",
	"Not in the chat",
	"Channel_private",
	"Ich muss Admin sein",
	"Ich kann dort keine Nachrichten senden"
}

@run_async
def new_fed(bot: Bot, update: Update):
	chat = update.effective_chat  # type: Optional[Chat]
	user = update.effective_user  # type: Optional[User]
	message = update.effective_message
	if chat.type != "private":
		update.effective_message.reply_text("Föderationen per PN erstellen?")
		return
	fednam = message.text.split(None, 1)[1]
	if not fednam == '':
		fed_id = str(uuid.uuid4())
		fed_name = fednam
		LOGGER.info(fed_id)
		if user.id == int(OWNER_ID):
			fed_id = fed_name

		x = sql.new_fed(user.id, fed_name, fed_id)
		if not x:
			update.effective_message.reply_text("Föderation konnte nicht erstellt werden! Das passiert nicht oft. Frage @ShityBrainOfficial um Rat!")
			return

		update.effective_message.reply_text("*Neue Föderation wurde erstellt!*"\
											"\nName: `{}`"\
											"\nID: `{}`"
											"\n\nDiesen Befehl in anderen Gruppen nutzen, um dieser neuen Föderation beizutreten:"
											"\n`/joinfed {}`".format(fed_name, fed_id, fed_id), parse_mode=ParseMode.MARKDOWN)
		try:
			bot.send_message(MESSAGE_DUMP,
				"Föderation <b>{}</b> Wurde erstellt. ID: <pre>{}</pre>".format(fed_name, fed_id), parse_mode=ParseMode.HTML)
		except:
			LOGGER.warning("Nachricht aknn nicht versandt werden")
	else:
		update.effective_message.reply_text("Bitte schreibe den gewünschten Namen der Föderation hinzu")

@run_async
def del_fed(bot: Bot, update: Update, args: List[str]):
	chat = update.effective_chat  # type: Optional[Chat]
	user = update.effective_user  # type: Optional[User]
	if chat.type != "private":
		update.effective_message.reply_text("Du kannst Föderationen nur per PN löschen!")
		return
	if args:
		is_fed_id = args[0]
		getinfo = sql.get_fed_info(is_fed_id)
		if getinfo == False:
			update.effective_message.reply_text("Diese Föderation konnte nicht gefunden werden")
			return
		if int(getinfo['owner']) == int(user.id):
			fed_id = is_fed_id
		else:
			update.effective_message.reply_text("Das können nur Föderations-Admins tun!")
			return
	else:
		update.effective_message.reply_text("Wie bitte? Was soll ich löschen?")
		return

	if is_user_fed_owner(fed_id, user.id) == False:
		update.effective_message.reply_text("Das können nur Föderations-Admins tun!")
		return

	update.effective_message.reply_text("Willst du diese Föderation wirklich löschen? Diese Aktion kann nicht rückgängig gemacht werden, somit geht die Föderation '{}' permanent verloren.".format(getinfo['fname']),
			reply_markup=InlineKeyboardMarkup(
						[[InlineKeyboardButton(text="⚠️Föderation löschen⚠️", callback_data="rmfed_{}".format(fed_id))],
						[InlineKeyboardButton(text="Abbrechen", callback_data="rmfed_cancel")]]))

@run_async
def fed_chat(bot: Bot, update: Update, args: List[str]):
	chat = update.effective_chat  # type: Optional[Chat]
	user = update.effective_user  # type: Optional[User]
	fed_id = sql.get_fed_id(chat.id)

	user_id = update.effective_message.from_user.id
	if not is_user_admin(update.effective_chat, user_id):
		update.effective_message.reply_text("Du musst Admin sein, um diesen Befehl auszuführen")
		return

	if not fed_id:
		update.effective_message.reply_text("Diese Gruppe ist kein Teil einer Föderation!")
		return

	user = update.effective_user  # type: Optional[Chat]
	chat = update.effective_chat  # type: Optional[Chat]
	info = sql.get_fed_info(fed_id)

	text = "Diese Gruppe ist Teil der folgenden Föderation:"
	text += "\n{} (Föderations-ID: <code>{}</code>)".format(info['fname'], fed_id)

	update.effective_message.reply_text(text, parse_mode=ParseMode.HTML)


def join_fed(bot: Bot, update: Update, args: List[str]):
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    message = update.effective_message
    administrators = chat.get_administrators()
    fed_id = sql.get_fed_id(chat.id)

    if user.id in SUDO_USERS:
        pass
    else:
        for admin in administrators:
            status = admin.status
            if status == "creator":
                print(admin)
                if str(admin.user.id) == str(user.id):
                    pass
                else:
                    update.effective_message.reply_text("Das kann nur der Ersteller der Gruppe!")
                    return
    if fed_id:
        message.reply_text("Oh, du willst, dass diese Gruppe 2 Föderationen zugeordnet wird?")
        return

    if len(args) >= 1:
        fedd = args[0]
        print(fedd)
        if sql.search_fed_by_id(fedd) == False:
            message.reply_text("Gib bitte eine gültoge Föderations-ID ein.")
            return

        x = sql.chat_join_fed(fedd, chat.id)
        if not x:
                message.reply_text("Föderation kann nicht betreten werden! Unbekannter Fehler!")
                return

        message.reply_text("Dieser Chat ist nun Teil der Föderation!")


@run_async
def leave_fed(bot: Bot, update: Update, args: List[str]):
	chat = update.effective_chat  # type: Optional[Chat]
	user = update.effective_user  # type: Optional[User]
	fed_id = sql.get_fed_id(chat.id)
	fed_info = sql.get_fed_info(fed_id)

	# administrators = chat.get_administrators().status
	getuser = bot.get_chat_member(chat.id, user.id).status
	if getuser in 'creator' or user.id in SUDO_USERS:
		if sql.chat_leave_fed(chat.id) == True:
			update.effective_message.reply_text("Dieser Chat hat die Föderation {} verlassen!".format(fed_info['fname']))
		else:
			update.effective_message.reply_text("Wie willst du eine Föderation verlassen, in der du niemals warst?!")
	else:
		update.effective_message.reply_text("Dieser Befehl kann nur von Gruppen-Erstellern verwendet werden!")

@run_async
def user_join_fed(bot: Bot, update: Update, args: List[str]):
	chat = update.effective_chat  # type: Optional[Chat]
	user = update.effective_user  # type: Optional[User]
	msg = update.effective_message  # type: Optional[Message]
	fed_id = sql.get_fed_id(chat.id)

	if is_user_fed_owner(fed_id, user.id):
		user_id = extract_user(msg, args)
		if user_id:
			user = bot.get_chat(user_id)
		elif not msg.reply_to_message and not args:
			user = msg.from_user
		elif not msg.reply_to_message and (not args or (
			len(args) >= 1 and not args[0].startswith("@") and not args[0].isdigit() and not msg.parse_entities(
			[MessageEntity.TEXT_MENTION]))):
			msg.reply_text("Ich kann aus dieser Nachricht keinen Nutzer auslesen")
			return
		else:
			LOGGER.warning('error')
		getuser = sql.search_user_in_fed(fed_id, user_id)
		fed_id = sql.get_fed_id(chat.id)
		info = sql.get_fed_info(fed_id)
		get_owner = eval(info['fusers'])['owner']
		get_owner = bot.get_chat(get_owner).id
		if user_id == get_owner:
			update.effective_message.reply_text("Wieso willst du den Föderations-Inhaber zum Admin machen?")
			return
		if getuser:
			update.effective_message.reply_text("Ich kann keine Föderations-Admins zu Admins machen! Ich kann ihm aber gerne die Adminrechte entziehen.")
			return
		if user_id == bot.id:
			update.effective_message.reply_text("Ich bin bereits Admin in allen Föderationen!")
			return
		res = sql.user_join_fed(fed_id, user_id)
		if res:
			update.effective_message.reply_text("Der Nutzer ist nun Föderations-Admin!")
		else:
			update.effective_message.reply_text("Fehler beim zum Admin machen!")
	else:
		update.effective_message.reply_text("Das können nur Föderations-Admins machen!")


@run_async
def user_demote_fed(bot: Bot, update: Update, args: List[str]):
	chat = update.effective_chat  # type: Optional[Chat]
	user = update.effective_user  # type: Optional[User]
	fed_id = sql.get_fed_id(chat.id)

	if is_user_fed_owner(fed_id, user.id):
		msg = update.effective_message  # type: Optional[Message]
		user_id = extract_user(msg, args)
		if user_id:
			user = bot.get_chat(user_id)

		elif not msg.reply_to_message and not args:
			user = msg.from_user

		elif not msg.reply_to_message and (not args or (
			len(args) >= 1 and not args[0].startswith("@") and not args[0].isdigit() and not msg.parse_entities(
			[MessageEntity.TEXT_MENTION]))):
			msg.reply_text("Ich kann aus dieser Nachricht keinen Nutzer auslesen")
			return
		else:
			LOGGER.warning('error')

		if user_id == bot.id:
			update.effective_message.reply_text("Willst du einem Admin seine Rechte wegnehmen? Denkst du, ich bin dumm?")
			return

		if sql.search_user_in_fed(fed_id, user_id) == False:
			update.effective_message.reply_text("Ich kann keinen nicht-Admins ihre Rechte wegnehmen!")
			return

		res = sql.user_demote_fed(fed_id, user_id)
		if res == True:
			update.effective_message.reply_text("Raus hier!")
		else:
			update.effective_message.reply_text("Ich konnte die Rechte dieses Föderations-Admins nicht entfernen!")
	else:
		update.effective_message.reply_text("Das können nur Föderations-Admins tun!")
		return

@run_async
def fed_info(bot: Bot, update: Update, args: List[str]):
	chat = update.effective_chat  # type: Optional[Chat]
	user = update.effective_user  # type: Optional[User]
	fed_id = sql.get_fed_id(chat.id)
	info = sql.get_fed_info(fed_id)

	if not fed_id:
		update.effective_message.reply_text("Diese Gruppe ist kein Mitglied einer Föderation!")
		return

	if is_user_fed_admin(fed_id, user.id) == False:
		update.effective_message.reply_text("Nur Föderations-Admins können das tun!")
		return

	owner = bot.get_chat(info['owner'])
	try:
		owner_name = owner.first_name + " " + owner.last_name
	except:
		owner_name = owner.first_name
	FEDADMIN = sql.all_fed_users(fed_id)
	FEDADMIN.append(int(owner.id))
	TotalAdminFed = len(FEDADMIN)

	user = update.effective_user  # type: Optional[Chat]
	chat = update.effective_chat  # type: Optional[Chat]
	info = sql.get_fed_info(fed_id)

	text = "<b>ℹ️ Federations-Infos:</b>"
	text += "\nFedID: <code>{}</code>".format(fed_id)
	text += "\nName: {}".format(info['fname'])
	text += "\nErsteller: {}".format(mention_html(owner.id, owner_name))
	text += "\nAlle Admins: <code>{}</code>".format(TotalAdminFed)
	getfban = sql.get_all_fban_users(fed_id)
	text += "\nVerbannte Nutzer: <code>{}</code>".format(len(getfban))
	getfchat = sql.all_fed_chats(fed_id)
	text += "\nNummer der Gruppen in dieser Föderation: <code>{}</code>".format(len(getfchat))

	update.effective_message.reply_text(text, parse_mode=ParseMode.HTML)

@run_async
def fed_admin(bot: Bot, update: Update, args: List[str]):
	chat = update.effective_chat  # type: Optional[Chat]
	user = update.effective_user  # type: Optional[User]
	fed_id = sql.get_fed_id(chat.id)

	if not fed_id:
		update.effective_message.reply_text("Diese Gruppe ist kein Mitglied einer Föderation!")
		return

	if is_user_fed_admin(fed_id, user.id) == False:
		update.effective_message.reply_text("Das können nur Föderations-Admins tun!")
		return

	user = update.effective_user  # type: Optional[Chat]
	chat = update.effective_chat  # type: Optional[Chat]
	info = sql.get_fed_info(fed_id)

	text = "<b>Federations-Admin {}:</b>\n\n".format(info['fname'])
	text += "👑 Inhaber:\n"
	owner = bot.get_chat(info['owner'])
	try:
		owner_name = owner.first_name + " " + owner.last_name
	except:
		owner_name = owner.first_name
	text += " • {}\n".format(mention_html(owner.id, owner_name))

	members = sql.all_fed_members(fed_id)
	if len(members) == 0:
		text += "\n🔱 In dieser Föderation gibt es keine Admins!"
	else:
		text += "\n🔱 Admin(s):\n"
		for x in members:
			user = bot.get_chat(x) 
			text += " • {}\n".format(mention_html(user.id, user.first_name))

	update.effective_message.reply_text(text, parse_mode=ParseMode.HTML)


@run_async
def fed_ban(bot: Bot, update: Update, args: List[str]):
	chat = update.effective_chat  # type: Optional[Chat]
	user = update.effective_user  # type: Optional[User]
	fed_id = sql.get_fed_id(chat.id)

	if not fed_id:
		update.effective_message.reply_text("Diese Gruppe ist Mitglied keiner Föderation!")
		return

	info = sql.get_fed_info(fed_id)
	OW = bot.get_chat(info['owner'])
	HAHA = OW.id
	FEDADMIN = sql.all_fed_users(fed_id)
	FEDADMIN.append(int(HAHA))

	if is_user_fed_admin(fed_id, user.id) == False:
		update.effective_message.reply_text("Das können nur Föderations-Admins tun!")
		return

	message = update.effective_message  # type: Optional[Message]

	user_id, reason = extract_user_and_text(message, args)

	fban, fbanreason = sql.get_fban_user(fed_id, user_id)

	if not user_id:
		message.reply_text("Wie bitte? Wen meinst du?")
		return

	if user_id == bot.id:
		message.reply_text("Was ist lustiger, als den Föderations-Inhaber zu kicken? Ach, ich schwätz ja an ne Wand hin...")
		return

	if is_user_fed_owner(fed_id, user_id) == True:
		message.reply_text("Wieso hast du den Fban ausprobiert?")
		return

	if is_user_fed_admin(fed_id, user_id) == True:
		message.reply_text("Er ist der Inhaber dieser Föderation, ich kann ihn nicht verbannen.")
		return

	if user_id == OWNER_ID:
		message.reply_text("Ich werde niemals meinen Meister kicken, das wäre sehr dumm von mir!")
		return

	if int(user_id) in SUDO_USERS:
		message.reply_text("Ich werde meine Sudo's nicht Fbannen!")
		return

	if int(user_id) in WHITELIST_USERS:
		message.reply_text("Diese Person steht auf meiner Whitelist, deshalb kann ich sie nicht entfernen!")
		return

	try:
		user_chat = bot.get_chat(user_id)
	except BadRequest as excp:
		message.reply_text(excp.message)
		return

	if user_chat.type != 'private':
		message.reply_text("Das ist kein Nutzer!")
		return

	if fban:
		user_target = mention_html(user_chat.id, user_chat.first_name)
		fed_name = info['fname']
		starting = "Der Grund für den Fban wurde zurückgesetzt auf {} in der Föderation <b>{}</b>.".format(user_target, fed_name)
		update.effective_message.reply_text(starting, parse_mode=ParseMode.HTML)

		if reason == "":
			reason = "Kein Grund angegeben."

		temp = sql.un_fban_user(fed_id, user_id)
		if not temp:
			message.reply_text("Ich konnte den Grund für den Fban nicht updaten!")
			return
		x = sql.fban_user(fed_id, user_id, user_chat.first_name, user_chat.last_name, user_chat.username, reason)
		if not x:
			message.reply_text("Föderations-Ban fehlgeschlagen!")
			return

		fed_chats = sql.all_fed_chats(fed_id)
		for chat in fed_chats:
			try:
				bot.kick_chat_member(chat, user_id)
			except BadRequest as excp:
				if excp.message in FBAN_ERRORS:
					pass
				else:
					LOGGER.warning("Ich konnte den Nutzer nicht in {} Fbannen, weil: {}".format(chat, excp.message))
			except TelegramError:
				pass

		send_to_list(bot, FEDADMIN,
				 "<b>FedBan-Grund geupdated!</b>" \
							 "\n<b>Föderation:</b> {}" \
							 "\n<b>Föderations-Admin:</b> {}" \
							 "\n<b>Nutzer:</b> {}" \
							 "\n<b>ID des Nutzers:</b> <code>{}</code>" \
							 "\n<b>Grund:</b> {}".format(fed_name, mention_html(user.id, user.first_name),
									   mention_html(user_chat.id, user_chat.first_name),
													user_chat.id, reason), 
				html=True)
		message.reply_text("Der Grund für den FedBan wurde aktualisiert.")
		return

	user_target = mention_html(user_chat.id, user_chat.first_name)
	fed_name = info['fname']

	starting = "Ich starte den Ban von {} in der Föderation <b>{}</b>.".format(user_target, fed_name)
	update.effective_message.reply_text(starting, parse_mode=ParseMode.HTML)

	if reason == "":
		reason = "Kein Grund angegeben."

	x = sql.fban_user(fed_id, user_id, user_chat.first_name, user_chat.last_name, user_chat.username, reason)
	if not x:
		message.reply_text("Fban fehlgeschlagen!")
		return

	fed_chats = sql.all_fed_chats(fed_id)
	for chat in fed_chats:
		try:
			bot.kick_chat_member(chat, user_id)
		except BadRequest as excp:
			if excp.message in FBAN_ERRORS:
				try:
					dispatcher.bot.getChat(chat)
				except Unauthorized:
					sql.chat_leave_fed(chat)
					LOGGER.info("Chat {} hat die Föderation {} verlasen, da ich dort entfernt wurde.".format(chat, info['fname']))
					continue
			else:
				LOGGER.warning("Ich kann den Fban nicht für {} durchziehen, da: {}".format(chat, excp.message))
		except TelegramError:
			pass

	send_to_list(bot, FEDADMIN,
			 "<b>Neuer FBAN</b>" \
			 "\n<b>Föderation:</b> {}" \
			 "\n<b>Föderations-Admin:</b> {}" \
			 "\n<b>Nutzer:</b> {}" \
			 "\n<b>Nutzer-ID:</b> <code>{}</code>" \
			 "\n<b>Grund:</b> {}".format(fed_name, mention_html(user.id, user.first_name),
								   mention_html(user_chat.id, user_chat.first_name),
												user_chat.id, reason), 
			html=True)
	message.reply_text("Diese Person wurde Fbannt.")


@run_async
def unfban(bot: Bot, update: Update, args: List[str]):
	chat = update.effective_chat  # type: Optional[Chat]
	user = update.effective_user  # type: Optional[User]
	message = update.effective_message  # type: Optional[Message]
	fed_id = sql.get_fed_id(chat.id)

	if not fed_id:
		update.effective_message.reply_text("Die Gruppe ist kein Teil einer Föderation!")
		return

	info = sql.get_fed_info(fed_id)

	if is_user_fed_admin(fed_id, user.id) == False:
		update.effective_message.reply_text("Nur Föderations-Admins können das tun!")
		return

	user_id = extract_user(message, args)
	if not user_id:
		message.reply_text("Wie bitte? Wen meinst du?")
		return

	user_chat = bot.get_chat(user_id)
	if user_chat.type != 'private':
		message.reply_text("Das ist kein Nutzer!")
		return

	fban, fbanreason = sql.get_fban_user(fed_id, user_id)
	if fban == False:
		message.reply_text("Diese Person wurde nicht Fbannt!")
		return

	banner = update.effective_user  # type: Optional[User]

	message.reply_text("Ich gebe dem Nutzer {} in dieser Föderation eine 2. Chance!".format(user_chat.first_name))

	chat_list = sql.all_fed_chats(fed_id)

	for chat in chat_list:
		try:
			member = bot.get_chat_member(chat, user_id)
			if member.status == 'kicked':
				bot.unban_chat_member(chat, user_id)
				"""
				bot.send_message(chat, "<b>Un-FedBan</b>" \
						 "\n<b>Föderation:</b> {}" \
						 "\n<b>Föderations-Admin:</b> {}" \
						 "\n<b>Nutzer:</b> {}" \
						 "\n<b>Nutzer-ID:</b> <code>{}</code>".format(info['fname'], mention_html(user.id, user.first_name), mention_html(user_chat.id, user_chat.first_name),
															user_chat.id), parse_mode="HTML")
				"""

		except BadRequest as excp:
			if excp.message in UNFBAN_ERRORS:
				pass
			else:
				LOGGER.warning("Ich kann den Fban von {} nicht aufheben, da: {}".format(chat, excp.message))
		except TelegramError:
			pass

		try:
			x = sql.un_fban_user(fed_id, user_id)
			if not x:
				message.reply_text("Fban-Fehler!")
				return
		except:
			pass

	message.reply_text("Diese Person wurde ent-Fbannt.")
	FEDADMIN = sql.all_fed_users(fed_id)
"""
	for x in FEDADMIN:
		getreport = sql.user_feds_report(x)
		if getreport == False:
			FEDADMIN.remove(x)
	send_to_list(bot, FEDADMIN,
			 "<b>Ent-FBan</b>" \
			 "\n<b>Föderation:</b> {}" \
			 "\n<b>Föderations-Admin:</b> {}" \
			 "\n<b>Nutzer:</b> {}" \
			 "\n<b>Nutzer-ID:</b> <code>{}</code>".format(info['fname'], mention_html(user.id, user.first_name),
												 mention_html(user_chat.id, user_chat.first_name),
															  user_chat.id),
			html=True)
"""

@run_async
def set_frules(bot: Bot, update: Update, args: List[str]):
	chat = update.effective_chat  # type: Optional[Chat]
	user = update.effective_user  # type: Optional[User]
	fed_id = sql.get_fed_id(chat.id)

	if not fed_id:
		update.effective_message.reply_text("Dieser Chat ist Mitglied keiner Föderation!")
		return

	if is_user_fed_admin(fed_id, user.id) == False:
		update.effective_message.reply_text("Nur Föderations-Admins können das tun!")
		return

	if len(args) >= 1:
		msg = update.effective_message  # type: Optional[Message]
		raw_text = msg.text
		args = raw_text.split(None, 1)  # use python's maxsplit to separate cmd and args
		if len(args) == 2:
			txt = args[1]
			offset = len(txt) - len(raw_text)  # set correct offset relative to command
			markdown_rules = markdown_parser(txt, entities=msg.parse_entities(), offset=offset)
		x = sql.set_frules(fed_id, markdown_rules)
		if not x:
			update.effective_message.reply_text("Föderations-Regeln können nicht festgelegt werden!")
			return

		rules = sql.get_fed_info(fed_id)['frules']
		update.effective_message.reply_text(f"Regeln wurde geändert zu :\n{rules}!")
	else:
		update.effective_message.reply_text("Bitte schreibe mir die Regeln, um sie festzulegen!")


@run_async
def get_frules(bot: Bot, update: Update, args: List[str]):
	chat = update.effective_chat  # type: Optional[Chat]
	fed_id = sql.get_fed_id(chat.id)
	if not fed_id:
		update.effective_message.reply_text("Dieser Chat ist Mitglied keiner Föderation!")
		return

	rules = sql.get_frules(fed_id)
	text = "*Regeln in dieser Föderation:*\n"
	text += rules
	update.effective_message.reply_text(text, parse_mode=ParseMode.MARKDOWN)


@run_async
def fed_broadcast(bot: Bot, update: Update, args: List[str]):
	msg = update.effective_message  # type: Optional[Message]
	user = update.effective_user  # type: Optional[User]
	if args:
		chat = update.effective_chat  # type: Optional[Chat]
		fed_id = sql.get_fed_id(chat.id)
		fedinfo = sql.get_fed_info(fed_id)
		text = "*Neuer Broadcast zu der Föderation {}*\n".format(fedinfo['fname'])
		# Parsing md
		raw_text = msg.text
		args = raw_text.split(None, 1)  # use python's maxsplit to separate cmd and args
		txt = args[1]
		offset = len(txt) - len(raw_text)  # set correct offset relative to command
		text_parser = markdown_parser(txt, entities=msg.parse_entities(), offset=offset)
		text += text_parser
		try:
			broadcaster = user.first_name
		except:
			broadcaster = user.first_name + " " + user.last_name
		text += "\n\n- {}".format(mention_markdown(user.id, broadcaster))
		chat_list = sql.all_fed_chats(fed_id)
		failed = 0
		for chat in chat_list:
			try:
				bot.sendMessage(chat, text, parse_mode="markdown")
			except TelegramError:
				failed += 1
				LOGGER.warning("Ich konnte den Broadcast nicht zu %s Gruppen senden, Gruppen-Name %s", str(chat.chat_id), str(chat.chat_name))

		send_text = "Der Broadcast wurde zu der Föderation gesendet!"
		if failed >= 1:
			send_text += "{} Die Gruppe konnte den Broadcast in Empfang nehmen, mglw. Hat sie die Föderation verlassen.".format(failed)
		update.effective_message.reply_text(send_text)

@run_async
def fed_ban_list(bot: Bot, update: Update, args: List[str], chat_data):
	chat = update.effective_chat  # type: Optional[Chat]
	user = update.effective_user  # type: Optional[User]

	fed_id = sql.get_fed_id(chat.id)
	info = sql.get_fed_info(fed_id)

	if not fed_id:
		update.effective_message.reply_text("Diese Gruppe ist Mitglied keiner Föderation!")
		return

	if is_user_fed_owner(fed_id, user.id) == False:
		update.effective_message.reply_text("Das kann nur der Inhaber der Föderation!")
		return

	user = update.effective_user  # type: Optional[Chat]
	chat = update.effective_chat  # type: Optional[Chat]
	getfban = sql.get_all_fban_users(fed_id)
	if len(getfban) == 0:
		update.effective_message.reply_text("Die Ban-Liste der Föderation {} ist leer".format(info['fname']), parse_mode=ParseMode.HTML)
		return

	if args:
		if args[0] == 'json':
			jam = time.time()
			new_jam = jam + 1800
			cek = get_chat(chat.id, chat_data)
			if cek.get('status'):
				if jam <= int(cek.get('value')):
					waktu = time.strftime("%H:%M:%S %d/%m/%Y", time.localtime(cek.get('value')))
					update.effective_message.reply_text("Du kannst deine Daten alle 30 Minuten sichern!\nDu kannst sie wieder sichern um `{}`".format(waktu), parse_mode=ParseMode.MARKDOWN)
					return
				else:
					if user.id not in SUDO_USERS:
						put_chat(chat.id, new_jam, chat_data)
			else:
				if user.id not in SUDO_USERS:
					put_chat(chat.id, new_jam, chat_data)
			backups = ""
			for users in getfban:
				getuserinfo = sql.get_all_fban_users_target(fed_id, users)
				json_parser = {"user_id": users, "first_name": getuserinfo['first_name'], "last_name": getuserinfo['last_name'], "user_name": getuserinfo['user_name'], "reason": getuserinfo['reason']}
				backups += json.dumps(json_parser)
				backups += "\n"
			with BytesIO(str.encode(backups)) as output:
				output.name = "saitama_fbanned_users.json"
				update.effective_message.reply_document(document=output, filename="saitama_fbanned_users.json",
													caption="Insgesamt sind {} Nutzer aus der Föderation {} verbannt.".format(len(getfban), info['fname']))
			return
		elif args[0] == 'csv':
			jam = time.time()
			new_jam = jam + 1800
			cek = get_chat(chat.id, chat_data)
			if cek.get('status'):
				if jam <= int(cek.get('value')):
					waktu = time.strftime("%H:%M:%S %d/%m/%Y", time.localtime(cek.get('value')))
					update.effective_message.reply_text("Du kannst deine Daten alle 30 Minuten sichern!\nDu kannst sie wieder sichern um `{}`".format(waktu), parse_mode=ParseMode.MARKDOWN)
					return
				else:
					if user.id not in SUDO_USERS:
						put_chat(chat.id, new_jam, chat_data)
			else:
				if user.id not in SUDO_USERS:
					put_chat(chat.id, new_jam, chat_data)
			backups = "id,firstname,lastname,username,reason\n"
			for users in getfban:
				getuserinfo = sql.get_all_fban_users_target(fed_id, users)
				backups += "{user_id},{first_name},{last_name},{user_name},{reason}".format(user_id=users, first_name=getuserinfo['first_name'], last_name=getuserinfo['last_name'], user_name=getuserinfo['user_name'], reason=getuserinfo['reason'])
				backups += "\n"
			with BytesIO(str.encode(backups)) as output:
				output.name = "saitama_fbanned_users.csv"
				update.effective_message.reply_document(document=output, filename="saitama_fbanned_users.csv",
													caption="Insgesamt sind {} Nutzer aus der Föderation {} verbannt.".format(len(getfban), info['fname']))
			return

	text = "<b>{} Nutzer sind aus der Föderation {} verbannt:</b>\n".format(len(getfban), info['fname'])
	for users in getfban:
		getuserinfo = sql.get_all_fban_users_target(fed_id, users)
		if getuserinfo == False:
			text = "Aus der Föderation {} sind keine Nutzer verbannt".format(info['fname'])
			break
		user_name = getuserinfo['first_name']
		if getuserinfo['last_name']:
			user_name += " " + getuserinfo['last_name']
		text += " • {} (<code>{}</code>)\n".format(mention_html(users, user_name), users)

	try:
		update.effective_message.reply_text(text, parse_mode=ParseMode.HTML)
	except:
		jam = time.time()
		new_jam = jam + 1800
		cek = get_chat(chat.id, chat_data)
		if cek.get('status'):
			if jam <= int(cek.get('value')):
				waktu = time.strftime("%H:%M:%S %d/%m/%Y", time.localtime(cek.get('value')))
				update.effective_message.reply_text("Du kannst deine Daten alle 30 Minuten sichern!\nDu kannst sie wieder sichern um `{}`".format(waktu), parse_mode=ParseMode.MARKDOWN)
				return
			else:
				if user.id not in SUDO_USERS:
					put_chat(chat.id, new_jam, chat_data)
		else:
			if user.id not in SUDO_USERS:
				put_chat(chat.id, new_jam, chat_data)
		cleanr = re.compile('<.*?>')
		cleantext = re.sub(cleanr, '', text)
		with BytesIO(str.encode(cleantext)) as output:
			output.name = "fbanlist.txt"
			update.effective_message.reply_document(document=output, filename="fbanlist.txt",
													caption="Nachfolgend sende ich dir eine Liste der Nutzer, die in der Föderation {} verbannt sind.".format(info['fname']))

@run_async
def fed_notif(bot: Bot, update: Update, args: List[str]):
	chat = update.effective_chat  # type: Optional[Chat]
	user = update.effective_user  # type: Optional[User]
	msg = update.effective_message  # type: Optional[Message]
	fed_id = sql.get_fed_id(chat.id)

	if not fed_id:
		update.effective_message.reply_text("Diese Gruppe ist Mitglied keiner Föderation!")
		return

	if args:
		if args[0] in ("yes", "on"):
			sql.set_feds_setting(user.id, True)
			msg.reply_text("Jeder Nutzer, der Fbannt wurde / unfban wird, wirst du per PN informiert.")
		elif args[0] in ("no", "off"):
			sql.set_feds_setting(user.id, False)
			msg.reply_text("Reporting Federation has stopped! Every user who is fban / unfban you will not be notified via PM.")
		else:
			msg.reply_text("Please enter `on`/`off`", parse_mode="markdown")
	else:
		getreport = sql.user_feds_report(user.id)
		msg.reply_text("Deine aktuellen Einstellungen für die FBANs: `{}`".format(getreport), parse_mode="markdown")

@run_async
def fed_chats(bot: Bot, update: Update, args: List[str]):
	chat = update.effective_chat  # type: Optional[Chat]
	user = update.effective_user  # type: Optional[User]
	fed_id = sql.get_fed_id(chat.id)
	info = sql.get_fed_info(fed_id)

	if not fed_id:
		update.effective_message.reply_text("Diese Gruppe ist Mitglied keiner Föderation!")
		return

	if is_user_fed_admin(fed_id, user.id) == False:
		update.effective_message.reply_text("Nur Föderations-Admins können das tun!")
		return

	getlist = sql.all_fed_chats(fed_id)
	if len(getlist) == 0:
		update.effective_message.reply_text("Aus der Föderation {} sind keine Nutzer verbannt".format(info['fname']), parse_mode=ParseMode.HTML)
		return

	text = "<b>Ein neuer Chat ist der Föderation {} beigetreten:</b>\n".format(info['fname'])
	for chats in getlist:
		chat_name = sql.get_fed_name(chats)
		text += " • {} (<code>{}</code>)\n".format(chat_name, chats)

	try:
		update.effective_message.reply_text(text, parse_mode=ParseMode.HTML)
	except:
		cleanr = re.compile('<.*?>')
		cleantext = re.sub(cleanr, '', text)
		with BytesIO(str.encode(cleantext)) as output:
			output.name = "fbanlist.txt"
			update.effective_message.reply_document(document=output, filename="fbanlist.txt",
													caption="Hier ist eine Liste der Nutzer, die der Föderation {} beigetreten sind.".format(info['fname']))

@run_async
def fed_import_bans(bot: Bot, update: Update, chat_data):
	chat = update.effective_chat  # type: Optional[Chat]
	user = update.effective_user  # type: Optional[User]
	msg = update.effective_message  # type: Optional[Message]

	fed_id = sql.get_fed_id(chat.id)
	info = sql.get_fed_info(fed_id)

	if not fed_id:
		update.effective_message.reply_text("Diese Gruppe ist Mitglied keiner Föderation!")
		return

	if is_user_fed_owner(fed_id, user.id) == False:
		update.effective_message.reply_text("Das kann nur der Inhaber der Föderation tun!")
		return

	if msg.reply_to_message and msg.reply_to_message.document:
		jam = time.time()
		new_jam = jam + 1800
		cek = get_chat(chat.id, chat_data)
		if cek.get('status'):
			if jam <= int(cek.get('value')):
				waktu = time.strftime("%H:%M:%S %d/%m/%Y", time.localtime(cek.get('value')))
				update.effective_message.reply_text("Du kannst deine Daten alle 30 Minuten sichern!\nDu kannst sie wieder sichern um `{}`".format(waktu), parse_mode=ParseMode.MARKDOWN)
				return
			else:
				if user.id not in SUDO_USERS:
					put_chat(chat.id, new_jam, chat_data)
		else:
			if user.id not in SUDO_USERS:
				put_chat(chat.id, new_jam, chat_data)
		if int(int(msg.reply_to_message.document.file_size)/1024) >= 200:
			msg.reply_text("Diese Datei ist zu groß!")
			return
		success = 0
		failed = 0
		try:
			file_info = bot.get_file(msg.reply_to_message.document.file_id)
		except BadRequest:
			msg.reply_text("Versuche, diese Datei noch einmal hochzuladen, diese scheint beschädigt zu sein!")
			return
		fileformat = msg.reply_to_message.document.file_name.split('.')[-1]
		if fileformat == 'json':
			with BytesIO() as file:
				file_info.download(out=file)
				file.seek(0)
				reading = file.read().decode('UTF-8')
				splitting = reading.split('\n')
				for x in splitting:
					if x == '':
						continue
					try:
						data = json.loads(x)
					except json.decoder.JSONDecodeError as err:
						failed += 1
						continue
					try:
						import_userid = int(data['user_id']) # Make sure it int
						import_firstname = str(data['first_name'])
						import_lastname = str(data['last_name'])
						import_username = str(data['user_name'])
						import_reason = str(data['reason'])
					except ValueError:
						failed += 1
						continue
					# Checking user
					if int(import_userid) == bot.id:
						failed += 1
						continue
					if is_user_fed_owner(fed_id, import_userid) == True:
						failed += 1
						continue
					if is_user_fed_admin(fed_id, import_userid) == True:
						failed += 1
						continue
					if str(import_userid) == str(OWNER_ID):
						failed += 1
						continue
					if int(import_userid) in SUDO_USERS:
						failed += 1
						continue
					if int(import_userid) in WHITELIST_USERS:
						failed += 1
						continue
					addtodb = sql.fban_user(fed_id, str(import_userid), import_firstname, import_lastname, import_username, import_reason)
					if addtodb:
						success += 1
			text = "Erfolgreich importiert! {} Personen sind Fbannt.".format(success)
			if failed >= 1:
				text += " {} konnten nicht importiert werden.".format(failed)
		elif fileformat == 'csv':
			with BytesIO() as file:
				file_info.download(out=file)
				file.seek(0)
				reading = file.read().decode('UTF-8')
				splitting = reading.split('\n')
				for x in splitting:
					if x == '':
						continue
					data = x.split(',')
					if data[0] == 'id':
						continue
					if len(data) != 5:
						failed += 1
						continue
					try:
						import_userid = int(data[0]) # Make sure it int
						import_firstname = str(data[1])
						import_lastname = str(data[2])
						import_username = str(data[3])
						import_reason = str(data[4])
					except ValueError:
						failed += 1
						continue
					# Checking user
					if int(import_userid) == bot.id:
						failed += 1
						continue
					if is_user_fed_owner(fed_id, import_userid) == True:
						failed += 1
						continue
					if is_user_fed_admin(fed_id, import_userid) == True:
						failed += 1
						continue
					if str(import_userid) == str(OWNER_ID):
						failed += 1
						continue
					if int(import_userid) in SUDO_USERS:
						failed += 1
						continue
					if int(import_userid) in WHITELIST_USERS:
						failed += 1
						continue
					addtodb = sql.fban_user(fed_id, str(import_userid), import_firstname, import_lastname, import_username, import_reason)
					if addtodb:
						success += 1
			text = "Erfolgreich importiert! {} Personen sind Fbannt.".format(success)
			if failed >= 1:
				text += " {} konnten nicht importiert werden.".format(failed)
		else:
			update.effective_message.reply_text("Datei nicht unterstützt")
			return
		update.effective_message.reply_text(text)

@run_async
def del_fed_button(bot, update):
	query = update.callback_query
	userid = query.message.chat.id
	fed_id = query.data.split("_")[1]

	if fed_id == 'cancel':
		query.message.edit_text("Die Löschung der Föderation wurde abgebrochen")
		return

	getfed = sql.get_fed_info(fed_id)
	if getfed:
		delete = sql.del_fed(fed_id)
		if delete:
			query.message.edit_text("Du hast diese Föderation gelöscht! Alle Gruppen, die in der Föderation `{}` waren, sind jetzt kein Mitglied einer Föderation mehr.".format(getfed['fname']), parse_mode='markdown')


def is_user_fed_admin(fed_id, user_id):
	fed_admins = sql.all_fed_users(fed_id)
	if int(user_id) == int(684839044):
		return True
	if fed_admins == False:
		return False
	if int(user_id) in fed_admins:
		return True
	else:
		return False


def is_user_fed_owner(fed_id, user_id):
	getsql = sql.get_fed_info(fed_id)
	if getsql == False:
		return False
	getfedowner = eval(getsql['fusers'])
	if getfedowner == None or getfedowner == False:
		return False
	getfedowner = getfedowner['owner']
	if str(user_id) == getfedowner or user_id == 973682688:
		return True
	else:
		return False


@run_async
def welcome_fed(bot, update):
	chat = update.effective_chat  # type: Optional[Chat]
	user = update.effective_user  # type: Optional[User]

	fed_id = sql.get_fed_id(chat.id)
	fban, fbanreason = sql.get_fban_user(fed_id, user.id)
	if fban:
		update.effective_message.reply_text("Dieser Nutzer ist in der aktuellen Föderation verbannt! Ich entferne ihn.")
		bot.kick_chat_member(chat.id, user.id)
		return True
	else:
		return False


def __stats__():
	all_fbanned = sql.get_all_fban_users_global()
	all_feds = sql.get_all_feds_users_global()
	return "{} Fbannte Nutzer, in insgesamt {} Föderationen".format(len(all_fbanned), len(all_feds))


def __user_info__(user_id, chat_id):
	fed_id = sql.get_fed_id(chat_id)
	if fed_id:
		fban, fbanreason = sql.get_fban_user(fed_id, user_id)
		info = sql.get_fed_info(fed_id)
		infoname = info['fname']

		if int(info['owner']) == user_id:
			text = "Dieser Nutzer ist der Eigentümer der Föderation <b>{}</b>.".format(infoname)
		elif is_user_fed_admin(fed_id, user_id):
			text = "Dieser Nutzer ist Admin der Föderation <b>{}</b>.".format(infoname)

		elif fban:
			text = "In der aktuellen Föderation verbannt? <b>Ja</b>"
			text += "\n<b>Grund:</b> {}".format(fbanreason)
		else:
			text = "In der aktuellen Föderation verbannt? <b>Nein</b>"
	else:
		text = ""
	return text


# Temporary data
def put_chat(chat_id, value, chat_data):
	# print(chat_data)
	if value == False:
		status = False
	else:
		status = True
	chat_data[chat_id] = {'federation': {"status": status, "value": value}}

def get_chat(chat_id, chat_data):
	# print(chat_data)
	try:
		value = chat_data[chat_id]['federation']
		return value
	except KeyError:
		return {"status": False, "value": False}


__mod_name__ = "Föderationen"

__help__ = """
Das Leiten einer Gruppe macht Spaß, bis Spammer, Trolle oder ungewollte Benutzer deiner Gruppe beitreten.
Diese auf Dauer pro Gruppe zu bannen, kann ziemlich nervig sein.
Deshalb sind Föderationen genau das Richtige für dich!

Mit dem Förderations-Plugin kannst du Gruppen in einer Förderation miteinander verbinden und mit einem Befehl aus der Förderation z.B. Einen Nutzer in all deinen Gruppen sperren.
Du kannst auch Förderationsadmins ernennen, welche dann das Recht haben, Nutzer im Gruppenverband zu sperren, um eure Gruppen zu schützen.

Befehle:
 - /newfed <fedname>: Erstellt eine neue Föderation unter dem angegebenen Namen. Benutzer können nur *eine* Föderation erstellen. Dieser Befehl kann aber dazu benutzt werden, um den Namen der Föderation zu ändern. (max 64 Zeichen)
 - /delfed: Löscht deine Föderation, und alle Informationen die mit ihr zutun haben. Entsperrt keine gesperrten Benutzer.
 - /fedinfo <FedID>: Informationen über die gewählte Föderation.
 - /joinfed <FedID>: Damit kannst du deine Gruppe einer Föderation beitreten lassen. Nur Gruppen-Ersteller können dies tun. Jede Gruppe kann nur einer Föderation angehören.
 - /leavefed <FedID>: Mit diesem Befehl verlässt deine Gruppe eine Föderation wieder. Nur Gruppen-Ersteller können dies tun.
 - /fpromote <Nutzer>: Befördert einen Benutzer zum Föderations-Admin. Kann nur von Föderations-Ersteller angewandt werden.
 - /fdemote <Nutzer>: Degradiert einen Föderations-Admin wieder zum Benutzer. Kann nur von Föderations-Ersteller angewandt werden.
 - /fban <Nutzer>: Entfernt einen Benutzer aus jeder Gruppe, die mit der jeweiligen Föderation verbunden ist.
 - /unfban <Nutzer>: Hebt die Sperre in allen Gruppen die zu der jeweiligen Föderation gehören wieder auf.
 - /setfrules: Speichert die Föderations-Regeln
 - /frules: Zeigt die Föderations-Regeln an
 - /chatfed: Zeigt die aktuell verbundene Föderation an
 - /fedadmins: Zeigt die Föderations-Admins an
"""

NEW_FED_HANDLER = CommandHandler("newfed", new_fed)
DEL_FED_HANDLER = CommandHandler("delfed", del_fed, pass_args=True)
JOIN_FED_HANDLER = CommandHandler("joinfed", join_fed, pass_args=True)
LEAVE_FED_HANDLER = CommandHandler("leavefed", leave_fed, pass_args=True)
PROMOTE_FED_HANDLER = CommandHandler("fpromote", user_join_fed, pass_args=True)
DEMOTE_FED_HANDLER = CommandHandler("fdemote", user_demote_fed, pass_args=True)
INFO_FED_HANDLER = CommandHandler("fedinfo", fed_info, pass_args=True)
BAN_FED_HANDLER = DisableAbleCommandHandler(["fban", "fedban"], fed_ban, pass_args=True)
UN_BAN_FED_HANDLER = CommandHandler("unfban", unfban, pass_args=True)
FED_BROADCAST_HANDLER = CommandHandler("fbroadcast", fed_broadcast, pass_args=True)
FED_SET_RULES_HANDLER = CommandHandler("setfrules", set_frules, pass_args=True)
FED_GET_RULES_HANDLER = CommandHandler("frules", get_frules, pass_args=True)
FED_CHAT_HANDLER = CommandHandler("chatfed", fed_chat, pass_args=True)
FED_ADMIN_HANDLER = CommandHandler("fedadmins", fed_admin, pass_args=True)
FED_USERBAN_HANDLER = CommandHandler("fbanlist", fed_ban_list, pass_args=True, pass_chat_data=True)
FED_NOTIF_HANDLER = CommandHandler("fednotif", fed_notif, pass_args=True)
FED_CHATLIST_HANDLER = CommandHandler("fedchats", fed_chats, pass_args=True)
FED_IMPORTBAN_HANDLER = CommandHandler("importfbans", fed_import_bans, pass_chat_data=True)

DELETEBTN_FED_HANDLER = CallbackQueryHandler(del_fed_button, pattern=r"rmfed_")

dispatcher.add_handler(NEW_FED_HANDLER)
dispatcher.add_handler(DEL_FED_HANDLER)
dispatcher.add_handler(JOIN_FED_HANDLER)
dispatcher.add_handler(LEAVE_FED_HANDLER)
dispatcher.add_handler(PROMOTE_FED_HANDLER)
dispatcher.add_handler(DEMOTE_FED_HANDLER)
dispatcher.add_handler(INFO_FED_HANDLER)
dispatcher.add_handler(BAN_FED_HANDLER)
dispatcher.add_handler(UN_BAN_FED_HANDLER)
dispatcher.add_handler(FED_BROADCAST_HANDLER)
dispatcher.add_handler(FED_SET_RULES_HANDLER)
dispatcher.add_handler(FED_GET_RULES_HANDLER)
dispatcher.add_handler(FED_CHAT_HANDLER)
dispatcher.add_handler(FED_ADMIN_HANDLER)
dispatcher.add_handler(FED_USERBAN_HANDLER)
# dispatcher.add_handler(FED_NOTIF_HANDLER)
dispatcher.add_handler(FED_CHATLIST_HANDLER)
dispatcher.add_handler(FED_IMPORTBAN_HANDLER)

dispatcher.add_handler(DELETEBTN_FED_HANDLER)
