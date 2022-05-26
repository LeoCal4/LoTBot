"""Module containing all the handlers for the budget menu"""

from lot_bot import keyboards as kyb
from lot_bot import logger as lgr
from lot_bot import constants as cst
from lot_bot import config as cfg
from lot_bot import utils
from lot_bot.dao import user_manager, budget_manager
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ConversationHandler
from telegram.ext.dispatcher import CallbackContext
from lot_bot import database as db #TODO creare file tipo budget_manager.py in stile user_manager.py
from typing import Dict

CREATE_BUDGET_NAME, SET_BUDGET_INTEREST, SET_BUDGET_BALANCE = range(3)
EDIT_BUDGET_NAME, EDIT_BUDGET_BALANCE,EDIT_BASE_SIMPLY_INTEREST, DELETE_BUDGET, CONFIRM_DELETE_BUDGET = range(5)
SET_FIRST_BUDGET_BALANCE = 0

def to_budgets_menu(update: Update, context: CallbackContext, send_new: bool = False):
    chat_id = update.effective_user.id
    retrieved_data = user_manager.retrieve_user_fields_by_user_id(chat_id, ["budgets"])
    if not retrieved_data or "budgets" not in retrieved_data:
        context.bot.edit_message_text(
            "ERRORE: utente o budget non trovati",
            chat_id=chat_id,
            message_id=update.callback_query.message.message_id,
            reply_markup=kyb.BUDGET_MENU_KEYBOARD, #imposta budget o torna indietro
        )
        return
    #budget_message = f"<b>I tuoi budget:</b>\n<i>Il tuo budget principale è evidenziato in grassetto, IS è il valore dell'interesse semplice da cui viene calcolato lo stake. "
    #budget_message += f"Questo parametro viene omesso in caso di interesse composto, dato che è pari al valore del budget stesso</i>\n"
    budget_message = "<b>Il tuo budget:</b>\n"
    if not retrieved_data["budgets"]:
        budget_message = f"Nessun budget è stato impostato."
    else:
        for budget in retrieved_data["budgets"]:
            user_budget = int(budget["balance"]) / 100
            #if budget["default"]:
            #    budget_message += "<b>"
            budget_message += f"{budget['budget_name']}: {user_budget:.2f}€" 
            #if budget["interest_type"] == "semplice":
            #    simply_interest_base = int(budget["simply_interest_base"]) / 100
            #    budget_message += " - IS: " + f"{simply_interest_base:.2f}€"
            #if budget["default"]:
            #    budget_message += "</b>" 
                
            budget_message += "\n"

    if not send_new:
        context.bot.edit_message_text(
            budget_message,
            chat_id=chat_id,
            message_id=update.callback_query.message.message_id,
            reply_markup=kyb.create_budgets_inline_keyboard(update), #edit_budget_<name> create_new_budget to_budget_menu
            parse_mode="HTML",
        )
    else:
        context.bot.send_message(
            chat_id,
            budget_message,
            reply_markup=kyb.create_budgets_inline_keyboard(update),
            parse_mode="HTML",
        )
    return ConversationHandler.END

def to_budgets_menu_end_conversation(update: Update, context: CallbackContext, send_new: bool = False):
    to_budgets_menu(update,context)
    return ConversationHandler.END

def create_new_budget(update: Update, context: CallbackContext):
    chat_id = update.callback_query.message.chat_id
    message_id = update.callback_query.message.message_id
    #keyboard = InlineKeyboardMarkup(inline_keyboard=[InlineKeyboardButton(text=f"Indietro ↩️", callback_data= "to_budget_menu")])    
    context.bot.edit_message_text(
        f"Inserisci il nome del nuovo budget, o torna indietro.",
        chat_id=chat_id,
        message_id=message_id,
        reply_markup=kyb.TO_BUDGETS_MENU_KEYBOARD,
        parse_mode="HTML"
    )
    return CREATE_BUDGET_NAME

