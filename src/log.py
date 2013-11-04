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

LOGGING = False  # to log or not to log

LOGFILE = os.path.join(alfred.work(True), u'debug.log')

_handler = None

def logger(name=u''):
    global _handler
    if not _handler:
        if LOGGING:
            _handler = logging.FileHandler(filename=LOGFILE,
                                           encoding=u'utf-8',
                                           delay=True)
        else:
            _handler = logging.NullHandler()
    log = logging.getLogger(name)
    log.addHandler(_handler)
    log.setLevel(logging.DEBUG)
    return log