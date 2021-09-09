import html
import json
import traceback

from telegram import ParseMode, Update
from telegram.ext.dispatcher import CallbackContext

from lot_bot import config as cfg
from lot_bot import keyboards as kyb
from lot_bot import logger as lgr
from lot_bot.dao import abbonamenti_manager, user_manager


def start_command(update: Update, context: CallbackContext):
    """Sends the welcome message and the sports channel 
        list message, updating the Update user's situazione
        and message
        TODO: we can update this by letting it return an appropriate
        int which repreresents "gestioneSport", in case we implement
        a ConversationHandler 

    Args:
        update (Update): the Update containing the command message
        context (CallbackContext)
    """
    user_id = update.effective_user.id
    lgr.logger.info(f"Received /start command from {user_id}")
    # the effective_message field is always present in normal messages
    # from_user gets the user which sent the message
    language_code = update.effective_user.language_code or "it"
    # update.message.reply_text is equal to bot.send_message(update.effective_message.chat_id, ...)
    bentornato_message = "Bentornato, puoi continuare ad utilizzare il bot"
    update.message.reply_text(bentornato_message, reply_markup=kyb.startup_reply_keyboard)
    lista_canali_message = "Questa è la lista dei canali di cui è possibile ricevere le notifiche"
    sent_message = update.message.reply_text(lista_canali_message, reply_markup=kyb.create_sports_inline_keyboard(update))
    new_user_data = {
        "situazione": "gestioneSport", 
        "message": json.dumps(sent_message), 
        "lingua": language_code
    }
    user_manager.update_user(user_id, new_user_data)


def reset_command(update: Update, context: CallbackContext):
    """Resets giocate, utenti and abbonamenti for the command sender,
        only if he/she is an admin

    Args:
        update (Update): the Update containing the reset command
        context (CallbackContext)
    """
    user_id = update.effective_user.id
    lgr.logger.info(f"Received /reset command from {user_id}")
    # ! TODO check for admin rights set on the DB, not for specific ID
    if user_id != ID_MANUEL and user_id != ID_MASSI:
        return
    user_manager.delete_user(user_id)
    abbonamenti_manager.delete_abbonamenti_for_user_id(user_id)


def error_handler(update: Update, context: CallbackContext):
    """Handles all the errors coming from any other handler.
         The error is written in the logs and a message is sent
         to all the developers to notify them about it.
         (taken from: 
         https://github.com/python-telegram-bot/python-telegram-bot/blob/master/examples/errorhandlerbot.py)

    Args:
        update (Update)
        context (CallbackContext)
    """
    lgr.logger.error(msg="Exception while handling an update:", exc_info=context.error)

    # traceback.format_exception returns the usual python message about an exception, but as a
    #   list of strings rather than a single string, so we have to join them together.
    tb_list = traceback.format_exception(None, context.error, context.error.__traceback__)
    tb_string = "".join(tb_list)

    update_str = update.to_dict() if isinstance(update, Update) else str(update)
    message = (
        f"An exception was raised while handling an update\n"
        f"<pre>update = {html.escape(json.dumps(update_str, indent=2, ensure_ascii=False))}"
        "</pre>\n\n"
        f"<pre>context.chat_data = {html.escape(str(context.chat_data))}</pre>\n\n"
        f"<pre>context.user_data = {html.escape(str(context.user_data))}</pre>\n\n"
        f"<pre>{html.escape(tb_string)}</pre>"
    )
    
    for dev_chat_id in cfg.config.DEVELOPER_CHAT_IDS:
        context.bot.send_message(chat_id=dev_chat_id, text=message, parse_mode=ParseMode.HTML)        


def fake_command_handler(update: Update, context: CallbackContext):
    update.message.reply_text("test successo wow")


