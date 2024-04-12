import os
import sys
import asyncio

from dotenv import load_dotenv
from waitress import serve
from flask import Flask
from helpers.dbhelper import Database as Db
from helpers.config import version
from application import application, ETHCronService, CELOCronService
from application.XRPCronService import main as xrp_main
from application.StellarService import main as xlm_main
from controllers.account import bp_app as account

load_dotenv()
application.register_blueprint(account)

def start_app():
    print(":::::::: Starting the MUDA LIQUIDITY RAIL :::::::::::::")
    print("version", version)

    if not os.getenv("callback_url"):
        print("callback url needs to be set")
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
            print("starting db migrations")
            with application.app_context():
                Db().migrate_db()
                sys.exit()

        if arg_1 != "provider":
            print("arg one should be 'provider'")
            sys.exit()

        arg_2 = "client" if arg_count <= 2 else args[2]

        if arg_2 == "service":
            arg_3 = args[3]
            if arg_3 == 'celo':
                print("starting service in provider mode")
                print("Initiating the CELO Ingestion Service")
                CELOCronService.main()
            elif arg_3 == "xlm":
                print("Initiating the Stellar Ingestion Service")
                asyncio.run(xlm_main())
            else:
                print("running on ETH chain")
                ETHCronService.main()
        elif arg_2 == "client":
            print("starting service in client mode")
            print(f"app started on port {os.environ.get('PORT')}")
            if os.getenv("mode") == "dev":
                application.run(port=os.environ.get("PORT"), host="0.0.0.0", debug=True)
            else:
                serve(application, host="0.0.0.0", port=os.environ.get("PORT"))
        else:
            print("unexpected argument")
            sys.exit()

    except Exception as e:
        print("An exception was thrown, make sure you have the correct arguments")
        print(e)
        sys.exit()

if __name__ == "__main__":
    start_app()
