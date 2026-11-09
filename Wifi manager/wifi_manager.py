import os
import time
import json
import smtplib
from email.mime.text import MIMEText
from typing import Dict, Any, List, Tuple, Optional

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv()

ROUTER_BASE_URL = os.getenv("ROUTER_BASE_URL", "http://192.168.0.1").rstrip("/")
ROUTER_USERNAME = os.getenv("ROUTER_USERNAME")
ROUTER_PASSWORD = os.getenv("ROUTER_PASSWORD")

POLL_SECONDS = int(os.getenv("POLL_SECONDS", "45"))

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

SMTP_HOST = os.getenv("SMTP_HOST")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
EMAIL_TO = os.getenv("EMAIL_TO")

STATE_FILE = "devices_state.json"


def telegram_send(message: str) -> None:
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    requests.post(url, json=payload, timeout=15)


def email_send(subject: str, body: str) -> None:
    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = subject
    msg["From"] = SMTP_USERNAME
    msg["To"] = EMAIL_TO

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=20) as server:
        server.starttls()
        server.login(SMTP_USERNAME, SMTP_PASSWORD)
        server.send_message(msg)


def load_state() -> Dict[str, Any]:
    if not os.path.exists(STATE_FILE):
        return {"known_macs": []}
    with open(STATE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_state(state: Dict[str, Any]) -> None:
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def router_login(session: requests.Session) -> None:
    """
    TODO (fill for your exact Tenda firmware):
    - Determine login endpoint URL
    - Determine POST payload fields
    - Ensure any special parameters/captcha/session keys are handled
    """
    login_url = f"{ROUTER_BASE_URL}/login"  # <-- placeholder
    payload = {
        "username": ROUTER_USERNAME,  # <-- placeholder keys
        "password": ROUTER_PASSWORD,  # <-- placeholder keys
    }

    # Example:
    # r = session.post(login_url, data=payload, timeout=15)
    # if "logout" not in r.text: raise RuntimeError("Login failed")

    raise NotImplementedError(
        "router_login() needs exact login URL + form field names for your router."
    )


def fetch_connected_devices(session: requests.Session) -> List[Dict[str, str]]:
    """
    TODO (fill for your exact connected-devices page):
    - Identify URL that returns/contains the online devices list
    - Parse MAC/IP/hostname
    """
    devices_url = f"{ROUTER_BASE_URL}/devices"  # <-- placeholder
    r = session.get(devices_url, timeout=15)
    r.raise_for_status()

    soup = BeautifulSoup(r.text, "html.parser")

    # TODO: replace with correct selectors for your table.
    # Example placeholder:
    # table = soup.select_one("table#clientList")
    # for row in table.select("tr")[1:]:
    #     mac = ...
    #     ip = ...
    #     name = ...

    return []


def diff_new_devices(prev_known: List[str], current_devices: List[Dict[str, str]]) -> List[Dict[str, str]]:
    prev_set = set(prev_known)
    new_devs = []
    for d in current_devices:
        mac = d.get("mac")
        if mac and mac not in prev_set:
            new_devs.append(d)
    return new_devs


def main():
    if not (TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID):
        print("Warning: Telegram notifications are not configured.")
    
    if not (SMTP_HOST and SMTP_USERNAME and SMTP_PASSWORD and EMAIL_TO):
        print("Warning: Email notifications are not configured.")

    state = load_state()
    known_macs = state.get("known_macs", [])

    session = requests.Session()

    print("Wi-Fi manager started. Polling every", POLL_SECONDS, "seconds...")
    while True:
        try:
            # 1) login
            router_login(session)

            # 2) fetch device list
            devices = fetch_connected_devices(session)

            # Normalize MAC format if needed (optional)
            for d in devices:
                if "mac" in d and d["mac"]:
                    d["mac"] = d["mac"].lower()

            # 3) detect new devices
            new_devs = diff_new_devices(known_macs, devices)

            if new_devs:
                for d in new_devs:
                    mac = d.get("mac", "unknown")
                    ip = d.get("ip", "")
                    name = d.get("name", "")

                    msg = f"New device detected!\nName: {name}\nIP: {ip}\nMAC: {mac}"
                    print(msg)

                    # Telegram + Email
                    telegram_send(msg)
                    email_send("WiFi: New device detected", msg)

                    # update known
                    if mac and mac not in known_macs:
                        known_macs.append(mac)

                state["known_macs"] = known_macs
                save_state(state)

            else:
                print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] No new devices. Total known: {len(known_macs)}")

        except Exception as e:
            print("Error:", repr(e))

        time.sleep(POLL_SECONDS)


if __name__ == "__main__":
    main()
