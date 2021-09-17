""" This module is used to define constants
"""

# write them lowercase and with no spaces or _
SPORTS = [
    "calcio",
    "basket",
    "tennis",
    "exchange",
    "speciali",
    "pingpong",
    "hockey",
    "freccette",
    "baseball",
    "pallavolo",
    "rugby",
    "sport2"
]


# those are the ones that are shown in the keyboards 
# the keys must be equal to the values of sports
SPORTS_DISPLAY_NAMES = {
    "calcio": "Calcio",
    "basket": "Basket",
    "tennis": "Tennis",
    "exchange": "Exchange",
    "speciali": "Speciali",
    "pingpong": "Ping Pong",
    "hockey": "Hockey",
    "freccette": "Freccette",
    "baseball": "Baseball",
    "pallavolo": "Pallavolo",
    "rugby": "Rugby",
    "sport2": "Sport2"
}


# the keys of the STRATEGIES dict must be equal to the values
#   of SPORTS
_base_strategie = ["raddoppio", "multiple", "singola", "live", "instagram"]
SPORT_STRATEGIES = {
  "calcio": _base_strategie + ["piaquest", "trilled"],
  "basket": _base_strategie + ["trilled"],
  "tennis": _base_strategie + ["trilled"],
  "pingpong": _base_strategie + ["trilled"],
  "freccette": _base_strategie + ["trilled"],
  "hockey": _base_strategie + ["trilled"],
  "baseball": _base_strategie + ["trilled"],
  "exchange": ["maxexchange", "instagram"],
  "speciali": _base_strategie,
  "rugby": _base_strategie + ["trilled"],
  "sport2": _base_strategie,
  "pallavolo": _base_strategie,
}


# those are the ones that are shown in the keyboards 
# the keys must be equal to the set of values of STRATEGIES
STRATEGIES_DISPLAY_NAME = {
  "raddoppio": "Raddoppio",
  "multiple": "Multiple",
  "singola": "Singola",
  "live": "Live",
  "instagram": "Instagram",
  "piaquest": "PiaQuest",
  "trilled": "Trilled",
  "maxexchange": "MaxExchange"
}

# {0}: first name of the user
# {1}: subscription expiration date 
WELCOME_MESSAGE_PART_ONE = """<b>Benvenuto/a {0}!</b> 👍

Questo bot ti notificherà degli eventi sportivi selezionati dai nostri analisti!"


Sono in arrivo molte altre funzioni, discutine con il team e la community per <b>creare insieme il primo strumento</b> di <b>supporto</b> e <b>prevenzione</b> nel mondo del gioco d'azzardo 🚀"


Riceverai gli eventi in base agli sport che scegli premendo su <i><b>Homepage</b></i> 🏠"
    
    
<i>La tua prova gratuita scadrà il {1}</i>


Versione Alpha 0.50"""



WELCOME_MESSAGE_PART_TWO = """<i><b>LoT</b></i> è una start up con l'obiettivo di <b>contrastare la ludopatia</b> e fornire <b>supporto agli scommettitori</b> nonché <b>formazione e metodo.</b> &#128394;
    
In base alle tue <b>preferenze</b> e ai tuoi <b>obiettivi</b> realizzeremo per te un percorso nel <b>medio-lungo termine.</b> &#128202;

Il <b>team di LoT</b> da il massimo ogni giorno e se vuoi <i><b>raggiungere il tuo obiettivo dovrai impegnarti anche tu! </b></i>&#127947;

<b>Noi</b> non rischiamo, <b>ponderiamo le esposizioni. </b>
<b>Noi</b> non esageriamo, <b>gestiamo</b> in base alle nostre <b>possibilità personali. </b>
<b>Noi</b> non scommettiamo, <b>investiamo. </b>
<b>Noi</b> non siamo tipsters, <b>siamo investitori. </b>

<b>Sei pronto ad approcciare professionalmente questo settore? </b>&#128293;
<i>(invia la tua risposta)</i>"
"""

# {0}: the expiration date for the user
TIP_MESSAGE = """Tip: Ti suggeriamo di seguire le indicazioni del team nella community 😜
    
Seleziona gli sport che vuoi seguire 👀

(Puoi selezionare la tipologia di evento di ogni sport!)

🟢 Attivato 🔴 Disattivato 

Il servizio terminerà il {0}"""


HOMEPAGE_MESSAGE = """ <b>Homepage</b> 📱

Seleziona un tasto oppure attendi una notifica dal bot !

<b>Fatto in  🇮🇹  con </b>♥️"""


ERROR_MESSAGE = """Abbiamo riscontrato un problema tecnico con il bot. 
Si consiglia di riprovare più tardi, ci scusiamo per il disagio."""


COMMUNITY_BUTTON_TEXT = "🙋🏼‍♀️ Vai alla Community 🙋🏾"
ASSISTANCE_BUTTON_TEXT = "👩🏾‍💻  Assistenza  🧑🏻"
HOMEPAGE_BUTTON_TEXT = "📱 Homepage 📱"

# this defines what will be imported if you import * from this module 
__all__ = ["SPORTS", "STRATEGIES"]
