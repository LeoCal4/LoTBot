import datetime
import random
import string
from typing import Callable, Dict, Tuple

import pytest
from lot_bot import database as db
from lot_bot import logger as lgr
from lot_bot.dao import giocate_manager, user_manager
from lot_bot.models import giocate as giocata_model


def get_random_string(length: int):
    return "".join([random.choice(string.digits + string.ascii_lowercase) for _ in range(length)])


def get_random_payment() -> Dict:
    return {
        "payment_id": get_random_string(16),
        "datetime_timestamp": 0.0,
        "invoice_payload": "payload_test",
        "telegram_payment_charge_id": get_random_string(12),
        "provider_payment_charge_id": get_random_string(12),
        "total_amount": random.randint(4000, 10000),
        "currency": "EUR",
    }


def test_create_user(monkeypatch):
    user_data = {
        "_id": 999,
        "name": "Franco",
        "surname": "Rossi"
    }
    assert user_manager.create_user(user_data)
    user = user_manager.retrieve_user(user_data["_id"])
    assert len(user_data.keys()) == len(user.keys())
    for key in user.keys():
        assert user[key] == user_data[key]
    monkeypatch.setattr(db, "mongo", None)
    user_data2 = {
        "_id": 1,
        "name": "Franco",
        "surname": "Rossi"
    }
    with pytest.raises(Exception):
        user_manager.create_user(user_data2)


# new_user is specified in the params of the funcion,
#   so that the fixture with the same name is called and 
#   its return/yield value is used as a parameter
def test_retrieve_user(new_user: Dict, monkeypatch):
    user_id = new_user["_id"]
    user_from_db = user_manager.retrieve_user(user_id)
    assert user_id == user_from_db["_id"]
    assert user_manager.retrieve_user(-1) is None
    monkeypatch.setattr(db, "mongo", None)
    assert user_manager.retrieve_user(user_id) is None


def test_update_user(new_user: Dict, monkeypatch):
    user_id = new_user["_id"]
    new_name = "Oiram"
    user_manager.update_user(user_id, {"name": new_name})
    updated_user = user_manager.retrieve_user(user_id)
    assert updated_user["name"] == new_name
    # wrong id
    assert not user_manager.update_user(-1, {"name": new_name})
    # db connection error
    monkeypatch.setattr(db, "mongo", None)
    with pytest.raises(Exception):
        user_manager.update_user(user_id, {"name": new_name})


def test_delete_user(new_user: Dict, monkeypatch):
    user_id = new_user["_id"]
    assert user_manager.delete_user(user_id)
    assert user_manager.retrieve_user(user_id) == None
    assert not user_manager.delete_user(-1)
    # db connection error
    monkeypatch.setattr(db, "mongo", None)
    assert not user_manager.delete_user(user_id)
    

def test_check_user_active_validity():
    user_expiration_date = str((datetime.datetime.now() + datetime.timedelta(days=1)).timestamp())
    user_data = {"lot_subscription_expiration": user_expiration_date}
    validity = user_manager.check_user_sport_subscription(datetime.datetime.now(), user_data)
    assert validity == True


def test_check_user_expired_validity():
    user_expiration_date = str((datetime.datetime.now() - datetime.timedelta(days=1)).timestamp())
    user_data = {"lot_subscription_expiration": user_expiration_date}
    validity = user_manager.check_user_sport_subscription(datetime.datetime.now(), user_data)
    assert validity == False


def test_retrieve_user_id_by_referral(new_user: Dict, monkeypatch):
    user_ref_code = new_user["referral_code"]
    user_from_db = user_manager.retrieve_user_id_by_referral(user_ref_code)
    assert new_user["_id"] == user_from_db["_id"]
    assert user_manager.retrieve_user_id_by_referral("fake code") is None
    monkeypatch.setattr(db, "mongo", None)
    with pytest.raises(Exception):
        user_manager.retrieve_user_id_by_referral(user_ref_code)


def test_register_payment_for_user_id(new_user: Dict, monkeypatch):
    user_id = new_user["_id"]
    payment = get_random_payment()
    user_manager.register_payment_for_user_id(payment, user_id)
    updated_user = user_manager.retrieve_user(user_id)
    user_payments = updated_user["payments"] 
    assert len(user_payments) == 1
    registered_payment = user_payments[0]
    for field in payment.keys():
        assert payment[field] == registered_payment[field]
    # wrong id
    assert not user_manager.register_payment_for_user_id(payment, -1)
    # db connection error
    monkeypatch.setattr(db, "mongo", None)
    with pytest.raises(Exception):
        user_manager.register_payment_for_user_id(payment, user_id)


