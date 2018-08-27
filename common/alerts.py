import os

# Trigger phrases and handles for binance monitor
# note that handle must be str and txt phrases nust be a list of strings
BINANCE_TRIGGERS = [
    {'handle': 'binance', 'txt': ['competition'], 'level': 'red', 'msg': 'binance competition'},
    {'handle': None, 'txt': ['upbit'], 'level': 'red', 'msg': 'upbit listing'},
    {'handle': None, 'txt': ['bithumb'], 'level': 'red', 'msg': 'bithumb listing'},
    {'handle': None, 'txt': ['huobi'], 'level': 'red', 'msg': 'huobi listing'},
    {'handle': None, 'txt': ['okex'], 'level': 'red', 'msg': 'okex listing'},
    {'handle': 'binance', 'txt': None, 'level': 'red', 'msg': 'binance update'},
    {'handle': None, 'txt': ['listed'], 'level': 'amber', 'msg': 'exchange listing'},
    {'handle': None, 'txt': ['announce'], 'level': 'amber', 'msg': 'announcement'},
    {'handle': None, 'txt': ['partnership'], 'level': 'amber', 'msg': 'partnership'}
]


def check_custom_triggers(handle, txt, custom_triggers=BINANCE_TRIGGERS):
    """
    Checks tweet handle and txt against list of custom triggers. Triggers specify combinations of phrases
    and username that the trader would like to trigger an alarm.
    :param handle: username of tweet poster
    :param txt: tweet txt
    :param custom_triggers: list of trigger dicts (see BINANCE_TRIGGERS for example format)
    :return: list of positively matched triggers
    """
    triggers = []
    if custom_triggers is not None:
        for trigger in custom_triggers:
            alert_flag = True

            # check handles
            if trigger['handle'] is not None and trigger['handle'] != handle:
                alert_flag = False

            # check txt phrases
            if trigger['txt'] is not None:
                for phrase in trigger['txt']:
                    if phrase not in txt.lower():
                        alert_flag = False

            # check alert level
            if alert_flag:
                triggers.append(trigger)  # stack alerts
                if trigger['level'] == 'red':
                    return triggers  # immediately return red alert
    return triggers


class Alert:
    """ Set up the alert object with all tweet info then call amber() or red() to create alerts"""
    def __init__(self, symbol, txt=None, url=None, quiet_mode=False, sms_client=None, logger=None):
        self.symbol = symbol
        self.url = url
        self.quiet_mode = quiet_mode
        self.logger = logger
        self.txt = txt
        self.sms_client = sms_client
        self.tier_map = {None: 0, 'amber': 1, 'red': 2}
        self.curr_tier = None  # current alert level
        self.history = [{'trigger': None, 'tier': None}]

    def amber(self, msg, trigger='price'):
        self._base(msg, 'amber', trigger=trigger)

    def red(self, msg, trigger='price'):
        full_msg = self._base(msg, 'red', trigger=trigger)

        if self.sms_client is not None and self._check_tier_increase():
            sms = full_msg + ' {}'.format(self.url)
            self.sms_client.messages.create(to='YOUR NUMBER', from_='CLIENT NUMBER', body=sms)

    def alert(self, msg, level='red', trigger='price'):
        if level == 'red':
            self.red(msg, trigger=trigger)
        elif level == 'amber':
            self.amber(msg, trigger=trigger)

    def export(self):
        data = {
            'history': self.history,
            'txt': self.txt,
            'url': self.url
        }
        return data

    def _base(self, msg, tier, trigger):
        """ Base alert code. Returns alert msg for logs. """
        self.curr_tier = tier
        hist_dict = {'trigger': trigger, 'tier': tier}
        self.history.append(hist_dict)
        msg = '{} alert'.format(tier) if msg is None else msg
        full_msg = '{} for {}'.format(msg, self.symbol)
        if self.txt is not None:
            full_msg += '\nTweet text: {}'.format(self.txt)
        if not self.quiet_mode and self._check_tier_increase():
            os.system('say "{}"'.format(full_msg))

        if self.logger is None:
            print(full_msg)
        else:
            self.logger.info(full_msg)
        return full_msg

    def _check_tier_increase(self):
        """ Returns True if tier has maintained or increased since last alert.
        Prevents spamming alerts when tier is decreasing """
        return self.tier_map[self.history[-1]['tier']] >= self.tier_map[self.history[-2]['tier']]