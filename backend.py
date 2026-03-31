from flask import Flask, send_from_directory, request, jsonify
from flask_cors import CORS
import os
from dotenv import load_dotenv
import requests
import sqlite3
import bcrypt
import random, string
import socket
import struct
import threading
import stripe

load_dotenv()
BASE_URL = os.getenv("BASE_URL")
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
webhook = os.getenv("DISCORD_WEBHOOK")

def get_connection():
    return sqlite3.connect("data/vm.db", check_same_thread=False)

##############################################################
#Note from Samuel: Ensure that banned_words.py is in the same folder or else you'll have to change the destination as to where the import request is fulfilled.
import banned_words

BANNED_WORDS = banned_words.BANNED_WORDS
def SEND_AUDIT_LOG(message,urgency): # Urgency can be "True" or "False", true for when pinging @eveyrone, false for normal messages
    
    BANNED_SET = set(word.lower() for word in BANNED_WORDS)

    filtered_message = message.split()

    for i, word in enumerate(filtered_message):
        if word.lower() in BANNED_SET:
            filtered_message[i] = "[BLEEP]"
    
    message = " ".join(filtered_message)
    
    ret = "@everyone\n" if urgency else ""
    ret += message

    
    message_data = {
        "content": ret,
    }

    try:
        response = requests.post(webhook, json=message_data)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Error sending webhook: {e}")

#####################################################3
app = Flask(
    __name__,
    static_folder="./dist",
    static_url_path=""
)

# Enable CORS (safe for dev, adjust for prod)
CORS(app)

# Robot bridge configuration/state
ROBOT_LISTEN_HOST = os.getenv("ROBOT_LISTEN_HOST", "0.0.0.0")
ROBOT_LISTEN_PORT = int(os.getenv("ROBOT_LISTEN_PORT", "3000"))

robot_lock = threading.Lock()
robot_socket = None
robot_connected = False
robot_addr = None


def sanitize_keys(keys):
    opposites = [
        ("w", "s"),
        ("a", "d"),
        ("arrowup", "arrowdown"),
        ("arrowleft", "arrowright"),
    ]

    normalized = set(k.lower().strip() for k in keys if k and k.strip())
    for k1, k2 in opposites:
        if k1 in normalized and k2 in normalized:
            normalized.discard(k1)
            normalized.discard(k2)
    return list(normalized)


def start_robot_server():
    def accept_loop():
        global robot_socket, robot_connected, robot_addr

        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((ROBOT_LISTEN_HOST, ROBOT_LISTEN_PORT))
        server.listen(1)
        print(f"Robot TCP server listening on {ROBOT_LISTEN_HOST}:{ROBOT_LISTEN_PORT}")

        while True:
            conn_socket, addr = server.accept()
            with robot_lock:
                if robot_socket:
                    try:
                        robot_socket.close()
                    except OSError:
                        pass
                robot_socket = conn_socket
                robot_connected = True
                robot_addr = addr
            print(f"Robot connected from {addr[0]}:{addr[1]}")

    thread = threading.Thread(target=accept_loop, daemon=True)
    thread.start()


def send_robot_command(command_text):
    global robot_socket, robot_connected, robot_addr

    payload = command_text.encode("utf-8")
    length_prefix = struct.pack(">I", len(payload))

    with robot_lock:
        if not robot_socket or not robot_connected:
            return False, "robot_disconnected"
        try:
            robot_socket.sendall(length_prefix + payload)
            return True, "sent"
        except OSError as e:
            try:
                robot_socket.close()
            except OSError:
                pass
            robot_socket = None
            robot_connected = False
            robot_addr = None
            return False, f"socket_error: {e}"


@app.route("/api/message", methods=["POST"])
def receive_message():
    data = request.get_json()
    text = data.get("text")

    # print("Received from frontend:", text)
    SEND_AUDIT_LOG(f"Received message from frontend: {text}", False)
    return jsonify({
        "reply": f"Thank you for your message: {text}"
    })

@app.route("/")
def serve_index():
    return send_from_directory(app.static_folder, "index.html")


# Handle React/Vite routing (important)
@app.route("/<path:path>")
def serve_static_files(path):
    file_path = os.path.join(app.static_folder, path)

    if os.path.exists(file_path):
        return send_from_directory(app.static_folder, path)
    else:
        # fallback to index.html for SPA routing
        return send_from_directory(app.static_folder, "index.html")




