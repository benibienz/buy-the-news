# Buy the news - Crypto tweet alerts

Everyone has heard the old adage "buy the rumour - sell the news". However, in the hype-driven crypto market, big news stories such as
partnership announcements and exchange listings can see large surges in price over many hours after the story breaks (usually via twitter).
This app monitors the official twitter accounts of every coin on Binance (the leading altcoin exchange) and alerts the user when a tweet
coincides with a significant upwards price movement or contains certain words. It uses modified code from a much larger suite of tools I
have developed for crypto trading.


# Dependencies
Core:
- python 3.5+
- numpy
- ccxt
- python-dateutil
- twython (user must create their own twitter client)

Optional:
- twilio (if you want sms alerts)

# How to run
First you will need to create a twitter client and optionally a twilio client for sending sms alerts. I have a file called private.py in my
python path, which initialises all my authenticated clients so they can be imported easily. You can also edit the code to initialise your
clients; they need to be passed into twitter.py in the monitors directory.

When this is set up you simply run run_twitter.py, which creates and runs a monitor. Paramaters are explained in comments in twitter.py. The monitor
periodically checks [this twitter list](https://twitter.com/tundra_beats/lists/binance-coins) for new tweets. Each new tweet starts a
new thread that monitors price movements for the corresponding coin for 10 minutes. Alerts are printed and can optionally be announced
by text-to-speech synthesis and texted to your phone. Thresholds for price and trigger words/twitter handles can be adjusted easily in
the code. There are 2 tiers of alerts - amber and red - which depending on what mode the monitor is set to will be relayed in different
ways (e.g. an amber alert will not be sent as an sms).
