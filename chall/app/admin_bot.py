import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

CHALLENGE_DOMAIN = os.getenv("CHALLENGE_DOMAIN", "http://localhost:5000")
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "pass")


def visit_url(paste_url: str):
    chrome_options = Options()

    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-software-rasterizer")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--single-process")
    chrome_options.add_argument("--disk-cache-dir=/dev/null")
    chrome_options.add_argument("--disable-notifications")

    service = Service()

    try:
        with webdriver.Chrome(service=service, options=chrome_options) as driver:
            print("[BOT] Opening login page…")
            driver.get(f"{CHALLENGE_DOMAIN}/login")
            print("[BOT] Login page loaded.")

            username_field = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.NAME, "username"))
            )
            password_field = driver.find_element(By.NAME, "password")

            username_field.send_keys(ADMIN_USERNAME)
            password_field.send_keys(ADMIN_PASSWORD)
            password_field.submit()

            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )

            driver.get(paste_url)

            time.sleep(5)

    except Exception as e:
        print(f"Bot error: {str(e)}")
        raise

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <PASTE_URL>")
        sys.exit(1)

    visit_url(sys.argv[1])
