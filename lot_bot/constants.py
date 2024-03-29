""" This module is used to define constants"""
# https://core.telegram.org/bots/api#markdownv2-style


# ================================== PAYMENTS =========================================

REFERRAL_CODE_LEN = 8

PAYMENT_BASE_TEXT = """<i>Se hai un <b>codice</b> sconto/amico o referral inseriscilo adesso e premi invio, oppure premi il pulsante sotto ! 😊</i>"""


EXISTING_LINKED_REFERRAL_CODE_TEXT = """Il codice amico a cui sei collegato è <b>{0}</b>.

Se vuoi cambiarlo, invia un messaggio con un altro codice amico valido oppure premi il bottone sottostante per procedere"""

ADD_LINKED_REFERRAL_CODE_TEXT = """Invia un messaggio con un codice amico valido oppure premi il bottone sottostante per procedere."""



UPDATE_PERSONAL_REFERRAL_CODE_TEXT = """Il tuo codice amico attuale è <b>{0}</b>.
<b>Invia un messaggio</b> con il codice che vorresti avere oppure premi il bottone sottostante per tornare indietro! ✌️

<b>ATTENZIONE:</b> per essere valido il nuovo codice deve contenere solo lettere e/o numeri. Alla fine codice verrà aggiunto in automatico "-lot" se non è già presente.""" 


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

👉 /start serve a lanciare questo menu che comprende i tasti:

- Energia, ricarica il tuo bot o condividilo con gli amici !
- Impostazioni, seleziona i tuoi sport, il tuo budget, i tuoi resoconti!
- Guida all'uso, ti spieghiamo come funziona !

Ti invierò analisi sportive non appena disponibili, per qualsiasi domanda scrivi su @TeamLoT"""


STRATEGIES_EXPLANATION_MESSAGE = """<b>Seleziona</b> le strategie che vuoi scoprire 🚀

<i>PS: contattaci su @teamlot per maggiori informazioni!</i>"""


BASE_RESOCONTI_MESSAGE = "Scegli il tipo di resoconto:"

# {0}: resoconto type
RESOCONTI_MESSAGE = """Hai ricevuto: {0}

Scegli il tipo di resoconto"""


# {0}: user first name
SERVICE_STATUS_MESSAGE = """Ciao {0} 😊
La tua ultima ricarica durerà fino al:\n"""

# {1}: linked referral code
# {2}: user successful_referrals_since_last_payment
"""Il tuo codice di affiliazione (da inviare ai tuoi amici): {0}

Il codice di affiliazione collegato al tuo account: {1}

Dal tuo ultimo pagamento, {2} altri utenti hanno rinnovato l'abbonamento utilizzando il tuo codice di referral."""

# {0}: user referral code
# {1}: user ref link
REFERRAL_MENU_MESSAGE = """💥 Questo è il tuo codice amico (referral): <b>{0}</b> 
<b>Condividi il tuo link 🔄:</b> {1} 🚀

Per ogni 10 amici che tramite il tuo codice <b>attivano</b> il bot, <b>riceverai un mese gratuito!!</b>

🌟 10 amici = BoT Gratis ✅

Conteggio attuale degli utenti che hanno utilizzato il tuo codice:
"""
HOW_WORK_MESSAGE = """<b>COME FUNZIONA ?</b> 
 
<b>Il bot ti notifica eventi analizzati dai nostri analisti in base alle tue preferenze ! ✅</b> 
 
Tramite il tasto "<i>il mio bot</i>" puoi configurare le tue preferenze! 
 
<b>Ti basterà attendere un evento e premere SI o NO</b> per aggiungerlo alla tuo report e <b>ricevere una notifica ad evento concluso ! ✅</b>
 
<b>Scopri di più sulla <a href="https://www.instagram.com/sportsignalsbot/">pagina Instagram</a> del bot o sul nostro <a href="https://www.lotverse.it/">sito web</a> ✌️</b> 
 
<i>Ti ricordiamo che hai sempre a disposizione un <b>consulente</b> per aiutarti nel tuo percorso. 
 
Parliamo di analisti sportivi che oltre a <b>fornirti analisi personalizzate</b> possono supportarti con competenza e passione nella <b>tua crescita personale e professionale</b> nel mondo del betting ! 🔥</i>"""

BOT_CONFIG_BUTTON_TEXT = "⚙️ Impostazioni 🤖"
ENERGY_BUTTON_TEXT = "🌟 Energia 💸"
USE_GUIDE_BUTTON_TEXT = "🧑🏽‍💻 Guida all'Uso 🧑🏽‍💻"

#TODO change these messages
BOT_CONFIG_MENU_MESSAGE = """<b>Configurazione Bot</b> 📱

👉<b>Seleziona</b> un tasto oppure <i>attendi una notifica dal bot</i>!
"""

