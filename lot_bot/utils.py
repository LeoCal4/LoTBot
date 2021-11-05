import re
from typing import Dict, List, Optional, Tuple

from lot_bot import custom_exceptions, filters
from lot_bot import logger as lgr
from lot_bot.models import giocate as giocata_model
from lot_bot.models import sports as spr
from lot_bot.models import strategies as strat
from lot_bot import constants as cst


def get_emoji_for_cashout_percentage(percentage_text: str) -> str:
    """Returns the emoji relative to the cashout percentage sign.
    The percentage text can either be integer number or a floating point
    number, with a "," or a "." dividing the decimal part. Additionally,
    it can have a "+" or a "-" sign as a first character.

    Args:
        percentage_text (str): the token of the message containing
            the cashout percentage

    Returns:
        str: 🟢 for a positive cashout,  
             🔴 for a negative cashout,
             ⚪️ for a neutral cashout 

            an empty string in case of errors

    Raises:
        e (Exception): in case of errors in the parsing
    """
    if "," in percentage_text:
        percentage_text = percentage_text.replace(",", ".")
    try:
        if float(percentage_text) > 0:
            return  "🟢"
        elif float(percentage_text) < 0:
            return "🔴"
        else: 
            return "⚪️"
    except Exception as e:
        lgr.logger.error(f"Could not parse the cashout percentage {percentage_text} - {str(e)}")
        raise e


def create_cashout_message(message_text: str) -> str: 
    """Creates the cashout message to be broadcasted from a cashout message text.
    The message_text needs to be in the form "#<giocata id> +|-<percentage>.
    The final cashout message has the form:
    🟢|🔴 CASHOUT Exchange <giocata id> 🟢|🔴 or
    ⚪️ Exchange #<giocata id> ABBINATA ⚪️

    Args:
        message_text (str): the text of the message containing the cashout.

    Returns:
        str: the cashout message to be broadcasted,
            or an empty string in case of errors
    """
    matches = re.search(filters.get_cashout_pattern(), message_text)
    giocata_num = matches.group(1).split()[0]
    cashout_percentage = matches.group(2)
    emoji = get_emoji_for_cashout_percentage(cashout_percentage)
    if emoji == "⚪️":
        return f"{emoji} Exchange #{giocata_num} ABBINATA {emoji}"
    else:        
        return f"{emoji} CASHOUT Exchange #{giocata_num} {emoji}"


def parse_float_string_to_int(float_string: str) -> int:
    """Converts a string containing a float to int, multiplying it by 100, in order
    to keep the first 2 floating point digits.

    Args:
        float_string (str)
    
    Returns:
        int: the float represented as an int (float to int * 100)
    """
    try:
        return int(float(float_string.strip().replace(",", ".")) * 100)
    except Exception as e:
        lgr.logger.error(f"Error during parsing of {float_string} to int * 100 - {str(e)}")
        raise e


def create_resoconto_message(giocate: List[Dict], user_giocate_data_dict: Dict) -> str:
    """Creates the resoconto message, given the base giocate and adding additional personalized
    stake data if any.
    Base structure:
        <index>) <Sport>#<giocata_num> @<Quota> Stake <(personalized) stake> = <outcome percentage>% 
    Example:
        1) Calcio#1124 @2.20 Stake 3%(3€) = +3,60%(+3,60€)

    Args:
        giocate (List[Dict])
        user_giocate_data_dict (Dict): user giocate for the personalized stakes

    Returns:
        str: the resoconto message
    """
    lgr.logger.debug(f"Creating resoconto with giocate {giocate}")
    resoconto_message = ""
    for index, giocata in enumerate(giocate, 1):
        stake = giocata["base_stake"]
        # * check for a personalized stake
        personalized_stake = user_giocate_data_dict[giocata["_id"]]["personal_stake"]
        if personalized_stake != 0:
            stake = personalized_stake
        # * get outcome percentage
        if "cashout" in giocata:
            outcome_percentage = giocata["cashout"] / 100
        else:
            outcome_percentage = giocata_model.get_outcome_percentage(giocata["outcome"], stake, giocata["base_quota"])
            outcome_percentage_string = f"= {outcome_percentage:.2f}%"
        # * not outcome percentage for exchange
        if giocata["sport"] == "exchange":
            outcome_percentage_string = ""
        # TODO only outcome, no need for %
        outcome_emoji = giocata_model.get_outcome_emoji(outcome_percentage, giocata["outcome"])
        parsed_quota = giocata["base_quota"] / 100
        parsed_stake = stake / 100
        sport_name = spr.sports_container.get_sport(giocata['sport']).display_name
        resoconto_message += f"{index}) {sport_name} #{giocata['giocata_num']}: @{parsed_quota:.2f} Stake {parsed_stake:.2f}% {outcome_percentage_string} {outcome_emoji}\n"
    return resoconto_message


def get_sport_and_strategy_from_normal_message(message_first_row: str) -> Tuple[spr.Sport, Optional[strat.Strategy]]:
    """Gets the sport and the strategy from the first row of 
    a /messaggio_abbonati command.

    Args:
        message_first_row (str): it has the form /messaggio_abbonati <sport>[ - <strategy>]

    Raises:
        custom_exceptions.NormalMessageParsingError: in case the sport or the strategy are not valid

    Returns:
        Tuple[spr.Sport, strat.Strategy | None]: the sport and the strategy found, if any
    """
    # * text on the first line after the command
    matches = re.search(r"^\/messaggio_abbonati\s*([\w\s]+)(?:\s-\s([\w\s]+))?", message_first_row.strip())
    if not matches:
        lgr.logger.error(f"Cannot parse {message_first_row=}")
        raise custom_exceptions.NormalMessageParsingError("messaggio non analizzabile, assicurati che segua la struttura '/messaggio_abbonati nomesport - nomestrategia'")
    sport_token = matches.group(1)
    sport = spr.sports_container.get_sport(sport_token)
    if not sport:
        lgr.logger.error(f"Sport {sport_token} not valid from {message_first_row=}")
        raise custom_exceptions.NormalMessageParsingError(f"sport '{sport_token}' non valido")
    strategy_token = matches.group(2)
    strategy = strat.strategies_container.get_strategy(strategy_token)
    # * check that a strategy has been found and if it is valid
    if strategy and strategy not in sport.strategies:
        lgr.logger.error(f"Strategy {strategy_token} not valid from {message_first_row=}")
        raise custom_exceptions.NormalMessageParsingError(f"strategia '{strategy_token}' non valida per lo sport '{sport_token}'")
    return sport, strategy


def create_personal_referral_updated_text(updated_referral: str) -> str:
    referral_link = f"https://t.me/SportSignalsBot?start={updated_referral}"
    return cst.REFERRAL_MENU_MESSAGE.format(updated_referral, referral_link)
