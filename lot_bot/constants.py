""" This module is used to define constants
"""

SPORTS = [
    "calcio",
    "basket",
    "tennis",
    "exchange",
    "speciali",
    "ping pong",
    "hockey",
    "freccette",
    "baseball",
    "pallavolo",
    "rugby",
    "sport2"
]


base_strategie = ["Raddoppio", "Multiple", "Singola", "Live", "Instagram"]
STRATEGIES = {
  "calcio": base_strategie + ["PiaQuest", "Trilled"],
  "basket": base_strategie + ["Trilled"],
  "tennis": base_strategie + ["Trilled"],
  "ping pong": base_strategie + ["Trilled"],
  "freccette": base_strategie + ["Trilled"],
  "hockey": base_strategie + ["Trilled"],
  "baseball": base_strategie + ["Trilled"],
  "exchange": ["MaxExchange"],
  "speciali": base_strategie,
  "rugby": base_strategie + ["Trilled"],
  "sport2": base_strategie,
  "pallavolo": base_strategie,
}

# this defines what will be imported if you import * from this module 
__all__ = ["SPORTS", "STRATEGIES"]
