from telegram import (InlineKeyboardButton, InlineKeyboardMarkup,
                      KeyboardButton, ReplyKeyboardMarkup, Update)

from lot_bot import constants as cst
from lot_bot.models import sports as spr
from lot_bot.dao import abbonamenti_manager

_startup_buttons = [
    [KeyboardButton(text=cst.HOMEPAGE_BUTTON_TEXT)],
    [KeyboardButton(text=cst.COMMUNITY_BUTTON_TEXT)],
    [KeyboardButton(text=cst.ASSISTANCE_BUTTON_TEXT)],
]
STARTUP_REPLY_KEYBOARD = ReplyKeyboardMarkup(keyboard=_startup_buttons, resize_keyboard=True)


_homepage_buttons = [
    [InlineKeyboardButton(text="⛹🏿‍♂️  Sport  📖", callback_data="to_sports_menu")], 
    [InlineKeyboardButton(text="⛹🏿‍♂️  Spiegazione Strategie  📖", callback_data="to_explanation_menu")], 
    [InlineKeyboardButton(text="⛹🏿‍♂️ Test pagamenti  📖", callback_data="to_add_referral")], 
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
    [InlineKeyboardButton(text="📉 Tracciabilità Produzione LoT +24h 📉 ", url="t.me/LoT_Tracciabilita")],
    [InlineKeyboardButton(text="📊 Report e Rendimenti 📊 ", url = "t.me/LoT_ReportGiornalieri")],
    [InlineKeyboardButton(text="📱 Pagina Instagram 📱 ", url="https://www.instagram.com/lot.official")],
    [InlineKeyboardButton(text="Indietro ↩️", callback_data= "to_homepage")]
]
USEFUL_LINKS_INLINE_KEYBOARD = InlineKeyboardMarkup(inline_keyboard=_useful_links_buttons, resize_keyboard=True)


_assistance_buttons = [
    [InlineKeyboardButton(text="Premi qui", url="https://t.me/LegacyOfTipstersBot")],
]
ASSISTANCE_KEYBOARD = InlineKeyboardMarkup(inline_keyboard=_assistance_buttons)

_register_giocata_buttons = [
    [InlineKeyboardButton(text="Sì", callback_data= "register_giocata_yes")],
    [InlineKeyboardButton(text="No", callback_data= "register_giocata_no")],
]
REGISTER_GIOCATA_KEYBOARD = InlineKeyboardMarkup(inline_keyboard=_register_giocata_buttons)

_proceed_to_payments_buttons = [
    [InlineKeyboardButton(text="Procedi al pagamento", callback_data= "to_payments")],
    [InlineKeyboardButton(text="Indietro ↩️", callback_data= "to_homepage_from_referral")]
]
PROCEED_TO_PAYMENTS_KEYBOARD = InlineKeyboardMarkup(inline_keyboard=_proceed_to_payments_buttons)

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
    emoji_sport = {sport.name: "🔴" for sport in spr.sports_container if sport.show_in_menu}
    for sport in sport_attivi:
        emoji_sport[sport] = "🟢"
    SPORT_STRING_MENU_LEN = 19
    # ljust appends " " at the end of the string, until the specified length is reached
    # capitalize makes the first letter uppercase and the rest lowercase
    # TODO try without ljust
    sport_menu_entries = [
        sport.display_name.ljust(SPORT_STRING_MENU_LEN) + emoji_sport[sport.name] 
        for sport in spr.sports_container 
        if sport.show_in_menu
    ]
    inline_buttons = {
        sport.name: entry 
        for sport, entry in zip(spr.sports_container, sport_menu_entries) 
        if sport.show_in_menu
    }
    keyboard_sport = []
    for i, sport in enumerate(spr.sports_container):
        if not sport.show_in_menu:
            continue
        sport_keyboard_button = InlineKeyboardButton(text=inline_buttons[sport.name], callback_data=f"sport_{sport.name}")
        if i % 2 == 0:
            keyboard_sport.append([sport_keyboard_button])
        else:
            keyboard_sport[(i-1)//2].append(sport_keyboard_button)
    keyboard_sport.append([InlineKeyboardButton(text=f"Indietro ↩️", callback_data= "to_homepage")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard_sport)
     


def create_strategies_inline_keyboard(update: Update, sport: spr.Sport) -> InlineKeyboardMarkup:
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
    abbonamento_sport = abbonamenti_manager.retrieve_abbonamenti({"telegramID": chat_id, "sport": sport.name})
    active_strategies = [entry["strategia"] for entry in abbonamento_sport]
    emoji_strategies = {strategy.name: "🔴" for strategy in sport.strategies}
    for strategy in active_strategies:
        emoji_strategies[strategy] = "🟢"
    strategies_buttons = []
    for strategy in sport.strategies:
        positive_callback = f"{sport.name}_{strategy.name}_activate"
        negative_callback = f"{sport.name}_{strategy.name}_disable"
        active_text = f"{strategy.display_name} SI"
        not_active_text = f"{strategy.display_name} NO"
        if emoji_strategies[strategy.name] == "🟢":
            active_text += f" {emoji_strategies[strategy.name]}"
        else:
            not_active_text += f" {emoji_strategies[strategy.name]}"
        strategies_buttons.append([
            InlineKeyboardButton(text=active_text, callback_data=positive_callback),
            InlineKeyboardButton(text=not_active_text, callback_data=negative_callback)
        ])
    strategies_buttons.append([InlineKeyboardButton(text="Indietro ↩️", callback_data= "to_sports_menu")])
    return InlineKeyboardMarkup(inline_keyboard=strategies_buttons)
