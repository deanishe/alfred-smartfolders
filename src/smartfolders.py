#!/usr/bin/python
# encoding: utf-8
#
# Copyright © 2013 deanishe@deanishe.net.
#
# MIT Licence. See http://opensource.org/licenses/MIT
#
# Created on 2013-11-01
#

"""Search Smart Folders (Saved Searches)."""

from __future__ import print_function, unicode_literals

import sys
import os
import subprocess

from docopt import docopt

from workflow import (Workflow, ICON_INFO, ICON_WARNING, ICON_ERROR,
                      ICON_SETTINGS, ICON_SYNC)
from workflow.background import run_in_background
from cache import cache_key


__usage__ = u"""\
Search smart folders

Usage:
    smartfolders [-f <folder>|--folder=<folder>] [<query>]
    smartfolders --config [<query>]
    smartfolders (-h|--help)
    smartfolders --helpfile

Options:
    --config                List Smart Folders with keywords
    -f, --folder=<folder>   Search contents of named folder
                            Specify the folder name, not the path
    -h, --help              Show this message
    --helpfile              Open the enclosed help file in your web browser

"""

DEFAULT_KEYWORD = '.sf'
MAX_RESULTS = 50
HELPFILE = os.path.join(os.path.dirname(__file__), 'Help.html')
DELIMITER = '⟩'
# DELIMITER = '/'
# DELIMITER = '⦊'
CACHE_AGE_FOLDERS = 20  # seconds
CACHE_AGE_CONTENTS = 10  # seconds

# Placeholder, replaced on run
log = None

ALFRED_SCRIPT = 'tell application "Alfred {}" to search "{}"'


def _applescriptify(text):
    """Replace double quotes in text."""
    return text.replace('"', '" + quote + "')


def run_alfred(query):
    """Run Alfred with ``query`` via AppleScript."""
    version = '2'
    if wf.alfred_version and wf.alfred_version.major == 3:
        version = '3'
    script = ALFRED_SCRIPT.format(version, _applescriptify(query))
    log.debug('calling Alfred with : {!r}'.format(script))
    return subprocess.call(['osascript', '-e', script])


class Backup(Exception):
    """Raised when query ends with DELIMITER.

    Signals workflow to back up one level, i.e. out of a folder.

    """


