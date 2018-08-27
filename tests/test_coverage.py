from common.dicts import BINANCE_BTC_MARKETS_TWITTER
from unittest import TestCase
import ccxt


class TestBinanceCoverage(TestCase):
    """
    The coins listed on Binance change constantly. I run this every now and then to check what needs to be
    updated in both the BINANCE_BTC_MARKETS_TWITTER dict and the twitter list itself.
    """

    def setUp(self):
        binance = ccxt.binance()
        self.markets = set(mar['base'] for mar in binance.fetch_markets())
        self.coverage = set(BINANCE_BTC_MARKETS_TWITTER.keys())

    def test_complete_coverage(self):
        exceptions = {'BTC',   # no btc-btc pair, no twitter anyway
                      'GAS',   # same as NEO
                      'TUSD',  # tethered to USD
                      }
        self.assertEqual(exceptions, self.markets - self.coverage)

    def test_no_extra_coverage(self):
        exceptions = set()  # rebranded symbols not updated by ccxt
        self.assertEqual(exceptions, self.coverage - self.markets)
