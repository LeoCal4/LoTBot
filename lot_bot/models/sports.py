import dataclasses
from typing import Optional

from lot_bot.models import strategies

@dataclasses.dataclass
class Sport:
    name : str
    strategies : list[strategies.Strategy] # ! should not partecipate in eq
    show_in_menu : bool = True
    display_name : str = ""

    def __post_init__(self):
        if self.display_name == "":
            self.display_name = self.name.capitalize()


strats = strategies.StrategyContainer()
_base_strategies = [
    strats.SINGOLA,
    strats.MULTIPLE, 
    strats.RADDOPPIO, 
    strats.SPECIALI,
]
_tutto_strategies = [
    strats.HOCKEY,
    strats.IPPICA,
    strats.PALLAVOLO,
    strats.AUTO,
    strats.MOTO,
    strats.RUGBY,
    strats.FOOTBALLAMERICANO,
    strats.ESPORTS,
    strats.PALLAMANO,
    strats.FRECCETTE,
    strats.SHOWTELEVISIVI,
    strats.MAXEXCHANGE,
]

# ! important: no _ in .name nor in var names
@dataclasses.dataclass
class SportsContainer:
    CALCIO : Sport = Sport("calcio", _base_strategies + [strats.PDRRADDOPPI, strats.PDRHIGHODD])
    BASKET : Sport = Sport("basket", _base_strategies)
    TENNIS : Sport = Sport("tennis", _base_strategies)
    EXCHANGE : Sport = Sport("exchange", [strats.MAXEXCHANGE])
    TUTTOILRESTO : Sport = Sport("tuttoilresto", _tutto_strategies, display_name="Tutto il Resto")
    # PINGPONG : Sport = Sport("pingpong", _base_strategies + [strats.TRILLED], display_name="Ping Pong")
    # FRECCETTE : Sport = Sport("freccette", _base_strategies + [strats.TRILLED], show_in_menu=False)
    # HOCKEY : Sport  = Sport("hockey", _base_strategies + [strats.TRILLED], show_in_menu=False)
    # BASEBALL : Sport = Sport("baseball", _base_strategies + [strats.TRILLED], show_in_menu=False)
    # SPECIALI : Sport = Sport("speciali", _base_strategies, show_in_menu=False)
    # RUGBY : Sport = Sport("rugby", _base_strategies + [strats.TRILLED], show_in_menu=False)
    # PALLAVOLO : Sport = Sport("pallavolo", _base_strategies, show_in_menu=False)
    # IPPICA : Sport = Sport("ippica", _base_strategies, show_in_menu=False)

    def __iter__(self):
        attributes = dataclasses.asdict(self).keys()
        yield from (getattr(self, attribute) for attribute in attributes)

    def __next__(self):
        yield

    def __contains__(self, item: Sport):
        return dataclasses.astuple(item) in dataclasses.astuple(self)

    def get_sport(self, sport_string: str) -> Optional[Sport]:
        parsed_sport_string = sport_string.upper().strip().replace(" ", "").replace("_", "")
        if hasattr(self, parsed_sport_string):
            return getattr(self, parsed_sport_string)
        else:
            return None
    
    def astuple(self):
        return tuple([self.__dict__[field.name] for field in dataclasses.fields(self)])


sports_container = SportsContainer()
