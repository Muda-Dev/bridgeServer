from flask import Blueprint, request, jsonify, json
from models.account import Account
from libs.modal import Modal as md, modal, token_required

bp_app = Blueprint('account', __name__)


def __init__(self):
    return md.make_response(403, "Not allowed ")


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


@bp_app.route("/account_statement/<account_id>", methods=["GET"])
def account_statement():
    return Account().get_account_statement()
