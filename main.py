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
CREDENTIAL_TRACKER_FILE = "credential_tracker.txt"
APK_TRACKER_FILE = "apk_tracker.txt"

def read_credentials():
    """Read credentials from user_key.txt and return as a list of tuples (username, access_key)."""
    with open(USER_KEY_FILE, "r") as f:
        lines = [line.strip() for line in f if line.strip()]
    
    if len(lines) % 2 != 0:
        raise Exception("Invalid user_key.txt format: Odd number of lines detected.")

    return [(lines[i], lines[i+1]) for i in range(0, len(lines), 2)]

def get_next_credential():
    """Get the next available credential and rotate properly."""
    credentials = read_credentials()
    if not credentials:
        raise Exception("No credentials found in user_key.txt")

    try:
        with open(CREDENTIAL_TRACKER_FILE, "r") as f:
            index = int(f.read().strip())
    except (FileNotFoundError, ValueError):
        index = 0  # Start from the first credential if file is missing or corrupted

    username, access_key = credentials[index]
    index = (index + 1) % len(credentials)  # Loop back when all are used

    with open(CREDENTIAL_TRACKER_FILE, "w") as f:
        f.write(str(index))

    return username, access_key

def get_next_apk():
    """Get the next available APK file and rotate properly."""
    try:
        with open(APK_TRACKER_FILE, "r") as f:
            index = int(f.read().strip())
    except (FileNotFoundError, ValueError):
        index = 0  # Start from the first APK if file is missing or corrupted

    apk_file = APK_FILES[index % len(APK_FILES)]  # Ensure index is valid

    with open(APK_TRACKER_FILE, "w") as f:
        f.write(str((index + 1) % len(APK_FILES)))

    return apk_file

def update_browserstack_yaml(username, access_key, apk_file):
    """Update the browserstack.yml file with new credentials and APK file."""
    with open(CONFIG_FILE, "w") as f:
        f.write(f"userName: {username}\n")
        f.write(f"accessKey: {access_key}\n")
        f.write(f"app: ./{apk_file}\n")

def run_browserstack_script():
    """Run browserstack.py script."""
    if not os.path.exists(BROWSERSTACK_SCRIPT):
        print(f"Error: {BROWSERSTACK_SCRIPT} not found!")
        return
    
    if subprocess.run(["which", "browserstack-sdk"], capture_output=True, text=True).returncode != 0:
        print("Error: browserstack-sdk not installed or not in PATH!")
        return

    print(f"Running {BROWSERSTACK_SCRIPT}...")
    subprocess.run(["browserstack-sdk", BROWSERSTACK_SCRIPT], check=True)

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
