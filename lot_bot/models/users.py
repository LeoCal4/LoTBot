from lot_bot import utils

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
        "referral_code": utils.create_valid_referral_code(),
        "linked_referral_code": "",
        "is_og_user": False,
        "successful_referrals_since_last_payment": [],
        "giocate": [],
        "payments": [],
        "sport_subscriptions": [],
        "available_sports": [],
    }


