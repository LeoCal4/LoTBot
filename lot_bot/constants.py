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


SUCCESSFUL_PAYMENT_TEXT = """Grazie per il tuo acquisto!
Stai dando un grande contributo al nostro progetto che punta a contrastare la ludopatia formando i giocatori di oggi e del domani!

Accedi premendo <a href="https://t.me/+jW-C8fxuYXU5ZDJk">qui al gruppo LoT Meister</a> dove trovi tutto il team, le dirette e registrazioni e tanto altro ancora!

<b>PS: Condividi questo screenshot taggandoci su Instagram per ricevere un omaggio!</b>"""


# ================================== MAIN MENU =========================================

BENTORNATO_MESSAGE = "Bentornato, puoi continuare ad utilizzare il bot"

LISTA_CANALI_MESSAGE = "Questa è la lista dei canali di cui è possibile ricevere le notifiche"

# {0}: the expiration date for the user
SPORT_MENU_MESSAGE = """<b>Seleziona</b> gli sport che vuoi seguire 🚀 

<i>Puoi selezionare la tipologia di evento di ogni sport!</i>

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
SERVICE_STATUS_MESSAGE = """Ciao {0} 😊 lo status della tua iscrizione al servizio è il seguente:\n"""

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

#TODO change these messages
BOT_CONFIG_MENU_MESSAGE = """<b>Configurazione Bot</b> 📱

👉<b>Seleziona</b> un tasto oppure <i>attendi una notifica dal bot</i>!

<b>Fatto in  🇮🇹  con</b> ♥️"""

EXPERIENCE_MENU_MESSAGE = """<b>Gestione Esperienza</b> 📱

👉<b>Seleziona</b> un tasto oppure <i>attendi una notifica dal bot</i>!

<b>Fatto in  🇮🇹  con</b> ♥️"""

USE_GUIDE_MENU_MESSAGE = """<b>Guida all' uso</b> 📱

👉<b>Seleziona</b> un tasto oppure <i>attendi una notifica dal bot</i>!

<b>Fatto in  🇮🇹  con</b> ♥️"""

#Configurazione Bot messaggi interni #valutare se modificare gestione budget con gestione andamento o gestione portafoglio oppure altro
GESTIONE_BUDGET_MENU_MESSAGE = """<b>Gestione Budget</b> 📱

👉<b>Seleziona</b> un tasto oppure <i>attendi una notifica dal bot</i>!

<b>Fatto in  🇮🇹  con</b> ♥️"""


# ================================== FIRST USAGE =========================================

# {0}: first name of the user
# {1}: subscription name
# {2}: subscription expiration date 
WELCOME_MESSAGE = """Benvenuto/a {0}! 👍

<i>Questo Bot ti aiuta a gestire i tuoi investimenti e notifica eventi sportivi analizzati dal nostro Team</i> ❗️

-Premi <b>Configurazione Bot</b> per scegliere gli <i>sport</i>, le <i>strategie</i>, modificare il tuo <i>budget</i> etc.

-Scrivi in <b>Assistenza</b> per <i>personalizzare la tua esperienza</i> in base alle tue preferenze e obiettivi

<b>La tua prova gratuita per l'abbonamento <b>{1}</b> scadrà il {2}</b>

Versione 1.00"""
WELCOME_MESSAGE_v2 = """Ciao! Io sono SportSignalsBoT il tuo strumento di supporto nel betting !
Grazie alle mie funzioni potrai: 

- Ricevere eventi analizzati da un team di analisi su vari sport!
- Tracciare i tuoi investimenti e avere la tua reportistica personale!
- Accedere al gruppo privato LoT – Meister dove trovi tutto il team di LoT per avere analisi personalizzate, consulenza per i tuoi obiettivi e migliorare i tuoi rendimenti !

Queste sono solo alcune delle principali funzioni a tua disposizione!

Prima di procedere per favore leggi il Disclaimer e la nostra breve Guida!
Premi avanti quando sei pronto, sarò qui ad aspettarti !!"""


# {0}: valid ref code
SUCC_REFERRED_USER_MESSAGE = "Il tuo account è stato collegato con successo tramite il codice {0}!"

# {0}: invalid ref code
NO_REFERRED_USER_FOUND_MESSAGE = """Purtroppo non siamo riusciti a trovare nessun utente collegato al codice referral {0}.
Contatta l'<a href="https://t.me/LegacyOfTipstersBot">Assistenza</a> e riporta il problema nella chat."""


SUCC_TEACHERBET_TRIAL_MESSAGE = "Il tuo account ha ottenuto 3 giorni di prova gratuita per l'abbonamento Teacherbet!"
ALREADY_USED_TEACHERBET_TRIAL_MESSAGE = "Il tuo account non può più utilizzare la prova gratuita per l'abbonamento Teacherbet."
FAILED_TEACHERBET_TRIAL_MESSAGE = """Purtroppo non siamo riusciti ad attivare la prova gratuita di Teacherbet.
Contatta l'<a href="https://t.me/LegacyOfTipstersBot">Assistenza</a> e riporta il problema nella chat."""


