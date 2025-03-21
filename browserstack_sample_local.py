from flask import Flask, jsonify
from threading import Thread
from appium import webdriver
from appium.options.android import UiAutomator2Options
from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

# Flask app
app = Flask(__name__)

# Global variable to track test status
status = {"appium_status": "Initializing", "error": None}

# Define the /status endpoint
@app.route('/status', methods=['GET'])
def get_status():
    return jsonify(status)

# Function to run the Appium test
def run_appium_test():
    global status
    try:
        options = UiAutomator2Options().load_capabilities({
            "deviceName": "Google Pixel 3",
            "platformName": "Android",
            "platformVersion": "9.0",
            "appPackage": "com.android.settings",
            "appActivity": ".Settings",
            "automationName": "UiAutomator2"
        })

        # Start Appium session
        driver = webdriver.Remote("http://127.0.0.1:4723/wd/hub", options=options)
        status["appium_status"] = "Running"

        # Wait for an element (Example: 'Network & internet' settings)
        wait = WebDriverWait(driver, 10)
        element = wait.until(EC.presence_of_element_located(
            (AppiumBy.XPATH, "//android.widget.TextView[@text='Network & internet']")
        ))
        element.click()
        
        status["appium_status"] = "Test completed"

    except Exception as e:
        status["appium_status"] = "Error"
        status["error"] = str(e)

    finally:
        driver.quit()

# Start Appium test in a separate thread
thread = Thread(target=run_appium_test)
thread.start()

# Start Flask on 0.0.0.0:8080
if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8080, debug=False)