# For setting a name to a new budget
def received_name_for_new_budget(update: Update, context: CallbackContext) -> int:
    chat_id = update.effective_user.id
    # * check if the budget is valid and get the eventual error
    invalid_budget_name = False
    retry_text = "Il nome del budget non è valido\n"
    try:
        budget_name = update.effective_message.text[:30]
    except:
        invalid_budget_name = True
    #budgets_result = budget_manager.retrieve_budgets_from_user_id(chat_id)
    query_results = budget_manager.retrieve_budget_from_name(chat_id,budget_name)
    #db.mongo.utenti.find_one({ "_id": user_id }, { "budgets": 1 })
    if query_results:
        retry_text += "Un budget con questo nome è gia esistente, scegline un altro";
        invalid_budget_name = True
        #raise Exception("User not found during budget name")
    if invalid_budget_name:
        update.effective_message.reply_text(
            retry_text,
            reply_markup=kyb.TO_BUDGETS_MENU_END_CONVERSATION_KEYBOARD,
        )
        return CREATE_BUDGET_NAME
    context.user_data["budget_name"] = budget_name
    # * send success message
    message_text = f"<b>{budget_name}</b>\nInserisci l'importo"
    update.message.reply_text(
        message_text,
        parse_mode="HTML"
    )
    # * load budget menu
    #to_budget_menu(update, context, send_new=True)
    return SET_BUDGET_BALANCE

#TODO eliminare, in quanto il tipo d'interesse di base è 'semplice'
def received_interest_type_for_new_budget(update: Update, context: CallbackContext) -> int:
    return SET_BUDGET_BALANCE

def received_balance_for_budget(update: Update, context: CallbackContext) -> int:
    '''
    This function can be used to set the balance for a new budget, that will be created here
    or to update the balance of an existing budget.
    '''
    chat_id = update.effective_user.id
    # * check if the budget is valid and get the eventual error
    invalid_budget = False
    # * check if the balance is for a new or existing budget
    budget_name = context.user_data["budget_name"]
    del context.user_data['budget_name']
    is_new_budget = budget_manager.retrieve_budget_from_name(chat_id,budget_name)
    retry_text = "ERRORE: il budget non è valido."
    try:
        new_budget_balance = utils.parse_float_string(update.effective_message.text)
        # * must be positive
        if new_budget_balance <= 0:
             invalid_budget = True
             retry_text += "\nIl budget deve essere maggiore di zero"
    except:
        invalid_budget = True
    if invalid_budget:
        update.effective_message.reply_text(
            retry_text,
            reply_markup=kyb.TO_BUDGETS_MENU_END_CONVERSATION_KEYBOARD,
        )
        if is_new_budget:
            return SET_BUDGET_BALANCE
        else:
            return EDIT_BUDGET_BALANCE
    new_budget_to_int = int(new_budget_balance * 100)


    #if budget_name exists, it means that the user is modifying an existing budget, else he/she is setting a balance for a new budget
    if is_new_budget:
        edit_balance_result = budget_manager.update_budget_balance(chat_id, budget_name, new_budget_to_int)
        if edit_balance_result:
            lgr.logger.debug(f"Budget balance modified - {budget_name=} is now {str(new_budget_to_int)} for {chat_id}")
        message_text = f"Budget aggiornato con successo:\n<b>{budget_name} - {new_budget_balance:.2f}€</b>!"
        update.message.reply_text(
            message_text,
            reply_markup=kyb.TO_BUDGETS_MENU_KEYBOARD_v2,
            parse_mode="HTML"
        )
    else:
        if not budget_manager.retrieve_budgets_from_user_id(chat_id): 
            is_default = True
        else:
            is_default = False
        budget_data = {"budget_name": budget_name, "balance": new_budget_to_int, "default":is_default, "interest_type":"semplice","simply_interest_base":new_budget_to_int}
        add_budget_result = budget_manager.add_new_budget(chat_id,budget_data) 
        if add_budget_result:
            lgr.logger.debug(f"Budget added - {str(budget_data)} for {chat_id}")
        # * send success message
        message_text = f"Budget creato con successo:\n<b>{budget_name} - {new_budget_balance:.2f}€</b>!"
        update.message.reply_text(
            message_text,
            reply_markup=kyb.TO_BUDGETS_MENU_KEYBOARD_v2,
            parse_mode="HTML"
        )
    return ConversationHandler.END

def set_budget_interest_semplice(update: Update, context: CallbackContext):
    chat_id = update.callback_query.message.chat_id
    budget_name = update.callback_query.data.split("_", 4)[4:][0] # set_budget_interest_semplice_<budget_name> -> <budget_name>
    context.user_data["budget_name"] = budget_name
    context.bot.edit_message_text(
        "Inserisci l'importo che verrà considerato come base, oppure torna indietro", #TODO modificare
        chat_id=chat_id,
        message_id=update.callback_query.message.message_id,
        reply_markup=kyb.TO_BUDGETS_MENU_END_CONVERSATION_KEYBOARD,
        parse_mode="HTML"
    )
    return EDIT_BASE_SIMPLY_INTEREST