# log in the administrators (works with adminLoginPage.js)
@app.route("/api/admin-login", methods=["POST"])
def admin_login():
    data = request.get_json()

    username = data.get("username")
    password = data.get("password")
    conn = get_connection()
    cursor = conn.cursor()
    
    #allows for checking username and password
    cursor.execute("""
    SELECT username, password, first_name, last_name
    FROM administrators
    WHERE username = ?
    """, (username,))

    #using bcrypt to make sure passwords stored in database are hashed
    user = cursor.fetchone()
    if user and bcrypt.checkpw(password.encode(), user[1].encode()):
        # mark admin as active
        cursor.execute("""
            UPDATE administrators
            SET last_seen = CURRENT_TIMESTAMP
            WHERE username = ?
            """, (username,))
        conn.commit()
        return jsonify({
            "success": True,
            "username": user[0],
            "first_name": user[2],
            "last_name": user[3]
        })
    else:
        return jsonify({"success": False})

#handles the logout of admin works with adminHomePage.js
@app.route("/api/admin-logout", methods=["POST"])
def admin_logout():
    data = request.get_json()
    username = data.get("username")

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE administrators SET last_seen = CURRENT_TIMESTAMP WHERE username = ?",
        (username,)
    )
    conn.commit()
    return jsonify({"success": True})


''' TOD: remove this function once stripe is implemented (this is purely for testing purposes, it generates a "stripe like" code)
def generate_session_id():
    return "test_" + "".join(random.choices(string.ascii_letters + string.digits, k=32))

#this generates a random code to store in database, so that we can provide users with their code after they pay
@app.route("/api/create-test-payment", methods=["POST"])
def create_test_payment():

    data = request.get_json()
    cart = data.get("items", {})
    conn = get_connection()
    cursor = conn.cursor()
    # check inventory first to make sure we have enough of said product
    for product_id, qty in cart.items():
        qty = int(qty)
        if qty <= 0:
            continue
        cursor.execute(
            "SELECT inventory FROM products WHERE product_id = ?",
            (product_id,)
        )
        result = cursor.fetchone()
        if result is None:
            return jsonify({"error": "Product not found"}), 400
        inventory = result[0]
        if qty > inventory:
            return jsonify({
                "error": f"Not enough inventory for product {product_id}"
            }), 400

    # subtract inventory --also prevents race conditions if two users try to do things at same time
    for product_id, qty in cart.items():
        qty = int(qty)
        if qty <= 0:
            continue
        cursor.execute("""
            UPDATE products
            SET inventory = inventory - ?
            WHERE product_id = ?
            AND inventory >= ?
        """, (qty, product_id, qty))
        if cursor.rowcount == 0:
            conn.rollback()
            return jsonify({
                "error": "Item just sold out"
            }), 400

    # generate payment code (needs fixing when we do stripe stuff)
    session_id = generate_session_id()
    while True:
        code = f"{random.randint(0,9999):04d}"
    
        try:
            conn.execute("""
                INSERT INTO valid_codes (code, stripe_session_id)
                VALUES (?, ?)
            """, (code, session_id))
            conn.commit()

            return jsonify({
                "session_id": session_id
            })

        except sqlite3.IntegrityError:
            continue
            '''


#this gets the code associated with a stripe session id, so that we can provide users with their code after they pay  
@app.route("/api/get-code")
def get_code():

    session_id = request.args.get("session_id")
    conn = get_connection()
    cursor = conn.cursor()

    result = cursor.execute(
        """
        SELECT code
        FROM valid_codes
        WHERE stripe_session_id = ?
        AND created_at >= datetime('now','-1 day') AND is_used = 0
        """,
        (session_id,)
    ).fetchone()

    if result is None:
        return jsonify({"error": "Code not found or expired"}), 404

    return jsonify({"code": result[0]})

#this is to get the products and display on the payment calculation (index.html) page
@app.route("/api/products", methods=["GET"])
def get_products_to_buy():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT product_id, name, price, inventory FROM products")
    rows = cursor.fetchall()

    return jsonify([
        {"id": r[0], "name": r[1], "price": r[2], "inventory": r[3]}
        for r in rows
    ])

#these are for the set inventory page
#get all the products for the dropdown menu
@app.route("/api/get-products", methods=["GET"])
def get_products():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT product_id, name FROM products")
    products = cursor.fetchall()

    return jsonify([
        {"id": row[0], "name": row[1]}
        for row in products
    ])

#get the current price and inventory for the product (to display on the ui)
@app.route("/api/get-inventory/<int:product_id>", methods=["GET"])
def get_inventory(product_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT price, inventory FROM products WHERE product_id = ?",
        (product_id,)
    )
    result = cursor.fetchone()

    return jsonify({
        "price": result[0],
        "inventory": result[1]
    })

#update the inventory for when changes are made on the page
@app.route("/api/update-inventory", methods=["POST"])
def update_inventory():
    data = request.get_json()
    conn = get_connection()
    cursor = conn.cursor()
    
    product_id = data.get("product_id")
    new_price = data.get("price")
    new_inventory = data.get("inventory")
    username = data.get("username")
    #the actual updating query
    cursor.execute("""
        UPDATE products
        SET price = ?, inventory = ?
        WHERE product_id = ?
    """, (new_price, new_inventory, product_id))
    #log which administrator did the change
    cursor.execute("""
        INSERT INTO actions (username, action_type_id)
        VALUES (?, 1)
    """, (username,))
    conn.commit()
    SEND_AUDIT_LOG(f"{username} updated inventory for product {product_id}", False)
    return jsonify({"success": True})

