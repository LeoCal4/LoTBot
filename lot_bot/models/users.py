from lot_bot import utils

def create_base_user_data():
    return {
        "_id": 0,
        "nome": "-",
        "nomeUtente": "-",
        "email": "",
        "validoFino": 0.0,
        "referral_code": utils.create_valid_referral_code(),
        "linked_referral_code": "",
        "successful_referrals": 0,
        "giocate": [],
        "payments": [],
        "sport_subscriptions": [],
        "available_sports": [],
    }