# {0}: user id
# {1}: user first name
# {2}: user username
NEW_USER_MESSAGE = """Un nuovo utente ha avviato il bot!

Telegram ID: {0}
Nome: {1}
Username: {2}"""

# {0}: user id
# {1}: user first name
# {2}: user username
# {3}: subscription
# {4}: new expiration date
# {5}: price
# The actual message sent to the channel has an additional string with information about success of the payment
NEW_PAYMENT_CHANNEL_MESSAGE = """Un utente ha effettuato un pagamento!

Telegram ID: {0}
Nome: {1}
Username: {2}
Servizio: {3}
Valido fino al: {4}
Costo: {5}\n"""

FIRST_BUDGET_NAME = "Demo"
# ================================== STRATEGIES EXPLANATION ========================================= 

SINGOLALOW_EXPL_TEXT = """Singole analisi di eventi con quota inferiore o uguale a 2.10"""
SINGOLAHIGH_EXPL_TEXT = """Singole analisi di eventi con quota superiore o uguale a 2.11"""
RADDOPPIO_EXPL_TEXT = """Singola o Doppia con quota compresa tra 1.90 e 2.40"""
SPECIALI_EXPL_TEXT = """Analisi su parametri non standard come Marcatori, Corner, Cartellini etc."""
MULTIPLALIGHT_EXPL_TEXT = """Pochi selezionati eventi per un moltiplicatore massimo di 9.90"""
PDR_EXPL_TEXT = """Analisi del Prof_Dei_Raddoppi, nostro partner e collega"""
MAXEXCHANGE_EXPL_TEXT = """L'Exchange di LoT perfetto sia per i neofiti che per gli esperti"""
MB_EXPL_TEXT = """Matched Betting significa accoppiare quote su diversi bookmakers per avere una percentuale di presa pari al 100%.\nSuggeriamo di Contattarci per usare al meglio questa strategia"""
SCALPING_EXPL_TEXT = """Scalping significa lavorare sulla variazione di quota e spesso trarre profitto prima che il match inizi grazie a notizie e informazioni che alterano il valore di quota.\nSuggeriamo di contattarci per usare al meglio questa strategia"""
BASE_EXPL_TEXT = """Analisi generali di eventi per sport che non hanno ancora sufficiente storico per diversificare le analisi"""
INSTAGRAMFREE_EXPL_TEXT = """Raccolta di eventi gratuiti pubblicati su Instagram"""
MULTIPLA_EXPL_TEXT = """Multipla di qualsiasi capienza e quota con moltiplicatori alti"""
SOFAR_EXPL_TEXT = """Eventi di lunga durata (settimane/mesi) come vincitori di tornei e competizioni"""

PRODUZIONE_EXPL_TEXT = """La strategia base di LoT per ogni sport con analisi ed esposizioni mirate, è possibile richiedere la personalizzazione stake scrivendo all' <a href="https://t.me/LegacyOfTipstersBot">Assistenza</a> ! """ #TODO inserire link assistenza
LIVE_EXPL_TEXT = """Solo eventi Live, in generale di tipo Singola"""
EXTRA_EXPL_TEXT = """Tutte quelle analisi che non rientrano nelle altre strategie, generalmente eventi più rischiosi che vanno gestiti con una minima quota del capitale (10%/mese al massimo!)"""
TEST_EXPL_TEXT = """Dedicata al team serve per testare nuove strategie, analisi, parametri etc."""
FREEBET_EXPL_TEXT = """La nostra produzione gratuita per tutti ! Spesso reperibili sui nostri vari social e canali ufficiali !"""
COMMUNITYBET_EXPL_TEXT = """Eventi analizzati dal team e scelti da voi tutti insieme ! Together is Better !"""
INFORMAZIONE_EXPL_TEXT = """Tutte le notizie del mondo del gioco d’azzardo direttamente dalla redazione di LoT !"""
FANTACONSIGLI_EXPL_TEXT = """In collaborazione con @CalciatoriPerSbaglio [inserire link ig] i migliori suggerimenti per la tua rosa !""" #TODO inserire link instragram
FATTENARISATA_EXPL_TEXT = """Il tuo sorriso giornaliero, vignette e meme per iniziare la giornata al meglio !"""

DEFAULT_STRAT_EXPLANATION_TEXT = """Contatta l'<a href="https://t.me/LegacyOfTipstersBot">Assistenza</a> per avere maggiori informazioni su questa strategia!"""

# ================================== ERRORS =========================================

ERROR_MESSAGE = """☠️ Abbiamo riscontrato un problema tecnico con il bot ☠️

Invia <i>uno screen</i> di questa chat all'<a href="https://t.me/LegacyOfTipstersBot">Assistenza</a> per mostrarci l'errore, <i>scrivendo brevemente</i> cosa stavi cercando di fare, grazie 🔥"""
