import datetime
import random
import string
from typing import Dict, List, Union

from dateutil.relativedelta import relativedelta
from lot_bot import constants as cst
from lot_bot import logger as lgr
from lot_bot.dao import user_manager, budget_manager
from lot_bot.models import giocate as giocata_model
from lot_bot.models import subscriptions as subs
from telegram import User 

# role: user, analyst, admin
ROLES = ["user", "analyst", "admin", "teacherbet"]

def create_base_user_data():
    return {
        "_id": 0,
        "name": "",
        "username": "",
        "email": "",
        "subscriptions": [],
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
        "budgets": [],
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


def add_days_to_user_subscription(user_id: int, days: int) -> bool:
    """Extends the main Lot subscription for the user_id by the specified days.

    Args:
        user_id (int)
        days (int)

    Returns:
        bool: _description_
    """
    retrieved_user = user_manager.retrieve_user_fields_by_user_id(user_id, ["subscriptions"])
    # extend subscription of 2 month
    retrieved_user_subs = retrieved_user["subscriptions"]
    user_subs_names = [entry["name"] for entry in retrieved_user_subs]
    lot_sub_name = subs.sub_container.LOTCOMPLETE.name
    if lot_sub_name not in user_subs_names:
        new_expiration_date = (datetime.datetime.utcnow() + datetime.timedelta(days=days)).timestamp()
        retrieved_user_subs.append({"name": lot_sub_name, "expiration_date": new_expiration_date})
    else:
        base_exp_date = [entry["expiration_date"] for entry in retrieved_user_subs if entry["name"] == lot_sub_name][0]
        new_expiration_date: float = extend_expiration_date(base_exp_date, days)
        for sub_entry in retrieved_user_subs:
            if sub_entry["name"] == lot_sub_name:
                sub_entry["expiration_date"] = new_expiration_date
                break
    # * reset user successful referrals
    user_data = {
        "subscriptions": retrieved_user_subs,
    }
    try:
        user_update_result = user_manager.update_user(user_id, user_data)
    except:
        user_update_result = False
    return user_update_result


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
        lgr.logger.debug(f"{giocata['cashout']=}")
        outcome_percentage = (giocata["cashout"] / 100) * int(giocata["outcome"] != "void") # just to be sure to avoid abbinate
    else:
        outcome_percentage = giocata_model.get_outcome_percentage(giocata["outcome"], stake, giocata["base_quota"])
    # * update budget with outcome percentange
    budget_difference = (user_budget * round(outcome_percentage / 100, 2))
    new_budget = user_budget + budget_difference
    lgr.logger.debug(f"New budget calculated: {user_budget=}  - {outcome_percentage=} - {budget_difference=}")
    return new_budget

def calculate_new_budget_after_giocata2(user_budget_balance: int, giocata: Dict, personalized_stake: int = None) -> int:
    """[summary]

    Args:
        user_budget_balance (int): actual budget * 100
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
        lgr.logger.debug(f"{giocata['cashout']=}")
        outcome_percentage = (giocata["cashout"] / 100) * int(giocata["outcome"] != "void") # just to be sure to avoid abbinate
    else:
        outcome_percentage = giocata_model.get_outcome_percentage(giocata["outcome"], stake, giocata["base_quota"])
    # * update budget with outcome percentange
    budget_difference = (user_budget_balance * round(outcome_percentage / 100, 2))
    new_budget = user_budget_balance + budget_difference
    lgr.logger.debug(f"New budget calculated: {user_budget_balance=}  - {outcome_percentage=} - {budget_difference=}")
    return new_budget



def update_single_user_budget_with_giocata(target_user_id: int, target_user_budget: int, giocata_id, 
                                            giocata_data: Dict, user_personal_stake: int = None) -> bool:
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

#TODO2 change every function with this message 
def update_single_user_budget_with_giocata2(target_user_id: int, target_user_budget_balance: int, giocata_id, 
                                            giocata_data: Dict, user_personal_stake: int = None) -> bool:
    """Calculates the new user's budget given the giocata, updates it and saves the pre-giocata budget in the personal user's giocata.

    Args:
        target_user_id (int)
        target_user_budget_balance (int)
        giocata_id:
        giocata_data (Dict)
        user_personal_stake (int, optional): Can be specified separately to calculate the new budget. Defaults to None.

    Returns:
        bool: True if the user's budget is updated and if the pre-giocata budget is saved, False otherwise
    """
    if target_user_budget_balance is None:
        return True
    # * calculate updated budget
    new_budget_balance = calculate_new_budget_after_giocata2(target_user_budget_balance, giocata_data, user_personal_stake)
    # * update user's budget
    default_budget_name = budget_manager.retrieve_default_budget_from_user_id(target_user_id)["budget_name"]
    update_result = budget_manager.update_budget_balance(target_user_id,default_budget_name,new_budget_balance)
    # * update personal giocata with pre-giocata budget info
    update_result = user_manager.update_user_giocata_with_previous_budget(
        target_user_id, 
        giocata_id,
        target_user_budget_balance) and update_result
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
        #if target_user["budget"] is None: #temporary
        default_budget = budget_manager.retrieve_default_budget_from_user_id(target_user["_id"]) 
        if not default_budget:
            continue
        #target_user_budget = int(target_user["budget"]) temporary
        target_user_budget = int(default_budget["balance"]) 
        target_user_personal_stake = int(target_user["giocate"]["personal_stake"])
        update_single_user_budget_with_giocata2(
            target_user["_id"], 
            target_user_budget, 
            updated_giocata["_id"],
            updated_giocata, 
            user_personal_stake=target_user_personal_stake
        )

#TODO2 change blabla
def update_users_budget_with_giocata2(updated_giocata: Dict):
    """Updates the budgets of the users who played the new giocata.

    Args:
        updated_giocata (Dict)
    """
    users_who_played_giocata = user_manager.retrieve_users_who_played_giocata(updated_giocata["_id"])
    if not users_who_played_giocata:
        return
    for target_user in users_who_played_giocata:
        default_budget = budget_manager.retrieve_default_budget_from_user_id(target_user["_id"])
        if default_budget is None:
            continue
        target_user_budget_balance = int(default_budget["balance"])
        target_user_personal_stake = int(target_user["giocate"]["personal_stake"])
        update_single_user_budget_with_giocata(
            target_user["_id"], 
            target_user_budget_balance, 
            updated_giocata["_id"],
            updated_giocata, 
            user_personal_stake=target_user_personal_stake
        )

#TODO find a better way to add default sport subscriptions
def create_first_time_user(user: User, ref_code: str = None, teacherbet_code: str = None) -> Dict:
    """Creates the user using the bot for the first time.
    First, it creates the user itself, setting its expiration date to 2 days 
    from now, then creates an sport_subscription to calcio - raddoppio and multipla and another
    one to exchange - maxexchange. 

    Args:
        user (User)
        ref_code (str): referral code for the new user. Defaults to None
        teacherbet_code (str): Teacherbet code for the new user. If it is present, activates the TB subscription trial
        instead of the LoT one. Defaults to None

    Returns:
        Dict: the created user data
    """
    # * create user
    user_data = create_base_user_data()
    user_data["_id"] = user.id
    user_data["name"] = user.first_name
    user_data["username"] = user.username
    user_data["first_access_timestamp"] = datetime.datetime.now().timestamp()
    user_data["sport_subscriptions"] = [
        {'sport':'calcio', 'strategies': ['produzione']},
        {'sport':'basket', 'strategies': ['produzione']},
        {'sport':'tennis', 'strategies': ['produzione']},
        {'sport':'exchange', 'strategies': ['produzione']},
        {'sport':'tuttoilresto', 'strategies': ['produzione']},
        {'sport':'analisimiste', 'strategies': ['communnitybet','freebet']},
    ]
    # * if a referral code is being used, update the user's field and the referrer's referred user count/list
    if ref_code:
        ref_user_data = user_manager.retrieve_user_id_by_referral(ref_code)
        if ref_user_data:
            ref_user_id = ref_user_data["_id"]
            user_data["linked_referral_user"] = {
                "linked_user_code": ref_code,
                "linked_user_id": ref_user_id
            }
            update_result = user_manager.update_user_succ_referrals(ref_user_id, user.id)
        if not ref_user_data or not update_result:
            lgr.logger.warning(f"Upon creating a new user, {ref_code=} was not valid")

    user_manager.create_user(user_data)
    return user_data


def check_user_permission(user_id: int, permitted_roles: List[str] = None, forbidden_roles: List[str] = None) -> Union[str, bool]:
    """Checks if the users specified by the user_id has the right permissions, based either on its presence in
    permitted_roles or its absence in forbidden_roles. Only one of them can be specified at a time.

    Args:
        user_id (int): [description]
        permitted_roles (List[str], optional): Defaults to None.
        forbidden_roles (List[str], optional): Defaults to None.

    Returns:
        Union[str, bool]: the user role if has the permission, False otherwise
    """
    user_role = user_manager.retrieve_user_fields_by_user_id(user_id, ["role"])["role"]
    lgr.logger.debug(f"Retrieved user role: {user_role} - {permitted_roles=} - {forbidden_roles=}")
    permitted = True
    if not permitted_roles is None:
        permitted = user_role if user_role in permitted_roles else False
    if not forbidden_roles is None:
        permitted = user_role if not user_role in forbidden_roles else False
    return permitted


def get_user_available_sports_names_from_subscriptions(user_subscriptions: List[Dict]) -> List[str]:
    user_available_sports = []
    now_timestamp = datetime.datetime.utcnow().timestamp()
    for sub_entry in user_subscriptions:
        sub = subs.sub_container.get_subscription(sub_entry["name"])
        if sub is None:
            raise Exception
        if float(sub_entry["expiration_date"]) < now_timestamp:
            continue
        if sub.available_sports == []:
            return []
        sports_names = [sub_sport.name for sub_sport in sub.available_sports]
        user_available_sports.extend(sports_names)
    return user_available_sports
 