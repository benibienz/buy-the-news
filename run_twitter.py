import ccxt
from monitors.twitter import TwitterMonitor
from common.dicts import BINANCE_BTC_MARKETS_TWITTER

binance_monitor = TwitterMonitor(
    client=ccxt.binance(),
    handle_list=BINANCE_BTC_MARKETS_TWITTER,
    reduced_mode=False,
    log_data=True,
    quiet_mode=False,
    sms=False
)


binance_monitor.main()