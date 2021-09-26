import dataclasses

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
    strats.LIVE, 
    strats.INSTAGRAM, 
]

# ! important: no _ in .name nor in var names
@dataclasses.dataclass
class SportsContainer:
    CALCIO : Sport = Sport("calcio", _base_strategies + [strats.TRILLED, strats.PIAQUEST])
    BASKET : Sport = Sport("basket", _base_strategies + [strats.TRILLED])
    TENNIS : Sport = Sport("tennis", _base_strategies + [strats.TRILLED])
    PINGPONG : Sport = Sport("pingpong", _base_strategies + [strats.TRILLED], display_name="Ping Pong")
    FRECCETTE : Sport = Sport("freccette", _base_strategies + [strats.TRILLED])
    HOCKEY : Sport  = Sport("hockey", _base_strategies + [strats.TRILLED])
    BASEBALL : Sport = Sport("baseball", _base_strategies + [strats.TRILLED])
    EXCHANGE : Sport = Sport("exchange", [strats.MAXEXCHANGE, strats.INSTAGRAM])
    SPECIALI : Sport = Sport("speciali", _base_strategies)
    RUGBY : Sport = Sport("rugby", _base_strategies + [strats.TRILLED])
    SPORT2 : Sport = Sport("sport2", _base_strategies)
    PALLAVOLO : Sport = Sport("pallavolo", _base_strategies)
    IPPICA : Sport = Sport("ippica", _base_strategies, show_in_menu=False)
    TUTTOILRESTO : Sport = Sport("tuttoilresto", _base_strategies, display_name="Tutto il Resto", show_in_menu=False)

    def __iter__(self):
        attributes = dataclasses.asdict(self).keys()
        yield from (getattr(self, attribute) for attribute in attributes)

    def __next__(self):
        yield

    def __contains__(self, item: Sport):
        return dataclasses.astuple(item) in dataclasses.astuple(self)

    def get_sport_from_string(self, sport_string: str) -> Sport:
        sport_string = sport_string.upper().strip()
        if hasattr(self, sport_string):
            return getattr(self, sport_string)
        else:
            return None
    
    def astuple(self):
        return tuple([self.__dict__[field.name] for field in dataclasses.fields(self)])


sports_container = SportsContainer()
