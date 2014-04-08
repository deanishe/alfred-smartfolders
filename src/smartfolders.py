#!/usr/bin/python
# encoding: utf-8
#
# Copyright © 2013 deanishe@deanishe.net.
#
# MIT Licence. See http://opensource.org/licenses/MIT
#
# Created on 2013-11-01
#

"""
Search Smart Folders (Saved Searches)
"""

from __future__ import print_function, unicode_literals

import sys
import os
import subprocess
import functools
import hashlib
import plistlib
from time import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__),
                'alfred-workflow-1.4.zip'))

from workflow import (Workflow, ICON_INFO, ICON_WARNING, ICON_ERROR,
                      ICON_SETTINGS)

from docopt import docopt


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

# Placeholder, replaced on run
log = None

ALFRED_SCRIPT = 'tell application "Alfred 2" to search "{}"'


def _applescriptify(text):
    """Replace double quotes in text"""
    return text.replace('"', '" + quote + "')


def run_alfred(query):
    """Run Alfred with ``query`` via AppleScript"""
    script = ALFRED_SCRIPT.format(_applescriptify(query))
    log.debug('calling Alfred with : {!r}'.format(script))
    return subprocess.call(['osascript', '-e', script])


class Backup(Exception):
    """
    Raised when query ends with DELIMITER to signal workflow to back up
    one level, i.e. out of a folder.

    """


class SmartFolders(object):

    def __init__(self):

        self.wf = None
        self.query = None
        self.folders = []
        self.keyword = DEFAULT_KEYWORD

    def run(self, wf):

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

        self.folders = self.wf.cached_data('folders', self._get_smart_folders,
                                           max_age=20)

        if folder_number:
            folder = self.wf.settings.get('folders', {}).get(folder_number)

            if not folder:
                return self._terminate_with_error(
                    'Unknown folder',
                    'Check your configuration with `smartfolders`')
            return self.do_search_in_folder(folder)

        return self.do_search_folders()

    def do_open_help_file(self):
        """Open the help file in the user's default browser"""

        log.debug('Opening help file...')
        subprocess.call(['open', HELPFILE])
        return 0

    def do_search_folders(self):
        """List/search all Smart Folders and return results to Alfred"""

        try:
            folder, query = self._parse_query(self.query)
        except Backup:
            return run_alfred('{} '.format(self.keyword))

        if folder:
            self.query = query
            return self.do_search_in_folder(folder)
        elif query:
            folders = self.wf.filter(query, self.folders, key=lambda t: t[0])
        else:
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
        """
        List/search contents of a specific Smart Folder and return
        results to Alfred

        :param folder: name or path of Smart Folder
        :type folder: ``unicode``

        """

        log.debug('Searching folder {!r} for {!r}'.format(folder, self.query))
        files = []
        folder_path = None
        for name, path in self.folders:
            if name == folder:
                folder_path = path
                break

        if not folder_path:
            return self._terminate_with_error(
                "Unknown folder '{}'".format(folder),
                'Check your configuration with `smartfolders`')

        files = self._folder_contents(folder_path)
        if self.query:
            results = []
            for path, score, rule in self.wf.filter(self.query, files,
                                                    key=os.path.basename,
                                                    include_score=True):
                log.debug('[{}/{}] {!r}'.format(score, rule, path))
                results.append(path)
            files = results

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
        """Show list of Smart Folders with custom keywords"""
        folders = self.wf.settings.get('folders')
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
        """Add a message to the results returned to Alfred"""

        self.wf.add_item(title, subtitle, icon=icon)

    def _terminate_with_error(self, title, subtitle=''):
        """Show an error message and send results to Alfred"""

        self._add_message(title, subtitle, ICON_ERROR)
        self.wf.send_feedback()
        return 1

    def _parse_query(self, query):
        """Split query on DELIMITER and return `(folder, query)`

        either ``folder`` or ``query`` may be ``None``

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

    def _get_smart_folders(self):
        """Return list of all Smart Folders on system

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

    def _folder_contents(self, path):
        """Return files in smart folder at path

        Returns:
            list of paths
        """
        log.debug('Retrieving contents of smartfolder : {} ...'.format(path))

        def _get_contents(path):
            """Return list of all paths in Smart Folder at ``path``"""
            if path.startswith(os.path.expanduser('~/Library/Saved Searches')):
                name = os.path.splitext(os.path.basename(path))[0]
                command = ['mdfind', '-s', name]

            else:  # parse the Saved Search and run the query
                plist = plistlib.readPlist(path)
                params = plist['RawQueryDict']
                query = params['RawQuery']
                locations = params['SearchScopes']
                log.debug('query : {}, locations : {}'.format(query, locations))
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

            log.debug('command : {}'.format(command))
            output = self.wf.decode(subprocess.check_output(command))

            files = [p.strip() for p in output.split('\n') if p.strip()]
            log.debug(u"{} files in folder '{}'".format(len(files), path))
            return files

        key = 'folder-contents-{}'.format(
            hashlib.md5(path.encode('utf-8')).hexdigest())

        return self.wf.cached_data(key,
                                   functools.partial(_get_contents, path),
                                   max_age=10)


if __name__ == '__main__':
    start = time()
    wf = Workflow()
    log = wf.logger
    sf = SmartFolders()
    retcode = wf.run(sf.run)
    log.debug('Finished in {:0.4f} seconds'.format(time() - start))
    log.debug('-' * 60)
    sys.exit(retcode)
