
def create_base_giocata():
    return {
        "sport": "",
        "strategia": "",
        "giocata_num": 0,
        "base_quota": 0, # [quota (float) * 100] => (int)
        "base_stake": 0, # %
        "sent_timestamp": 0.0,
        "raw_text": "",
        "outcome": "?"
    }


def create_user_giocata():
    return {
        "original_id": 0,
        "acceptance_timestamp": 0.0,
        "personal_quota": 0,
        "personal_stake": 0,
    }


def get_outcome_percentage(outcome: str, stake: int, quota: int):
    # TODO handle outcomes Exchange
    if outcome == "win":
        outcome_percentage = stake * (quota - 100)
    elif outcome == "loss":
        outcome_percentage = -stake
    else:
        outcome_percentage = 0
    return outcome_percentage
