from typing import Optional
import dataclasses

@dataclasses.dataclass
class Strategy:
    name : str
    display_name : str = ""

    def __post_init__(self):
        if self.display_name == "":
            self.display_name = self.name.capitalize()

# ! important: no _ in .name nor in var names
@dataclasses.dataclass
class StrategyContainer:
    RADDOPPIO : Strategy = Strategy("raddoppio")
    MULTIPLA : Strategy = Strategy("multipla")
    SINGOLA : Strategy = Strategy("singola")
    PINGPONG : Strategy = Strategy("pingpong", display_name="Ping Pong")
    SPECIALI : Strategy = Strategy("speciali")
    PDRRADDOPPI : Strategy = Strategy("pdrraddoppi", display_name="PDR Raddoppi")
    PDRHIGHODD : Strategy = Strategy("pdrhighodd", display_name="PDR High Odd")
    HOCKEY : Strategy = Strategy("hockey")
    IPPICA : Strategy = Strategy("ippica")
    PALLAVOLO : Strategy = Strategy("pallavolo")
    AUTO: Strategy = Strategy("auto")
    MOTO : Strategy = Strategy("moto")
    RUGBY : Strategy = Strategy("rugby")
    FOOTBALLAMERICANO : Strategy = Strategy("footballamericano", display_name="Football Americano")
    BASEBALL : Strategy = Strategy("baseball")
    ESPORTS : Strategy = Strategy("esports")
    PALLAMANO : Strategy = Strategy("pallamano")
    FRECCETTE : Strategy = Strategy("freccette")
    SHOWTELEVISIVI : Strategy = Strategy("showtelevisivi", display_name="Show Televisivi")
    MAXEXCHANGE : Strategy = Strategy("maxexchange", display_name="MaxExchange")

    def astuple(self):
        return tuple([self.__dict__[field.name] for field in dataclasses.fields(self)])

    def __iter__(self):
        # attributes = dataclasses.asdict(self).keys()
        # yield from (getattr(self, attribute) for attribute in attributes)
        yield from self.astuple()
    
    def __next__(self):
        yield

    def __contains__(self, item: Strategy):
        pass

    def get_strategy(self, strategy_token: str) -> Optional[Strategy]:
        strategy_token = strategy_token.upper().strip().replace(" ", "").replace("_", "")
        if hasattr(self, strategy_token):
            return getattr(self, strategy_token)
        else:
            return None
    


strategies_container = StrategyContainer()
