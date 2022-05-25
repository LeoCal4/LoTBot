from telegram import (InlineKeyboardButton, InlineKeyboardMarkup,
                      KeyboardButton, ReplyKeyboardMarkup, Update)

from lot_bot import constants as cst
from lot_bot.models import sports as spr
from lot_bot.models import strategies as strat
from lot_bot.models import users
from lot_bot.dao import sport_subscriptions_manager, user_manager, budget_manager
from lot_bot import logger as lgr


_startup_buttons = [
    [KeyboardButton(text=cst.BOT_CONFIG_BUTTON_TEXT)],
    [KeyboardButton(text=cst.PAYMENTS_AND_REFERRALS_BUTTON_TEXT)],
    [KeyboardButton(text=cst.USE_GUIDE_BUTTON_TEXT)],
]
STARTUP_REPLY_KEYBOARD = ReplyKeyboardMarkup(keyboard=_startup_buttons, resize_keyboard=True)

_homepage_buttons = [
    [InlineKeyboardButton(text=cst.BOT_CONFIG_BUTTON_TEXT, callback_data="to_bot_config_menu")],
    [InlineKeyboardButton(text=cst.PAYMENTS_AND_REFERRALS_BUTTON_TEXT, callback_data="to_payments_and_referrals_menu")],
    [InlineKeyboardButton(text=cst.USE_GUIDE_BUTTON_TEXT, callback_data="to_use_guide_menu")],
    
]
HOMEPAGE_INLINE_KEYBOARD = InlineKeyboardMarkup(inline_keyboard=_homepage_buttons)

_to_how_work_button = [
    [InlineKeyboardButton(text="Indietro ↩️", callback_data= "to_homepage")]
]
TO_HOW_WORK_KEYBOARD = InlineKeyboardMarkup(inline_keyboard=_to_how_work_button)

# ===================================== FIRST START KEYBOARDS =====================================

_to_first_budget_button = [
    [InlineKeyboardButton(text="Avanti", callback_data= "create_first_budget")]
]
TO_FIRST_BUDGET_KEYBOARD = InlineKeyboardMarkup(inline_keyboard=_to_first_budget_button)

_to_socials_list_button = [
    [InlineKeyboardButton(text="Avanti", callback_data= "send_socials_list")]
]
TO_SOCIALS_LIST_FIRST_START = InlineKeyboardMarkup(inline_keyboard=_to_socials_list_button)

# ===================================== CONFIGURAZIONE BOT MENU =====================================


_bot_configuration_buttons = [
    [InlineKeyboardButton(text="🤾🏽‍♂️  Seleziona Sport 🏟", callback_data="to_sports_menu")],
    [InlineKeyboardButton(text="🏗  Gestione Budget 📈", callback_data="to_budgets_menu")], 
    [InlineKeyboardButton(text="📈  Visualizza report  🧮", callback_data="to_resoconti")],
    [InlineKeyboardButton(text="Indietro ↩️", callback_data= "to_homepage")]
]
BOT_CONFIGURATION_INLINE_KEYBOARD = InlineKeyboardMarkup(inline_keyboard=_bot_configuration_buttons)


# ===================================== CONFIGURAZIONE BOT SUBMENU =====================================


_budget_menu_buttons = [
    [InlineKeyboardButton(text="🔍 Imposta Budget 📊", callback_data="to_set_budget_menu")],
    [InlineKeyboardButton(text="Indietro ↩️", callback_data= "to_bot_config_menu")]
]
BUDGET_MENU_KEYBOARD = InlineKeyboardMarkup(inline_keyboard=_budget_menu_buttons)

_to_budgets_menu_buttons = [
    [InlineKeyboardButton(text="Indietro ↩️", callback_data= "to_budgets_menu")]
]
TO_BUDGETS_MENU_KEYBOARD = InlineKeyboardMarkup(inline_keyboard=_to_budgets_menu_buttons)

_to_budgets_menu_buttons_v2 = [
    [InlineKeyboardButton(text="Torna all' elenco dei budgets ↩️", callback_data= "to_budgets_menu")]
]
TO_BUDGETS_MENU_KEYBOARD_v2 = InlineKeyboardMarkup(inline_keyboard=_to_budgets_menu_buttons_v2)

TO_BUDGETS_MENU_END_CONVERSATION_KEYBOARD = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=f"Torna all'elenco dei budgets ↩️", callback_data= "to_budgets_menu_end_conversation")],])    

_to_resoconti_buttons = [
    [InlineKeyboardButton(text="⛹🏿‍♂️  Ultime 24 Ore 📖", callback_data="resoconto_24_hours")], 
    [InlineKeyboardButton(text="⛹🏿‍♂️  Ultimi 7 Giorni 📖", callback_data="resoconto_7_days")], 
    [InlineKeyboardButton(text="⛹🏿‍♂️  Ultimi 30 Giorni 📖", callback_data="resoconto_30_days")], 
    [InlineKeyboardButton(text="Indietro ↩️", callback_data= "to_bot_config_menu")]
]
RESOCONTI_KEYBOARD = InlineKeyboardMarkup(inline_keyboard=_to_resoconti_buttons)


