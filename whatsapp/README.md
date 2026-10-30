# Passenger WhatsApp alerts

The Depot desk has a **Notify passengers on WhatsApp** button on every alarm. It talks to a small helper
that runs on the depot PC and sends the messages with [pywhatkit](https://pypi.org/project/pywhatkit/).

pywhatkit works by opening WhatsApp Web in the PC's default browser and pressing Send, so:

- messages go out from whichever WhatsApp account is logged in to <https://web.whatsapp.com> on that PC;
- the PC must be unlocked, and for about 25 seconds per passenger the helper takes over the keyboard.

## Setup

1. `pip install pywhatkit`
2. Copy `passengers.example.json` to `passengers.json` and fill in the sender and passengers
   (`passengers.json` is git-ignored, so the numbers stay off GitHub).
3. Log in to WhatsApp Web in your default browser with the sender's phone.
4. Start the helper: `python notify_server.py` (or `python notify_server.py --dry-run` to test without sending).
5. Open the site, go to **Depot desk**. The *Passenger WhatsApp alerts* panel shows *Helper connected*.
   You can add passengers there too.

The helper only listens on `127.0.0.1:8765` and only accepts requests from the origins in
`allowed_origins` (the Vercel site), `localhost` and local files.
