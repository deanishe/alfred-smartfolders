#!/usr/bin/python
# encoding: utf-8
#
# Copyright (c) 2013 deanishe@deanishe.net.
#
# MIT Licence. See http://opensource.org/licenses/MIT
#
# Created on 2013-11-01
#

"""Search smart folders

Usage:
    smartfolders [-f <folder>] [<query>]
    smartfolders --config [<query>]
    smartfolders (-h|--help)

Options:
    --config                list Smart Folders with keywords
    -f, --folder=<folder>   search contents of named folder
                            specify the folder name, not the path
    -h, --help              show this message

"""

from __future__ import print_function

from collections import namedtuple
import os

from docopt import docopt

from workflow import (Workflow3, ICON_INFO, ICON_WARNING, ICON_ERROR,
                      ICON_SYNC)
from workflow.background import is_running, run_in_background
from workflow.util import run_trigger
from cache import cache_key

ICON_LOADING = 'loading.png'

MAX_RESULTS = 100
UPDATE_SETTINGS = {'github_slug': 'deanishe/alfred-smartfolders'}
HELPFILE = os.path.join(os.path.dirname(__file__), 'Help.html')
DELIMITER = u'\U0001F782'
CACHE_AGE_FOLDERS = 20  # seconds
CACHE_AGE_CONTENTS = 10  # seconds

# Placeholder, replaced on run
log = None


Folder = namedtuple('SmartFolder', 'name path')


class Backup(Exception):
    """Raised when query ends with DELIMITER. Signals workflow to exit a folder."""


class SmartFolders(object):
    """Workflow controller."""

    def __init__(self):
        """Create new `SmartFolders` object."""
        self.wf = None
        self.query = None
        self.folders = []

    def run(self, wf):
        """Run workflow."""
        self.wf = wf
        args = docopt(__doc__, argv=wf.args)
        log.debug(u'args=%r', args)
        self.query = args['<query>'] or ''
        folder = args['--folder']

        # show error encountered by background script
        err = self.wf.cached_data('error', max_age=0)
        if err and os.getenv('rerun'):
            wf.add_item(u'Error Loading Smart Folder', str(err), icon=ICON_ERROR)
            wf.send_feedback()
            return

        # get list of Smart Folders; update in background if necessary
        self.folders = [
            Folder(*t) for t in self.wf.cached_data('folders', max_age=0) or []
        ]

        # update folder list if it's old
        running = False
        if not self.wf.cached_data_fresh('folders', CACHE_AGE_FOLDERS):
            self.wf.rerun = 0.5
            log.debug('updating list of Smart Folders in background...')
            run_in_background('folders', [
                '/usr/bin/python', self.wf.workflowfile('cache.py')
            ])
            running = True

        if running or is_running('folders'):
            self.wf.rerun = 0.5
            self.wf.setvar('rerun', 'true')

        # has a specific folder been specified?
        if folder:
            return self.do_search_in_folder(folder)

        return self.do_search_folders()

    def do_search_folders(self):
        """List/search all Smart Folders and return results to Alfred."""
        if not self.query and self.wf.update_available:
            self.wf.add_item(u'A new version of Smart Folders is available',
                             u'\U00002B90 or \u21E5 to upgrade',
                             autocomplete='workflow:update',
                             valid=False,
                             icon=ICON_SYNC)

        try:
            folder, query = self._parse_query(self.query)
        except Backup:
            return run_trigger('search')

        if folder:  # search within folder
            self.query = query
            return self.do_search_in_folder(folder)

        elif query:  # filter folder list
            folders = self.wf.filter(query, self.folders, key=lambda t: t.name,
                                     min_score=30)
        else:  # show all folders
            folders = self.folders

        # Show results
        if not folders:
            self._add_message('No matching Smart Folders',
                              'Try a different query',
                              icon=ICON_WARNING)
        i = 0
        for f in folders:
            subtitle = f.path.replace(os.getenv('HOME'), '~')
            it = self.wf.add_item(f.name, subtitle,
                                  uid=f.path,
                                  arg=f.path,
                                  autocomplete=u'{} {} '.format(f.name, DELIMITER),
                                  valid=True,
                                  icon=f.path,
                                  icontype='fileicon',
                                  type='file')

            it.add_modifier('cmd', 'Reveal in Finder').setvar('reveal', '1')

            i += 1
            if i >= MAX_RESULTS:
                break

        self.wf.send_feedback()

    def do_search_in_folder(self, folder):
        """List/search contents of a specific Smart Folder.

        Sends results to Alfred.

        :param folder: name or path of Smart Folder
        :type folder: ``unicode``

        """
        log.info(u'searching folder "%s" for "%s" ...', folder, self.query)
        files = []
        path = None
        for f in self.folders:
            if f.path == folder or f.name == folder:
                path = f.path
                break
        else:
            return self._show_error(u'Unknown Folder \u201C%s\u201D' % folder,
                                    'Check your configuration')

        # Get contents of folder; update if necessary
        key = cache_key(path)
        files = self.wf.cached_data(key, max_age=0)
        if files is None:
            files = []

        loading = False
        if not self.wf.cached_data_fresh(key, CACHE_AGE_CONTENTS):
            self.wf.rerun = 0.5
            run_in_background(key, [
                '/usr/bin/python', self.wf.workflowfile('cache.py'), '--folder', path
            ])
            loading = True

        if loading or is_running(key):
            self.wf.rerun = 0.5
            self.wf.setvar('rerun', 'true')

        if self.query:
            files = self.wf.filter(self.query, files, key=os.path.basename, min_score=10)

        if not files:  # no results
            if not self.query:
                if loading:
                    self._add_message(u'Loading Folder Contents\U00002026',
                                      icon=ICON_LOADING)
                else:
                    self._add_message('Empty Smart Folder', icon=ICON_WARNING)
            else:
                self._add_message('No matching results', 'Try a different query',
                                  icon=ICON_WARNING)
        else:  # show results
            home = os.getenv('HOME')
            for i, path in enumerate(files):
                title = os.path.basename(path)
                subtitle = path.replace(home, '~')
                it = self.wf.add_item(title, subtitle,
                                      uid=path,
                                      arg=path,
                                      valid=True,
                                      icon=path,
                                      icontype='fileicon',
                                      type='file')

                it.add_modifier('cmd', 'Reveal in Finder').setvar('reveal', '1')

                if i >= MAX_RESULTS - 1:
                    break

        self.wf.send_feedback()

    def _add_message(self, title, subtitle=u'', icon=ICON_INFO):
        """Add a message to the results returned to Alfred."""
        self.wf.add_item(title, subtitle, icon=icon)

    def _show_error(self, title, subtitle=''):
        """Show an error message and send results to Alfred."""
        self._add_message(title, subtitle, ICON_ERROR)
        self.wf.send_feedback()

    def _parse_query(self, query):
        """Split query on DELIMITER and return `(folder, query)`.

        Either `folder` or `query` may be `None`.

        """
        if query.endswith(DELIMITER):
            log.debug('backing up...')
            raise Backup()

        index = query.find(DELIMITER)

        if index > -1:
            folder = query[:index].strip()
            query = query[index + len(DELIMITER):].strip()

        else:
            folder = None
            query = query.strip()

        log.debug('folder=%r  query=%r', folder, query)
        return (folder, query)


if __name__ == '__main__':
    wf = Workflow3(update_settings=UPDATE_SETTINGS)
    log = wf.logger
    sf = SmartFolders()
    wf.run(sf.run)
