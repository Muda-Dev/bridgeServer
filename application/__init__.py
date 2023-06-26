from flask import Flask, redirect, request, url_for, render_template
from flask_mysqldb import MySQL
import os
from web3 import Web3
from helpers.config import rpc_endpoints

eth_rpc_url = rpc_endpoints["ETH"]["url"]
celo_rpc_url = rpc_endpoints["CELO"]["url"]
web3 = Web3(Web3.HTTPProvider(eth_rpc_url))
Maticweb3 = Web3(Web3.HTTPProvider(celo_rpc_url))


application = Flask(__name__)

application.config['MYSQL_HOST'] = os.getenv("HOST_NAME")
application.config['MYSQL_USER'] = os.getenv("USER_NAME")
application.config['MYSQL_PASSWORD'] =os.getenv("PASSWORD")
application.config['MYSQL_DB'] = os.getenv("DBNAME")
application.config['MYSQL_CURSORCLASS'] = 'DictCursor'
mysql = MySQL(application)