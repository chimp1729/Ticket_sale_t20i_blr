import json
import os
import re
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse

URL = (
    "https://ticketgenie.in/member/"
    "india-vs-west-indies-5th-t20i-match-bengaluru-Oct17-2026/511"
)
STATE_FILE = Path("state.json")

# SAFETY: Keep these phrases specific. Generic terms like "Book Now" may
# refer to member-only booking or unrelated content and should not trigger a call.
# Update these only after checking the page's actual public-sale wording.
PUBLIC_SALE_PHRASES = [
    "general public sale is live",
    "public booking is now open",
    "tickets available for general public",
]

NOT_PUBLIC_PHRASES = [
    "general public sale not started",
    "public booking opens soon",
    "coming soon for general public",
]

def load_state():
    try:
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {"alert_sent": False}

def save_state(state):
    STATE_FILE.write_text(
        json.dumps(state, indent=2) + "\n",
        encoding="utf-8"
    )

def get_page_text():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)

        page = browser.new_page(
            user_agent=(
                "Mozilla/5.0 (X11; Linux x86_64) "
                "AppleWebKit/537.36 Chrome/131.0.0.0 Safari/537.36"
            )
        )

        try:
            response = page.goto(
                URL,
                wait_until="domcontentloaded",
                timeout=60000,
            )

            page.wait_for_timeout(5000)

            print(
                "HTTP status:",
                response.status if response else "No response"
            )

            text = page.locator("body").inner_text(timeout=15000)

            print("Rendered text length:", len(text))
            print("Rendered text preview:", repr(text[:1500]))

            return re.sub(r"\s+", " ", text).lower()

        finally:
            browser.close()

def public_sale_confirmed(text):
    # Fail closed if page is inaccessible, changed, or lacks explicit sale wording.
    if any(phrase in text for phrase in NOT_PUBLIC_PHRASES):
        return False
    return any(phrase in text for phrase in PUBLIC_SALE_PHRASES)

def place_call():
    required = [
        "TWILIO_ACCOUNT_SID",
        "TWILIO_AUTH_TOKEN",
        "TWILIO_FROM_NUMBER",
        "ALERT_TO_NUMBER",
    ]
    missing = [key for key in required if not os.environ.get(key)]
    if missing:
        raise RuntimeError("Missing GitHub Actions secrets: " + ", ".join(missing))

    voice = VoiceResponse()
    voice.say(
        "Ticket alert. Public ticket sales may now be open for India versus "
        "West Indies, fifth T20 international, in Bengaluru on October "
        "seventeenth, twenty twenty-six. Please open TicketGenie and confirm "
        "availability now.",
        language="en-IN",
    )
    voice.pause(length=1)
    voice.say(
        "The booking page is ticketgenie dot in. Please check the match page.",
        language="en-IN",
    )

    client = Client(
        os.environ["TWILIO_ACCOUNT_SID"],
        os.environ["TWILIO_AUTH_TOKEN"],
    )
    call = client.calls.create(
        to=os.environ["ALERT_TO_NUMBER"],
        from_=os.environ["TWILIO_FROM_NUMBER"],
        twiml=str(voice),
    )
    print("Call requested. SID:", call.sid)

def main():
    if os.environ.get("TEST_CALL", "").lower() == "true":
        print("TEST_CALL enabled; placing a test call.")
        place_call()
        return
    state = load_state()
    if state.get("alert_sent"):
        print("Alert already sent; skipping duplicate call.")
        return

    text = get_page_text()
    print("Page fetched. Visible text length:", len(text))

    if public_sale_confirmed(text):
        print("Explicit public-sale phrase found; placing alert call.")
        place_call()
        state["alert_sent"] = True
        save_state(state)
    else:
        print("Public ticket sale NOT confirmed; no call placed.")
        print("If the page uses different wording, review the Actions log and update PUBLIC_SALE_PHRASES.")
        
if __name__ == "__main__":
    main()
