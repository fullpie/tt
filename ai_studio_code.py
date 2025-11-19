# @title 🤖 Colab 全自動登入 + 狙擊 (實驗性功能)
# @markdown ### 1. 帳號設定
EMAIL = "" # @param {type:"string"}
PASSWORD = "" # @param {type:"string"}

# @markdown ### 2. 搶購設定
PRODUCT_ID = "A2829694002" # @param {type:"string"}
QTY = 2 # @param {type:"integer"}

import os
import time
import json
import requests
from bs4 import BeautifulSoup
from datetime import datetime

# === 第一步：安裝環境 (只需執行一次) ===
print("⚙️ 正在安裝 Chrome 與 Selenium (約需 30 秒)...")
!apt-get update -y > /dev/null
!apt-get install -y chromium-chromedriver > /dev/null
!pip install selenium > /dev/null
print("✅ 安裝完成！")

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from IPython.display import Image, display

# === 設定 Chrome (無頭模式) ===
chrome_options = Options()
chrome_options.add_argument('--headless') # 無螢幕模式
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')
chrome_options.add_argument('--disable-blink-features=AutomationControlled')
chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

# === 核心：自動登入 ===
def auto_login():
    log("🚀 啟動隱形瀏覽器...")
    driver = webdriver.Chrome(options=chrome_options)
    
    try:
        # 1. 前往登入頁
        log("連線到登入頁面...")
        driver.get("https://p-bandai.com/tw/login")
        
        # 2. 輸入帳密
        log("正在輸入帳號密碼...")
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, "username")))
        
        driver.find_element(By.NAME, "username").send_keys(EMAIL)
        driver.find_element(By.NAME, "password").send_keys(PASSWORD)
        
        # 3. 點擊登入
        # 尋找登入按鈕 (通常包含 '登入' 或 'SIGN IN')
        try:
            login_btn = driver.find_element(By.XPATH, "//button[contains(text(), '登入') or contains(text(), 'SIGN IN')]")
            login_btn.click()
            log("已點擊登入按鈕，等待跳轉...")
        except:
            log("❌ 找不到登入按鈕，請看截圖")
            driver.save_screenshot("error_login.png")
            display(Image("error_login.png"))
            return None

        # 4. 等待登入成功 (檢查網址是否改變，或出現會員元素)
        time.sleep(5) # 等待 5 秒
        
        # 檢查是否還在登入頁
        if "login" in driver.current_url:
            log("⚠️ 警告：似乎還在登入頁面 (可能遇到驗證碼)")
            # 截圖給你看
            driver.save_screenshot("stuck.png")
            display(Image("stuck.png"))
            print("如果看到驗證碼圖片，代表 Colab 無法通過機器人驗證。請改用手動複製 Cookie 的方法。")
            return None
        
        log("✅ 登入成功！正在提取 Cookie...")
        
        # 5. 提取 Cookie 轉換為 requests 格式
        selenium_cookies = driver.get_cookies()
        cookie_str = ""
        for cookie in selenium_cookies:
            cookie_str += f"{cookie['name']}={cookie['value']}; "
            
        return cookie_str

    except Exception as e:
        log(f"❌ 發生錯誤: {e}")
        driver.save_screenshot("crash.png")
        display(Image("crash.png"))
        return None
        
    finally:
        driver.quit()

# === 搶購邏輯 (API) ===
def start_sniping(cookie_str):
    HEADERS = {
        "User-Agent": "Mozilla/5.0",
        "Content-Type": "application/json",
        "Origin": "https://p-bandai.com",
        "Referer": f"https://p-bandai.com/tw/item/{PRODUCT_ID}",
        "Cookie": cookie_str
    }
    
    api_url = "https://p-bandai.com/api/cart/addToCart"
    
    # 獲取 Token
    log("🕵️ 正在獲取 CSRF Token...")
    try:
        res = requests.get(f"https://p-bandai.com/tw/item/{PRODUCT_ID}", headers=HEADERS)
        soup = BeautifulSoup(res.text, 'html.parser')
        token_tag = soup.find('meta', {'name': 'csrf-token'}) or soup.find('meta', {'name': 'x-csrf-token'})
        
        if not token_tag:
            log("❌ 抓不到 Token，可能登入失效")
            return

        token = token_tag.get('content')
        log(f"🔑 Token: {token[:10]}...")
        
        # 發送購買
        payload = {"sku_code": PRODUCT_ID, "qty": QTY, "_csrf": token}
        req_headers = HEADERS.copy()
        req_headers["X-CSRF-Token"] = token
        req_headers["X-Requested-With"] = "XMLHttpRequest"
        
        log("🚀 發射 API...")
        res = requests.post(api_url, headers=req_headers, json=payload)
        
        if res.status_code == 200:
            log(f"🎉🎉🎉 搶購成功！回傳: {res.text}")
        else:
            log(f"☠️ 失敗 ({res.status_code}): {res.text}")
            
    except Exception as e:
        log(f"❌ 連線錯誤: {e}")


# === 主程式 ===
if not EMAIL or not PASSWORD:
    print("❌ 請先填寫 EMAIL 和 PASSWORD")
else:
    my_cookie = auto_login()
    
    if my_cookie:
        print("-" * 30)
        print("身分驗證完成，開始執行搶購...")
        start_sniping(my_cookie)
    else:
        print("⛔ 自動登入失敗，無法執行。")