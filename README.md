# Ticket Sale Alert — India vs West Indies 5th T20I

Target page:
https://ticketgenie.in/ticket/india-vs-west-indies-5th-t20i-match-bengaluru-Oct17-2026/511

## Files
- `monitor.py`: fetches the page and calls through Twilio only when an explicit public-sale phrase is found.
- `.github/workflows/ticket-alert.yml`: scheduled GitHub Actions workflow (15-minute cron).
- `state.json`: avoids duplicate calls after the alert has been sent.

## Before enabling calls
The wording on the ticket page must be checked and `PUBLIC_SALE_PHRASES` in `monitor.py` adjusted to match the site's exact public-sale status wording. The detector deliberately does **not** use generic phrases like "Book Now", because those can refer to member-only booking. It may not detect a dynamically rendered page; inspect the Actions logs first.

## GitHub repository secrets
Add these under Settings → Secrets and variables → Actions:
- `TWILIO_ACCOUNT_SID`
- `TWILIO_AUTH_TOKEN`
- `TWILIO_FROM_NUMBER`
- `ALERT_TO_NUMBER`

Never commit credentials to the repository or share them in chat. Use international phone number format for `ALERT_TO_NUMBER` (e.g. `+91...`).

## Deploy
Copy the files into the repository, then use Actions → Ticket Sale Monitor → Run workflow to test manually.
The workflow may run later than the scheduled time. GitHub Actions scheduling is best-effort, not a strict real-time guarantee.

## Important
A successful manual call test does not guarantee that every automated API call to an Indian number will be permitted by the Twilio account's region, caller ID, and trial restrictions. Verify the call flow before relying on it.
