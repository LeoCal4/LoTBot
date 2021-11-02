import datetime
import random
import string
from typing import Dict, List

from dateutil.relativedelta import relativedelta
from lot_bot import constants as cst
from lot_bot import logger as lgr
from lot_bot.dao import (sport_subscriptions_manager, user_manager)
from lot_bot.models import sports as spr
from lot_bot.models import strategies as strat
from telegram import User

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
        "blocked": False,
        "successful_referrals_since_last_payment": [],
        "referred_payments": [],
        "giocate": [],
        "payments": [],
        "sport_subscriptions": [],
        "available_sports": [],
        "personal_stakes": [],
    }

def generate_referral_code() -> str:
    """Generates a random referral code.
    The pattern is lot-ref-<8 chars among digits and lowercase letters>

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


def create_first_time_user(user: User, ref_code: str) -> Dict:
    """Creates the user using the bot for the first time.
    First, it creates the user itself, setting its expiration date to 7 days 
    from now, then creates an sport_subscription to calcio - raddoppio and multipla and another
    one to exchange - maxexchange. 

    Args:
        user (User)

    Returns:
        Dict: the created user data
    """
    # * create user
    user_data = create_base_user_data()
    user_data["_id"] = user.id
    user_data["name"] = user.first_name
    user_data["username"] = user.username
    if ref_code:
        ref_user_data = user_manager.retrieve_user_id_by_referral(ref_code)
        if ref_user_data:
            user_data["linked_referral_user"] = {
                "linked_user_code": ref_code,
                "linked_user_id": ref_user_data["_id"]
            }
    else:
        lgr.logger.warning(f"Upon creating a new user, {ref_code=} was not valid")
    # ! TODO REVERT
    # trial_expiration_timestamp = (datetime.datetime.now() + datetime.timedelta(days=7)).timestamp()
    trial_expiration_timestamp = datetime.datetime(2021, 11, 7, hour=23, minute=59).timestamp()
    user_data["lot_subscription_expiration"] = trial_expiration_timestamp
    user_manager.create_user(user_data)
    # * create calcio -  sport_subscription
    sport_subscriptions_calcio_raddoppio_data = {
        "user_id": user.id,
        "sport": spr.sports_container.CALCIO.name,
        "strategy": strat.strategies_container.RADDOPPIO.name,
    }
    sub_creation_result = False
    try:
        sub_creation_result = sport_subscriptions_manager.create_sport_subscription(sport_subscriptions_calcio_raddoppio_data)
    except Exception as e:
        lgr.logger.error(f"Could not create subscription {sport_subscriptions_calcio_raddoppio_data} for new user {user_data['_id']} - {str(e)}")
    sport_subscriptions_calcio_multiple_data = {
        "user_id": user.id,
        "sport": spr.sports_container.CALCIO.name,
        "strategy": strat.strategies_container.MULTIPLA.name,
    }
    try:
        sub_creation_result = sub_creation_result and sport_subscriptions_manager.create_sport_subscription(sport_subscriptions_calcio_multiple_data)
    except Exception as e:
        lgr.logger.error(f"Could not create subscription {sport_subscriptions_calcio_multiple_data} for new user {user_data['_id']} - {str(e)}")
    # * create exchange - maxexchange sport_subscription
    sport_subscriptions_exchange_data = {
        "user_id": user.id,
        "sport": spr.sports_container.EXCHANGE.name,
        "strategy": strat.strategies_container.MAXEXCHANGE.name,  
    }
    try:
        sub_creation_result = sub_creation_result and sport_subscriptions_manager.create_sport_subscription(sport_subscriptions_exchange_data)
    except Exception as e:
        lgr.logger.error(f"Could not create subscription {sport_subscriptions_exchange_data} for new user {user_data['_id']} - {str(e)}")
    if not sub_creation_result:
        # send_messages_to_developers(context, [error_message]) # TODO decide if this is the right approach or not
        pass
    return user_data



def check_user_permission(user_id: int, permitted_roles: List[str] = None, forbidden_roles: List[str] = None):
    user_role = user_manager.retrieve_user_fields_by_user_id(user_id, ["role"])["role"]
    lgr.logger.error(f"Retrieved user role: {user_role} - {permitted_roles=} - {forbidden_roles=}")
    permitted = True
    if not permitted_roles is None:
        permitted = user_role in permitted_roles
    if not forbidden_roles is None:
        permitted = not user_role in forbidden_roles 
    return permitted

