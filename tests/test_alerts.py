from unittest import TestCase
from common.alerts import Alert, check_custom_triggers


class TestAlert(TestCase):

    def setUp(self):
        self.alert = Alert('SYMBOL', 'TXT', 'URL')

    def test_base(self):
        self.assertEqual(self.alert._base('MSG', 'amber', None), 'MSG for SYMBOL\nTweet text: TXT')


class TestCheckCustomTargets(TestCase):

    def setUp(self):
        self.txt = 'this is Example tweet Text'
        self.handle = 'handle'

    def test_negative(self):
        targets = [{'handle': 'nothandle', 'txt': ['no'], 'level': 'red', 'msg': 'msg'},
                   {'handle': 'handle', 'txt': ['this', 'no'], 'level': 'red', 'msg': 'msg'},
                   {'handle': 'nothandle', 'txt': ['this'], 'level': 'red', 'msg': 'msg'}]
        result = check_custom_triggers(self.handle, self.txt, custom_triggers=targets)
        # print(result)
        self.assertFalse(result)

    def test_positive(self):
        targets = [{'handle': 'handle', 'txt': None, 'level': 'amber', 'msg': 'msg'},
                   {'handle': None, 'txt': ['example', 'this'], 'level': 'amber', 'msg': 'msg'}]
        result = check_custom_triggers(self.handle, self.txt, custom_triggers=targets)
        # print(result)
        self.assertEqual(targets, result)

    def test_alert_priority(self):
        targets = [{'handle': 'handle', 'txt': None, 'level': 'amber', 'msg': 'msg'},
                   {'handle': None, 'txt': ['example', 'this'], 'level': 'red', 'msg': 'msg'},
                   {'handle': None, 'txt': ['example', 'this'], 'level': 'amber', 'msg': 'msg'}]
        result = check_custom_triggers(self.handle, self.txt, custom_triggers=targets)
        self.assertEqual(targets[:2], result)
