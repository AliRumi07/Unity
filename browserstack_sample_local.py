from appium import webdriver
from appium.options.android import UiAutomator2Options
import time

# Set Appium capabilities
options = UiAutomator2Options().load_capabilities({
    "deviceName": "Google Pixel 3",
    "platformName": "android",
    "platformVersion": "9.0",
})

# Start Appium session
driver = webdriver.Remote("http://127.0.0.1:4723/wd/hub", options=options)

# Wait for 60 seconds
time.sleep(60)

# Quit driver
driver.quit()
