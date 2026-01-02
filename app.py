import os
import json
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# --- KONFIGURACE Z TVÉHO PAYPALU ---
PAYPAL_CLIENT_ID = "ASCq5RYMUcN-l9GQbjDJ9KmoFj4VYdUYdvY-xW40I4mEWnEWu5pO0ddVtABdyiUilSoOZdsWf5IL_Yxt"
PAYPAL_SECRET = "EN1clvdclqvFebDCwgDZszJYo4GxykvIHQYy9UL4C-ok1KJXyaRVJg9Bj7C_zUjmy1Gh_6Mycm5C_5aw"

# Sandbox pro testování, až budeš chtít brát real peníze, změníš na: https://api-m.paypal.com
PAYPAL_API_URL = "https://api-m.sandbox.paypal.com"

DB_FILE = "users_db.json"

def load_db():
    if not os.path.exists(DB_FILE): return {}
    try:
        with open(DB_FILE, "r") as f: return json.load(f)
    except: return {}

def save_db(data):
    with open(DB_FILE, "w") as f: json.dump(data, f, indent=4)

def get_paypal_token():
    """Získá přístupový token od PayPalu."""
    url = f"{PAYPAL_API_URL}/v1/oauth2/token"
    auth = (PAYPAL_CLIENT_ID, PAYPAL_SECRET)
    headers = {"Accept": "application/json", "Accept-Language": "en_US"}
    data = {"grant_type": "client_credentials"}
    response = requests.post(url, auth=auth, headers=headers, data=data)
    return response.json().get("access_token")

@app.route('/')
def home():
    return "Funny Face Casino Backend is LIVE and Secure!"

@app.route('/get_balance', methods=['GET'])
def get_balance():
    user_id = request.args.get('user_id', 'player_1')
    db = load_db()
    return jsonify({"balance": db.get(user_id, 1000.0)})

@app.route('/update_balance', methods=['POST'])
def update_balance():
    data = request.json
    user_id = data.get('user_id', 'player_1')
    new_balance = data.get('balance')
    db = load_db()
    db[user_id] = new_balance
    save_db(db)
    return jsonify({"status": "success", "balance": new_balance})

@app.route('/confirm_payment', methods=['POST'])
def confirm_payment():
    data = request.json
    order_id = data.get('order_id')
    user_id = data.get('user_id', 'player_1')

    token = get_paypal_token()
    # Dotaz na PayPal: Opravdu tato platba proběhla?
    url = f"{PAYPAL_API_URL}/v2/checkout/orders/{order_id}"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    response = requests.get(url, headers=headers)
    order_details = response.json()

    if order_details.get("status") == "COMPLETED":
        # Získáme částku přímo z oficiálního potvrzení PayPalu (nelze zfalšovat)
        amount = float(order_details["purchase_units"][0]["amount"]["value"])
        
        db = load_db()
        current_balance = db.get(user_id, 1000.0)
        db[user_id] = current_balance + amount
        save_db(db)
        
        return jsonify({"status": "verified", "new_balance": db[user_id]})
    else:
        return jsonify({"status": "failed", "message": "Platba nebyla nalezena nebo dokončena"}), 400

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