class SmartFolders(object):
    """Workflow controller."""

    def __init__(self):
        """Create new `SmartFolders` object."""
        self.wf = None
        self.query = None
        self.folders = []
        self.keyword = DEFAULT_KEYWORD

    def run(self, wf):
        """Run workflow."""
        self.wf = wf
        self.keyword = self.wf.settings.get('keyword', DEFAULT_KEYWORD)
        args = docopt(__usage__, self.wf.args)
        log.debug('args : {}'.format(args))

        # Open Help file
        if args.get('--helpfile'):
            return self.do_open_help_file()

        # Perform search
        self.query = args.get('<query>') or ''

        # List Smart Folders with custom keywords
        if args.get('--config'):
            self.do_configure_folders()

        # Was a configured folder passed?
        folder_number = args.get('--folder')

        # Get list of Smart Folders. Update in background if necessary.
        self.folders = self.wf.cached_data('folders', max_age=0)
        if self.folders is None:
            self.folders = []

        # Update folder list if it's old
        if not self.wf.cached_data_fresh('folders', CACHE_AGE_FOLDERS):
            log.debug('Updating list of Smart Folders in background...')
            run_in_background('folders',
                              ['/usr/bin/python',
                               self.wf.workflowfile('cache.py')])

        # if is_running('folders'):
        #     self.wf.add_item('Updating list of Smart Folders…',
        #                      icon=ICON_INFO)

        # Has a specific folder been specified?
        if folder_number:
            folder = self.wf.settings.get('folders', {}).get(folder_number)

            if not folder:
                return self._terminate_with_error(
                    'Unknown folder',
                    'Check your configuration with `smartfolders`')
            folder = folder['path']
            return self.do_search_in_folder(folder)

        return self.do_search_folders()

    def do_open_help_file(self):
        """Open the help file in the user's default browser."""
        log.debug('Opening help file...')
        subprocess.call(['open', HELPFILE])
        return 0

    def do_search_folders(self):
        """List/search all Smart Folders and return results to Alfred."""
        try:
            folder, query = self._parse_query(self.query)
        except Backup:
            return run_alfred('{} '.format(self.keyword))

        if folder:  # search within folder
            self.query = query
            return self.do_search_in_folder(folder)

        elif query:  # filter folder list
            folders = self.wf.filter(query, self.folders, key=lambda t: t[0],
                                     min_score=30)
        else:  # show all folders
            folders = self.folders

        # Show results
        if not folders:
            self._add_message('No matching Smart Folders',
                              'Try a different query',
                              icon=ICON_WARNING)
        i = 0
        for name, path in folders:
            subtitle = path.replace(os.getenv('HOME'), '~')
            self.wf.add_item(name, subtitle,
                             uid=path,
                             arg=path,
                             autocomplete='{} {} '.format(name, DELIMITER),
                             valid=True,
                             icon=path,
                             icontype='fileicon',
                             type='file')
            i += 1
            if i == MAX_RESULTS:
                break

        self.wf.send_feedback()

    def do_search_in_folder(self, folder):
        """List/search contents of a specific Smart Folder.

        Sends results to Alfred.

        :param folder: name or path of Smart Folder
        :type folder: ``unicode``

        """
        log.debug('Searching folder {!r} for {!r}'.format(folder, self.query))
        files = []
        folder_path = None
        for name, path in self.folders:
            if path == folder:
                folder_path = path
                break
            elif name == folder:
                folder_path = path
                break

        if not folder_path:
            return self._terminate_with_error(
                "Unknown folder '{}'".format(folder),
                'Check your configuration with `smartfolders`')

        # Get contents of folder; update if necessary
        key = cache_key(folder_path)
        files = self.wf.cached_data(key, max_age=0)
        if files is None:
            files = []

        if not self.wf.cached_data_fresh(key, CACHE_AGE_CONTENTS):
            run_in_background(key,
                              ['/usr/bin/python',
                               self.wf.workflowfile('cache.py'),
                               '--folder', folder_path])
        # if is_running(key):
        #     self.wf.add_item('Updating contents of Smart Folder…',
        #                      icon=ICON_INFO)

        if self.query:
            files = self.wf.filter(self.query, files,
                                   key=os.path.basename,
                                   min_score=10)
            # results = []
            # for path, score, rule in self.wf.filter(self.query, files,
            #                                         key=os.path.basename,
            #                                         include_score=True,
            #                                         min_score=10):
            #     log.debug('[{}/{}] {!r}'.format(score, rule, path))
            #     results.append(path)
            # files = results

        if not files:
            if not self.query:
                self._add_message('Empty Smart Folder', icon=ICON_WARNING)
            else:
                self._add_message('No matching results',
                                  'Try a different query',
                                  icon=ICON_WARNING)
        else:
            for i, path in enumerate(files):
                title = os.path.basename(path)
                subtitle = path.replace(os.getenv('HOME'), '~')
                self.wf.add_item(title, subtitle,
                                 uid=path,
                                 arg=path,
                                 valid=True,
                                 icon=path,
                                 icontype='fileicon',
                                 type='file')

                if (i+1) == MAX_RESULTS:
                    break

        self.wf.send_feedback()

    def do_configure_folders(self):
        """Show list of Smart Folders with custom keywords."""
        folders = self.wf.settings.get('folders')

        if wf.update_available:
            self.wf_add_item('A new version of Smart Folders is available',
                             '↩ or ⇥ to upgrade',
                             autocomplete='workflow:update',
                             valid=False,
                             icon=ICON_SYNC)

        if not folders:
            self._add_message('No Smart Folders assigned custom keywords',
                              ("Use '{}' and right-arrow on a Smart Folder "
                               'to assign a keyword').format(self.keyword),
                              icon=ICON_WARNING)

        for key, data in folders.items():
            subtitle = data['path'].replace(os.getenv('HOME'), '~')
            icon = data.get('icon', ICON_SETTINGS)
            self.wf.add_item(data['name'],
                             subtitle,
                             arg=data['path'],
                             icon=icon)

        self.wf.send_feedback()

    def _add_message(self, title, subtitle='', icon=ICON_INFO):
        """Add a message to the results returned to Alfred."""
        self.wf.add_item(title, subtitle, icon=icon)

    def _terminate_with_error(self, title, subtitle=''):
        """Show an error message and send results to Alfred."""
        self._add_message(title, subtitle, ICON_ERROR)
        self.wf.send_feedback()
        return 1

    def _parse_query(self, query):
        """Split query on DELIMITER and return `(folder, query)`.

        Either `folder` or `query` may be `None`.

        """
        if query.endswith(DELIMITER):
            log.debug('Backing up…')
            raise Backup()

        index = query.find(DELIMITER)

        if index > -1:
            folder = query[:index].strip()
            query = query[index+1:].strip()

        else:
            folder = None
            query = query.strip()

        log.debug('folder : {!r}  query : {!r}'.format(folder, query))
        return (folder, query)


if __name__ == '__main__':
    wf = Workflow(
        update_settings={'github_slug': 'deanishe/alfred-smartfolders'})
    log = wf.logger
    sf = SmartFolders()
    sys.exit(wf.run(sf.run))
