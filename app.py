from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import os

app = Flask(__name__)
# CORS umožní tvému webu na GitHubu volat tento server
CORS(app)

DB_FILE = "users_db.json"

def load_db():
    if not os.path.exists(DB_FILE):
        return {}
    try:
        with open(DB_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save_db(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f, indent=4)

@app.route('/')
def home():
    return "Slot Machine Backend is Online!"

# Získání zůstatku
@app.route('/get_balance', methods=['GET'])
def get_balance():
    user_id = request.args.get('user_id', 'player_1')
    db = load_db()
    # Pokud uživatel neexistuje, začne s 1000 Kč
    return jsonify({"balance": db.get(user_id, 1000.0)})

# Uložení zůstatku po hře
@app.route('/update_balance', methods=['POST'])
def update_balance():
    data = request.json
    user_id = data.get('user_id', 'player_1')
    new_balance = data.get('balance')
    
    db = load_db()
    db[user_id] = new_balance
    save_db(db)
    return jsonify({"status": "success", "balance": new_balance})

# Potvrzení PayPal platby
@app.route('/confirm_payment', methods=['POST'])
def confirm_payment():
    data = request.json
    user_id = data.get('user_id', 'player_1')
    amount = float(data.get('amount'))
    
    db = load_db()
    current_balance = db.get(user_id, 1000.0)
    db[user_id] = current_balance + amount
    save_db(db)
    
    return jsonify({"status": "ok", "new_balance": db[user_id]})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)