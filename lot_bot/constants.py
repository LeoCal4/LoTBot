""" This module is used to define constants"""
# https://core.telegram.org/bots/api#markdownv2-style


# ================================== PAYMENTS =========================================

REFERRAL_CODE_LEN = 8

PAYMENT_BASE_TEXT = """Se hai un <i>codice sconto o referral</i> <b>inseriscilo</b> adesso 🚀

<i>(Durante il pagamento ti chiederemo email e nome al solo fine di contattarti in caso di necessità)</i>"""


PAYMENT_EXISTING_REFERRAL_CODE_TEXT = """Il codice di referral che hai aggiunto è {0}.

Se vuoi cambiarlo, invia un messaggio con un altro codice di referral valido oppure premi il bottone sottostante per procedere"""

PAYMENT_ADD_REFERRAL_CODE_TEXT = """Invia un messaggio con un codice di referral valido oppure premi il bottone sottostante per procedere."""


# ================================== MAIN MENU =========================================

BENTORNATO_MESSAGE = "Bentornato, puoi continuare ad utilizzare il bot"

LISTA_CANALI_MESSAGE = "Questa è la lista dei canali di cui è possibile ricevere le notifiche"

# {0}: the expiration date for the user
SPORT_MENU_MESSAGE = """<b>Seleziona</b> gli sport che vuoi seguire 🚀 

PS: nel gruppo <a href="http://t.me/LoTVerse">Community</a> trovi suggerimenti e consigli giornalieri!

(<i>Puoi selezionare la tipologia di evento di ogni sport!</i>)

🟢 Attivato 🔴 Disattivato"""


HOMEPAGE_MESSAGE = """<b>Homepage</b> 📱

👉<b>Seleziona</b> un tasto oppure <i>attendi una notifica dal bot</i>!

<b>Fatto in  🇮🇹  con</b> ♥️"""


STRATEGIES_EXPLANATION_MESSAGE = """<b>Seleziona</b> le strategie che vuoi scoprire 🚀

<i>PS: tramite l'assistenza possiamo <b>personalizzarle</b> solo per te!</i>"""


RESOCONTI_MESSAGE = "Scegli il tipo di resoconto"

# {0}: user first name
# {1}: the expiration date for the user
SERVICE_STATUS_MESSAGE = """Ciao {0} 😊 il tuo abbonamento è attivo fino al {1}.

Status Servizio: ✅ nessuna manutenzione programmata."""


BOT_CONFIG_BUTTON_TEXT = "⚙️ Configurazione Bot 🤖"
EXPERIENCE_BUTTON_TEXT = "🚥 Gestione Esperienza 🚥"
ASSISTANCE_BUTTON_TEXT = "🧑🏽‍💻 Assistenza 👩🏻‍💼 "


# ================================== FIRST USAGE =========================================

# {0}: first name of the user
# {1}: subscription expiration date 
WELCOME_MESSAGE = """Benvenuto/a {0}! 👍

<i>Questo Bot ti aiuta a gestire i tuoi investimenti e notifica eventi sportivi analizzati dal nostro Team</i> ❗️

-Premi <b>Configurazione Bot</b> per scegliere gli <i>sport</i>, le <i>strategie</i>, modificare il tuo <i>budget</i> etc.

-Scrivi in <b>Assistenza</b> per <i>personalizzare la tua esperienza</i> in base alle tue preferenze e obiettivi

<b>La tua prova gratuita scadrà il {1}</b>

Versione 1.00"""


# {0}: user id
# {1}: user first name
# {2}: user username
NEW_USER_MESSAGE = """Un nuovo utente ha avviato il bot!

Telegram ID: {0}
Nome: {1}
Username: {2}"""

# ================================== ERRORS =========================================

ERROR_MESSAGE = """Abbiamo riscontrato un problema tecnico con il bot. 
Si consiglia di riprovare più tardi, ci scusiamo per il disagio."""