def test_update_user_succ_referrals(new_user: Dict):
    user_id = new_user["_id"]
    payment_ids = []
    for _ in range(2, 10):
        payment_id = get_random_string(16)
        payment_ids.append(payment_id)
        assert user_manager.update_user_succ_referrals(user_id, payment_id)
    payment_data = user_manager.retrieve_user_fields_by_user_id(user_id, ["successful_referrals_since_last_payment", "referred_payments"])
    assert len(payment_data["successful_referrals_since_last_payment"]) == len(payment_ids)
    assert len(payment_data["referred_payments"]) == len(payment_ids)
    for succ_refs, normal_refs in zip(payment_data["successful_referrals_since_last_payment"], payment_data["referred_payments"]):
        assert succ_refs in payment_ids
        assert normal_refs in payment_ids


def test_get_subscription_price_for_user(new_user: Dict, monkeypatch):
    user_id = new_user["_id"]
    # * new user 50% discount
    price = user_manager.get_subscription_price_for_user(user_id)
    assert price == 3999
    # * price with one referral and og user
    user_manager.update_user_succ_referrals(user_id, get_random_string(12))
    price = user_manager.get_subscription_price_for_user(user_id)
    assert price == 3999 - int(3999 * 0.33)
    # * price with 3 referrals
    user_manager.update_user_succ_referrals(user_id, get_random_string(12))
    user_manager.update_user_succ_referrals(user_id, get_random_string(12))
    price = user_manager.get_subscription_price_for_user(user_id)
    assert price == 0
    # * normal no discount
    user_manager.update_user(user_id, {"is_og_user": False, "successful_referrals_since_last_payment": []})
    payment = get_random_payment()
    user_manager.register_payment_for_user_id(payment, user_id)
    price = user_manager.get_subscription_price_for_user(user_id)
    assert price == 7999
    # * normal with referral
    user_manager.update_user_succ_referrals(user_id, get_random_string(12))
    price = user_manager.get_subscription_price_for_user(user_id)
    assert price == 7999 - int(7999 * 0.33)
    # * db connection error
    monkeypatch.setattr(db, "mongo", None)
    with pytest.raises(Exception):
        user_manager.get_subscription_price_for_user(user_id)


def test_retrieve_user_giocate_since_timestamp(new_user: Dict, correct_giocata_function_fixture: Callable[[], Tuple[str, Dict]]):
    user_id = new_user["_id"]
    recent_giocate = []
    older_giocate = []
    base_giocata_day = random.choice((1, 7, 30))
    # recent giocate
    for _ in range(random.randint(2, 10)):
        correct_giocata_text, _ = correct_giocata_function_fixture()
        parsed_giocata = giocata_model.parse_giocata(correct_giocata_text)
        created_giocata_id = giocate_manager.create_giocata(parsed_giocata)
        assert created_giocata_id
        user_giocata = giocata_model.create_user_giocata()
        user_giocata["acceptance_timestamp"] = datetime.datetime.utcnow().timestamp()
        user_giocata["original_id"] = created_giocata_id
        user_manager.register_giocata_for_user_id(user_giocata, user_id)
        recent_giocate.append(user_giocata)
    # older giocate
    for _ in range(random.randint(2, 10)):
        older_giocata_text, _ = correct_giocata_function_fixture()
        older_parsed_giocata = giocata_model.parse_giocata(older_giocata_text)
        older_giocata_id = giocate_manager.create_giocata(older_parsed_giocata)
        assert older_giocata_id
        older_user_giocata = giocata_model.create_user_giocata()
        random_old_day = random.randint(base_giocata_day + 1, base_giocata_day + 30)
        older_user_giocata["acceptance_timestamp"] = (datetime.datetime.utcnow() - datetime.timedelta(days=random_old_day)).timestamp()
        older_user_giocata["original_id"] = older_giocata_id
        user_manager.register_giocata_for_user_id(older_user_giocata, user_id)
        older_giocate.append(user_giocata)
    giocate = user_manager.retrieve_user_giocate_since_timestamp(user_id, (datetime.datetime.utcnow() - datetime.timedelta(days=base_giocata_day)).timestamp())
    lgr.logger.error(f"{giocate=}")
    assert len(giocate) == len(recent_giocate)
    for giocata, original_giocata in zip(giocate, recent_giocate):
        assert giocata["original_id"] == original_giocata["original_id"]


def test_retrieve_user_fields_by_user_id(new_user: Dict):
    random_fields = []
    user_fields = list(new_user.keys())
    for _ in range(random.randint(1, 4)):
        random_fields.append(random.choice(user_fields))
    retrieved_fields = user_manager.retrieve_user_fields_by_user_id(new_user["_id"], random_fields)
    for field in random_fields:
        assert new_user[field] == retrieved_fields[field]  
    # * non-existent field
    retrieved_only_id = user_manager.retrieve_user_fields_by_user_id(new_user["_id"], "fake field")
    assert list(retrieved_only_id.keys()) == ["_id"]
