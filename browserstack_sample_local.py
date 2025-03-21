from flask import Flask
from appium import webdriver
from appium.options.android import UiAutomator2Options
import time
import threading

app = Flask(__name__)

# Flag to check if script is running
script_running = True

@app.route('/')
def status():
    return "Script is running" if script_running else "Script has stopped"

def run_appium_script():
    global script_running
    try:
        options = UiAutomator2Options().load_capabilities({
            "deviceName": "Google Pixel 3",
            "platformName": "android",
            "platformVersion": "9.0",
        })

        driver = webdriver.Remote("http://127.0.0.1:4723/wd/hub", options=options)

        # Wait for 10 seconds
        time.sleep(1)

        # Invoke driver.quit() after the test is done to indicate that the test is completed.
        driver.quit()
    except Exception as e:
        print(f"Error occurred: {e}")
    finally:
        # Schedule the script to run again after 2 minutes
        threading.Timer(1, run_appium_script).start()

if __name__ == '__main__':
    # Run Appium script for the first time
    threading.Thread(target=run_appium_script, daemon=True).start()

    # Start Flask server
    app.run(host="0.0.0.0", port=8080)
