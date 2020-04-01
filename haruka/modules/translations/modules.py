"""
 - /adminlist | /admins: Liste der Admins im Chat

*Nur für Admins:*
 - /pin: Pinnt eine Nachricht an
 - /unpin: Pinnt die aktuell angepinnte Nachricht ab!
 - /invitelink: Spuckt den Einladungslink raus
 - /promote: Macht den Nutzer, auf den geantwortet wird, zum Admin
 - /demote: Degradiert den markierten Admin
"""
"""
 - /afk <Grund>: Markiere dich selbst als AFK.
 - brb <reason>: Das gleiche wie /afk, doch nicht als Befehl.
"""
"""
 - /flood: Die aktuelle Einstellung zur Flood-Kontrolle zu erhalten

*Nur für Admins:*
 - /setflood <int/'no'/'off'>: Aktiviert oder deaktiviert die Flood-Kontrolle
"""
"""
*Nur für Admins:*
 - /antispam <on/off/yes/no>: Aktiviert/Deaktiviert den Spamschutz in deiner Gruppe. 
"""
"""
 - /kickme: Kickt den Nutzer, der den Befehl nutzt.

*Nur für Admins:*
 - /ban <userhandle>: Verbannt einen Nutzer.
 - /tban <userhandle> x(m/h/d): Verbannt einen Nutzer für x Zeit. m = Minuten, h = Stunden, d = Tage.
 - /unban <userhandle>: Hebt den Ban eines Nutzers auf.
 - /kick <userhandle>: Kickt einen Nutzer.
"""
"""
Aktionen, die auf verbundene Gruppen angewandt werden können:
 • Notizen anzeigen lassen und bearbeiten
 • Filter anzeigen lassen und bearbeiten
 • Blacklists anzeigen lassen und bearbeiten
 • Nutzer hochstufen/degradieren
 • Admin-Liste und Einladungslink sehen
 • Befehle des Chats aktivieren/deaktivieren
 • Nutzer Muten/Entmuten
 • Nutzer vom Chat verbannen/Entbannen

 - /connection <Chat-ID>: Mit einem Chat, in dem du Admin bist, verbinden
 - /disconnect: Die Verbindung zum Chat trennen
 - /allowconnect on/yes/off/no: Es erlauben/Verbieten, dass die Gruppe verknüpft werden kann.
"""
"""
 - /filters: Aktuelle Filter im Chat anzeigen lassen

*Nur für Admins:*
 - /filter <keyword> <Antwortnachricht>: Eine automatische Antwort zum Chat hinzufügen , \
wenn ein festgelegtes Wort/ein  festgelegter Satz im Chat erwähnt wird,  \
antworte ich mit einem festgelegten Wort/Satz- z.B.: /filter 'Hey, was geht?' Yo, wat up? \
 - /stop <Filter-Keyword>: Stoppt den Filter.
"""
"""
 - /cmds: Den aktuellen Status deaktivierter Befehele einsehen

*Nur für Admins:*
 - /enable <Befehlname>: Den Befehl aktivieren
 - /disable <Befehlname>: Den Befehl deaktivieren
 - /listcmds: Liste aller veränderbaren Befehle
"""
"""
 - /locktypes: Eine Liste der möglichen Inhaltssperren erhalten

*Nur für Admins:*
 - /lock <type>: Sperrt Inhalte deiner Wahl
 - /unlock <type>: Entsperrt Inhalte deiner Wahl
 - /locks: the current list of locks in this chat.

Sperren können dazu genutzt werden, Nutzer zu sperren
z.B.:
Das Sperren von URLs löscht alle Nachrichten mit URLs, die nicht auf die Whitelist gesetzt wurden. Das Sperren von Stickern wird alle gesendeten Sticker löschen \
etc...
Mit /lock bots kannst du verhindern, dass nicht-Admins Bots hinzufügen.
"""
"""
*Nur für Admins:*
- /logchannel: Die Log-Kanal-Info erhalten
- /setlog: Den Log-Kanal setzen.
- /unsetlog: Den Log-Kanal entfernen.

So kannst du den Log-Kanal setzen:
- Den Bot zum gewünschten Kanal als Admin hinzufügen
- /setlog in den Kanal senden
- Die /setlog Nachricht aus dem Kanal in die Gruppe weiterleiten.
"""
"""
 - /id: Die Gruppen-ID erhalten. Falls mit der Nachricht auf einen Nutzer geantwortet wird, wird seine ID ausgegeben.
 - /info: Infos über den entsprechenden Nutzer erhalten.
 - /stickerid: Auf einen Sticker antworten, um seine ID zu erhalten.
 - /getsticker: Auf einen Sticker antworten, um ihn als PNG Bild zu erhalten.
"""
"""
*Nur für Admins:*
 - /del: Löscht die Nachricht, auf die geantwortet wird.
 - /purge: Löscht alles zwischen der Nachricht, auf die geantwortet wird und der geschickten.
"""
"""
*Nur für Admins:*
 - /mute <userhandle>: Schält einen User stumm.
 - /unmute <userhandle>: Hebt die Stummschaltung eines Nutzers auf.
 - /restrict <userhandle>: Einem Nutzer verbieten, z.B. Medien oder Links zu schicken.
 - /trestrict <userhandle> x(m/h/d): restricts a user for x time. (via handle, or reply). m = minutes, h = hours, d = days.
 - /unrestrict <userhandle>: unrestricts a user from sending stickers, gif, embed links or media. Can also be used as a reply, restrict the replied to user.
"""
"""
 - /get <notename>: get the note with this notename
 - #<notename>: same as /get
 - /notes or /saved: list all saved notes in this chat

If you would like to retrieve the contents of a note without any formatting, use `/get <notename> noformat`. This can \
be useful when updating a current note.

*Admin only:*
 - /save <notename> <notedata>: saves notedata as a note with name notename
A button can be added to a note by using standard markdown link syntax - the link should just be prepended with a \
`buttonurl:` section, as such: `[somelink](buttonurl:example.com)`. Check /markdownhelp for more info.
 - /save <notename>: save the replied message as a note with name notename
 - /clear <notename>: clear note with this name
"""
"""
 - /report <reason>: reply to a message to report it to admins.
 - @admin: reply to a message to report it to admins.
NOTE: neither of these will get triggered if used by admins

*Admin only:*
 - /reports <on/off>: change report setting, or view current status.
   - If done in pm, toggles your status.
   - If in chat, toggles that chat's status.
"""
"""
 - /addrss <link>: add an RSS link to the subscriptions.
 - /removerss <link>: removes the RSS link from the subscriptions.
 - /rss <link>: shows the link's data and the last entry, for testing purposes.
 - /listrss: shows the list of rss feeds that the chat is currently subscribed to.

NOTE: In groups, only admins can add/remove RSS links to the group's subscription
"""
"""
 - /rules: get the rules for this chat.

*Admin only:*
 - /setrules <your rules here>: set the rules for this chat.
 - /clearrules: clear the rules for this chat.
"""
"""
 - s/<text1>/<text2>(/<flag>): Reply to a message with this to perform a sed operation on that message, replacing all \
occurrences of 'text1' with 'text2'. Flags are optional, and currently include 'i' for ignore case, 'g' for global, \
or nothing. Delimiters include `/`, `_`, `|`, and `:`. Text grouping is supported. The resulting message cannot be \
larger than {}.

*Reminder:* Sed uses some special characters to make matching easier, such as these: `+*.?\\`
If you want to use these characters, make sure you escape them!
eg: `\\?`.
"""
"""
 - /setbio <text>: while replying, will save another user's bio
 - /bio: will get your or another user's bio. This cannot be set by yourself.
 - /setme <text>: will set your info
 - /me: will get your or another user's info
"""
"""
 - /warns <userhandle>: get a user's number, and reason, of warnings.
 - /warnlist: list of all current warning filters

*Admin only:*
 - /warn <userhandle>: warn a user. After 3 warns, the user will be banned from the group. Can also be used as a reply.
 - /resetwarn <userhandle>: reset the warnings for a user. Can also be used as a reply.
 - /addwarn <keyword> <reply message>: set a warning filter on a certain keyword. If you want your keyword to \
be a sentence, encompass it with quotes, as such: `/addwarn "very angry" This is an angry user`. 
 - /nowarn <keyword>: stop a warning filter
 - /warnlimit <num>: set the warning limit
 - /strongwarn <on/yes/off/no>: If set to on, exceeding the warn limit will result in a ban. Else, will just kick.
"""

