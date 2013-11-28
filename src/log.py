#!/usr/bin/env python
# encoding: utf-8
#
# Copyright © 2013 deanishe@deanishe.net.
#
# MIT Licence. See http://opensource.org/licenses/MIT
#
# Created on 2013-11-03
#

"""
"""

from __future__ import print_function

import os
import alfred
import logging
import json

LOGGING_DEFAULT = False  # to log or not to log


class LoggingConfig(object):

    log_path = os.path.join(alfred.work(True), u'debug.log')
    settings_path = os.path.join(alfred.work(True), u'log_config.json')

    def __init__(self):
        self._logging = LOGGING_DEFAULT
        self._load()

    def _load(self):
        if not os.path.exists(self.settings_path):  # use default
            self._save()
            return
        with open(self.settings_path, u'rb') as file:
            d = json.load(file)
            self._logging = d['logging']

    def _save(self):
        with open(self.settings_path, u'wb') as file:
            json.dump(dict(logging=self._logging), file)

    def get_logging(self):
        return self._logging

    def set_logging(self, bool):
        self._logging = bool
        self._save()

    logging = property(get_logging, set_logging)


LOG_CONFIG = LoggingConfig()

_handler = None

def logger(name=u''):
    global _handler
    if not _handler:
        if LOG_CONFIG.logging:
            _handler = logging.FileHandler(filename=LOG_CONFIG.log_path,
                                           encoding=u'utf-8',
                                           delay=True)
            _handler.setFormatter(logging.Formatter(
                fmt=u'%(lineno)d:%(funcName)s : %(message)s'))
        else:
            _handler = logging.NullHandler()
    log = logging.getLogger(name)
    log.addHandler(_handler)
    log.setLevel(logging.DEBUG)
    return log