# Menu for editing the selected budget
def edit_budget(update: Update, context: CallbackContext) -> int:
    '''Callback for this: edit_budget_<budget_name>'''
    chat_id = update.callback_query.message.chat_id
    budget_name = update.callback_query.data.split("_", 2)[2:][0] # edit_budget_<budget_name> -> <budget_name>
    budget_query_result =  db.mongo.utenti.find_one({"_id":chat_id, "budgets.budget_name": budget_name}, {'budgets.$': 1})
    if not budget_query_result:
        retry_text = "ERRORE: Budget non trovato\nInfo: potrebbe essere stato eliminato di recente"
        #raise Exception("User not found during budget name")
        context.bot.edit_message_text(
            retry_text,
            chat_id=chat_id,
            message_id=update.callback_query.message.message_id,
            reply_markup=kyb.create_budgets_inline_keyboard(update),
            parse_mode="HTML"
        )
        return ConversationHandler.END
    # * send success message
    balance = int(budget_query_result["budgets"][0]["balance"]) / 100
    message_text = f"<b>{budget_name} - {balance:.2f}€</b>\nCosa vuoi fare?"
    context.bot.edit_message_text(
        message_text,
        chat_id=chat_id,
        message_id=update.callback_query.message.message_id,
        reply_markup=kyb.create_edit_budget_inline_keyboard(update),
        parse_mode="HTML"
    )

def edit_budget_name(update: Update, context: CallbackContext):
    chat_id = update.callback_query.message.chat_id
    message_id = update.callback_query.message.message_id
    budget_name = update.callback_query.data.split("_", 3)[3:][0] # edit_budget_name_<budget_name> -> <budget_name>
    context.user_data["budget_name"] = budget_name #storing the old budget_name that will be modified
    #TODO  forse modificare keyboard
    context.bot.edit_message_text(
        f"Budget: <b>{budget_name}</b>\nInserisci il nuovo nome per il budget, o torna indietro.",
        chat_id=chat_id,
        message_id=message_id,
        reply_markup= kyb.TO_BUDGETS_MENU_END_CONVERSATION_KEYBOARD,
        parse_mode="HTML"
    )
    return EDIT_BUDGET_NAME

def edit_budget_interest_menu(update: Update, context: CallbackContext):  
    '''Callback for this: edit_budget_interest_<budget_name>''' 
    chat_id = update.callback_query.message.chat_id
    message_id = update.callback_query.message.message_id
    lgr.logger.debug(update.callback_query.data)
    budget_name = update.callback_query.data.split("_", 3)[3:][0] # edit_budget_interest_<budget_name> -> <budget_name>
    #keyboard = InlineKeyboardMarkup(inline_keyboard=[InlineKeyboardButton(text=f"Indietro ↩️", callback_data= "to_budget_menu")])    
    context.bot.edit_message_text(
        f"Budget: <b>{budget_name}</b>\nInserisci il tipo d'interesse",
        chat_id=chat_id,
        message_id=message_id,
        reply_markup=kyb.create_select_budget_interest(chat_id,budget_name),
        parse_mode="HTML"
    )

def set_budget_interest_composto(update: Update, context: CallbackContext):  
    '''Callback for this: set_budget_interest_composto_<budget_name>''' 
    chat_id = update.callback_query.message.chat_id
    message_id = update.callback_query.message.message_id
    budget_name = update.callback_query.data.split("_",4)[4:][0]
    interest_type = update.callback_query.data.split("_")[3]
    result = budget_manager.update_budget_data(chat_id,budget_name,{"interest_type":"composto"} )
    if result:
        text = f"<b>{budget_name}</b>\nIl budget ha ora un tipo d'interesse composto"
    else:
        text = f"Errore: interesse budget non modificato <b>{budget_name}</b>\n"
    context.bot.edit_message_text(
        text,
        chat_id=chat_id,
        message_id=message_id,
        parse_mode="HTML"
    )
    to_budgets_menu(update, context, send_new=True)


