import os
import subprocess
import threading
from flask import Flask, jsonify

# Flask App Setup
app = Flask(__name__)
status = {"running": False, "last_username": None, "last_apk": None}

USER_KEY_FILE = "user_key.txt"
APK_FILES = [f"app{i}.apk" for i in range(1, 9)]
CONFIG_FILE = "browserstack.yml"
BROWSERSTACK_SCRIPT = "browserstack.py"

def read_credentials():
    """Read credentials from user_key.txt and return as a list of tuples (username, access_key)."""
    with open(USER_KEY_FILE, "r") as f:
        lines = [line.strip() for line in f if line.strip()]
    return [(lines[i], lines[i+1]) for i in range(0, len(lines), 2)]

def get_next_credential():
    """Get the next available credential and rotate the file."""
    credentials = read_credentials()
    if not credentials:
        raise Exception("No credentials found in user_key.txt")
    
    selected_cred = credentials.pop(0)
    
    # Rotate credentials
    with open(USER_KEY_FILE, "w") as f:
        for username, access_key in credentials:
            f.write(f"{username}\n{access_key}\n")
    
    return selected_cred

def get_next_apk():
    """Get the next available APK file and rotate the list."""
    if not os.path.exists("apk_tracker.txt"):
        with open("apk_tracker.txt", "w") as f:
            f.write("0")  # Start from the first APK
    
    with open("apk_tracker.txt", "r") as f:
        index = int(f.read().strip())

    apk_file = APK_FILES[index]

    # Update tracker for next run
    index = (index + 1) % len(APK_FILES)
    with open("apk_tracker.txt", "w") as f:
        f.write(str(index))

    return apk_file

def update_browserstack_yaml(username, access_key, apk_file):
    """Update the browserstack.yml file with new credentials and APK file."""
    with open(CONFIG_FILE, "w") as f:
        f.write(f"userName: {username}\n")
        f.write(f"accessKey: {access_key}\n")
        f.write(f"app: ./{apk_file}\n")

def run_browserstack_script():
    """Run browserstack.py script."""
    if os.path.exists(BROWSERSTACK_SCRIPT):
        print(f"Running {BROWSERSTACK_SCRIPT}...")
        subprocess.run(["browserstack-sdk", BROWSERSTACK_SCRIPT], check=True)
    else:
        print(f"Error: {BROWSERSTACK_SCRIPT} not found!")

@app.route("/")
def home():
    """Show script status on a web page."""
    return jsonify(status)

def flask_thread():
    """Run Flask server in a separate thread."""
    app.run(host="0.0.0.0", port=8080, debug=False, use_reloader=False)

def main():
    global status
    status["running"] = True

    username, access_key = get_next_credential()
    apk_file = get_next_apk()
    update_browserstack_yaml(username, access_key, apk_file)

    status["last_username"] = username
    status["last_apk"] = apk_file

    print(f"Updated {CONFIG_FILE} with {username}, {apk_file}")

    # Run browserstack.py after updating config
    run_browserstack_script()

    status["running"] = False

if __name__ == "__main__":
    # Start Flask server in a background thread
    threading.Thread(target=flask_thread, daemon=True).start()

    # Run main process
    main()
