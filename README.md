# Setup
1. Download the latest Python version (3.9.6 when this was written)
2. Update pip using:  
    `pip install --user --upgrade pip`
3. Run the following command to create a virtual environment
    `virtualenv -p python3 venv`
4. To open the virtualenv, use the appropriate command among the followings, depending on the shell:  
    - PowerShell: `.\venv\Scripts\activate.ps1`
    - bash: `/venv/bin/activate`
5. Once in the virtualenv, install the application's requirements using:  
    `pip install -r requirements.txt`

**You should always activate the _virtual env_; everything written here assumes that you have activated it**

Now that the bot has been installed, you must create a _config.py_ file in the *lot_bot* directory, copying the *sample_config.py*.
In the _config.py_ file, add all the values to the variables marked with _"TBA"_ (_To Be Added_). They are all set to `None`, so the bot won't work if you don't set them first.

# Environments
_LoTBot_ has three different environments:
- **Development**: the default environment, used when developing the application. Everything should be as local as possible and should not rely on external parts.
- **Testing**: the environment in which tests (both unit and integration) are run. More on those two in the _Testing_ section.
- **Production**: the environment in which the bot is run once it is deployed.

# Running the bot
To run the bot locally, simply run:
    `py .\main.py`

TODO: account on test server

# Branches

## Branch basic workflow

1. `git branch <local branch name>` to create a new local branch
2. `git checkout <local branch name>` to move on the new local branch
3. create commits with the new code on the newly created branch
4. `git remote add <remote branch name> https://github.com/LeoCal4/LoTBot.git` to create a new remote branch
5. `git push --set-upstream <remote branch name> <local branch name>` to connect the local branch to the remote one
6. now you can push your commits to the remote branch
7. once you have done your work on the branch, create a pull request on GitHub and solve the eventual conflicts
8. you can then delete the branch directly on GitHub
9. `git branch -d <local branch name>` to remove the useless local branch 
10. `git fetch --prune` to remove references to useless remote branches (they won't show up anymore with `git branch -a`) 

## General commands
- `git branch`: lists local branches
- `git branch -a`: lists remote branches

- `git branch -m <new branch name>`: renames the current branch

- `git branch -d`: deletes the current branch (if it has no uncommited changes)
- `git push origin --delete remote_branch_name`: deletes the remote branch

- `git branch local_branch_name`: creates a local branch with the specified name
- `git remote add remote_branch_name repository_link`: creates a new remote branch on the repo

- `git checkout branch_name`: switches to the specified (local or remote) branch

- `git push <remote_branch_name> local_branch_name~`: pushes the local branch to the remote one
- `git fetch --all`: fetches the contents of the remote branches

- `git checkout -b local_branch_name2 local_branch_name1`: creates a new branch based on local_branch_name2

- `git fetch --prune`: deletes useless branches (for example after merging them) 



# Development
## Main components
_LoTBot_ has three main components, that are initialized in the main entry point 
of the application and that are shared among different modules:

- **config**: an object containing constant data, which varies among the different environments. It must be the **first** to be initialized.
- **logger**: the object used to log information across the modules. It must be initialized **after** _config_ and **before** _mongo_, as it depends on settings specified in _congif_.
- **mongo**: the object representing the database, it must be initialized **after** the previous two, as it depends on both of them, and must be used only from the _managers_ in _DAO_.
## Adding new Python packages
In the virtualenv, install the desired package using:  
    `pip install <package_name>`

Once you have installed it, run:  
    `pip freeze > requirements.txt`  
to add the new package in the requirements file.

## Usage of logging
https://docs.python.org/3/howto/logging.html

The _logger_ can be used instead of normal prints, since they either appear on the console or they can 
be redirected to actual log files if needed.

They implicitely 
define the following levels of information:

- debug info: `logger.debug("...)`  
- normal event: `logger.info("...")`  
- warning: `logger.warning("...")`  
- error or exception: `logger.error("...")`

As of now, the __DEBUG__ level is set only when in _development_; for all the other envs
it is set to __INFO__ (this means that all the info reported using `logger.debug()` will be seen only in _development_).

## Deploying to production
As it stands now, to deploy the application in production, 
you must define the ENV enviromental variable and set it to "dotenv",
in order to read the .env file that will be placed on the server and 
load the right env vars.

## Database
There are three different database settings, one for each environment:

- __Development__: a local db can be used. In order to do so, 
    Mongo must be installed on the local machine (alternatively, you can use 
    the integration test db)
- __Testing__: 
    - _Unit Tests_: a mock database is used, everything is automatically set up
        at the start of the tests
    - _Integration Tests_: a remote test db hosted on cloud.mongo is used
- __Production__: the actual production remote db hosted on cloud.mongo is used

## Structure and coding conventions
The following coding conventions should be maintained during the development of the bot:

- use snake_case for variables and modules (file names)
- use UpperCamelCase for classes
- when importing a _local module_, import it directly  
    `from lot_bot import module [as ...]`

    instead of importing single functions or variables    
    `from lot_bot.module import function/variable`

    This ensures that the code is more readable and that any change on the module is 
    reflected on all the other modules importing it (this is the case of the three base 
    modules of the application: _config.py_, _logger.py_, _database.py_, which ideally
    should be modified only by the main entry point of the bot, which as of now is _main.py_)
- there is no convention when importing _external modules_ (libraries)
- all of the operation involving the database must be implemented in a DAO, in the appropriate manager. 
    For example: all the methods involving users operations can be found in *lot_bot/dao/user_manager.py*

# Testing
Ideally, every function of the codebase should have its own tests, which inspect the correctness of said function in normal and extreme cases.
## Running tests
To run all the tests, simply run the following command

`pytest`

You can also run unit and integration tests separately:

`pytest .\tests\unit`

`pytest .\tests\integration`

### Unit tests
This kind of tests only check for the correctness of 
single functions in an isolate environment. To do so, 
_mocks_ (fake objects/results) are employed in order to mimic
external parts, such as databases.

### Integration tests
Integration tests are used to test the bot using external parts, which are as similiar as possible to the real ones, used in production. 

To do so, a test bot has been created in Telegram's test servers and a test db has been created on cloud.mongo. 

The code in `conftests.py` takes care of running the bot automatically, at the beginning of the tests.

#### Channel admin client
There are tests which require to have a client which is the admin of one of the sport test channels.  
Integration tests involving said channels won't work if you have not performed the following steps yet.
To create an admin for the channel, choose a phone number among the
available ones (those with pattern 99966<dc_id><4 random digits>) and run the following lines of code to have that
account join the channel:  
    `from telethon.tl.functions.channels import JoinChannelRequest`
    `await channel_admin_client(JoinChannelRequest(channel))`

where `channel_admin_client` is the client and `channel` is the id of the channel.
Once the client is part of the channel, you have to manually make it an admin.  

## _pytest.ini_
All the information regarding where are tests found and the implicit command line arguments for the `pytest` command can be found in the _pytest.ini_ file.