"""
Your group's welcome/goodbye messages can be personalised in multiple ways. If you want the messages \
to be individually generated, like the default welcome message is, you can use *these* variables:
 - `{{first}}`: this represents the user's *first* name
 - `{{last}}`: this represents the user's *last* name. Defaults to *first name* if user has no last name.
 - `{{fullname}}`: this represents the user's *full* name. Defaults to *first name* if user has no last name.
 - `{{username}}`: this represents the user's *username*. Defaults to a *mention* of the user's first name if has no username.
 - `{{mention}}`: this simply *mentions* a user - tagging them with their first name.
 - `{{id}}`: this represents the user's *id*.
 - `{{count}}`: this represents the user's *member number*.
 - `{{chatname}}`: this represents the *current chat name*.
Each variable MUST be surrounded by `{{}}` to be replaced.
Welcome messages also support markdown, so you can make any elements bold/italic/code/links. \
Buttons are also supported, so you can make your welcomes look awesome with some nice intro \
buttons. To create a button linking to your rules, use this: `[Rules](buttonurl://t.me/{}?start=group_id)`. \
Simply replace `group_id` with your group's id, which can be obtained via /id, and you're good to \
go. Note that group ids are usually preceded by a `-` sign; this is required, so please don't \
remove it. \
If you're feeling fun, you can even set images/gifs/videos/voice messages as the welcome message by \
replying to the desired media, and calling /setwelcome.

*Admin only:*
 - /welcome <on/off>: enable/disable welcome messages.
 - /welcome: shows current welcome settings.
 - /welcome noformat: shows current welcome settings, without the formatting - useful to recycle your welcome messages!
 - /goodbye -> same usage and args as /welcome.
 - /setwelcome <sometext>: set a custom welcome message. If used replying to media, uses that media.
 - /setgoodbye <sometext>: set a custom goodbye message. If used replying to media, uses that media.
 - /resetwelcome: reset to the default welcome message.
 - /resetgoodbye: reset to the default goodbye message.
 - /cleanwelcome <on/off>: On new member, try to delete the previous welcome message to avoid spamming the chat.
 - /cleanservice <on/off/yes/no>: deletes all service message; those are the annoying "x joined the group" you see when people join.
 - /welcomesecurity <off/soft/hard>: soft - restrict user's permission to send media files for 24 hours, hard - restict user's permission to send messages until they click on the button \"I'm not a bot\"
"""