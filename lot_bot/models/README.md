# User model
- _id: telegram ID
- name: str
- username: str
- email: str
- subscription_validity: timestamp
- referral_code: str
- linked_referral_code: str
- succesful_referrals: int
- giocate: []
    - original_id
    - personal_stake: int
    - personal_quota: int
    - acceptance_timestamp: float
- payments: []
    - invoice_payload: str
    - telegram_payment_charge_id: str
    - provider_payment_charge_id: str
    - total_amount: float 
    - currency: str
    - order_info:
        - email: str
- abbonamenti: []
    - sport_name: str
    - strategies: []
        - strat_name: str
- available_sports: []
    - sport_name: str
    - strategies: []
        - strat_name: str


# Giocate model
- sport: str
- strategy: str
- num: int
- base_stake: int
- base_quota: int
- sent_date: float
- outcome: bool