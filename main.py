import os
import yaml
from flask import Flask
import threading
import subprocess  # Import the subprocess module

app = Flask(__name__)

# Global variables to store configuration
USERNAME = None
ACCESS_KEY = None
APP_PATH = None
TEST_COMMAND = "echo 'Running tests... (replace with your actual test command)'"  # Default test command
BROWSERSTACK_SCRIPT = "browserstack.py"  # Name of the BrowserStack script

def update_browserstack_config(username, access_key, app_path, config_file="browserstack.yml"):
    """
    Updates the browserstack.yml file with the provided username, access key, and app path.
    """
    global USERNAME, ACCESS_KEY, APP_PATH

    try:
        with open(config_file, 'r') as f:
            config = yaml.safe_load(f)
    except FileNotFoundError:
        config = {}  # Start with an empty dictionary if the file doesn't exist.
        print(f"Warning: {config_file} not found. Creating a new one.")
    except yaml.YAMLError as e:
        print(f"Error reading {config_file}: {e}")
        return False

    config['userName'] = username
    config['accessKey'] = access_key
    config['app'] = app_path

    try:
        with open(config_file, 'w') as f:
            yaml.dump(config, f, default_flow_style=False)
        USERNAME = username
        ACCESS_KEY = access_key
        APP_PATH = app_path
        return True
    except IOError as e:
        print(f"Error writing to {config_file}: {e}")
        return False

def get_credentials(credentials_file="user_key.txt"):
    """
    Reads username and access keys from the user_key.txt file.
    Assumes the file has username and key on alternating lines.
    """
    usernames = []
    access_keys = []
    try:
        with open(credentials_file, 'r') as f:
            lines = f.read().splitlines()
            for i in range(0, len(lines), 2):
                usernames.append(lines[i].strip())
                if i + 1 < len(lines):
                    access_keys.append(lines[i + 1].strip())
                else:
                    print("Warning: Odd number of lines in user_key.txt.  A username might be missing a corresponding key.")
    except FileNotFoundError:
        print("Error: user_key.txt not found.")
        return [], []
    return usernames, access_keys

@app.route("/")
def run_tests():
    """
    Flask route to execute the test command and the browserstack.py script.
    """
    global USERNAME, ACCESS_KEY, APP_PATH, TEST_COMMAND, BROWSERSTACK_SCRIPT
    if not USERNAME or not ACCESS_KEY or not APP_PATH:
        return "Error: browserstack.yml not configured yet. Run the main script first.", 500

    print(f"Executing test command: {TEST_COMMAND}")
    test_result = os.system(TEST_COMMAND)

    if test_result != 0:
        return f"Tests failed with exit code: {test_result}", 500

    print(f"Executing BrowserStack script: {BROWSERSTACK_SCRIPT}")
    try:
        # Use subprocess.run for better error handling and capturing output
        browserstack_process = subprocess.run(["browserstack-sdk", BROWSERSTACK_SCRIPT], capture_output=True, text=True, check=True)
        print(f"BrowserStack script output:\n{browserstack_process.stdout}")
        return f"Tests and BrowserStack script executed successfully with Username: {USERNAME}, App: {APP_PATH}\nBrowserStack script output:\n{browserstack_process.stdout}", 200
    except subprocess.CalledProcessError as e:
        print(f"BrowserStack script error:\n{e.stderr}")
        return f"BrowserStack script failed with exit code: {e.returncode}\nError:\n{e.stderr}", 500
    except FileNotFoundError:
        return f"Error: BrowserStack script '{BROWSERSTACK_SCRIPT}' not found.", 500

def run_flask_app():
    app.run(host="0.0.0.0", port=8080, debug=False, use_reloader=False)

def main():
    """
    Main function to orchestrate the updating of browserstack.yml and running tests.
    """
    global TEST_COMMAND, BROWSERSTACK_SCRIPT
    usernames, access_keys = get_credentials()
    apk_files = [f"app{i}.apk" for i in range(1, 4)]  # app1.apk, app2.apk, app3.apk

    if not usernames or not access_keys:
        print("No credentials found.  Please check user_key.txt.")
        return

    num_credentials = len(usernames)
    num_apks = len(apk_files)

    # Determine the number of iterations based on the shorter list
    num_iterations = min(num_credentials, num_apks)

    # Start Flask app in a separate thread
    flask_thread = threading.Thread(target=run_flask_app)
    flask_thread.daemon = True  # Allow the main thread to exit even if the Flask thread is running
    flask_thread.start()

    for i in range(num_iterations):
        username = usernames[i]
        access_key = access_keys[i]
        app_path = apk_files[i]

        print(f"Updating browserstack.yml with: Username={username}, App={app_path}")
        if update_browserstack_config(username, access_key, app_path):
            print("browserstack.yml updated successfully.")
            print(f"Configuration {i+1}: Access the Flask endpoint at http://localhost:8080/ to run tests and BrowserStack script with this configuration.")
            print("Waiting for Flask endpoint to be accessed...\n")
        else:
            print("Failed to update browserstack.yml. Skipping tests for this configuration.\n")

if __name__ == "__main__":
    main()
