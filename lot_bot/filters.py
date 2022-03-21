from telegram.ext.filters import Filters

from lot_bot import config as cfg
from lot_bot.models import strategies as strat


def get_giocata_filter() -> Filters:
    """Creates the filter for the giocate. It checks if the
    sender id is among the ones of the sport channels and if
    the message contains "Stake" and the giocata emoji.

    Returns:
        Filter
    """
    # GIOCATA_EMOJI = "⚜️"
    # GIOCATA_EMOJI2 = "⚜"
    sport_channels_filter = Filters.chat()
    sport_channels_filter.add_chat_ids(cfg.config.SPORTS_CHANNELS_ID.values())
    giocata_text_filter = Filters.regex(r"[⚜️⚜][\s\S]*(?:[Ss]take)")
    return sport_channels_filter & giocata_text_filter


def get_teacherbet_giocata_filter() -> Filters:
    tb_channel_filter = Filters.chat()
    tb_channel_filter.add_chat_ids(cfg.config.TEACHERBET_CHANNEL_ID)
    giocata_text_filter = Filters.regex(r"^UPDATE:")
    return tb_channel_filter & giocata_text_filter



def get_normal_messages_filter() -> Filters:
    """Creates the filter that gets all the non-command
    text messages.

    Returns:
        Filters
    """
    return (Filters.text & (~ Filters.command))

def get_cashout_filter() -> Filters:
    """Creates the filter for the cashout messages of the Exchange channel.
    Cashout messages must come from the Exchange channel and have the form:
         #<numero giocata> (+|-)<giocata percentage>

    Returns:
        Filters
    """
    exchange_channel_filter = Filters.chat(cfg.config.SPORTS_CHANNELS_ID["exchange"])
    cashout_text_filter = Filters.regex(get_cashout_pattern())
    return exchange_channel_filter & cashout_text_filter


def get_sport_channel_normal_message_filter() -> Filters:
    """Creates the filter for all text messages coming from any 
    sport channels.
    Regardless, they should have the form:
    <sport> <strategy>
    <...> 

    Returns:
        Filters: [description]
    """
    sport_channels_filter = Filters.chat()
    sport_channels_filter.add_chat_ids(cfg.config.SPORTS_CHANNELS_ID.values())
    return sport_channels_filter & Filters.regex("/messaggio_abbonati")


def get_homepage_filter() -> Filters:
    return Filters.regex(r"[hH]omepage")


def get_bot_config_filter() -> Filters:
    return Filters.regex(r"[Cc]onfigurazione [Bb]o[Tt]")


def get_experience_settings_filter() -> Filters:
    return Filters.regex(r"[Gg]estione [Ee]sperienza")

def get_use_guide_filter() -> Filters:
    return Filters.regex(r"[Gg]uida [Aa]ll'[Uu]so")


def get_assistance_filter() -> Filters:
    return Filters.regex(r"[Aa]ssistenza")


def get_outcome_giocata_filter() -> Filters:
    """Creates the filter for all the text messages coming from
    any of the sport channels which include a giocata outcome.
    
    An example giocata is:
        🟢 PingPong#67 Vincente +8,50% 🟢

    Returns:
        Filters
    """
    sport_channels_filter = Filters.chat()
    sport_channels_filter.add_chat_ids(cfg.config.SPORTS_CHANNELS_ID.values())
    return sport_channels_filter & Filters.regex(get_giocata_outcome_pattern())


def get_teacherbet_giocata_outcome_filter() -> Filters:
    """
    Example:
        #65✅
        #65❌

    Returns:
        Filters: [description]
    """
    tb_channel_filter = Filters.chat()
    tb_channel_filter.add_chat_ids(cfg.config.TEACHERBET_CHANNEL_ID)
    giocata_text_filter = Filters.regex(get_teacherbet_giocata_outcome_pattern())
    return tb_channel_filter & giocata_text_filter


def get_send_file_id_filter() -> Filters:
    return Filters.caption(["/file_id"])


def get_all_filter() -> Filters:
    return Filters.all

def get_text_messages_filter() -> Filters:
    return Filters.text

def get_command_messages_filter() -> Filters:
    return Filters.command

def get_broadcast_media_filter() -> Filters:
    return Filters.caption(["/broadcast"])


# ================================================ PATTERNS ================================================


def get_giocata_num_pattern() -> str:
    """# <giocata_index> [MB] [<month/year>]

    Returns:
        str
    """
    return r"#\s*([\w]+(?:\s*MB)?(?:\s+\d\d\/\d\d)?)"


def get_giocata_outcome_pattern() -> str:
    """Creates the regex pattern to identify a giocata outcome.
    The structure of a giocata is:
        <🟢/🔴> <sport name>#<giocata_index> <month/year> <Vincente/Perdente> <percentage> <🟢/🔴>
    
    The regex only checks 
        "<sport name>#<giocata_index month/year> <Vincente/Perdente>"
    to determine if the message is a giocata or not.

    The regex gathers the following groups:
        - group(1) = sport
        - group(2) = giocata_num
        - group(3) = outcome


    Returns:
        str: giocata outcome regex pattern
    """
    return rf"([\w\s]+)\s*{get_giocata_num_pattern()}\s*([a-zA-Z]+)"


def get_teacherbet_giocata_outcome_pattern() -> str:
    return r"^#(\d+(?:\s+\d+/\d+)?)\s*([✅✔️☑️❌❎])"


def get_cashout_pattern() -> str:
    """Returns the regex pattern to identify a cashout.
    The structure is:
        #<giocata num> <+/-><cashout percentage, either an int or a float with , or .>
    
    The groups are:
        - 1) giocata num
        - 2) cashout percentage
    
    Returns:
        str: cashout regex pattern
    """
    return rf"^\s*{get_giocata_num_pattern()}\s*([+-]?\d+(?:[\.,]\d+)?)\s*$"


def get_explanation_pattern() -> str:
    """
    explanation_(<str1>|<str2>|...|<strN>)

    Returns:
        str: [description]
    """
    pattern = "explanation_("
    for strategy in strat.strategies_container:
        pattern += strategy.name + "|"
    return pattern[:-1] + ")"

def get_strat_text_explanation_pattern() -> str: #related to text explanations (not video!)
    """
    text_explanation_(<str1>|<str2>|...|<strN>)

    Returns:
        str: [description]
    """
    pattern = "text_explanation_("
    for strategy in strat.strategies_container:
        pattern += strategy.name + "|"
    return pattern[:-1] + ")"

#TODO forse inutile
def get_modify_budget_pattern() -> str:
    """
    modify_budget_(<str1>|<str2>|...|<strN>)

    Returns:
        str: [description]
    """
    pattern = "text_explanation_("
    for strategy in strat.strategies_container:
        pattern += strategy.name + "|"
    return pattern[:-1] + ")"


# ==============================================================================================================


def get_referral_filter() -> Filters:
    # [a-z A-Z 0-9 _ -]
    return Filters.regex(r"^(\w|-)+-lot$")


def get_successful_payment_filter() -> Filters:
    return Filters.successful_payment


def get_float_filter() -> Filters:
    return Filters.regex(r"\d+(?:[.,]\d+)?")

def get_nothing() -> Filters:
    return Filters.regex(r"^NothingThatUsersWillActuallySend$")