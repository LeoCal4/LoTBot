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
### Nel Bot
- `/aggiungi_giorni <username o ID utente> <numero giorni (positivo)>`: aggiunge giorni di abbonamento all'utente specificato
- `/visualizza_stake <username o ID utente>`: mostra gli stake personalizzati assegnati all'utente specificato
- `/crea_stake <username o ID utente> <quota minima> <quota massima> <stake personalizzato>`: crea uno stake personalizzato per l'utente specificato. In questo modo, tutte le giocate ricevute dall'utente che hanno una quota compresa tra la minima e la massima indicate (valori estremi compresi), avranno uno stake pari a quello indicato nel comando.
- `/elimina_stake <username o ID utente> <numero dello stake personalizzato da eliminare>`: elimina uno degli stake personalizzati dell'utente specificato. Il numero dello stake personalizzato è dato dal comando `/visualizza_stake`. *ATTENZIONE: __ogni volta__ che uno stake viene eliminato e se ne vuole successivamente eliminare un altro, il comando /visualizza_stake __deve essere eseguito__, in quanto eliminando uno stake i numeri degli altri ancora presenti possono variare.*.
    Esempio: il comando /visualizza_stake utente1 ha il seguente output:
    *1) Calcio - Singola - Quota Minima: 1 - Quota Massima: 2 - Stake: 10.0%*
    2) Calcio - Singola - Quota Minima: 2.1 - Quota Massima: 3 - Stake: 5.0%
    *3) Calcio - Singola - Quota Minima: 3.1 - Quota Massima: 4 - Stake: 2.5%*
    4) Tennis - Multipla - Quota Minima: 1.5 - Quota Massima: 2.5 - Stake: 5.0%

    Assumiamo che si vogliano eliminare lo stake 1 e lo stake 3 (in corsivo), quindi viene innanzitutto eseguito il comando /elimina_stake utente1 1.
    Lanciando di nuovo /visualizza_stake utente1, gli stake dell'utente ora sono i seguenti:
    1) Calcio - Singola - Quota Minima: 2.1 - Quota Massima: 3 - Stake: 5.0%
    *2) Calcio - Singola - Quota Minima: 3.1 - Quota Massima: 4 - Stake: 2.5%*
    3) Tennis - Multipla - Quota Minima: 1.5 - Quota Massima: 2.5 - Stake: 5.0%

    Come si può vedere, quella che inizialmente era riportato come lo stake personalizzato 3, ora è lo stake 2, in quanto il primo è stato eliminato.
    Quindi, per eliminarlo, viene eseguito il comando /elimina_stake utente1 2. Il risultato finale lanciando /visualizza_stake utente1 è il seguente:
    1) Calcio - Singola - Quota Minima: 2.1 - Quota Massima: 3 - Stake: 5.0%
    2) Tennis - Multipla - Quota Minima: 1.5 - Quota Massima: 2.5 - Stake: 5.0%



### In un qualsiasi canale sport
- `/messaggio_abbonati <sport> - <strategia> A CAPO <messaggio>`: invia un messaggio a tutti gli utenti abbonati alla strategia dello sport indicati
- `<giocata>`: la giocata è analizzata, salvata ed è inviata tutti i relativi utenti abbonati. Nel caso in cui lo sport, la strategia, lo stake o la quota 
    non siano state scritte correttamente, o il numero della giocata sia stato già utilizzato, la giocata non viene inviata agli utenti e l'errore viene riportato all'analista. 
- `<risultato giocata>`: il risultato della giocata è analizzato, la relativa giocata viene aggiornata e il risultato è inviato a tutti i relativi utenti abbonati.
    Se il numero della giocata non è valido o se la parola indicante l'esito non è riconosciuta, il risultato non è inviato agli utenti e l'errore viene riportato all'analista

### Canale Exchange
- `<messaggio cashout>`: il messaggio di cashout è analizzato e inviato a tutti gli utenti abbonati a MaxExchange. La percentuale di guadagno/perdita è utilizzata come risultato della giocata ai fini del resoconto.


## Admin
- `/cambia_ruolo <user id|username> <ruolo>`: cambia il ruolo dell'utente in _base_ or _analyst_
- `/send_file_id` with <media> attached: sends a message containing the file_id of the sent media
- `/broadcast A CAPO <messaggio da inviare>`: invia un messaggio a tutti gli utenti tramite il bot
- `/modifica_referral <username o ID utente> <nuovo referral>`: modifica il codice referral dell'utente specificato. Se il nuovo referral è già utilizzato o non è valido, il referral non viene modificato e un messaggio di errore viene inviato per spiegare l'entità del problema.
