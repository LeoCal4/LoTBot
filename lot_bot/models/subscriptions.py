import dataclasses
import datetime
from typing import Optional, List

from lot_bot.models import sports


@dataclasses.dataclass
class Subscription:
    name : str
    display_name : str = ""
    available_sports : List[sports.Sport] = dataclasses.field(default_factory=list)
    description : str = ""
    price : int = 0
    aliases : List[str] = dataclasses.field(default_factory=list)

    def __post_init__(self):
        if self.display_name == "":
            self.display_name = self.name.capitalize()


@dataclasses.dataclass
class SubContainer:
    # * available_sports is not set, meaning that every one of the is included 
    LOTCOMPLETE : Subscription = Subscription(
        "lotcomplete", 
        display_name="LoT Abbonamento Completo", 
        price=7900, 
        description="Accesso completo a tutta la produzione LoT (include tutti gli abbonamenti)",
        aliases=["lot", "lot completo", "lot complete", "lot totale"]
    )
    TEACHERBET : Subscription = Subscription(
        "teacherbet", 
        available_sports=[sports.sports_container.TEACHERBET], 
        price=1500,
        description="Accesso alla produzione Teacherbet",
        aliases=["teacher", "teacher bet", "tb"]
    )

    def __iter__(self):
        attributes = dataclasses.asdict(self).keys()
        yield from (getattr(self, attribute) for attribute in attributes)

    def __next__(self):
        yield

    def astuple(self):
        return tuple([self.__dict__[field.name] for field in dataclasses.fields(self)])

    def get_subscription(self, sub_string: str) -> Optional[Subscription]:
        if not sub_string:
            return None
        parsed_sub_string = sub_string.upper().strip().replace(" ", "").replace("_", "")
        if hasattr(self, parsed_sub_string):
            return getattr(self, parsed_sub_string)
        else:
            for sub in self.astuple():
                if sub_string in sub.aliases:
                    return sub
        return None

sub_container = SubContainer()



def create_teacherbet_base_sub():
    trial_expiration_timestamp = (datetime.datetime.now() + datetime.timedelta(days=3)).timestamp()
    return {"name": sub_container.TEACHERBET.name, "expiration_date": trial_expiration_timestamp}
