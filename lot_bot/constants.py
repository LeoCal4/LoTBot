""" This module is used to define constants
"""

SPORTS = [
    "calcio",
    "basket",
    "tennis",
    "exchange",
    "speciali",
    "ping pong",
    "hockey",
    "freccette",
    "baseball",
    "pallavolo",
    "rugby",
    "sport2"
]


base_strategie = ["Raddoppio", "Multiple", "Singola", "Live", "Instagram"]
STRATEGIES = {
  "calcio": base_strategie + ["PiaQuest", "Trilled"],
  "basket": base_strategie + ["Trilled"],
  "tennis": base_strategie + ["Trilled"],
  "ping pong": base_strategie + ["Trilled"],
  "freccette": base_strategie + ["Trilled"],
  "hockey": base_strategie + ["Trilled"],
  "baseball": base_strategie + ["Trilled"],
  "exchange": ["MaxExchange"],
  "speciali": base_strategie,
  "rugby": base_strategie + ["Trilled"],
  "sport2": base_strategie,
  "pallavolo": base_strategie,
}

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

<b>Sei pronto ad approcciare professionalmente questo settore ? </b>&#128293;
<i>(invia la tua risposta)</i>"
"""


# this defines what will be imported if you import * from this module 
__all__ = ["SPORTS", "STRATEGIES"]