def edit_budget_balance(update: Update, context: CallbackContext):   
    chat_id = update.callback_query.message.chat_id
    message_id = update.callback_query.message.message_id
    budget_name = update.callback_query.data.split("_", 3)[3:][0] # edit_budget_balance_<budget_name> -> <budget_name>
    context.user_data["budget_name"] = budget_name #storing the budget_name that will be modified
    #keyboard = InlineKeyboardMarkup(inline_keyboard=[InlineKeyboardButton(text=f"Indietro ↩️", callback_data= "to_budget_menu")])    
    context.bot.edit_message_text(
        f"Budget: <b>{budget_name}</b>\nInserisci il nuovo importo per il budget, o torna indietro.",
        chat_id=chat_id,
        message_id=message_id,
        reply_markup=kyb.TO_BUDGETS_MENU_END_CONVERSATION_KEYBOARD,
        parse_mode="HTML"
    )
    return EDIT_BUDGET_BALANCE

def received_name_for_existing_budget(update: Update, context: CallbackContext) -> int:
    chat_id = update.effective_user.id
    # * check if the budget is valid and get the eventual error
    invalid_budget_name = False
    retry_text = "Il nome del budget non è valido\n"
    try:
        new_budget_name = update.effective_message.text[:30]
    except:
        invalid_budget_name = True

    #searching if a budget with this new name already exists
    #budgets_result = retrieve_budgets_from_user_id(chat_id) - TODO forse conviene creare una funzione di questo tipo
    query_results = db.mongo.utenti.find_one({"_id":chat_id, "budgets" : { "$elemMatch": { "budget_name": new_budget_name } } })#db.mongo.utenti.find_one({ "_id": user_id }, { "budgets": 1 })
    lgr.logger.debug("I RISULTATI SONO:")
    lgr.logger.debug(str(query_results))
    if query_results:
        retry_text += "Un budget con questo nome è gia esistente, scegline un altro";
        invalid_budget_name = True
        #raise Exception("User not found during budget name")
    if invalid_budget_name:
        update.effective_message.reply_text(
            retry_text,
            reply_markup=kyb.TO_BUDGETS_MENU_END_CONVERSATION_KEYBOARD,
        )
        return EDIT_BUDGET_NAME
    old_budget_name = context.user_data["budget_name"]
    if "budget_name" in context.user_data:
        del context.user_data["budget_name"]

    #db.mongo.utenti.update_one({"_id":chat_id, "budgets" : { "$elemMatch": { "budget_name": old_budget_name } } }, {"$set":{"budget_name":new_budget_name}})
    update_result = budget_manager.update_budget_data(chat_id,old_budget_name,{"budget_name":new_budget_name})
    if not update_result:
        context.bot.send_message(
            user_chat_id,
            "Non siamo riusciti ad aggiornare il nome del budget, riprova più tardi",
            reply_markup=kyb.TO_BUDGETS_MENU_KEYBOARD
        )
    else:
        message_text = f"Correttamente modificato il nome di <b>{old_budget_name}</b> in <b>{new_budget_name}</b>"
        update.message.reply_text(
            message_text,
            reply_markup=kyb.TO_BUDGETS_MENU_KEYBOARD,
            parse_mode="HTML"
        )
    # * load budget menu
    #to_budget_menu(update, context, send_new=True)
    return ConversationHandler.END

#TODO da finire di scrivere
def received_base_interest_semplice(update: Update, context: CallbackContext) -> int:
    '''
    This function can be used to set the base balance for a budget with simply interest
    '''
    chat_id = update.effective_user.id
    budget_name = context.user_data["budget_name"]
    del context.user_data['budget_name']
    # * check if the budget is valid and get the eventual error
    invalid_budget = False
    retry_text = "ERRORE: l'importo inserito non è valido."
    try:
        new_value = utils.parse_float_string(update.effective_message.text)
        if new_value <= 0:
             invalid_budget = True
             retry_text += "\nIl valore deve essere maggiore di zero"
    except:
        invalid_budget = True

    if invalid_budget:
        update.effective_message.reply_text(
            retry_text,
            reply_markup=kyb.TO_BUDGETS_MENU_END_CONVERSATION_KEYBOARD,
        )
        return EDIT_BASE_SIMPLY_INTEREST
    new_budget_to_int = int(new_value * 100)

    #if budget_name exists, it means that the user is modifying an existing budget, else he/she is setting a balance for a new budget
    result = budget_manager.update_budget_data(chat_id, budget_name, {"interest_type":"semplice","simply_interest_base":new_budget_to_int})

    if result:
        lgr.logger.debug(f"Budget balance of simply interest - {budget_name=} is now {str(new_budget_to_int)} for {chat_id}")
        message_text = f"Il valore da cui verrà calcolato lo stake per il budget <b>{budget_name} è ora pari a {new_value:.2f}€</b>!"
        update.message.reply_text(
            message_text,
            parse_mode="HTML"
        )
    else:
        lgr.logger.error(f"Error in setting budget balance of simply interest - {budget_name=} is now {str(new_budget_to_int)} for {chat_id}")
        # * send success message
        message_text = f"Abbiamo riscontrato un errore durante la modifica dell'interesse base per il budget <b>{budget_name}</b>!"
        update.message.reply_text(
            message_text,
            reply_markup=kyb.TO_BUDGETS_MENU_KEYBOARD_v2,
            parse_mode="HTML"
        )
    to_budgets_menu(update,context,send_new=True)
    return ConversationHandler.END

