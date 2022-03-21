from typing import Optional
from lot_bot import constants as cst
import dataclasses

@dataclasses.dataclass
class Strategy:
    name : str
    display_name : str = ""
    emoji : str = "📑"
    explanation : str = cst.DEFAULT_STRAT_EXPLANATION_TEXT # Aggiunto l'attributo explanation

    def __post_init__(self):
        if self.display_name == "":
            self.display_name = self.name.capitalize()



# ! important: no _ in .name nor in var names
@dataclasses.dataclass
class StrategyContainer:
    #SINGOLALOW : Strategy = Strategy("singolalow", display_name="Singola Low", explanation=cst.SINGOLALOW_EXPL_TEXT)
    #SINGOLAHIGH : Strategy = Strategy("singolahigh", display_name="Singola High", explanation=cst.SINGOLAHIGH_EXPL_TEXT)
    #RADDOPPIO : Strategy = Strategy("raddoppio", explanation = cst.RADDOPPIO_EXPL_TEXT)
    #SPECIALI : Strategy = Strategy("speciali", explanation = cst.SPECIALI_EXPL_TEXT)
    PRODUZIONE : Strategy = Strategy("produzione", explanation = cst.PRODUZIONE_EXPL_TEXT)
    LIVE : Strategy = Strategy("live", explanation = cst.LIVE_EXPL_TEXT)
    EXTRA : Strategy = Strategy("extra", explanation = cst.EXTRA_EXPL_TEXT)
    #MULTIPLALIGHT : Strategy = Strategy("multiplalight", display_name="Multipla Light", explanation = cst.MULTIPLALIGHT_EXPL_TEXT)
    #PDR : Strategy = Strategy("pdr", display_name="PDR", explanation = cst.PDR_EXPL_TEXT)
    # * Exchange
    #MAXEXCHANGE : Strategy = Strategy("maxexchange", display_name="MaxExchange", explanation = cst.MAXEXCHANGE_EXPL_TEXT)
    #MB : Strategy = Strategy("mb", display_name="MB", explanation = cst.MB_EXPL_TEXT)
    #SCALPING : Strategy = Strategy("scalping", display_name="Scalping", explanation = cst.SCALPING_EXPL_TEXT) 
    # * Base strategies
    #BASE : Strategy = Strategy("base", explanation = cst.BASE_EXPL_TEXT)
    TEST : Strategy = Strategy("test", display_name="TEST", explanation = cst.TEST_EXPL_TEXT)
    FREEBET : Strategy = Strategy("freebet", display_name = "Free Bet", explanation = cst.FREEBET_EXPL_TEXT)
    COMMUNITYBET : Strategy = Strategy("communitybet", display_name="Community Bet", explanation = cst.COMMUNITYBET_EXPL_TEXT)
    INFORMAZIONE : Strategy = Strategy("informazione", explanation = cst.INFORMAZIONE_EXPL_TEXT)
    FANTACONSIGLI : Strategy = Strategy("fantaconsigli", explanation = cst.FANTACONSIGLI_EXPL_TEXT)
    FATTENARISATA : Strategy = Strategy("fattenarisata", display_name="Fatte 'na risata", explanation = cst.FATTENARISATA_EXPL_TEXT)


    # * Analisi Miste
    #INSTAGRAMFREE : Strategy = Strategy("instagramfree", display_name="Instagram Free", explanation = cst.INSTAGRAMFREE_EXPL_TEXT)
    #COMMUNITYBET : Strategy = Strategy("communitybet", display_name="Community Bet", explanation = cst.COMMUNITYBET_EXPL_TEXT)
    #MULTIPLA : Strategy = Strategy("multipla", display_name="Multipla", explanation = cst.MULTIPLA_EXPL_TEXT)
    #SOFAR : Strategy = Strategy("sofar", display_name="So Far", explanation = cst.SOFAR_EXPL_TEXT)
    # * Teacherbet
    #TEACHERBETLUXURY : Strategy = Strategy("teacherbetluxury", display_name="Teacherbet Luxury")
    # HOCKEY : Strategy = Strategy("hockey", display_name="Hockey (TEST)")
    # BASEBALL : Strategy = Strategy("baseball", display_name="Baseball (TEST)")
    # FOOTBALLAMERICANO : Strategy = Strategy("footballamericano", display_name="Football Americano (TEST)")
    # PALLAVOLO : Strategy = Strategy("pallavolo", display_name="Pallavolo (TEST)")
    # PINGPONG : Strategy = Strategy("pingpong", display_name="Ping Pong", emoji="🏓")
    # MMA : Strategy = Strategy("mma", display_name="MMA (TEST)")
    # IPPICA : Strategy = Strategy("ippica")
    # AUTO: Strategy = Strategy("auto")
    # MOTO : Strategy = Strategy("moto")
    # RUGBY : Strategy = Strategy("rugby")
    # ESPORTS : Strategy = Strategy("esports")
    # PALLAMANO : Strategy = Strategy("pallamano")
    # FRECCETTE : Strategy = Strategy("freccette")
    # SHOWTELEVISIVI : Strategy = Strategy("showtelevisivi", display_name="Show Televisivi")


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
        if not strategy_token:
            return None
        strategy_token = strategy_token.upper().strip().replace(" ", "").replace("_", "")
        if hasattr(self, strategy_token):
            return getattr(self, strategy_token)
        else:
            return None
    


strategies_container = StrategyContainer()
