import json
import time
import requests
import os
from bs4 import BeautifulSoup

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
USERS_FILE = os.path.join(BASE_DIR, "users.json")
HISTORY_FILE = os.path.join(BASE_DIR, "history.json")

print("[*] 뉴스 전송 백그라운드 워커 시작됨")

def load_users():
    try:
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

def load_history():
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def save_history(history):
    try:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[에러] history 저장 실패: {e}")

def search_news(keyword):
    url = f"https://search.naver.com/search.naver?where=news&query={keyword}"
    try:
        response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
        soup = BeautifulSoup(response.text, "html.parser")
        links = soup.select(".news_tit")
        results = []
        for link in links[:3]:
            title = link.get("title")
            href = link.get("href")
            results.append({"title": title, "link": href})
        return results
    except Exception as e:
        print(f"[에러] 뉴스 검색 실패: {e}")
        return []

def send_message(token, chat_id, text):
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    try:
        response = requests.post(url, data={"chat_id": chat_id, "text": text})
        print(f"[📤] 전송됨: {text[:30]}... 상태: {response.status_code}")
    except Exception as e:
        print(f"[에러] 전송 오류: {e}")

last_sent = load_history()

while True:
    print("\n[🔁] 루프 시작")
    users = load_users()
    for user in users:
        chat_id = user["chat_id"]
        token = user["telegram_token"]
        keywords = user.get("keywords", [])
        interval = int(user.get("interval", 600))
        last_time = int(user.get("last_sent", 0))

        if time.time() - last_time < interval:
            continue

        for kw in keywords:
            articles = search_news(kw)
            for article in articles:
                key = f"{chat_id}_{kw}_{article['link']}"
                if key not in last_sent:
                    send_message(token, chat_id, f"📰 {article['title']}\n🔗 {article['link']}")
                    last_sent[key] = int(time.time())

        user["last_sent"] = int(time.time())

    save_history(last_sent)
    time.sleep(60)
