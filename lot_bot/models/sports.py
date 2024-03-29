import dataclasses
from typing import Optional, List

from lot_bot.models import strategies

@dataclasses.dataclass
class Sport:
    name : str
    strategies : List[strategies.Strategy] # ! should not partecipate in eq
    show_in_menu : bool = True
    display_name : str = ""
    emoji : str = "📑"
    outcome_percentage_in_resoconto : bool = True

    def __post_init__(self):
        if self.display_name == "":
            self.display_name = self.name.capitalize()


strats = strategies.StrategyContainer()
_base_strategies = [
    strats.PRODUZIONE,
    strats.LIVE,
    strats.EXTRA,
    strats.TEST
]

_analisi_miste_strategies = [
    strats.FREEBET, 
    strats.COMMUNITYBET, 
]

_news_strategies = [
    strats.INFORMAZIONE,
    strats.FANTACONSIGLI,
    #strats.FATTENARISATA
]

_sport_americani_strategies = [
    strats.HOCKEY,
    strats.BASEBALL,
    #strats.BASKET,
    strats.FOOTBALLAMERICANO
]

# ! important: no _ in .name nor in var names
@dataclasses.dataclass
class SportsContainer:
    EXCHANGE : Sport = Sport("exchange", [strats.PRODUZIONE,strats.TEST], emoji="📊", outcome_percentage_in_resoconto=False)
    CALCIO : Sport = Sport("calcio", _base_strategies, emoji="⚽️")
    BASKET : Sport = Sport("basket", _base_strategies, emoji="🏀")
    TENNIS : Sport = Sport("tennis", _base_strategies, emoji="🎾")
    TUTTOILRESTO : Sport = Sport("tuttoilresto", _base_strategies, display_name="Tutto il Resto", outcome_percentage_in_resoconto=False)
    ANALISIMISTE : Sport = Sport("analisimiste", _analisi_miste_strategies, display_name="Analisi Miste") 
    #HOCKEY : Sport = Sport("hockey", _base_strategies, emoji="🏒")
    #BASEBALL : Sport = Sport("baseball", _base_strategies, emoji="⚾️")
    #FOOTBALLAMERICANO : Sport = Sport("footballamericano", _base_strategies, emoji="🏈", display_name="Football Americano")
    #SPORTAMERICANI : Sport = Sport("sportamericani", _sport_americani_strategies, display_name="Sport Americani")
    #PALLAVOLO : Sport = Sport("pallavolo", _base_strategies, emoji="🏐")
    #PINGPONG : Sport = Sport("pingpong", _base_strategies, display_name="Ping Pong", emoji="🏓")
    #MMA : Sport = Sport("mma", _base_strategies, emoji="🥋", display_name="MMA")
    #NEWS : Sport = Sport("news", _news_strategies, display_name="News") 

    def __iter__(self):
        attributes = dataclasses.asdict(self).keys()
        yield from (getattr(self, attribute) for attribute in attributes)

    def __next__(self):
        yield

    def __contains__(self, item: Sport):
        return dataclasses.astuple(item) in dataclasses.astuple(self) # wat

    def __eq__(self, __o: object) -> bool:
        if hasattr(__o, "name"):
            return self.name == __o.name
        return False

    def get_sport(self, sport_string: str) -> Optional[Sport]:
        if not sport_string:
            return None
        parsed_sport_string = sport_string.upper().strip().replace(" ", "").replace("_", "")
        if hasattr(self, parsed_sport_string):
            return getattr(self, parsed_sport_string)
        else:
            return None
    
    def astuple(self):
        return tuple([self.__dict__[field.name] for field in dataclasses.fields(self)])


sports_container = SportsContainer()
