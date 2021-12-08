from telegram import (InlineKeyboardButton, InlineKeyboardMarkup,
                      KeyboardButton, ReplyKeyboardMarkup, Update)

from lot_bot import constants as cst
from lot_bot.models import sports as spr
from lot_bot.models import users
from lot_bot.dao import sport_subscriptions_manager
from lot_bot import logger as lgr


_startup_buttons = [
    [KeyboardButton(text=cst.BOT_CONFIG_BUTTON_TEXT)],
    [KeyboardButton(text=cst.EXPERIENCE_BUTTON_TEXT)],
    [KeyboardButton(text=cst.USE_GUIDE_BUTTON_TEXT)],
]
STARTUP_REPLY_KEYBOARD = ReplyKeyboardMarkup(keyboard=_startup_buttons, resize_keyboard=True)


_homepage_buttons = [
    [InlineKeyboardButton(text=cst.BOT_CONFIG_BUTTON_TEXT, callback_data="to_bot_config_menu")],
    [InlineKeyboardButton(text=cst.EXPERIENCE_BUTTON_TEXT, callback_data="to_experience_menu")],
    [InlineKeyboardButton(text=cst.USE_GUIDE_BUTTON_TEXT, callback_data="to_use_guide_menu")],
    
]
HOMEPAGE_INLINE_KEYBOARD = InlineKeyboardMarkup(inline_keyboard=_homepage_buttons)

# ===================================== CONFIGURAZIONE BOT MENU =====================================


_bot_configuration_buttons = [
    [InlineKeyboardButton(text="🤾🏽‍♂️  Seleziona Sport 🏟", callback_data="to_sports_menu")],
    [InlineKeyboardButton(text="📖  Spiegazione Strategie (IN ARRIVO) 🧭", callback_data="new")], # to_explanation_menu
    [InlineKeyboardButton(text="🏗  Gestione Budget 📈", callback_data="to_gestione_budget_menu")], 
    [InlineKeyboardButton(text="🌟  Status Servizio 📶", callback_data="to_service_status")],
    [InlineKeyboardButton(text="Indietro ↩️", callback_data= "to_homepage")]
]
BOT_CONFIGURATION_INLINE_KEYBOARD = InlineKeyboardMarkup(inline_keyboard=_bot_configuration_buttons)


# ===================================== CONFIGURAZIONE BOT SUBMENU =====================================

_explanation_test_buttons = [
    [InlineKeyboardButton(text="⛹🏿‍♂️  Singola  📖", callback_data="explanation_singola")], 
    [InlineKeyboardButton(text="⛹🏿‍♂️  Multiple 📖", callback_data="explanation_multiple")], 
    [InlineKeyboardButton(text="Indietro ↩️", callback_data= "to_bot_config_menu")]
]
EXPLANATION_TEST_INLINE_KEYBOARD = InlineKeyboardMarkup(inline_keyboard=_explanation_test_buttons)

_gestione_budget_buttons = [
    [InlineKeyboardButton(text="📈  I miei report  🧮", callback_data="to_resoconti")],
    [InlineKeyboardButton(text="🔍  Le mie statistiche  📊 (IN ARRIVO)", callback_data="new")],
    [InlineKeyboardButton(text="Indietro ↩️", callback_data= "to_bot_config_menu")]
]
GESTIONE_BUDGET_MENU_KEYBOARD = InlineKeyboardMarkup(inline_keyboard=_gestione_budget_buttons)

_to_resoconti_buttons = [
    [InlineKeyboardButton(text="⛹🏿‍♂️  Ultime 24 Ore 📖", callback_data="resoconto_24_hours")], 
    [InlineKeyboardButton(text="⛹🏿‍♂️  Ultimi 7 Giorni 📖", callback_data="resoconto_7_days")], 
    [InlineKeyboardButton(text="⛹🏿‍♂️  Ultimi 30 Giorni 📖", callback_data="resoconto_30_days")], 
    [InlineKeyboardButton(text="Indietro ↩️", callback_data= "to_bot_config_menu")]
]
RESOCONTI_KEYBOARD = InlineKeyboardMarkup(inline_keyboard=_to_resoconti_buttons)