_register_giocata_buttons = [
    [InlineKeyboardButton(text="SI ✅", callback_data= "register_giocata_yes"),
    InlineKeyboardButton(text="NO ❌", callback_data= "register_giocata_no")],
]
REGISTER_GIOCATA_KEYBOARD = InlineKeyboardMarkup(inline_keyboard=_register_giocata_buttons)


# ===================================== PAGAMENTO E REFERRAL MENU =====================================

_payment_and_referral_buttons = [
    [InlineKeyboardButton(text="🌟  Rinnova Servizio 📶", callback_data="to_service_status")],
    [InlineKeyboardButton(text="🏷  Codice Referral 🔗", callback_data="to_referral")],
    [InlineKeyboardButton(text="Indietro ↩️", callback_data= "to_homepage")],
]
PAYMENT_AND_REFERRAL_MENU_INLINE_KEYBOARD = InlineKeyboardMarkup(inline_keyboard=_payment_and_referral_buttons)


# ===================================== PAGAMENTO E REFERRAL SUBMENU =====================================

service_status_buttons = [
    [InlineKeyboardButton(text="🌟 Prolunga Servizio Bot 🌟", callback_data="to_add_referral")], 
    [InlineKeyboardButton(text="Indietro ↩️", callback_data="to_payments_and_referrals_menu")]
]
SERVICE_STATUS_KEYBOARD = InlineKeyboardMarkup(inline_keyboard=service_status_buttons)


def get_referral_menu_keyboard(number_of_referrals: int = 0) -> InlineKeyboardMarkup:
    _referral_menu_buttons = []
    if number_of_referrals >= 10:
        free_month_button = [InlineKeyboardButton(text="🌟 RISCATTA MESE GRATUITO 🌟", callback_data="to_get_free_month_subscription")]
        _referral_menu_buttons.append(free_month_button)
    _referral_menu_buttons.append(
        [InlineKeyboardButton(text="🪂  Modifica il tuo codice di referral  🎰", callback_data="to_update_personal_ref_code_conversation")]
    )
    _referral_menu_buttons.append(
        [InlineKeyboardButton(text="Indietro ↩️", callback_data= "to_payments_and_referrals_menu")]
    )
    REFERRAL_MENU_KEYBOARD = InlineKeyboardMarkup(inline_keyboard=_referral_menu_buttons)
    return REFERRAL_MENU_KEYBOARD


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
    [InlineKeyboardButton(text="🧮 Come funziona? 📖", callback_data= "to_how_work")],
    [InlineKeyboardButton(text="🧑🏽‍💻 Assistenza 👩🏻‍💼 ", url="https://t.me/LegacyOfTipstersBot")],
    [InlineKeyboardButton(text="🗓  Storico Segnali  🗃", url="t.me/LoT_Tracciabilita")],
    [InlineKeyboardButton(text="Indietro ↩️", callback_data= "to_homepage")],
]
USE_GUIDE_MENU_KEYBOARD = InlineKeyboardMarkup(inline_keyboard=_use_guide_buttons)

# ======================================== GUIDA ALL'USO SUBMENUS =======================================


