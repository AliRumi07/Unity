from appium import webdriver
from appium.options.android import UiAutomator2Options
from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time


options = UiAutomator2Options().load_capabilities({
    # Specify device and os_version for testing
    "deviceName": "Google Pixel 3",
    "platformName": "android",
    "platformVersion": "9.0",

})

driver = webdriver.Remote("http://127.0.0.1:4723/wd/hub", options=options)

# Wait for 1 seconds
time.sleep(1)


# Invoke driver.quit() after the test is done to indicate that the test is completed.
driver.quit()
