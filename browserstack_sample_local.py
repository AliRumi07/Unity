from appium import webdriver
from appium.options.android import UiAutomator2Options
from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time


driver = webdriver.Remote("http://127.0.0.1:4723/wd/hub", options=options)

# Wait for 60 seconds
time.sleep(60)

driver.quit()