@app.route("/api/get-actions", methods=["GET"])
def get_actions():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT a.action_time, a.username, type_name
        FROM actions a
        JOIN action_type AS at ON a.action_type_id = at.type_id
        ORDER BY a.action_time DESC
        LIMIT 20
    """)
    rows = cursor.fetchall()

    return jsonify([
        {
            "action_time": r[0],
            "username": r[1],
            "type_name": r[2],
        }
        for r in rows
    ])
@app.route("/api/update-activity", methods=["POST"])
def update_activity():
    data = request.get_json()
    username = data.get("username")
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE administrators
        SET last_seen = CURRENT_TIMESTAMP
        WHERE username = ?
    """, (username,))
    conn.commit()
    return jsonify({"success": True})

@app.route("/api/is-admin-active", methods=["GET"])
def is_admin_active():
    username = request.args.get("username")
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT last_seen > datetime('now','-2 minutes') FROM administrators WHERE username = ?
    """, (username,))
    result = cursor.fetchone()
    if result is None:
        return jsonify({"active": False}), 404

    is_active = bool(result[0])

    return jsonify({"active": is_active}), 200

@app.route("/api/robot-status", methods=["GET"])
def robot_status():
    with robot_lock:
        status = {
            "connected": robot_connected,
            "address": f"{robot_addr[0]}:{robot_addr[1]}" if robot_addr else None,
            "listen_host": ROBOT_LISTEN_HOST,
            "listen_port": ROBOT_LISTEN_PORT,
        }
    return jsonify(status)


@app.route("/api/robot-command", methods=["POST"])
def robot_command():
    data = request.get_json(silent=True) or {}
    raw_command = data.get("command")

    if not raw_command or not isinstance(raw_command, str):
        return jsonify({"error": "Missing required string field: command"}), 400

    command_to_send = raw_command.strip()
    if "+" in command_to_send:
        command_to_send = "+".join(sanitize_keys(command_to_send.split("+")))

    if not command_to_send:
        return jsonify({"error": "Command became empty after sanitization"}), 400

    ok, status = send_robot_command(command_to_send)
    response = {
        "command": command_to_send,
        "status": status,
    }
    return jsonify(response), (200 if ok else 503)

#Backend for the payment system (stripe stuff will go here eventually, for now it's just testing stuff)
##########################################


@app.route("/api/create-checkout-session", methods=["POST"])
def create_checkout_session():
    data = request.get_json()
    cart = data.get("items", {})

    conn = get_connection()
    cursor = conn.cursor()

    try:
        # 1. CHECK INVENTORY
        total_amount = 0

        for product_id, qty in cart.items():
            qty = int(qty)
            if qty <= 0:
                continue

            cursor.execute(
                "SELECT inventory, price, name FROM products WHERE product_id = ?",
                (product_id,)
            )
            result = cursor.fetchone()

            if result is None:
                return jsonify({"error": "Product not found"}), 400

            inventory, price, name = result

            if qty > inventory:
                return jsonify({
                    "error": f"Not enough inventory for product {product_id}"
                }), 400

            total_amount += int(price * 100) * qty  # convert to cents

        # 2. SUBTRACT INVENTORY (race-condition safe)
        for product_id, qty in cart.items():
            qty = int(qty)
            if qty <= 0:
                continue

            cursor.execute("""
                UPDATE products
                SET inventory = inventory - ?
                WHERE product_id = ? AND inventory >= ?
            """, (qty, product_id, qty))

            if cursor.rowcount == 0:
                conn.rollback()
                return jsonify({"error": "Item just sold out"}), 400

        # 3. CREATE STRIPE SESSION
        session = stripe.checkout.Session.create(
            mode="payment",
            line_items=[{
                "price_data": {
                    "currency": "usd",
                    "product_data": {
                        "name": "Vending Machine Purchase",
                    },
                    "unit_amount": total_amount,  # total in cents
                },
                "quantity": 1,
            }],
            success_url=f"{BASE_URL}/pages/paymentCode.html?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{BASE_URL}/pages/paymentError.html",
        )

        # 4. GENERATE CODE + STORE STRIPE SESSION
        while True:
            code = f"{random.randint(0,9999):04d}"
            try:
                cursor.execute("""
                    INSERT INTO valid_codes (code, stripe_session_id)
                    VALUES (?, ?)
                """, (code, session.id))

                conn.commit()
                break
            except sqlite3.IntegrityError:
                continue

        return jsonify({
            "url": session.url
        })

    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 400


if __name__ == "__main__":
    start_robot_server()
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "3001")), debug=False)
