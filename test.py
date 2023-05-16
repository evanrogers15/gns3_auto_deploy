from selenium import webdriver

# Create a WebDriver instance (e.g., Chrome)
driver = webdriver.Chrome()

# Navigate to the desired website
driver.get("http://100.92.8.44/static/web-ui/server/1/project/8c622e19-44aa-4703-9d46-b1a49399007b")

# Capture a screenshot and save it as "screenshot.png"
driver.save_screenshot("screenshot.png")

# Close the WebDriver
driver.quit()
