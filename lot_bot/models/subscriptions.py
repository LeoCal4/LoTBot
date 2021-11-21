import dataclasses
from typing import Optional, List

from lot_bot.models import sports


@dataclasses.dataclass
class Subscription:
    name : str
    available_sports : List[sports.Sport] = []
    price : int = 0 # ?


@dataclasses.dataclass
class SubContainer:
    LOTCOMPLETE : Subscription = Subscription("lotcomplete")
    TEACHERBET : Subscription = Subscription("teacherbet", available_sports=[sports.sports_container.TEACHERBET])

    def __iter__(self):
        attributes = dataclasses.asdict(self).keys()
        yield from (getattr(self, attribute) for attribute in attributes)

    def __next__(self):
        yield

    def get_subscription(self, sub_string: str) -> Optional[Subscription]:
        if not sub_string:
            return None
        parsed_sub_string = sub_string.upper().strip().replace(" ", "").replace("_", "")
        if hasattr(self, parsed_sub_string):
            return getattr(self, parsed_sub_string)
        else:
            return None


sub_container = SubContainer()
