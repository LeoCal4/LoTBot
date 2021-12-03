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

    def __post_init__(self):
        if self.display_name == "":
            self.display_name = self.name.capitalize()


strats = strategies.StrategyContainer()
_base_strategies = [
    strats.BASE,
    strats.TEST,
]
_adv_strategies = [
    strats.SINGOLA,
    strats.MULTIPLA, 
    strats.RADDOPPIO, 
    strats.SPECIALI,
    strats.TEST
]

# ! important: no _ in .name nor in var names
@dataclasses.dataclass
class SportsContainer:
    CALCIO : Sport = Sport("calcio", _adv_strategies + [strats.PDRRADDOPPI, strats.PDRHIGHODD], emoji="⚽️")
    BASKET : Sport = Sport("basket", _adv_strategies, emoji="🏀", display_name="Basket")
    TENNIS : Sport = Sport("tennis", _adv_strategies, emoji="🎾")
    EXCHANGE : Sport = Sport("exchange", [strats.MAXEXCHANGE, strats.MB], emoji="📊")
    HOCKEY : Sport = Sport("hockey", _base_strategies, emoji="🏒")
    BASEBALL : Sport = Sport("baseball", _base_strategies, emoji="⚾️")
    FOOTBALLAMERICANO : Sport = Sport("footballamericano", _base_strategies, emoji="🏈", display_name="Football Americano")
    PALLAVOLO : Sport = Sport("pallavolo", _base_strategies, emoji="🏐")
    PINGPONG : Sport = Sport("pingpong", _base_strategies, display_name="Ping Pong", emoji="🏓")
    MMA : Sport = Sport("mma", _base_strategies, emoji="🥋", display_name="MMA")
    TUTTOILRESTO : Sport = Sport("tuttoilresto", _base_strategies, display_name="Tutto il Resto")

    def __iter__(self):
        attributes = dataclasses.asdict(self).keys()
        yield from (getattr(self, attribute) for attribute in attributes)

    def __next__(self):
        yield

    def __contains__(self, item: Sport):
        return dataclasses.astuple(item) in dataclasses.astuple(self)

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
