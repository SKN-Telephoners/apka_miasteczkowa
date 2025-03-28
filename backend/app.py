
import logging
from flask import Flask, request


app = Flask(__name__)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

log_formatter = logging.Formatter('[%(asctime)s] %(message)s', datefmt='%H:%M:%S')
file_handler = logging.FileHandler('server_logs.txt')
file_handler.setFormatter(log_formatter)

logger = logging.getLogger('server_logger')
logger.setLevel(logging.INFO)
logger.addHandler(file_handler)

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    user = data.get("username", "unknown_user")
    ip = request.remote_addr
    logger.info(f"{user} - Log in attempt - {ip}")
    return {"message": "Login attempt logged"}, 200

@app.route('/register', methods=['POST'])
def register():
    data = request.json
    user = data.get("username", "unknown_user")
    ip = request.remote_addr
    logger.info(f"{user} - Registration attempt - {ip}")
    return {"message": "Registration attempt logged"}, 200

if __name__ == '__main__':
    app.run(debug=True)