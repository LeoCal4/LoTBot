from telegram import (InlineKeyboardButton, InlineKeyboardMarkup,
                      KeyboardButton, ReplyKeyboardMarkup, Update)

from lot_bot import constants as cst
from lot_bot.dao import abbonamenti_manager

_startup_buttons = [
    [KeyboardButton(text="🙋🏼‍♀️ Vai alla Community 🙋🏾")],
    [KeyboardButton(text="👩🏾‍💻  Assistenza  🧑🏻")],
    [KeyboardButton(text="📱 Homepage 📱")]
]
STARTUP_REPLY_KEYBOARD = ReplyKeyboardMarkup(keyboard=_startup_buttons, resize_keyboard=True)

_homepage_buttons = [
    [InlineKeyboardButton(text="⛹🏿‍♂️  Sport  📖", callback_data="to_sports_menu")], 
    [InlineKeyboardButton(text="⛹🏿‍♂️  Spiegazione Strategie  📖", callback_data="to_explanation_menu")], 
    [InlineKeyboardButton(text="👩🏾‍💻  Assistenza  🧑🏻", url="https://t.me/LegacyOfTipstersBot")], 
    [InlineKeyboardButton(text="🙋🏼‍♀️  Community e Team LoT 🙋🏾", url="https://t.me/LoTVerse")],
    [InlineKeyboardButton(text ="📲 Link Utili e Reportistica 📚", callback_data="links")], 
]
HOMEPAGE_INLINE_KEYBOARD = InlineKeyboardMarkup(inline_keyboard=_homepage_buttons)


_explanation_test_buttons = [
    [InlineKeyboardButton(text="⛹🏿‍♂️  Singola  📖", callback_data="explanation_singola")], 
    [InlineKeyboardButton(text="⛹🏿‍♂️  Multiple 📖", callback_data="explanation_multiple")], 
    [InlineKeyboardButton(text="Indietro ↩️", callback_data= "to_homepage")]
]
EXPLANATION_TEST_INLINE_KEYBOARD = InlineKeyboardMarkup(inline_keyboard=_explanation_test_buttons)

_useful_links_buttons = [
    [InlineKeyboardButton(text="📉 Tracciabilità Produzione LoT +24h📉 ", url="t.me/LoT_Tracciabilita")],
    [InlineKeyboardButton(text="📊 Report e Rendimenti 📊 ", url = "t.me/LoT_ReportGiornalieri")],
    [InlineKeyboardButton(text="📱 Pagina Instagram 📱 ", url="https://www.instagram.com/lot.official")],
    [InlineKeyboardButton(text="Indietro ↩️", callback_data= "to_homepage")]
]
USEFUL_LINKS_INLINE_KEYBOARD = InlineKeyboardMarkup(inline_keyboard=_useful_links_buttons, resize_keyboard=True)


def create_sports_inline_keyboard(update: Update) -> InlineKeyboardMarkup:
    """Creates the inline keyboard listing the available sports,
        together with a 🔴 or a 🟢, depending on the user's 
        preferences.
    
    The callbacks for this keyboard are in the form of:
        sport_<sport>

    Args:
        update (Update): the Update containing the message sent from the user

    Returns:
        InlineKeyboardMarkup: the aformentioned keyboard
    """

    chat_id = update.effective_chat.id
    abbonamenti = abbonamenti_manager.retrieve_abbonamenti({"telegramID": chat_id})
    sport_attivi = [entry["sport"].lower() for entry in abbonamenti]
    emoji_sport = {sport: "🔴" for sport in cst.SPORTS}
    for sport in sport_attivi:
        emoji_sport[sport] = "🟢"
    SPORT_STRING_MENU_LEN = 19
    # ljust appends " " at the end of the string, until the specified length is reached
    # capitalize makes the first letter uppercase and the rest lowercase
    sport_menu_entries = [cst.SPORTS_DISPLAY_NAMES[sport].ljust(SPORT_STRING_MENU_LEN) + emoji_sport[sport] for sport in cst.SPORTS]
    inline_buttons = {sport: entry for sport, entry in zip(cst.SPORTS, sport_menu_entries)}
    keyboard_sport = []
    for i, sport in enumerate(cst.SPORTS):
        sport_keyboard_button = InlineKeyboardButton(text=inline_buttons[sport], callback_data=f"sport_{sport}")
        if i % 2 == 0:
            keyboard_sport.append([sport_keyboard_button])
        else:
            keyboard_sport[(i-1)//2].append(sport_keyboard_button)
    keyboard_sport.append([InlineKeyboardButton(text=f"Indietro ↩️", callback_data= "to_homepage")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard_sport)
     


def create_strategies_inline_keyboard(update: Update, sport: str) -> InlineKeyboardMarkup:
    """Creates the inline keyboard for the strategies of sports,
        populating it with a 🔴 or a 🟢, depending on the user's 
        preferences.
    
    The callbacks for this keyboard are in the form:
        <sport>_<strategy>_(activate|disable)  

    Args:
        update (Update)
        sport (str)

    Returns:
        InlineKeyboardMarkup
    """
    chat_id = update.effective_chat.id
    abbonamento_sport = abbonamenti_manager.retrieve_abbonamenti({"telegramID": chat_id, "sport": sport})
    active_strategies = [entry["strategia"] for entry in abbonamento_sport]
    emoji_strategies = {strategy: "🔴" for strategy in cst.SPORT_STRATEGIES[sport]}
    for strategy in active_strategies:
        emoji_strategies[strategy] = "🟢"
    strategies_buttons = []
    for strategy in cst.SPORT_STRATEGIES[sport]:
        positive_callback = f"{sport}_{strategy}_activate"
        negative_callback = f"{sport}_{strategy}_disable"
        active_text = f"{cst.STRATEGIES_DISPLAY_NAME[strategy]} SI"
        not_active_text = f"{cst.STRATEGIES_DISPLAY_NAME[strategy]} NO"
        if emoji_strategies[strategy] == "🟢":
            active_text += f" {emoji_strategies[strategy]}"
        else:
            not_active_text += f" {emoji_strategies[strategy]}"
        strategies_buttons.append([
            InlineKeyboardButton(text=active_text, callback_data=positive_callback),
            InlineKeyboardButton(text=not_active_text, callback_data=negative_callback)
        ])
    strategies_buttons.append([InlineKeyboardButton(text="Indietro ↩️", callback_data= "to_sports_menu")])
    return InlineKeyboardMarkup(inline_keyboard=strategies_buttons)
