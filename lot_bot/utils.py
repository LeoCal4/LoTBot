import datetime
import re
from typing import Dict, List, Optional, Tuple

from lot_bot import config as cfg
from lot_bot import custom_exceptions, filters
from lot_bot import logger as lgr
from lot_bot.models import giocate as giocata_model
from lot_bot.models import sports as spr
from lot_bot.models import strategies as strat
from lot_bot.dao import analytics_manager
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
    ⚪️ Exchange #<giocata id> VOID ⚪️

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
        return f"{emoji} Exchange #{giocata_num} VOID {emoji}"
    else:        
        return f"{emoji} CASHOUT Exchange #{giocata_num} {emoji}"

def parse_float_string(float_string: str) -> float:
    try:
        return float(float_string.strip().replace(",", "."))
    except Exception as e:
        lgr.logger.error(f"Error during parsing of {float_string} to float - {str(e)}")
        raise e


def parse_float_string_to_int(float_string: str) -> int:
    """Converts a string containing a float to int, multiplying it by 100, in order
    to keep the first 2 floating point digits.

    Args:
        float_string (str)
    
    Returns:
        int: the float represented as an int (float to int * 100)
    """
    try:
        return int(parse_float_string(float_string) * 100)
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
        user_giocata = user_giocate_data_dict[giocata["_id"]]
        stake_section = ""
        sport = spr.sports_container.get_sport(giocata['sport'])
        if "base_stake" in giocata:
            stake = giocata["base_stake"]
            # * check for a personalized stake
            personalized_stake = user_giocata["personal_stake"]
            if personalized_stake != 0:
                stake = personalized_stake
            parsed_stake = stake / 100
            stake_section = f"Stake {parsed_stake:.2f}%"
        # * get outcome percentage
        if sport.outcome_percentage_in_resoconto:
            outcome_percentage = giocata_model.get_outcome_percentage(giocata["outcome"], stake, giocata["base_quota"])
            outcome_percentage_string = f" = {outcome_percentage:.2f}%"
            if "pre_giocata_budget" in user_giocata:
                user_old_budget = int(user_giocata["pre_giocata_budget"]) / 100
                stake_money = user_old_budget * parsed_stake / 100
                if stake_section != "":
                    stake_section += f" ({stake_money:.2f}€)"
                outcome_money = user_old_budget * outcome_percentage / 100
                outcome_sign = "" if outcome_money < 0 else "+"
                outcome_percentage_string += f" ({outcome_sign}{outcome_money:.2f}€)"
        else:
            outcome_percentage_string = ""
        outcome_emoji = f" {giocata_model.OUTCOME_EMOJIS[giocata['outcome']]}"
        # * get quota
        quota_section = ""
        if "base_quota" in giocata:
            parsed_quota = giocata["base_quota"] / 100
            quota_section = f"@{parsed_quota:.2f} "
        resoconto_message += f"{index}) {sport.display_name} #{giocata['giocata_num']}: {quota_section}{stake_section}{outcome_percentage_string}{outcome_emoji}\n"
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


def create_personal_referral_updated_text(updated_referral: str, num_of_referred_users: int) -> str:
    referral_link = f"https://t.me/{cfg.config.BOT_NAME}?start={updated_referral}"
    final_text = cst.REFERRAL_MENU_MESSAGE.format(updated_referral, referral_link) + "\n"
    num_of_referred_users = int(min(10, num_of_referred_users))
    for _ in range(num_of_referred_users):
        final_text += "🟢"
    for _ in range(10 - num_of_referred_users):
        final_text += "🔴"
    final_text += f"\n{num_of_referred_users} utenti!"
    return final_text


def get_month_and_year_string(previous_month:bool=False):
    target_time = datetime.datetime.utcnow()
    if previous_month:
        target_time = target_time.replace(day=1) - datetime.timedelta(days=2)
    return datetime.datetime.strftime(target_time, "%m/%Y").replace("/20", "/") # will need to change this in 2100


def create_strategies_explanation_message(sport: spr.Sport) -> str:
    message = f"Ecco le strategie disponibili per <b>{sport.display_name}</b>:"
    for strategy in sport.strategies:
        message += f"\n\n- <b>{strategy.display_name}</b>: {strategy.explanation}"
    return message
    

def create_checklist_completion_message(chat_id: int) -> str:
    checklist_info = analytics_manager.retrieve_checklist_information_by_user_id(chat_id)
    if checklist_info["has_completed_checklist"]:
        return ""
    #* extend message with checklist
    budget_check = "✅" if bool(checklist_info["has_modified_budget"]) else "❌"
    event_registered_check = "✅" if bool(checklist_info["accepted_giocate"]) else "❌"
    referral_check = "✅" if bool(checklist_info["has_modified_referral"]) else "❌"
    return "\n" + cst.TUTORIAL_CHECKLIST.format(
        budget_check=budget_check, event_check=event_registered_check, referral_check=referral_check
    )
