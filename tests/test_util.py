from unittest import TestCase
from common.util import load_tweet, dt_time_diff, twitter_ts, last_trade_before_dt, binance_ts, splice_trades, OutOfRangeError
from datetime import datetime, timezone


class TestTwitterTS(TestCase):

    def setUp(self):
        self.tweet = load_tweet(path='{}.p'.format('tweet'))

    def test_datetime(self):
        # Sun Mar 25 16:40:59 +0000 2018
        self.assertEqual(twitter_ts(self.tweet['created_at']).time(), datetime(2018, 3, 25, 16, 40, 59).time())


class TestDTTimeDiff(TestCase):

    def test_small_diff(self):
        ts0 = datetime(2018, 3, 10, 23, 59, 47)
        ts1 = datetime(2018, 3, 10, 23, 59, 50)
        self.assertEqual(3, dt_time_diff(ts0, ts1))

    def test_neg_diff(self):
        ts0 = datetime(2018, 3, 10, 23, 59, 50)
        ts1 = datetime(2018, 3, 10, 23, 59, 47)
        self.assertEqual(-3, dt_time_diff(ts0, ts1))

    def test_over_midnight(self):
        ts0 = datetime(2018, 3, 10, 23, 59, 50)
        ts1 = datetime(2018, 3, 11, 0, 0, 11)
        self.assertEqual(21, dt_time_diff(ts0, ts1))

    def test_neg_diff_over_midnight(self):
        ts0 = datetime(2018, 3, 11, 0, 0, 11)
        ts1 = datetime(2018, 3, 10, 23, 59, 50)
        self.assertEqual(-21, dt_time_diff(ts0, ts1))

    def test_no_diff(self):
        ts0 = datetime.now()
        ts1 = datetime.now()
        self.assertAlmostEqual(0, dt_time_diff(ts0, ts1), places=3)


class TestBinanceTS(TestCase):

    def test_general(self):
        ts = 1524049645669
        ts1 = 1524049645.669
        self.assertEqual(ts1, binance_ts(ts).replace(tzinfo=timezone.utc).timestamp())


class TestLastTradeBeforeDT(TestCase):

    def setUp(self):
        self.trades = [{'timestamp': 1524008629637}, {'timestamp': 1524008637057}]
        self.before = datetime(2018, 4, 17, 23, 43, 44)
        self.during = datetime(2018, 4, 17, 23, 43, 55)
        self.after = datetime(2018, 4, 17, 23, 44, 5)

    def test_in_range(self):
        self.assertEqual(self.trades[0], last_trade_before_dt(self.trades, self.during))

    def test_after_range(self):
        self.assertEqual(self.trades[1], last_trade_before_dt(self.trades, self.after))

    def test_not_in_range(self):
        self.assertRaises(OutOfRangeError, last_trade_before_dt, self.trades, self.before)


class TestSpliceTrades(TestCase):

    def test_raises(self):
        trades1 = [1, 2, 3]
        trades2 = [5]
        self.assertRaises(OutOfRangeError, splice_trades, trades1, trades2, 2)
        self.assertRaises(OutOfRangeError, splice_trades, trades1, trades2)

    def test_general(self):
        trades1 = [1, 2, 3, 4]
        trades2 = [3, 4, 5, 6, 7, 8, 9, 10]
        ret1 = [1, 2, 3, 4, 5, 6, 7]
        ret2 = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        self.assertEqual(ret1, splice_trades(trades1, trades2, targ_len=7))
        self.assertEqual(ret2, splice_trades(trades1, trades2))
