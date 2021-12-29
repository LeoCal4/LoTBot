"""Module containing all the handlers for the budget menu"""

from lot_bot import keyboards as kyb
from lot_bot import logger as lgr
from lot_bot import utils
from lot_bot.dao import user_manager
from telegram import Update
from telegram.ext import ConversationHandler
from telegram.ext.dispatcher import CallbackContext

SET_BUDGET = 0


def to_budget_menu(update: Update, context: CallbackContext, send_new: bool = False):
    chat_id = update.effective_user.id
    retrieved_data = user_manager.retrieve_user_fields_by_user_id(chat_id, ["budget"])
    if not retrieved_data or "budget" not in retrieved_data:
        context.bot.edit_message_text(
            "ERRORE: utente o budget non trovato",
            chat_id=chat_id,
            message_id=update.callback_query.message.message_id,
            reply_markup=kyb.BUDGET_MENU_KEYBOARD,
        )
        return
    if not retrieved_data["budget"] is None:
        user_budget = int(retrieved_data["budget"]) / 100
        budget_message = f"Budget: {user_budget:.2f}€"
    else:
        budget_message = f"Il budget non è stato impostato."
    if not send_new:
        context.bot.edit_message_text(
            budget_message,
            chat_id=chat_id,
            message_id=update.callback_query.message.message_id,
            reply_markup=kyb.BUDGET_MENU_KEYBOARD,
            parse_mode="HTML",
        )
    else:
        context.bot.send_message(
            chat_id,
            budget_message,
            reply_markup=kyb.BUDGET_MENU_KEYBOARD,
            parse_mode="HTML",
        )
    return ConversationHandler.END


def to_set_budget_menu(update: Update, context: CallbackContext):
    chat_id = update.callback_query.message.chat_id
    message_id = update.callback_query.message.message_id
    context.bot.edit_message_text(
        f"Inserisci il nuovo budget o torna indietro",
        chat_id=chat_id,
        message_id=message_id,
        reply_markup=kyb.SET_BUDGET_MENU_KEYBOARD,
    )
    return SET_BUDGET


def received_new_budget(update: Update, context: CallbackContext) -> int:
    chat_id = update.effective_user.id
    # * check if the budget is valid and get the eventual error
    invalid_budget = False
    try:
        new_budget = utils.parse_float_string(update.effective_message.text)
    except:
        invalid_budget = True
    # * must be non negative
    # if new_budget < 0:
    #     invalid_budget = True
    if invalid_budget:
        retry_text = "ERRORE: il budget non è valido."
        update.effective_message.reply_text(
            retry_text,
            reply_markup=kyb.SET_BUDGET_MENU_KEYBOARD,
        )
        return SET_BUDGET
    new_budget_to_int = int(new_budget * 100)
    # * update user budget
    user_manager.update_user(chat_id, {"budget": new_budget_to_int})
    lgr.logger.debug(f"Correctly updated budget {new_budget_to_int} for user {chat_id}")
    # * send success message
    message_text = f"Budget aggiornato con successo: <b>{new_budget:.2f}€</b>!"
    update.message.reply_text(
        message_text,
        parse_mode="HTML"
    )
    # * load budget menu
    to_budget_menu(update, context, send_new=True)
    return ConversationHandler.END
