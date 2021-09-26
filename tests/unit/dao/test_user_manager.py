import datetime
import random
import string
from typing import Dict

from lot_bot import database as db
from lot_bot.dao import user_manager


def get_random_string(length: int):
    return "".join([random.choice(string.digits + string.ascii_lowercase) for _ in range(length)])


def get_random_payment() -> Dict:
    return {
        "invoice_payload": "payload_test",
        "telegram_payment_charge_id": get_random_string(12),
        "provider_payment_charge_id": get_random_string(12),
        "total_amount": random.randint(4000, 10000),
        "currency": "EUR",
    }


def test_create_user(monkeypatch):
    user_data = {
        "_id": 0,
        "name": "Franco",
        "surname": "Rossi"
    }
    user_manager.create_user(user_data)
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
    assert not user_manager.create_user(user_data2)


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
    assert updated_user["surname"] == new_user["surname"]
    # wrong id
    assert not user_manager.update_user(-1, {"name": new_name})
    # db connection error
    monkeypatch.setattr(db, "mongo", None)
    assert not user_manager.update_user(user_id, {"name": new_name})


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
    user_data = {"validoFino": user_expiration_date}
    validity = user_manager.check_user_validity(datetime.datetime.now(), user_data)
    assert validity == True


def test_check_user_expired_validity():
    user_expiration_date = str((datetime.datetime.now() - datetime.timedelta(days=1)).timestamp())
    user_data = {"validoFino": user_expiration_date}
    validity = user_manager.check_user_validity(datetime.datetime.now(), user_data)
    assert validity == False


def test_retrieve_user_by_referral(new_user: Dict, monkeypatch):
    user_ref_code = new_user["referral_code"]
    user_from_db = user_manager.retrieve_user_by_referral(user_ref_code)
    assert new_user["_id"] == user_from_db["_id"]
    assert user_manager.retrieve_user_by_referral("fake code") is None
    monkeypatch.setattr(db, "mongo", None)
    assert user_manager.retrieve_user_by_referral(user_ref_code) is None


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
    assert not user_manager.register_payment_for_user_id(payment, user_id)


def test_get_discount_for_user(new_user: Dict, monkeypatch):
    user_id = new_user["_id"]
    # new user 50% discount
    discount = user_manager.get_discount_for_user(user_id)
    assert discount == 0.5
    # normal no discount
    payment = get_random_payment()
    user_manager.register_payment_for_user_id(payment, user_id)
    discount = user_manager.get_discount_for_user(user_id)
    assert discount == 0
    # db connection error
    monkeypatch.setattr(db, "mongo", None)
    discount = user_manager.get_discount_for_user(user_id)
    assert discount == 0    
