import re
from typing import Dict, List, Tuple

from lot_bot import custom_exceptions, filters
from lot_bot import logger as lgr
from lot_bot.models import giocate as giocata_model
from lot_bot.models import sports as spr
from lot_bot.models import strategies as strat


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
        lgr.logger.error(f"Could not parse the cashout percentage {percentage_text}")
        return ""


def create_cashout_message(message_text: str) -> str: 
    """Creates the cashout message to be broadcasted from a cashout message text.
    The message_text needs to be in the form "#<giocata id> +|-<percentage>.
    The final cashout message has the form:
    🟢|🔴 CASHOUT Exchange <giocata id> +|-<percentage>% 🟢|🔴 or
    ⚪️ Exchange #<giocata id> ABBINATA ⚪️

    Args:
        message_text (str): the text of the message containing the cashout.

    Returns:
        str: the cashout message to be broadcasted,
            or an empty string in case of errors
    """
    matches = re.search(filters.get_cashout_pattern(), message_text)
    giocata_num = matches.group(1)
    cashout_percentage = matches.group(2)
    # TODO handle no emoji case
    emoji = get_emoji_for_cashout_percentage(cashout_percentage)
    if emoji == "⚪️":
        return f"{emoji} Exchange #{giocata_num} ABBINATA {emoji}"
    else:        
        return f"{emoji} CASHOUT Exchange #{giocata_num} {cashout_percentage}% {emoji}"


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


def create_resoconto_message(giocate: List[Dict]):
    # Resoconto 24-09-2021
    # 1) Calcio#1124 @2.20 Stake 3%(3€) = +3,60%(+3,60€)
    lgr.logger.debug(f"Creating resoconto with giocate {giocate}")
    # resoconto_message = f"Resoconto {datetime.date.today().strftime('%d-%m-%Y')}\n"
    resoconto_message = ""
    for index, giocata in enumerate(giocate, 1):
        outcome_percentage = giocata_model.get_outcome_percentage(giocata["outcome"], giocata["base_stake"], giocata["base_quota"])
        if outcome_percentage > 0:
            outcome_emoji = "🟢"
        elif outcome_percentage == 0:
            outcome_emoji = "🕔" # TODO add even case 
        else:
            outcome_emoji = "🔴"
        parsed_quota = giocata["base_quota"] / 100
        parsed_stake = giocata["base_stake"] / 100
        sport_name = spr.sports_container.get_sport(giocata['sport']).display_name
        resoconto_message += f"{index}) {sport_name} #{giocata['giocata_num']}: @{parsed_quota:.2f} Stake {parsed_stake:.2f}% = {outcome_percentage:.2f}% {outcome_emoji}\n"
    return resoconto_message


def get_sport_and_strategy_from_normal_message(message: str) -> Tuple[spr.Sport, strat.Strategy]:
    """Gets the sport and the strategy from the first row of 
    a /messaggio_abbonati command.

    Args:
        message (str): it has the form /messaggio_abbonati <sport> - <strategy>

    Raises:
        custom_exceptions.NormalMessageParsingError: in case the sport or the strategy are not valid

    Returns:
        Tuple[spr.Sport, strat.Strategy]: the sport and the strategy found
    """
    # text on the first line after the command
    first_row = message.split("\n")[0]
    matches = re.search(r"^\/messaggio_abbonati\s*([\w\s]+)\s*-\s*([\w\s]+)", first_row)
    if not matches:
        lgr.logger.error(f"Cannot parse {message} with {first_row=}")
        raise custom_exceptions.NormalMessageParsingError("messaggio non analizzabile, assicurati che segua la struttura '/messaggio_abbonati nomesport - nomestrategia'")
    sport_token = matches.group(1)
    sport = spr.sports_container.get_sport(sport_token)
    if not sport:
        lgr.logger.error(f"Sport {sport_token} not valid from normal message {message} - {first_row=}")
        raise custom_exceptions.NormalMessageParsingError(f"sport '{sport_token}' non valido")
    strategy_token = matches.group(2)
    strategy = strat.strategies_container.get_strategy(strategy_token)
    if not strategy or strategy not in sport.strategies:
        lgr.logger.error(f"Strategy {strategy_token} not valid from normal message {message} - {first_row=}")
        raise custom_exceptions.NormalMessageParsingError(f"strategia '{strategy_token}' non valida per lo sport '{sport}'")
    return sport, strategy
