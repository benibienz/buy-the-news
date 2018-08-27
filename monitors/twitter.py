import os
import threading
import traceback
import numpy as np
import time
from datetime import datetime
import pickle
from private import TWITTER_CLIENT
from common.util import dt_time_diff, twitter_ts, print_time, last_trade_before_dt, splice_trades, reduce_trades, OutOfRangeError
from common.logger_config import init_logger, error_msg
from common.alerts import Alert, check_custom_triggers

DATA_LOG_PATH = os.path.join('logs', 'data')

RED_ALERT_GAIN_THRESH = {30: 0.6, 60: 1.1, 150: 1.8, 300: 3.0, 600: 5.0}  # interval (seconds) : % gain
AMBER_ALERT_GAIN_THRESH = {30: 0.4, 60: 0.9, 150: 1.4, 300: 2.5, 600: 4.5}  # interval (seconds) : % gain
LONG_MA_LEN = 100
TWITTER_CHECK_INTERVALS = [15, 60]  # seconds - recommended 15 for normal and 60 for reduced
MONITOR_INTERVALS = [30, 60, 150, 300, 600]  # seconds
MONITOR_INTERVALS_REDUCED = [60, 300, 600]  # seconds - for longer twitter check intervals


class TwitterMonitor:
    """
    Monitors a twitter list and checks coin price movements after every tweet.
    If a tweet coincides with a significant price gain, the user is alerted.
    There are two tiers of monitors:
    - Amber: audio announcement and print to console
    - Red: audio announcement, print to console and text to user
    Alerts can also be assigned to other signals such as keywords in tweets.
    """
    def __init__(self, client, handle_list, reduced_mode=False, log_data=True, quiet_mode=False, sms=False):
        self.client = client
        self.handle_list = handle_list
        self.reduced_mode = reduced_mode  # lightweight version with fewer API calls and monitoring intervals
        self.quiet_mode = quiet_mode  # no audio announcements for amber monitors
        if sms:
            from private import TWILIO_CLIENT
            self.sms_client = TWILIO_CLIENT  # sends sms msgs for red alerts
        else:
            self.sms_client = None
        self.log_data = log_data  # set to True to log data for each coin monitored

        self.refresh_rate = TWITTER_CHECK_INTERVALS[1] if reduced_mode else TWITTER_CHECK_INTERVALS[0]

        self.logger = init_logger('Alerts', 'monitors.log')
        self.thread_count = 0

    def main(self):
        """ Call to main monitor loop. Will restart if there is an exception """
        self.logger.info('Main monitor started at {} ({} mode with data logging {} and sms msgs {})'.format(
            print_time(), ('reduced' if self.reduced_mode else 'normal'), ('on' if self.log_data else 'off'),
            ('on' if self.sms_client is not None else 'off')))
        self.logger.info('Refreshing twitter every {} seconds'.format(self.refresh_rate))

        while True:
            try:
                self._main()
            except Exception as e:
                self.logger.error(error_msg(e))
                traceback.print_exc()
                self.logger.info('Attempting to restart after 60 seconds'.format(print_time()))
                time.sleep(60)
                self.logger.info('Restarting main monitor')

    def monitor_market(self, symbol, alert=None, logger=None, init_dt=None):
            """
            Checks the price of a given market at the time intervals given in the MONITOR_INTERVALS variable.
            :param symbol: market symbol
            :param alert: optional custom alert object
            :param logger: optional logger
            :param init_dt: starting datetime (cannot be bigger than first interval) - defaults to now
            """
            if logger is None:
                logger = self.logger
            if alert is None:
                alert = Alert(symbol, logger=logger)
            intervals = MONITOR_INTERVALS if not self.reduced_mode else MONITOR_INTERVALS_REDUCED
            pair = symbol + '/BTC'
            init_trades = self.client.fetch_trades(pair)

            if init_dt is not None:
                last_trade = last_trade_before_dt(init_trades, init_dt)
            else:
                last_trade = init_trades[-1]
                init_dt = datetime.utcnow()

            prev_interval = dt_time_diff(init_dt, datetime.utcnow())
            assert prev_interval < intervals[0], \
                'Cannot monitor {}s interval for an initial time of {}'.format(intervals[0], init_dt)

            init_price = last_trade['price']
            obs = [self.client.fetch_order_book(pair)]
            gains = []
            trades_after = [last_trade]

            for i, curr_interval in enumerate(intervals):
                time.sleep(curr_interval - prev_interval)
                if trades_after is not None and len(trades_after) < 100:
                    trades = self.client.fetch_trades(pair)
                    try:
                        trades_after = splice_trades(trades_after, trades)
                    except OutOfRangeError:
                        logger.warning('trade splicing failed - there may be too many trades to log')
                        trades_after = None

                obs.append(self.client.fetch_order_book(pair))
                price = self.client.fetch_ticker(pair)['last']
                gain_since = 100 * (price / init_price - 1)  # %
                gains.append(gain_since)
                logger.info('{}m monitoring of {} complete at {}. Gain = {:.2f}%'.format(
                    curr_interval / 60, symbol, print_time(), gain_since))

                if gain_since > RED_ALERT_GAIN_THRESH[curr_interval]:
                    alert.red('large gain', trigger='{}s gain'.format(curr_interval))
                elif gain_since > AMBER_ALERT_GAIN_THRESH[curr_interval]:
                    alert.amber('medium gain', trigger='{}s gain'.format(curr_interval))
                prev_interval = curr_interval

            if self.log_data and alert.curr_tier is not None:
                # OHLCV should be replaced later
                ohlcv = np.array(
                    self.client.fetch_ohlcv(pair, timeframe='1m', limit=int(intervals[-1] / 60) + LONG_MA_LEN))

                if trades_after is not None and not self.reduced_mode:
                    # 100 trades either side of init dt
                    trades_log = {'before': reduce_trades(init_trades), 'after': reduce_trades(trades_after)}
                else:
                    trades_log = None

                data = {
                    'init price': init_price,
                    'symbol': symbol,
                    'ohlcv': ohlcv,
                    'trades': trades_log,
                    'gains': gains,
                    'order books': obs,
                    'timestamp': init_dt,
                    'alert history': alert.export()
                }
                pickle.dump(data, open(os.path.join(DATA_LOG_PATH, '{}-{}.p'.format(init_dt, symbol)), 'wb'))

    def _main(self):
        """ Main monitor loop """
        while True:
            time.sleep(self.refresh_rate - time.time() % self.refresh_rate)
            tweets = TWITTER_CLIENT.get_list_statuses(slug='binance-coins', owner_screen_name='tundra_beats')
            # LOGGER.debug('Retrieved tweets')
            for tweet in tweets:
                tweet_dt = twitter_ts(tweet['created_at'])
                time_since = dt_time_diff(tweet_dt, datetime.utcnow())
                if 0 <= time_since < self.refresh_rate:
                    handle = tweet['user']['screen_name'].lower()
                    symbol = [coin for coin, name in self.handle_list.items() if name == handle]
                    if not symbol or len(symbol) > 1:
                        self.logger.error('Twitter handle not in list. Symbol list: {}. Handle: {}'.format(
                            symbol, handle))
                    else:
                        symbol = symbol[0]
                        self.thread_count += 1  # make a new thread
                        t = threading.Thread(
                            target=self._new_monitor_thread,
                            args=(symbol, handle, tweet, tweet_dt))
                        t.start()
                else:
                    break

    def _new_monitor_thread(self, symbol, handle, tweet, tweet_dt):
        thread_logger = init_logger('Thread {}'.format(self.thread_count), 'monitors.log')
        thread_logger.info(
            'Monitoring {} tweet posted at {}'.format(symbol, tweet_dt.time().strftime('%H:%M:%S')))

        txt = tweet['text']
        alert = Alert(
            symbol=symbol,
            txt=txt,
            url=tweet['entities']['urls'][-1]['url'] if tweet['entities']['urls'] else None,
            quiet_mode=self.quiet_mode,
            sms_client=self.sms_client,
            logger=thread_logger
        )
        try:
            triggers = check_custom_triggers(handle, txt)
            for trigger in triggers:
                alert.alert(trigger['msg'], level=trigger['level'], trigger=trigger['msg'])
            self.monitor_market(symbol, alert=alert, logger=thread_logger, init_dt=tweet_dt)
        except Exception as e:
            traceback.print_exc()
            thread_logger.error(error_msg(e))