_social_buttons = [
    [InlineKeyboardButton(text="🙋🏼‍♀️ Community Telegram 🙋🏾", url="https://t.me/LoTVerse")], 
    [InlineKeyboardButton(text="📱 Pagina Instagram IT 🇮🇹 ", url="https://www.instagram.com/lot.verse")], 
    [InlineKeyboardButton(text="📱 Pagina Instagram EU 🇪🇺", url="https://www.instagram.com/lot.official")], 
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

#related to text explanations 
def create_strategies_expl_inline_keyboard(update: Update) -> InlineKeyboardMarkup:
    """Creates the inline keyboard for the strategies of sports,
        user can click on a button to see the explanation of that strategy
    
    The callbacks for this keyboard are in the form:
        text_explanation_<strategy>

    Args:
        update (Update)

    Returns:
        InlineKeyboardMarkup
    """
    chat_id = update.effective_chat.id
    strategies_to_expl_buttons = []

#    for strategy in strat.strategies_container:
#        callback_data = f"text_explanation_{strategy.name}"
#        text = "📖  "+ strategy.display_name +"  📈"
#        strategies_to_expl_buttons.append([
#            InlineKeyboardButton(text=text, callback_data=callback_data)
#        ])

    for i, strategy in enumerate(strat.strategies_container):
        strategy_callback_data = f"text_explanation_{strategy.name}"
        strategy_keyboard_button = InlineKeyboardButton(text="📖  "+ strategy.display_name +"  📈", callback_data=strategy_callback_data)
        if i % 2 == 0:
            strategies_to_expl_buttons.append([strategy_keyboard_button])
        else:
            strategies_to_expl_buttons[(i-1)//2].append(strategy_keyboard_button)
    strategies_to_expl_buttons.append([InlineKeyboardButton(text=f"Indietro ↩️", callback_data= "to_bot_config_menu")])
    return InlineKeyboardMarkup(inline_keyboard=strategies_to_expl_buttons)


def create_budgets_inline_keyboard(update: Update) -> InlineKeyboardMarkup:
    """Creates the inline keyboard listing the user's budgets.
    
    The callbacks of this keyboard are in the form of:
        edit_budget_<nome_budget>
        create_new_budget
        to_budget_menu

    Args:
        update (Update): the Update containing the message sent from the user

    Returns:
        InlineKeyboardMarkup: the aformentioned keyboard
    """

    chat_id = update.effective_chat.id
    # sport_subscriptions = sport_subscriptions_manager.retrieve_sport_subscriptions_from_user_id(chat_id)
    user_data = user_manager.retrieve_user_fields_by_user_id(chat_id,["budgets"])
    budgets = user_data["budgets"]
    budget_names = [entry["budget_name"] for entry in budgets]

    keyboard_budget = []
    for name in budget_names:
        budget_callback_data = f"edit_budget_{name}"
        budget_keyboard_button = InlineKeyboardButton(text=name, callback_data=budget_callback_data)
        keyboard_budget.append([budget_keyboard_button])
    #keyboard_budget.append([InlineKeyboardButton(text=f"Aggiungi budget", callback_data= "create_new_budget"),InlineKeyboardButton(text=f"Indietro ↩️", callback_data= "to_budget_menu")])
    keyboard_budget.append([InlineKeyboardButton(text=f"Indietro ↩️", callback_data= "to_bot_config_menu")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard_budget)

def create_edit_budget_inline_keyboard(update: Update) -> InlineKeyboardMarkup:
    """Creates the inline keyboard to edit the selected budget
    
    The callbacks of this keyboard are in the form of:
        edit_budget_name_<nome_budget>
        edit_budget_balance_<nome_budget>
        delete_budget_<nome_budget>
        to_budget_menu

    Args:
        update (Update): edit_budget_<budget_name>

    Returns:
        InlineKeyboardMarkup: the aformentioned keyboard
    """
    callback_data = update.callback_query.data
    budget_name = callback_data.split("_", 2)[2:][0] # edit_budget_<budget_name> -> <budget_name>
    #TODO2 change every function with this message - also this keyboard
    _edit_budget_buttons = [
    [InlineKeyboardButton(text="Modifica nome", callback_data=f"edit_budget_name_{budget_name}"),InlineKeyboardButton(text="Modifica saldo", callback_data=f"edit_budget_balance_{budget_name}"),InlineKeyboardButton(text="Modifica tipo d'interesse", callback_data=f"edit_budget_interest_{budget_name}")],
    [InlineKeyboardButton(text="Imposta come principale", callback_data= f"set_default_budget_{budget_name}"), InlineKeyboardButton(text="Elimina budget", callback_data= f"pre_delete_budget_{budget_name}")],
    [InlineKeyboardButton(text="Indietro ↩️", callback_data= "to_budgets_menu")]
    ]
    _edit_budget_buttons2 = [
    [InlineKeyboardButton(text="Modifica nome", callback_data=f"edit_budget_name_{budget_name}"),InlineKeyboardButton(text="Modifica saldo", callback_data=f"edit_budget_balance_{budget_name}")],
    [InlineKeyboardButton(text="Indietro ↩️", callback_data= "to_budgets_menu")],
    ]
    EDIT_BUDGET_MENU_KEYBOARD = InlineKeyboardMarkup(inline_keyboard=_edit_budget_buttons2)

    return EDIT_BUDGET_MENU_KEYBOARD

def create_select_budget_interest(user_id, budget_name) -> InlineKeyboardMarkup:
    """Creates the inline keyboard to set interest type of the selected budget
    
    The callbacks of this keyboard are in the form of:
        #TODO add
    Args:
        update (Update): edit_budget_<budget_name>

    Returns:
        InlineKeyboardMarkup: the aformentioned keyboard
    """
    current_interest_type = budget_manager.retrieve_budget_from_name(user_id,budget_name)["interest_type"]
    if current_interest_type == "semplice":
        interesse_semplice_button = InlineKeyboardButton(text="Interesse semplice (attuale)", callback_data=f"do_nothing")
        interesse_composto_button = InlineKeyboardButton(text="Interesse composto", callback_data=f"set_budget_interest_composto_{budget_name}")
    elif current_interest_type == "composto":
        interesse_semplice_button = InlineKeyboardButton(text="Interesse semplice", callback_data=f"set_budget_interest_semplice_{budget_name}")
        interesse_composto_button = InlineKeyboardButton(text="Interesse composto (attuale)", callback_data=f"do_nothing")
    else:
        interesse_semplice_button = InlineKeyboardButton(text="Interesse semplice", callback_data=f"set_budget_interest_semplice_{budget_name}")
        interesse_composto_button = InlineKeyboardButton(text="Interesse composto", callback_data=f"set_budget_interest_composto_{budget_name}")

    _edit_interest_type_buttons = [
    [interesse_semplice_button,interesse_composto_button],
    [InlineKeyboardButton(text="Indietro ↩️", callback_data= "to_budgets_menu")]
    ]
    EDIT_BUDGET_MENU_KEYBOARD = InlineKeyboardMarkup(inline_keyboard=_edit_interest_type_buttons)

    return EDIT_BUDGET_MENU_KEYBOARD