PAY_AND_REF_MENU_MESSAGE = """<b>Energia</b> 📱"""

"""
👉<b>Seleziona</b> un tasto oppure <i>attendi una notifica dal bot</i>!
"""

EXPERIENCE_MENU_MESSAGE = """<b>Gestione Esperienza</b> 📱

👉<b>Seleziona</b> un tasto oppure <i>attendi una notifica dal bot</i>!
"""

USE_GUIDE_MENU_MESSAGE = """<b>Guida all' uso</b> 📱

👉<b>Seleziona</b> un tasto oppure <i>attendi una notifica dal bot</i>!
"""

#Configurazione Bot messaggi interni #valutare se modificare gestione budget con gestione andamento o gestione portafoglio oppure altro
GESTIONE_BUDGET_MENU_MESSAGE = """<b>Gestione Budget</b> 📱

👉<b>Seleziona</b> un tasto oppure <i>attendi una notifica dal bot</i>!
"""


# ================================== FIRST USAGE =========================================

# {0}: first name of the user
# {1}: subscription name
# {2}: subscription expiration date 
WELCOME_MESSAGE = """Benvenuto/a {0}! 👍

<i>Questo Bot ti aiuta a gestire i tuoi investimenti e notifica eventi sportivi analizzati dal nostro Team</i> ❗️

-Premi <b>Configurazione Bot</b> per scegliere gli <i>sport</i>, le <i>strategie</i>, modificare il tuo <i>budget</i> etc.

-Scrivi a <b>@teamlot</b> per <i>personalizzare la tua esperienza</i> in base alle tue preferenze e obiettivi

<b>La tua prova gratuita per l'abbonamento <b>{1}</b> scadrà il {2}</b>

Versione 1.00"""
WELCOME_MESSAGE_v2 = """<i><b>Ciao {0}! </b></i>👋

Tramite questo bot riceverai <b>eventi analizzati</b> dal nostro team di analisti su vari sport e <b>molto altro.</b>
Se ti serve aiuto -> <i>@TeamLoT</i>

Premi qui ⬇️ per ricevere le analisi!
"""

"""<i><b>Ciao {0}! </b>👋
Io sono <b>SportSignalsBoT</b> il tuo strumento di supporto nel betting!  
 
Grazie alle mie funzioni potrai: </i> 
 
- Ricevere <b>eventi analizzati</b> dal <b>team di analisi</b> di LoT su vari sport! 
 
- <b>Tracciare i tuoi investimenti</b> e avere la tua reportistica personale! 
 
- Ricevere supporto da <b>un consulente a te dedicato</b> per il tuo percorso e per analisi personalizzate! 
 
<i>Queste sono solo alcune delle principali funzioni a tua disposizione!  
 
<b>Prima di procedere per favore leggi il Disclaimer!</b></i> 
 
Premi <b>avanti</b> quando sei pronto, sarò qui ad aspettarti ✌️"""

NO_GIOCATA_TO_SEND_ON_FIRST_USAGE = """<b>Attualmente non ci sono eventi da visualizzare.</b>
Scrivi a @TeamLoT per ricevere delle analisi private! ✌️

Oppure

Attendi l’invio dei match dal bot!

PS: ti suggerisco di creare una cartella così da non perdermi mai di vista"""

MSG_BENVENUTO = """Messaggio da @TeamLoT:

Ciao {0}!
È un piacere averti a bordo con noi ! 🚀

Io sono <b>Massimiliano Malfatti</b> fondatore del progetto e su telegram mi trovi scrivendo a @TeamLoT o in privato a @Pentium077 ✌️

Sono un consulente finanziario e <b>studio da oltre 10 anni il settore del gioco d'azzardo</b> perché desidero migliorarlo, renderlo più sicuro.

<b>Dalle mie ricerche e dai preziosi feedback raccolti in questi ultimi anni è nata LoT</b>, start up che sta realizzando tecnologie per rinnovare il mercato.

Quello che ti presento oggi, lo SportSignalsBoT, è solo il <b>primo di diversi progetti che arriveranno nei prossimi anni</b> <i>(scopri di più sul nostro sito!)</i>

<b>Questo BoT nasce perché mi sono stancato di vedere quanti tipster fanno perdere denaro alle persone 😡</b>

Con il team abbiamo fatto una <b>scelta:</b>
<b>
NON lavorare con i Casinò
e NON guadagnare sulle tue perdite.
</b>
Noi <b>guadagniamo da quegli utenti che scelgono di pagare il nostro servizio premium</b>, quello che hai di prova per questi 5 giorni.🔥

Forniamo anche <b>Consulenze private INCLUSE</b> con l'acquisto del bot e tantissime <b>analisi personalizzate</b> in base alle proprie preferenze.

<b>Anche se sei un esperto di Betting ti chiedo di metterti in contatto con noi tramite</b> @TeamLoT per poterti guidare al meglio alla scoperta del servizio che abbiamo creato per te ! 😊

Ti manderò altri messaggi durante questi giorni per sapere come sta andando, per qualsiasi cosa <b>non esitare a contattarmi</b>, a presto!

<i>-Massimiliano Malfatti</i>


PS: <i>Dietro ogni analisi che ti manda il bot <b>c'è il mio team di analisti sportivi</b> e nessun algoritmo preimpostato!</i>
<i>Suggerimento: Ti consiglio di fissare in alto il bot, ti basterà tenere premuto sul bot e premere "fissa" così non perderai nessun match !</i>🔥
"""

