from dateutil import parser
import pickle
import os
import numpy as np
from datetime import datetime
from twython import Twython, TwythonError


def twitter_ts(created_at):
    """Parse twitter timestamp - returns datetime object. WARNING: ignores tweet date and uses today's date!"""
    ts_idx = created_at.find(':') - 2
    return parser.parser().parse(created_at[ts_idx: ts_idx + 8])


def binance_ts(ts):
    """Parse timestamps from ccxt binance client"""
    if isinstance(ts, int) or isinstance(ts, float):
        return datetime.utcfromtimestamp(ts / 1000)
    elif isinstance(ts, np.ndarray) or isinstance(ts, list):
        return np.array([binance_ts(t) for t in ts])


def dt_time_diff(dt0, dt1):
    """Subtract two datetime objects to get time difference in seconds"""
    return (dt1 - dt0).total_seconds()


def last_trade_before_dt(trades, dt):
    """
    Finds last trade before given time from a list of trades.
    :param trades: the return from ccxt.fetch_trades()
    :param dt: datetime object
    :return: last trade before dt
    """
    for i in range(len(trades) - 1, -1, -1):
        if dt_time_diff(binance_ts(trades[i]['timestamp']), dt) > 0:
            return trades[i]
    else:
        raise OutOfRangeError('Earliest trade: {}, dt: {}'.format(binance_ts(trades[0]['timestamp']), dt))


def splice_trades(trades1, trades2, targ_len=100):
    """ Splice 2 calls to ccxt.fetch_trades() without overlap """

    if len(trades1) >= targ_len:
        raise OutOfRangeError('Length of first trades list exceeds target')
    try:
        idx = trades2.index(trades1[-1]) + 1
    except ValueError:
        raise OutOfRangeError('Trades do not overlap')
    spliced = trades1 + trades2[idx:idx + targ_len - len(trades1)]
    return spliced


def reduce_trades(trades):
    """ Reduce trades dict down to relevant info """
    reduced = []
    for trade in trades:
        reduced.append({k: trade[k] for k in ('timestamp', 'price', 'amount', 'cost')})
    return reduced


def save_tweet(tweet, name='tweet'):
    pickle.dump(tweet, open(os.path.join('logs', 'tweets', '{}.p'.format(name)), 'wb'))


def load_tweet(name='tweet', path=None):
    if path is None:
        path = os.path.join('logs', 'tweets', '{}.p'.format(name))
    with open(path, 'rb') as f:
        tweet = pickle.load(f)
    return tweet


def print_time():
    return datetime.utcnow().time().strftime('%H:%M:%S')


def make_twitter_list(list_name, creator_handle, client, handles):
    client.create_list(name=list_name, slug=list_name, owner_screen_name=creator_handle)
    for coin, handle in handles:
        try:
            client.add_list_member(slug=list_name, owner_screen_name=creator_handle, screen_name=handle)
        except TwythonError as e:
            print(e)

class OutOfRangeError(Exception):
    pass