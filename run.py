import os
import sys
import asyncio
import logging
from dotenv import load_dotenv
from waitress import serve
from flask import Flask
from helpers.dbhelper import Database as Db
from helpers.config import version
from application import application, CELOCronService
from application.XRPCronService import main as xrp_main
from application.StellarService import main as xlm_main
from application.TronHelperService import main as tron
from application.BSCService import main as bsc
from controllers.account import bp_app as account
from application.BantuService import main as bantu

# Load environment variables
load_dotenv()
application.register_blueprint(account)

# Initialize logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

# Define loggers
logger = logging.getLogger("run_services")
tron_logger = logging.getLogger("tron_service")
celo_logger = logging.getLogger("celo_service")
stellar_logger = logging.getLogger("stellar_service")
bantu_logger = logging.getLogger("bantu_service")

# Dynamically set logging levels
selected_service = os.getenv("SERVICE", "all").lower()

if selected_service == "tron":
    tron_logger.setLevel(logging.DEBUG)
    celo_logger.setLevel(logging.ERROR)
    stellar_logger.setLevel(logging.ERROR)
elif selected_service == "celo":
    tron_logger.setLevel(logging.ERROR)
    celo_logger.setLevel(logging.DEBUG)
    stellar_logger.setLevel(logging.ERROR)
elif selected_service == "stellar":
    tron_logger.setLevel(logging.ERROR)
    celo_logger.setLevel(logging.ERROR)
    stellar_logger.setLevel(logging.DEBUG)
else:  # Default to INFO level
    tron_logger.setLevel(logging.INFO)
    celo_logger.setLevel(logging.INFO)
    stellar_logger.setLevel(logging.INFO)

def start_app():
    print(":::::::: Starting the MUDA LIQUIDITY RAIL :::::::::::::")
    print("version", version)

    if not os.getenv("callback_url"):
        print("Callback URL needs to be set")
        sys.exit()

    try:
        args = sys.argv
        arg_count = len(args)
        arg_1 = "provider" if arg_count <= 1 else args[1]

        with application.app_context():
            if not Db().checkConnection():
                print("Database connection error. Exiting ...")
                sys.exit()

        if arg_1 == "db-migrate":
            print("Starting DB migrations")
            with application.app_context():
                Db().migrate_db()
                sys.exit()

        if arg_1 != "provider":
            print("Arg one should be 'provider'")
            sys.exit()

        arg_2 = "client" if arg_count <= 2 else args[2]

        if arg_2 == "service":
            print("Starting service in provider mode")
            try:
                asyncio.get_running_loop()  # If an event loop is running, use `create_task`
                asyncio.create_task(run_services())
            except RuntimeError:
                asyncio.run(run_services())  # If no event loop is running, start one
        elif arg_2 == "client":
            print("Starting service in client mode")
            print(f"App started on port {os.environ.get('PORT')}")
            if os.getenv("mode") == "dev":
                application.run(port=os.environ.get("PORT"), host="0.0.0.0", debug=True)
            else:
                serve(application, host="0.0.0.0", port=os.environ.get("PORT"))
        else:
            print("Unexpected argument")
            sys.exit()

    except Exception as e:
        print("An exception was thrown, make sure you have the correct arguments")
        print(e)
        sys.exit()

async def run_services():
    services = []

    if selected_service in ("all", "stellar"):
        logger.info("Starting Stellar Service")
        services.append(asyncio.create_task(xlm_main()))

    if selected_service in ("all", "bsc"):
        logger.info("Starting BSC Service")
        services.append(asyncio.create_task(bsc()))

    if selected_service in ("all", "celo"):
        logger.info("Starting Celo Service")
        services.append(asyncio.create_task(CELOCronService.main()))

    if selected_service in ("all", "tron"):
        logger.info("Starting Tron Service")
        services.append(asyncio.create_task(tron()))

    if selected_service in ("all", "bantu"):
        logger.info("Starting Bantu Service")
        services.append(asyncio.create_task(bantu()))

    if not services:
        logger.warning("No valid services selected to run. Exiting.")
        return

    logger.info("🚀 Running all selected services now")
    await asyncio.gather(*services) 
    
if __name__ == "__main__":
    start_app()
