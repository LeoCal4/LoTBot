import dataclasses
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
    LOTCOMPLETE : Subscription = Subscription(
        "lotcomplete", 
        display_name="LoT Abbonamento Completo", 
        price=500, 
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

    def get_subscription(self, sub_string: str) -> Optional[Subscription]:
        if not sub_string:
            return None
        parsed_sub_string = sub_string.upper().strip().replace(" ", "").replace("_", "")
        if hasattr(self, parsed_sub_string):
            return getattr(self, parsed_sub_string)
        else:
            return None


sub_container = SubContainer()