_register_giocata_buttons = [
    [InlineKeyboardButton(text="Sì", callback_data= "register_giocata_yes")],
    [InlineKeyboardButton(text="No", callback_data= "register_giocata_no")],
]
REGISTER_GIOCATA_KEYBOARD = InlineKeyboardMarkup(inline_keyboard=_register_giocata_buttons)


service_status_buttons = [
    [InlineKeyboardButton(text="🌟 Rinnovo Abbonamento (IN ARRIVO) 🌟", callback_data="to_add_referral")], 
    [InlineKeyboardButton(text="Indietro ↩️", callback_data= "to_bot_config_menu")]
]
SERVICE_STATUS_KEYBOARD = InlineKeyboardMarkup(inline_keyboard=service_status_buttons)

# ===================================== GESTIONE ESPERIENZA MENU =====================================

_experience_buttons = [
    [InlineKeyboardButton(text="🧑🏽‍💻 Assistenza 👩🏻‍💼 ", url="https://t.me/LegacyOfTipstersBot")],
    # [InlineKeyboardButton(text="👨🏼‍🏫  Formazione e Lezioni  📋 (IN ARRIVO)", callback_data="new")],
    [InlineKeyboardButton(text="🏷  Codice Referral 🔗", callback_data="to_referral")],
    # [InlineKeyboardButton(text="🪂  Supporto Gioco Compulsivo  🎰 (IN ARRIVO)", callback_data="new")],
    [InlineKeyboardButton(text="🗓  Tracciabilità LoT  🗃", url="t.me/LoT_Tracciabilita")],
    [InlineKeyboardButton(text="Indietro ↩️", callback_data= "to_homepage")],
]
EXPERIENCE_MENU_INLINE_KEYBOARD = InlineKeyboardMarkup(inline_keyboard=_experience_buttons)


# ===================================== GESTIONE ESPERIENZA SUBMENU =====================================


_referral_menu_buttons = [
    [InlineKeyboardButton(text="🪂  Modifica il tuo codice di referral  🎰", callback_data="to_update_personal_ref_code_conversation")],
    [InlineKeyboardButton(text="🪂  Collega un codice di referral  🎰", callback_data="to_update_linked_ref_code_conversation")],
    [InlineKeyboardButton(text="Indietro ↩️", callback_data= "to_experience_menu")]
]
REFERRAL_MENU_KEYBOARD = InlineKeyboardMarkup(inline_keyboard=_referral_menu_buttons)

_back_to_ref_code_menu_buttons = [
    [InlineKeyboardButton(text="Indietro ↩️", callback_data= "to_ref_code_menu_from_referral")],
]
BACK_TO_REF_CODE_MENU_KEYBOARD = InlineKeyboardMarkup(inline_keyboard=_back_to_ref_code_menu_buttons)

# ===================================== STATUS SERVIZIO SUBMENUS =====================================

_proceed_to_payments_buttons = [
    [InlineKeyboardButton(text="Procedi al pagamento", callback_data= "to_payments")],
    [InlineKeyboardButton(text="Indietro ↩️", callback_data= "to_homepage_from_referral")]
]
PROCEED_TO_PAYMENTS_KEYBOARD = InlineKeyboardMarkup(inline_keyboard=_proceed_to_payments_buttons)

# ======================================== GUIDA ALL'USO MENU =======================================

_use_guide_buttons = [
    [InlineKeyboardButton(text="🧮 Come funziona? (IN ARRIVO) 📖", callback_data= "new")],
    [InlineKeyboardButton(text="❔ F.A.Q. (IN ARRIVO) ❔", callback_data= "new")],
    [InlineKeyboardButton(text="📱  Social  🌐", callback_data="to_social_menu")],
    [InlineKeyboardButton(text="Indietro ↩️", callback_data= "to_homepage")],
]
USE_GUIDE_MENU_KEYBOARD = InlineKeyboardMarkup(inline_keyboard=_use_guide_buttons)

