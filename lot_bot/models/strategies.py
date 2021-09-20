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
    MULTIPLE : Strategy = Strategy("multiple")
    SINGOLA : Strategy = Strategy("singola")
    LIVE : Strategy = Strategy("live")
    INSTAGRAM : Strategy = Strategy("instagram")
    PIAQUEST : Strategy = Strategy("piaquest", display_name="PiaQuest")
    TRILLED : Strategy = Strategy("trilled")
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

    def get_strategy_from_string(self, strategy_token: str) -> Strategy:
        strategy_token = strategy_token.upper().strip()
        if hasattr(self, strategy_token):
            return getattr(self, strategy_token)
        else:
            return None
    


strategies_container = StrategyContainer()
