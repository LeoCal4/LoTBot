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


# Funzioni del Bot:
*NOTA: "<" e ">" NON sono da intendere letteralmente. Ad esempio "<sport>" sta ad indicare il nome di uno degli sport disponibili, e così via.*
## Utenti
- `/start`: attiva il bot, creando l'utente nel caso in cui sia il suo primo utilizzo. I suoi dati vengono salvati, viene generato un suo codice
    di affiliazione randomico e viene abbonato a _Calcio - Multipla_, _Calcio - Raddoppio_, _Exchange - MaxExchange_, ed infine viene inviato un messaggio 
    nel canale Nuovi Utenti, contenente i dati dell'utente.
- messaggio contenente `homepage`: carica il menu dell'homepage
- messaggio contenente `gestione bot`: carica il menu Configurazione Bot
- messaggio contenente `configurazione esperienza`: carica il menu Gestione Esperienza

## Analista/Consulente
### In un qualsiasi canale sport
- `/messaggio_abbonati <sport> - <strategia> A CAPO <messaggio>`: invia un messaggio a tutti gli utenti abbonati alla strategia dello sport indicati
- `<giocata>`: la giocata è analizzata, salvata ed è inviata tutti i relativi utenti abbonati. Nel caso in cui lo sport, la strategia, lo stake o la quota 
    non siano state scritte correttamente, o il numero della giocata sia stato già utilizzato, la giocata non viene inviata agli utenti e l'errore viene riportato all'analista. 
- `<risultato giocata>`: il risultato della giocata è analizzato, la relativa giocata viene aggiornata e il risultato è inviato a tutti i relativi utenti abbonati.
    Se il numero della giocata non è valido o se la parola indicante l'esito non è riconosciuta, il risultato non è inviato agli utenti e l'errore viene riportato all'analista

### Canale Exchange
- `<messaggio cashout>`: il messaggio di cashout è analizzato e inviato a tutti gli utenti abbonati a MaxExchange


## Admin
- `/set_user_role <user id|username> <ruolo>`: cambia il ruolo dell'utente in _base_ or _analyst_
- `/send_file_id` with <media> attached: sends a message containing the file_id of the sent media
