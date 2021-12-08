""" This module is used to define constants"""
# https://core.telegram.org/bots/api#markdownv2-style


# ================================== PAYMENTS =========================================

REFERRAL_CODE_LEN = 8

PAYMENT_BASE_TEXT = """Se hai un <i>codice sconto o referral</i> <b>inseriscilo</b> adesso 🚀

<i>(Durante il pagamento ti chiederemo email e nome al solo fine di contattarti in caso di necessità)</i>"""


EXISTING_LINKED_REFERRAL_CODE_TEXT = """Il codice di referral a cui sei collegato è <b>{0}</b>.

Se vuoi cambiarlo, invia un messaggio con un altro codice di referral valido oppure premi il bottone sottostante per procedere"""

ADD_LINKED_REFERRAL_CODE_TEXT = """Invia un messaggio con un codice di referral valido oppure premi il bottone sottostante per procedere."""



UPDATE_PERSONAL_REFERRAL_CODE_TEXT = """Il tuo codice di referral attuale è <b>{0}</b>.
Invia un messaggio con un codice di referral valido oppure premi il bottone sottostante per procedere.

ATTENZIONE: per essere valido, il nuovo codice deve contenere <i>solo lettere o numeri</i>. Inoltre, alla fine del codice, verrà aggiunto in automatico '-lot'.""" 


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


BASE_RESOCONTI_MESSAGE = "Scegli il tipo di resoconto:"

# {0}: resoconto type
RESOCONTI_MESSAGE = """Hai ricevuto: {0}

Scegli il tipo di resoconto"""


# {0}: user first name
SERVICE_STATUS_MESSAGE = """Ciao {0} 😊 lo status dei tuoi abbonamenti è il seguente:\n"""

# {1}: linked referral code
# {2}: user successful_referrals_since_last_payment
"""Il tuo codice di affiliazione (da inviare ai tuoi amici): {0}

Il codice di affiliazione collegato al tuo account: {1}

Dal tuo ultimo pagamento, {2} altri utenti hanno rinnovato l'abbonamento utilizzando il tuo codice di referral."""

# {0}: user referral code
# {1}: user ref link
REFERRAL_MENU_MESSAGE = """💥 Questo è il tuo codice referral: <b>{0}</b> 
E questo è il link che puoi condividere per farlo collegare ai tuoi amici: {1} 🚀

Per ogni amico che <i>tramite il tuo codice</i> acquista un mese di LoT <b>riceverai il 33% di sconto</b> sul prossimo acquisto!

🌟 <b>3 amici = LoT Gratis</b> ✅

<i>PS: raggiunti i 3 amici LoT ti permette di guadagnare su ogni referenza. <a href="http://t.me/LegacyOfTipstersBot/">Contattaci qui</a> scrivendo "Info Referral" 👍</i>"""


BOT_CONFIG_BUTTON_TEXT = "⚙️ Configurazione Bot 🤖"
EXPERIENCE_BUTTON_TEXT = "🚥 Gestione Esperienza 🚥"
USE_GUIDE_BUTTON_TEXT = "🧑🏽‍💻 Guida all'Uso 🧑🏽‍💻"


# ================================== FIRST USAGE =========================================

# {0}: first name of the user
# {1}: subscription expiration date 
WELCOME_MESSAGE = """Benvenuto/a {0}! 👍

<i>Questo Bot ti aiuta a gestire i tuoi investimenti e notifica eventi sportivi analizzati dal nostro Team</i> ❗️

-Premi <b>Configurazione Bot</b> per scegliere gli <i>sport</i>, le <i>strategie</i>, modificare il tuo <i>budget</i> etc.

-Scrivi in <b>Assistenza</b> per <i>personalizzare la tua esperienza</i> in base alle tue preferenze e obiettivi

<b>La tua prova gratuita scadrà il {1}</b>

Versione 1.00"""


# {0}: valid ref code
SUCC_REFERRED_USER_MESSAGE = "\n\nIl tuo account è stato collegato con successo tramite il codice {0}!"

# {0}: invalid ref code
NO_REFERRED_USER_FOUND_MESSAGE = """\n\nPurtroppo non siamo riusciti a trovare nessun utente collegato al codice referral {0}.
Contatta l'<a href="https://t.me/LegacyOfTipstersBot">Assistenza</a> e riporta il problema nella chat."""


# {0}: user id
# {1}: user first name
# {2}: user username
NEW_USER_MESSAGE = """Un nuovo utente ha avviato il bot!

Telegram ID: {0}
Nome: {1}
Username: {2}"""

# ================================== ERRORS =========================================

ERROR_MESSAGE = """☠️ Abbiamo riscontrato un problema tecnico con il bot ☠️

Invia <i>uno screen</i> di questa chat all'<a href="https://t.me/LegacyOfTipstersBot">Assistenza</a> per mostrarci l'errore, <i>scrivendo brevemente</i> cosa stavi cercando di fare e riceverai <b>un giorno di servizio in più</b>! 🔥"""
