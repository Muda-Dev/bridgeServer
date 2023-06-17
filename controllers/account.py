from flask import Blueprint, request

from models.account import Account
from helpers.modal import Modal as md

bp_app = Blueprint('account', __name__)

@bp_app.route("/")
def index():
    return md.make_response(403, "Not allowed")

@bp_app.route("/account/create-key", methods=["GET"])
def generate_keypair():
    return Account().generate_keypair()

@bp_app.route("/account/<account_id>", methods=["GET"])
def account_balance(account_id):
    return Account().get_account_balance(account_id)

@bp_app.route("/payment", methods=["POST"])
def make_transfer():
    return Account().make_transfer(request)

@bp_app.route("/get_balance", methods=["GET"])
def get_balance():
    return Account().get_env_balance()

@bp_app.route("/get_linked_address", methods=["GET"])
def get_linked_address():
    return Account().get_linked_address()

@bp_app.route("/account_statement/<account_id>", methods=["GET"])
def account_statement(account_id):
    return Account().get_account_statement(account_id)
