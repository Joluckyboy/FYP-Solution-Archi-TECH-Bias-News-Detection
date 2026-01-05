
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time
import os
from datetime import datetime
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import uuid # Used for unique generation of image names


from PIL import Image
import pytesseract

from flask import Flask, request, jsonify
app = Flask(__name__)


@app.route('/get-article', methods=['GET'])
def get_article():
    url = request.args.get('url')
    
    # Get the current timestamp for the image name -- OLD
    today = datetime.now()
    ss_string = today.strftime("%Y-%m-%dT%H-%M-%S").replace(" ", "")

    # UUID 4 generation is a completely random generation, there are other uuid generations, check the docs
    random_uuid = uuid.uuid4()
    ss_string = random_uuid

    # Set the path where the screenshot will be saved
    path = os.path.dirname(os.path.abspath(__file__))
    # Configure Chrome WebDriver options
    options = Options()
    options.add_argument("--headless")  # Run in headless mode to not open a browser window. If you disable this, you only get a viewport screenshot
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")  # Set window size for proper screenshot capturing
    options.add_argument('blink-settings=imagesEnabled=false') # Don't load any images

    # Initialize the Chrome WebDriver
    driver = webdriver.Chrome(options=options)

    # Navigate to the URL you want to capture
    driver.get(url)

    try:
        # Wait up to 10 seconds for the page to load
        # WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "article-content")))  # Wait for the first 'article' tag to load

        time.sleep(3)

        # Get the page height for full page screenshot
        page_height = driver.execute_script("return document.body.scrollHeight")
        driver.set_window_size(1920, page_height)  # Set the window size to full page height

        # Need to convert the UUID to string
        image_name = str(ss_string) + ".png"
    
        driver.get_screenshot_as_file(image_name)  # Capture and save screenshot to the specified path

        return jsonify({"body": pytesseract.image_to_string(Image.open(image_name)).strip().replace("\n"," ")})

    finally:
        driver.quit()

if __name__ == '__main__':
    app.run(debug=True)



# try:
#     # Wait up to 10 seconds for the page to load
#     WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "article-content")))  # Wait for the first 'article' tag to load

#     # Get the page height for full page screenshot
#     page_height = driver.execute_script("return document.body.scrollHeight")
#     driver.set_window_size(1920, page_height)  # Set the window size to full page height

#     # Need to convert the UUID to string
#     image_name = str(ss_string) + ".png"

#     driver.get_screenshot_as_file(image_name)  # Capture and save screenshot to the specified path
#     print(f"Screenshot saved to: {path}")
    
#     print(pytesseract.image_to_string(Image.open(image_name)))

# finally:
#     driver.quit()

# # Wait 3 seconds for page to load
# time.sleep(3)

# page_height = driver.execute_script("return document.body.scrollHeight")
# driver.set_window_size(1920, page_height)  # Set the window size to full page height

# # Need to convert the UUID to string
# image_name = str(ss_string) + ".png"
# # image_name = "testingthis.png"
# # Capture a full-page screenshot
# driver.get_screenshot_as_file(image_name)  # Capture and save screenshot to the specified path
# print(f"Screenshot saved to: {path}")

# # Close the browser window
# driver.quit()