from typing import Dict


def create_base_analytics() -> Dict:
    return {
        "_id": None, # user id
        "has_completed_checklist": False,
        "has_modified_referral": False,
        "has_modified_budget": False,
        # these are already available in the user's data, but they'll be repeated here,
        #   just for the sake of having every data related to the checklist 
        #   in the same place
        "accepted_giocate": [], # list of giocate ids
        "refused_giocate": [], # list of giocate ids
        # TODO implement ====== 
        "resoconto_requests": [], # list of resoconto types and timestamps
        "referred_users": [], # list of referred users ids and timestamps
    }
