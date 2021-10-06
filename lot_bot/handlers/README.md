# Current bot functionalities:

## Users
- `/start`: starts the bot, creating the user if it is not already present in the db
- `homepage`: loads the bot's homepage

## Analyst
### In channels
- `/messaggio_abbonati <sport> - <strategy> \n <message text>`: sends message text to all the user subscribed to sport and strategy 
- `<giocata>`: the giocata is parsed, saved and sent to all subscribed users
- `<giocata outcome>`: the giocata outcome is parsed, the related giocata is updated and the outcome is sent to all subscribed users
- `<cashout message>`: the cashout message is parsed and sent to all the users subscribed to MaxExchange

## Admin
- `/set_user_role <user id|username> <role>`: changes the role of a user to be either _base_ or _analyst_
- `/send_file_id` with <media> attached: sends a message containing the file_id of the sent media
