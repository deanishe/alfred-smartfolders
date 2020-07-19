#!/usr/bin/python
# encoding: utf-8
#
# Copyright © 2014 deanishe@deanishe.net
#
# MIT Licence. See http://opensource.org/licenses/MIT
#
# Created on 2014-05-25
#

"""cache.py [-f <folder>]

Cache Smart Folders and their contents

Usage:
    cache.py --folder <DIR>
    cache.py

Options:
    -f, --folder=<DIR>   Cache contents of specified folder

"""

from __future__ import print_function

import sys
import os
import plistlib
import hashlib
import subprocess
from time import time

from docopt import docopt

from workflow import Workflow3

# Placeholder, replaced on run
log = None


def cache_key(path):
    """Return cache key for `path`."""
    return 'folder-{}'.format(hashlib.md5(path.encode('utf-8')).hexdigest())


class Cache(object):
    """Cache of all smart folders or their contents."""

    def __init__(self):
        """Create new `Cache`."""
        self.wf = None

    def run(self, wf):
        """Run Cache."""
        self.wf = wf
        args = docopt(__doc__, argv=wf.args)
        path = args['--folder']

        try:
            if path:  # cache contents of Smart Folder
                wf.cache_data(cache_key(path), self.folder_contents(path))

            else:  # cache list of all Smart Folders
                wf.cache_data('folders', self.smart_folders())

            wf.cache_data('error', None)  # clear existing error
        except Exception as err:
            wf.cache_data('error', err)
            raise err

    def folder_contents(self, path):
        """Return `list` of files in Smart Folder at `path`."""
        # Smart Folders in ~/Library/Saved Searches *can* be called by name,
        # but (on Catalina at least) location restrictions aren't observed,
        # so we'll parse these files, too.
        # if path.startswith(os.path.expanduser('~/Library/Saved Searches')):
        #     name = os.path.splitext(os.path.basename(path))[0]
        #     cmd = ['mdfind', '-s', name]

        # Parse .savedSearch file and construct corresponding `mdfind` command.
        plist = plistlib.readPlist(path)
        params = plist['RawQueryDict']
        query = params['RawQuery']
        locations = params['SearchScopes']
        log.debug('[cache] query=%r, locations=%r', query, locations)
        cmd = ['mdfind']
        for p in locations:
            if p == 'kMDQueryScopeHome':
                p = os.path.expanduser('~/')
            elif p == 'kMDQueryScopeComputer' or not os.path.exists(p):
                continue
            cmd.extend(['-onlyin', p])

        cmd.append(query)

        log.debug('[cache] cmd=%r', cmd)
        output = self.wf.decode(subprocess.check_output(cmd))

        files = [p.strip() for p in output.split('\n') if p.strip()]
        log.debug('%d file(s) in folder %r', len(files), path)
        return files

    def smart_folders(self):
        """Return list of all Smart Folders on system.

        Returns:
            list of tuples (name, path)
        """
        folders = []
        log.debug('[cache] querying mds for Smart Folders ...')
        output = subprocess.check_output([
            'mdfind', 'kMDItemContentType == com.apple.finder.smart-folder'
        ])

        for path in [p.strip() for p in self.wf.decode(output).split('\n')]:
            if not path:
                continue
            name = os.path.splitext(os.path.basename(path))[0]
            folders.append((name, path))
            log.debug('[cache] "%s" (%s)', (name, path))

        folders.sort()
        log.debug('[cache] %d smartfolder(s) found', len(folders))
        return folders


if __name__ == '__main__':
    wf = Workflow3()
    log = wf.logger
    cache = Cache()
    wf.run(cache.run)