# {0}: valid ref code
SUCC_REFERRED_USER_MESSAGE = "Il tuo account è stato collegato con successo tramite il codice {0}!"

# {0}: invalid ref code
NO_REFERRED_USER_FOUND_MESSAGE = """Purtroppo non siamo riusciti a trovare nessun utente collegato al codice referral {0}.
Contattaci su @teamlot e riporta il problema nella chat."""


SUCC_TEACHERBET_TRIAL_MESSAGE = "Il tuo account ha ottenuto 3 giorni di prova gratuita per l'abbonamento Teacherbet!"
ALREADY_USED_TEACHERBET_TRIAL_MESSAGE = "Il tuo account non può più utilizzare la prova gratuita per l'abbonamento Teacherbet."
FAILED_TEACHERBET_TRIAL_MESSAGE = """Purtroppo non siamo riusciti ad attivare la prova gratuita di Teacherbet.
Contattaci su @teamlot e riporta il problema nella chat."""


# {0}: user id
# {1}: user first name
# {2}: user username
NEW_USER_MESSAGE = """Un nuovo utente ha avviato il bot!

Telegram ID: {0}
Nome: {1}
Username: @{2}"""

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

FIRST_BUDGET_NAME = "Primo budget"

# ================================== TUTORIAL CHECKLIST ==========================================
# spots needs to be filled with the relative emoji (✅ or ❌)
TUTORIAL_CHECKLIST = """<b>-----------HAPPY TASK------------------</b>\nCompleta i seguenti obiettivi per ottenere <b>2 giorni extra</b> 🚀
✅ Avvia il bot
{budget_check} Imposta il budget
{event_check} Registra un evento
{referral_check} Personalizza il codice amico
<b>-----------HAPPY TASK------------------</b>"""

CHECKLIST_COMPLETED =  "💥 <b>Complimenti!</b> 💥\nHai completato tutti gli obiettivi, il tuo abbonamento è stato esteso di 2 giorni! 🚀"

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

PRODUZIONE_EXPL_TEXT = """La strategia base di LoT per ogni sport con analisi ed esposizioni mirate <i>(puoi avere la personalizzazione degli stake scrivendo su @teamlot)</i>"""
LIVE_EXPL_TEXT = """ Solo eventi Live o che iniziano nei prossimi 15 minuti, in generale di tipo Singola"""
EXTRA_EXPL_TEXT = """Tutte le analisi che non rientrano nelle altre strategie, generalmente eventi più rischiosi che vanno gestiti con una minima quota del capitale <i>(10%/mese al massimo!)</i> """
TEST_EXPL_TEXT = """Utilizzata dal team per testare nuove strategie, analisi, parametri etc."""
FREEBET_EXPL_TEXT = """La nostra produzione gratuita per tutti! Spesso reperibili sui nostri vari social e canali ufficiali!"""
COMMUNITYBET_EXPL_TEXT = """Eventi analizzati dal team e scelti da voi tutti insieme! <i>Together is Better!</i>"""
INFORMAZIONE_EXPL_TEXT = """Tutte le notizie del mondo del gioco d’azzardo direttamente dalla redazione di LoT!"""
FANTACONSIGLI_EXPL_TEXT = """In collaborazione con <a href="https://www.instagram.com/calciatori_per_sbaglio_">@CalciatoriPerSbaglio</a> i migliori suggerimenti per la tua rosa!""" #TODO inserire link instragram
#FATTENARISATA_EXPL_TEXT = """Il tuo sorriso giornaliero, vignette e meme per iniziare la giornata al meglio!"""

DEFAULT_STRAT_EXPLANATION_TEXT = """Contattaci su @teamlot per avere maggiori informazioni su questa strategia!"""

# ================================== ERRORS =========================================

ERROR_MESSAGE = """☠️ Abbiamo riscontrato un problema tecnico con il bot ☠️

Invia <i>uno screen</i> di questa chat a @teamlot per mostrarci l'errore, <i>scrivendo brevemente</i> cosa stavi cercando di fare, grazie 🔥"""
