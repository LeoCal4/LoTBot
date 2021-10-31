import datetime
import random
import string
from typing import Dict

from dateutil.relativedelta import relativedelta
from lot_bot import constants as cst
from lot_bot import logger as lgr
from lot_bot.dao import user_manager
from lot_bot.models import giocate as giocata_model

# role: user, analyst, admin
ROLES = ["user", "analyst", "admin"]

def create_base_user_data():
    return {
        "_id": 0,
        "name": "",
        "username": "",
        "email": "",
        "lot_subscription_expiration": 0.0,
        "role": "user",
        "referral_code": create_valid_referral_code(),
        "linked_referral_user": {
            "linked_user_id": None,
            "linked_user_code": ""
        },
        "is_og_user": True, # TODO remember to switch this off
        "successful_referrals_since_last_payment": [],
        "referred_payments": [],
        "giocate": [],
        "payments": [],
        "sport_subscriptions": [],
        "available_sports": [],
        "budget": None,
        "personal_stakes": [],
    }

def generate_referral_code() -> str:
    """Generates a random referral code.
    The pattern is <8 chars among digits and lowercase letters>-lot

    Returns:
        str: the referral code
    """
    code_chars = string.ascii_lowercase + string.digits
    return "".join((random.choice(code_chars) for x in range(cst.REFERRAL_CODE_LEN))) + "-lot"


def check_referral_code_availability(new_referral: str) -> bool:
    return user_manager.retrieve_user_id_by_referral(new_referral) is None


def create_valid_referral_code() -> str:
    """Creates a valid referral code for a new user, generating them
    until one which is not already used is found.

    Returns:
        str: a valid referral code
    """
    new_referral = ""
    while True:
        new_referral = generate_referral_code()
        if check_referral_code_availability(new_referral):
            break
    return new_referral


def extend_expiration_date(expiration_date_timestamp: float, giorni_aggiuntivi: int) -> float:
    """Adds giorni_aggiuntivi to the expiration date timestamp in case it is in the future,
    otherwise it adds giorni_aggiuntivi to the current timestamp.

    Args:
        expiration_date_timestamp (float)
        giorni_aggiuntivi (int)

    Returns:
        float: the original timestamp + giorni_aggiuntivi
    """
    now_timestamp = datetime.datetime.utcnow().timestamp()
    if datetime.datetime.utcnow().timestamp() > expiration_date_timestamp:
        base_timestamp = now_timestamp
    else:
        base_timestamp = expiration_date_timestamp
    return (datetime.datetime.utcfromtimestamp(base_timestamp) + relativedelta(days=giorni_aggiuntivi)).timestamp()


def calculate_new_budget_after_giocata(user_budget: int, giocata: Dict, personalized_stake: int = None) -> int:
    """[summary]

    Args:
        user_budget (int): actual budget * 100
        giocata (Dict): [description]
        personalized_stake (int, optional): [description]. Defaults to None.

    Returns:
        int: the new budget after the giocata
    """
    stake = giocata["base_stake"]
    # * check if there is a personalized stake
    if not personalized_stake is None and personalized_stake != 0:
        stake = personalized_stake
    # * get outcome percentage
    if "cashout" in giocata:
        outcome_percentage = (giocata["cashout"] / 100) * int(giocata["outcome"] != "abbinata") # just to be sure to avoid abbinate
    else:
        outcome_percentage = giocata_model.get_outcome_percentage(giocata["outcome"], stake, giocata["base_quota"])
    # * update budget with outcome percentange
    budget_difference = (user_budget * round(outcome_percentage / 100, 2))
    new_budget = user_budget + budget_difference
    return new_budget


def update_single_user_budget_with_giocata(target_user_id: int, target_user_budget: int, giocata_id, giocata_data: Dict, user_personal_stake: int = None) -> bool:
    """Calculates the new user's budget given the giocata, updates it and saves the pre-giocata budget in the personal user's giocata.

    Args:
        target_user_id (int)
        target_user_budget (int)
        giocata_id:
        giocata_data (Dict)
        user_personal_stake (int, optional): Can be specified separately to calculate the new budget. Defaults to None.

    Returns:
        bool: True if the user's budget is updated and if the pre-giocata budget is saved, False otherwise
    """
    if target_user_budget is None:
        return True
    # * calculate updated budget
    new_budget = calculate_new_budget_after_giocata(target_user_budget, giocata_data, user_personal_stake)
    # * update user's budget
    update_result = user_manager.update_user(target_user_id, {"budget": new_budget})
    # * update personal giocata with pre-giocata budget info
    update_result = user_manager.update_user_giocata_with_previous_budget(
        target_user_id, 
        giocata_id,
        target_user_budget) and update_result
    return update_result


def update_users_budget_with_giocata(updated_giocata: Dict):
    """Updates the budgets of the users who played the new giocata.

    Args:
        updated_giocata (Dict)
    """
    users_who_played_giocata = user_manager.retrieve_users_who_played_giocata(updated_giocata["_id"])
    if not users_who_played_giocata:
        return
    for target_user in users_who_played_giocata:
        target_user_budget = int(target_user["budget"])
        target_user_personal_stake = int(target_user["giocate"]["personal_stake"])
        update_single_user_budget_with_giocata(
            target_user["_id"], 
            target_user_budget, 
            updated_giocata["_id"],
            updated_giocata, 
            user_personal_stake=target_user_personal_stake
        )