def set_default_budget(update: Update, context: CallbackContext) -> int:
    '''
    Callback: set_default_budget_<budget_name>

    Set the budget <budget_name> as the default one.
    If there is already a default budget, it becomes a normal one and <budget_name> becomes default
    Does nothing if <budget_name> already is default
    '''
    chat_id = update.effective_user.id
    message_id = update.callback_query.message.message_id
    current_default_budget = budget_manager.retrieve_default_budget_from_user_id(chat_id)
    new_default_budget_name = update.callback_query.data.split("_", 3)[3:][0]
    if current_default_budget: 
        current_default_budget_name = current_default_budget["budget_name"]
        if current_default_budget_name == new_default_budget_name:
            context.bot.edit_message_text(
            f"<b>{new_default_budget_name}</b> è già impostato come budget principale",
            chat_id=chat_id,
            message_id=message_id,
            parse_mode="HTML"
        )
        else:
            budget_manager.update_budget_data(chat_id,current_default_budget_name,{"default":False} )
            budget_manager.update_budget_data(chat_id,new_default_budget_name,{"default":True} )
            context.bot.edit_message_text(
            f"<b>{new_default_budget_name}</b> è stato impostato come budget principale sostituendo {current_default_budget_name}",
            chat_id=chat_id,
            message_id=message_id,
            parse_mode="HTML"
        )
    else:
        budget_manager.update_budget_data(chat_id,new_default_budget_name,{"default":True} )
        context.bot.edit_message_text(
            f"<b>{new_default_budget_name}</b> è stato impostato come budget principale",
            chat_id=chat_id,
            message_id=message_id,
            parse_mode="HTML"
        )
    # * load budget menu
    to_budgets_menu(update, context, send_new=True)

def pre_delete_budget(update: Update, context: CallbackContext) -> int:
    '''
    Callback: pre_delete_budget_<budget_name>

    Ask user if wants to delete the budget with <budget_name>.

    TODO valutare se aggiungere un controllo per evitare di cancellare il budget se è l'unico che l'utente ha, 
         e forse evitare anche di cancellare il budget di default
    '''
    chat_id = update.effective_user.id
    message_id = update.callback_query.message.message_id 
    #current_default_budget = budget_manager.retrieve_default_budget_from_user_id(chat_id)
    #user_budgets = budget_manager.retrieve_budgets_from_user_id(chat_id)
    budget_to_delete = update.callback_query.data.split("_", 3)[3:][0]
    #considerare di far apparire anche il saldo del budget oltre al nome 
    #budget_to_delete_balance = budget_manager.retrieve_budget_from_name(chat_id,budget_to_delete)
    _pre_delete_budget_buttons = [
    [InlineKeyboardButton(text="Conferma", callback_data="delete_budget_"+budget_to_delete)],
    [InlineKeyboardButton(text="Indietro ↩️", callback_data= "to_budgets_menu")]
    ]
    PRE_DELETE_BUDGET_KEYBOARD = InlineKeyboardMarkup(inline_keyboard=_pre_delete_budget_buttons)
    context.bot.edit_message_text(
    f"<b>{budget_to_delete}</b>\nConfermi di voler eliminare questo budget? ",
    chat_id=chat_id,
    message_id=message_id,
    reply_markup = PRE_DELETE_BUDGET_KEYBOARD,
    parse_mode="HTML"
    )

