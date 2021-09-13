from flask import Flask
from controllers.account import bp_app as account

app = Flask(__name__)

app.register_blueprint(account)
app.run(port=8002, host="0.0.0.0", debug=True)
