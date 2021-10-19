"""Module containing all the custom exceptions for lot_bot"""

class SportNotFoundError(Exception):
    def __init__(self, sport_token: str, update=None):
        self.sport_token = sport_token
        self.update = update
    
    def __str__(self):
        string = f"Could not open strategies for sport {self.sport_token}"
        if self.update:
            string += f"\n{str(self.update)=}"
        return string


class StrategyNotFoundError(Exception):
    def __init__(self, sport_token: str, strategy_token: str, update=None):
        self.sport_token = sport_token
        self.strategy_token = strategy_token
        self.update = update
    
    def __str__(self):
        string = f"Could not open strategy {self.strategy_token} for sport {self.sport_token}"
        if self.update:
            string += f"\n{str(self.update)=}"
        return string


class SendMessageError(Exception):
    def __init__(self, message_text: str, update=None):
        self.message_text = message_text
        self.update = update
    
    def __str__(self) -> str:
        string = f"Error sending message {self.message_text}"
        if self.update:
            string += f"\n{str(self.update)=}"
        return string


class UserNotFound(Exception):
    def __init__(self, user_id: str = "", update=None):
        self.user_id = user_id
        self.update = update

    def __str__(self) -> str:
        string = f"Error finding user {self.user_id}"
        if self.update:
            string += f"\n{str(self.update)=}"
        return string


class GiocataParsingError(Exception):
    def __init__(self, message: str):
        self.message = message

    # ! this will be sent as an answer to the analisti
    def __str__(self) -> str:
        return self.message


class GiocataCreationError(Exception):
    def __init__(self, message: str = ""):
        self.message = message

    # ! this will be sent as an answer to the analisti
    def __str__(self) -> str:
        return self.message


class GiocataOutcomeParsingError(Exception):
    def __init__(self, message: str = ""):
        self.message = message

    # ! this will be sent as an answer to the analisti
    def __str__(self) -> str:
        return self.message


class NormalMessageParsingError(Exception):
    def __init__(self, message: str):
        self.message = message

    # ! this will be sent as an answer to the analisti
    def __str__(self) -> str:
        return self.message

class PersonalStakeParsingError(Exception):
    def __init__(self, message: str):
        self.message = message

    # ! this will be sent as an answer to the analisti
    def __str__(self) -> str:
        return self.message