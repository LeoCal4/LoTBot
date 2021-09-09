from telegram import (InlineKeyboardButton, InlineKeyboardMarkup,
                      KeyboardButton, ReplyKeyboardMarkup, Update)

from lot_bot.constants import SPORTS
from lot_bot.dao.abbonamenti_manager import retrieve_abbonamenti_from_user_id
from lot_bot.logger import logger

startup_buttons = [
    [KeyboardButton(text="🙋🏼‍♀️ Vai alla Community 🙋🏾")],
    [KeyboardButton(text="👩🏾‍💻  Assistenza  🧑🏻")],
    [KeyboardButton(text="📱 Homepage 📱")]
]
startup_reply_keyboard = ReplyKeyboardMarkup(keyboard=startup_buttons, resize_keyboard=True)


gestione_account_buttons = [
    [InlineKeyboardButton(text="Sport e strategie", callback_data="Sport e strategie")], 
    [InlineKeyboardButton(text="Assistenza", callback_data="Assistenza")], 
    [InlineKeyboardButton(text="Nuove funzionalità in arrivo!", callback_data="Nuove funzionalità in arrivo!")]
]
gestione_account_inline_keyboard =  InlineKeyboardMarkup(inline_keyboard=gestione_account_buttons)


next_button = [InlineKeyboardButton(text="Next", callback_data="next")]
next_inline_keyboard = InlineKeyboardMarkup(inline_keyboard=[next_button])


homepage_buttons = [
    [InlineKeyboardButton(text="⛹🏿‍♂️  Sport e Strategie  📖", callback_data="Sport e strategie")], 
    [InlineKeyboardButton(text="💰  Capitale e Obiettivi  🎯  in arrivo", callback_data="c e obiettivi")], 
    [InlineKeyboardButton(text="🏆    Record e Statistiche   📊  in arrivo", callback_data="Nuove funzionalità in arrivo!")], 
    [InlineKeyboardButton(text="👩🏾‍💻  Assistenza  🧑🏻", url="https://t.me/LegacyOfTipstersBot")], 
    [InlineKeyboardButton(text="👨‍🏫 Formazione e Lezioni  🧑‍🎓  in arrivo", callback_data="formazione e lezioni")], 
    [InlineKeyboardButton(text="👩🏼‍⚕️  Supporto al gioco d'azzardo  🎰 ", callback_data="c e obiettivi")], 
    [InlineKeyboardButton(text="🙋🏼‍♀️  Community e Team LoT 🙋🏾", url="https://t.me/LoTVerse")], 
    [InlineKeyboardButton(text ="📲 Link Utili e Reportistica 📚", callback_data="link utili")], 
    [InlineKeyboardButton(text="⚙️️  Impostazioni ⚙️", callback_data="Impostazioni")]
]
homepage_inline_keyboard = InlineKeyboardMarkup(inline_keyboard=homepage_buttons)


back_keyboard_button = InlineKeyboardButton(text=f"Indietro ↩", callback_data= "Indietro")


def create_sports_inline_keyboard(update: Update) -> InlineKeyboardMarkup:
    """Creates the inline keyboard listing the available sports,
        together with a 🔴 or a 🟢, depending on the user's 
        preferences.

    Args:
        update (Update): the Update containing the message sent from the user

    Returns:
        InlineKeyboardMarkup: the aformentioned keyboard
    """

    chat_id = update.effective_chat.id
    abbonamenti = retrieve_abbonamenti_from_user_id(chat_id)
    sport_attivi = [entry["sport"] for entry in abbonamenti]
    emoji_sport = {sport: "🔴" for sport in SPORTS}
    for sport in sport_attivi:
        emoji_sport[sport] = "🟢"
    SPORT_STRING_MENU_LEN = 19
    # ljust appends " " at the end of the string, until the specified length is reached
    sport_menu_entries = [sport.ljust(SPORT_STRING_MENU_LEN) + emoji_sport[sport] for sport in SPORTS]
    inline_buttons = {sport: entry for sport, entry in zip(SPORTS, sport_menu_entries)}
    keyboard_sport = []
    for i, sport in enumerate(SPORTS):
        sport_keyboard_button = InlineKeyboardButton(text=inline_buttons[sport], callback_data=sport)
        if i % 2 == 0:
            keyboard_sport.append([sport_keyboard_button])
        else:
            keyboard_sport[i-1].append(sport_keyboard_button)
    keyboard_sport.append([back_keyboard_button])
    inline_sport = InlineKeyboardMarkup(inline_keyboard=keyboard_sport)
    return inline_sport
