from dotenv import load_dotenv
load_dotenv()  
from application import application
from flask import Flask
from controllers.account import bp_app as account
import os
from waitress import serve
from helpers.dbhelper import Database as Db
from application import cron
import sys
from config import currencies
application.register_blueprint(account)

if(os.getenv("callback_url") == ""):
    print("callback url needs to be set")
    exit()

if(os.getenv("currency") not in currencies):
    print("currency needs to be one of ", str(currencies))
    exit()

try:
    arg_1 = sys.argv[1]
    arg_2 = sys.argv[2]
    if arg_1 != "provider":
        print("arg one should be 'provider'")
        exit()

    if arg_2 == "service":
        print("provider ingestion started")
        cron.main()
    elif arg_2 == "client":
        print("app started on port "+os.environ.get("PORT"))
        application.run(port=os.environ.get("PORT"), host="0.0.0.0", debug=True)
    else:
        print("invalid argument")
        exit()
except Exception as e:
    print("an exception was thrown, make sure you have the correct arguments")
    print(e)
    exit()






