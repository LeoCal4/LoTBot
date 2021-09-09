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

**You should always activate the _virtual env_ to run the bot** 

# Environments
_LoTBot_ has three different environments:
- **Development**: the default environment, used when developing the application. Everything should be as local as possible and should not rely on external parts.
- **Testing**: the environment in which tests (both unit and integration) are run. More on those two in the _Testing_ section.
- **Production**: the environment in which the bot is run once it is deployed.

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

### Unit tests
This kind of tests only check for the correctness of 
single functions in an isolate environment. To do so, 
_mocks_ (fake objects/results) are employed in order to mimic
external parts, such as databases.

### Integration tests
Integration tests are used to test the bot using external parts, which are as similiar as possible to the real ones, used in production. 

To do so, a test bot has been created in Telegram's test servers and a test db has been created on cloud.mongo. 

The code in `conftests.py` takes care of running the bot automatically, at the beginning of the tests.

## _pytest.ini_
All the information regarding where are tests found and the implicit command line arguments for the `pytest` command can be found in the _pytest.ini_ file.
