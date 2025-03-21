from appium import webdriver
from appium.options.android import UiAutomator2Options
from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

# Options are only available since client version 2.3.0
# If you use an older client then switch to desired_capabilities
# instead: https://github.com/appium/python-client/pull/720
options = UiAutomator2Options().load_capabilities({
    # Specify device and os_version for testing
    "deviceName": "Google Pixel 3",
    "platformName": "android",
    "platformVersion": "9.0",

    # Add your caps here
})

driver = webdriver.Remote("http://127.0.0.1:4723/wd/hub", options=options)

# Wait for 60 seconds
time.sleep(60)


# Invoke driver.quit() after the test is done to indicate that the test is completed.
driver.quit()