# ======================================== GUIDA ALL'USO SUBMENUS =======================================


_social_buttons = [
    [InlineKeyboardButton(text="🙋🏼‍♀️ Community Telegram 🙋🏾", url="https://t.me/LoTVerse")], 
    [InlineKeyboardButton(text="💻 Pagina Instagram 📱", url="https://www.instagram.com/lot.official")], 
    [InlineKeyboardButton(text="Indietro ↩️", callback_data= "to_use_guide_menu")]
]
SOCIAL_MENU_INLINE_KEYBOARD = InlineKeyboardMarkup(inline_keyboard=_social_buttons)




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
    # sport_subscriptions = sport_subscriptions_manager.retrieve_sport_subscriptions_from_user_id(chat_id)
    user_data = sport_subscriptions_manager.retrieve_subs_from_user_id(chat_id)
    sport_subscriptions = user_data["sport_subscriptions"]
    available_sports = users.get_user_available_sports_names_from_subscriptions(user_data["subscriptions"])
    subscribed_sports = [entry["sport"].lower() for entry in sport_subscriptions]
    sports_in_menu = [sport for sport in spr.sports_container if sport.show_in_menu]
    if available_sports == []:
        emoji_sport = {sport.name: "🔴" for sport in sports_in_menu}
    else:
        emoji_sport = {sport.name: "🔴" if sport.name in available_sports else "🔒" for sport in sports_in_menu}
    for sport in subscribed_sports:
        emoji_sport[sport] = "🟢"
    sport_menu_entries = [
        emoji_sport[sport.name] + " " + sport.display_name 
        for sport in sports_in_menu
    ]
    inline_buttons = {
        sport.name: entry 
        for sport, entry in zip(sports_in_menu, sport_menu_entries) 
    }
    keyboard_sport = []
    for i, sport in enumerate(sports_in_menu):
        sport_callback_data = f"sport_{sport.name}" if emoji_sport[sport.name] != "🔒" else "new"
        sport_keyboard_button = InlineKeyboardButton(text=inline_buttons[sport.name], callback_data=sport_callback_data)
        if i % 2 == 0:
            keyboard_sport.append([sport_keyboard_button])
        else:
            keyboard_sport[(i-1)//2].append(sport_keyboard_button)
    keyboard_sport.append([InlineKeyboardButton(text=f"Indietro ↩️", callback_data= "to_bot_config_menu")])
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
    active_strategies = sport_subscriptions_manager.retrieve_subscribed_strats_from_user_id_and_sport(chat_id, sport.name)
    lgr.logger.debug(f"User active strategies: {active_strategies=}")
    emoji_strategies = {strategy.name: "🔴" for strategy in sport.strategies}
    for strategy in active_strategies:
        emoji_strategies[strategy] = "🟢"
    strategies_buttons = []
    for strategy in sport.strategies:
        positive_callback = f"{sport.name}_{strategy.name}_activate"
        negative_callback = f"{sport.name}_{strategy.name}_disable"
        active_text = ""
        not_active_text = ""
        if emoji_strategies[strategy.name] == "🟢":
            active_text += f"{emoji_strategies[strategy.name]} "
        else:
            not_active_text += f"{emoji_strategies[strategy.name]} "
        active_text += f"{strategy.display_name} SI"
        not_active_text += f"{strategy.display_name} NO"

        strategies_buttons.append([
            InlineKeyboardButton(text=active_text, callback_data=positive_callback),
            InlineKeyboardButton(text=not_active_text, callback_data=negative_callback)
        ])
    strategies_buttons.append([InlineKeyboardButton(text="Indietro ↩️", callback_data= "to_sports_menu")])
    return InlineKeyboardMarkup(inline_keyboard=strategies_buttons)