def delete_budget(update: Update, context: CallbackContext) -> int:
    '''
    Callback: delete_budget_<budget_name>

    Delete budget with <budget_name>.
    '''
    chat_id = update.effective_user.id
    message_id = update.callback_query.message.message_id 
    #current_default_budget = budget_manager.retrieve_default_budget_from_user_id(chat_id)
    budget_to_delete = update.callback_query.data.split("_", 2)[2:][0]
    result = budget_manager.delete_budget(chat_id,budget_to_delete)
    if result: 
        context.bot.edit_message_text(
        f"<b>{budget_to_delete}</b> eliminato con successo.",
        chat_id=chat_id,
        message_id=message_id,
        parse_mode="HTML"
    )
    else:
        context.bot.edit_message_text(
        f"Non è stato possibile eliminare <b>{new_default_budget_name}</b> a causa di un errore, riprova più tardi o contatta l' <a href='https://t.me/LegacyOfTipstersBot'>assistenza</a>",
        chat_id=chat_id,
        message_id=message_id,
        parse_mode="HTML"
    )
    # * load budget menu
    to_budgets_menu(update, context, send_new=True)

def to_budget_menu(update: Update, context: CallbackContext):
    chat_id = update.callback_query.message.chat_id
    message_id = update.callback_query.message.message_id
    context.bot.edit_message_text(
        f"Scegli il budget che vuoi modificare o creane un altro",
        chat_id=chat_id,
        message_id=message_id,
        reply_markup=kyb.create_budgets_inline_keyboard(update),
        parse_mode="HTML"
    )
    return MODIFY_OR_CREATE_BUDGET

def create_first_budget(update: Update, context: CallbackContext):
    chat_id = update.callback_query.message.chat_id
    message_id = update.callback_query.message.message_id
    reply_text = """Ottimo, adesso <b>impostiamo il tuo primo Budget 💰 ! </b> 
 
<i>Questo ti permetterà di ricevere gli eventi con il <b>suggerito stake* massimo in % e euro!</b> 
 
(*stake: porzione di capitale che si investe in un mercato) 
 
PS: potrai modificarlo in un secondo momento ! </i> 
 
Quando vuoi <b>invia</b> il tuo budget (es: scrivi "87,25" senza virgolette)👇👇"""

    context.bot.send_message(
    chat_id = cfg.config.NEW_USERS_CHANNEL_ID,
    text= f"L'utente con id: {chat_id} ha premuto su 'Avanti' dopo il messaggio di benvenuto"
)

    update.effective_message.reply_text(
    reply_text,
    parse_mode="HTML"
    ) 
    return SET_FIRST_BUDGET_BALANCE

def received_balance_for_first_budget(update: Update, context: CallbackContext) -> int:
    chat_id = update.effective_user.id
    # * check if the budget is valid and get the eventual error
    invalid_budget = False
    retry_text = "ERRORE: l'importo inserito non è valido."
    try:
        new_budget_balance = utils.parse_float_string(update.effective_message.text)
        # * must be positive
        if new_budget_balance <= 0:
             invalid_budget = True
             retry_text += "\nIl budget deve essere maggiore di zero"
    except:
        invalid_budget = True
    if invalid_budget:
        lgr.logger.error("Invalid budget error")
        update.effective_message.reply_text(
            retry_text
        )
        return SET_FIRST_BUDGET_BALANCE
    budget_name = cst.FIRST_BUDGET_NAME
    new_budget_to_int = int(new_budget_balance * 100)
    is_default = True
    budget_data = {"budget_name": budget_name, "balance": new_budget_to_int, "default":is_default, "interest_type":"semplice","simply_interest_base":new_budget_to_int}
    # * update user budget
    add_budget_result = budget_manager.add_new_budget(chat_id,budget_data) 
    if add_budget_result:
        lgr.logger.debug(f"Budget added - {str(budget_data)} for {chat_id}")
    # * send success message
    message_text = f"""Budget creato con successo:\n<b>{budget_name} - {new_budget_balance:.2f}€</b>! 

<b>Ben fatto ! </b>🔥
""" #TODO add tutorial Guarda questo <b>breve tutorial su come funziono</b> e poi possiamo iniziare! 🎉
    update.message.reply_text(
        message_text,
        reply_markup=kyb.TO_SOCIALS_LIST_FIRST_START,
        parse_mode="HTML"
    )
    # file_id = 123
    #context.bot.send_video(
    #    chat_id,
    #    file_id,
    #    caption=message_text
    #    )

    context.bot.send_message(
    chat_id = cfg.config.NEW_USERS_CHANNEL_ID, 
    text= f"L'utente con id: {chat_id} ha impostato il primo budget"
)

    return ConversationHandler.END
