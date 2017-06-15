#!/usr/bin/env python
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

from workflow import Workflow

# Placeholder, replaced on run
log = None


def cache_key(folder_path):
    """Return cache key for `folder_path`."""
    return 'folder-contents-{}'.format(hashlib.md5(
        folder_path.encode('utf-8')).hexdigest())


class Cache(object):
    """Cache of all smart folders or their contents."""

    def __init__(self):
        """Create new `Cache`."""
        self.wf = None

    def run(self, wf):
        """Run Cache."""
        wf.args  # Check for magic arguments
        self.wf = wf
        args = docopt(__doc__)
        folder_path = wf.decode(args.get('--folder') or '')

        if folder_path:  # Cache contents of Smart Folder
            wf.cache_data(cache_key(folder_path),
                          self.folder_contents(folder_path))

        else:  # Cache list of all Smart Folders
            wf.cache_data('folders', self.smart_folders())

    def folder_contents(self, folder_path):
        """Return `list` of files in Smart Folder at `folder_path`."""
        if folder_path.startswith(
                os.path.expanduser('~/Library/Saved Searches')):
            name = os.path.splitext(os.path.basename(folder_path))[0]
            command = ['mdfind', '-s', name]

        else:  # parse the Saved Search and run the query
            plist = plistlib.readPlist(folder_path)
            params = plist['RawQueryDict']
            query = params['RawQuery']
            locations = params['SearchScopes']
            log.debug('query=%r, locations=%r', query, locations)
            command = ['mdfind']
            for path in locations:
                if path == 'kMDQueryScopeHome':
                    path = os.path.expanduser('~/')
                elif path == 'kMDQueryScopeComputer':
                    continue
                elif not os.path.exists(path):
                    continue
                command.extend(['-onlyin', path])
            command.append(query)

        log.debug('command=%r', command)
        output = self.wf.decode(subprocess.check_output(command))

        files = [p.strip() for p in output.split('\n') if p.strip()]
        log.debug('%d files in folder %r', len(files), folder_path)
        return files

    def smart_folders(self):
        """Return list of all Smart Folders on system.

        Returns:
            list of tuples (name, path)
        """
        results = []
        log.debug('Querying mds ...')
        output = subprocess.check_output([
            'mdfind',
            'kMDItemContentType == com.apple.finder.smart-folder'])
        paths = [p.strip() for p in
                 self.wf.decode(output).split('\n') if p.strip()]
        for path in paths:
            name = os.path.splitext(os.path.basename(path))[0]
            results.append((name, path))
            log.debug('smartfolder {!r} @ {!r}'.format(name, path))
        results.sort()
        log.debug('{} smartfolders found'.format(len(results)))
        return results


if __name__ == '__main__':
    start = time()
    wf = Workflow()
    log = wf.logger
    cache = Cache()
    retcode = wf.run(cache.run)
    log.debug('Finished in {:0.4f} seconds'.format(time() - start))
    sys.exit(retcode)
