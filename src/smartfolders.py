#!/usr/bin/env python
# encoding: utf-8
#
# Copyright © 2013 deanishe@deanishe.net.
#
# MIT Licence. See http://opensource.org/licenses/MIT
#
# Created on 2013-11-01
#

# TODO : figure out meaningful separator
# TODO : implement search in as well as starts with

"""
Search one or all Smart Folders (Saved Searches) in '~/Library/Saved Searches'
"""

from __future__ import print_function

import sys
import os
import logging
import subprocess
import plistlib

import alfred
from docopt import docopt

__usage__ = u"""Search smart folders

Usage:
    smartfolders [-f <folder>|--folder=<folder>] [<query>]
    smartfolders (-h|--help)
    smartfolders --helpfile

Options:
    -f, --folder=<folder>   Search contents of named folder
                            Specify the folder name, not the path
    -h, --help              Show this message
    --helpfile              Open the enclosed help file in your web browser

"""

MAX_RESULTS = 50
HELPFILE = os.path.join(os.path.dirname(__file__), u'Help.html')

logging.basicConfig(filename=os.path.join(os.path.dirname(__file__),
                                          'debug.log'),
                    level=logging.DEBUG)

log = logging.getLogger(u'smartfolders')


def open_help_file():
    subprocess.call([u'open', HELPFILE])


def make_folder_items(folders):
    """Make alfred.Item for smart folders `folders`

    Returns:
        list of alfred.Item instances
    """
    items = []
    for i, folder in enumerate(folders):
        folder, path = folder
        item = alfred.Item(
            {'uid': alfred.uid(i),
             'arg': path,
             'valid': 'yes',
             'autocomplete': folder + u' ',
             # Hard to know what to do with smart folders.
             # Most 'file' functions don't work on them,
             # only 'Reveal in Finder' and that's about it.
             'type': 'file',
             # 'path': path
             },
            folder,
            u'',
            icon=('com.apple.finder.smart-folder',
                  {'type' : 'filetype'})
        )
        items.append(item)
    return items


def get_smart_folders():
    """Return list of all Smart Folders on system

    Returns:
        list of tuples (name, path)
    """
    results = []
    output = subprocess.check_output([u'mdfind', u'kind:saved search']).decode(u'utf-8')
    paths = [path.strip() for path in output.split(u'\n') if path.strip()]
    for path in paths:
        name = os.path.splitext(os.path.basename(path))[0]
        results.append((name, path))
    return results


def folder_contents(path):
    """Return files in smart folder at path

    Returns:
        list of paths
    """
    if path.startswith(os.path.expanduser(u'~/Library/Saved Searches')):
        name = os.path.splitext(os.path.basename(path))[0]
        command = [u'mdfind', u'-s', name]
    else:  # parse the Saved Search and run the query
        plist = plistlib.readPlist(path)
        params = plist[u'RawQueryDict']
        query = params[u'RawQuery']
        locations = params[u'SearchScopes']
        log.debug(u'query : {}, locations : {}'.format(query, locations))
        command = [u'mdfind']
        for path in locations:
            if not os.path.exists(path):
                continue
            command.extend([u'-onlyin', path])
        command.append(query)
    log.debug(u'command : {}'.format(command))
    output = subprocess.check_output(command).decode(u"utf-8")
    files = [path.strip() for path in output.split('\n') if path.strip()]
    log.debug(u'{} files in folder {}'.format(len(files), path))
    return files


def search_folder(folder, query, limit=MAX_RESULTS):
    """Return list of items in `folder` matching `query`

    Returns:
        list of alfred.Item instances
    """
    log.debug(u'folder : {!r} query : {!r}'.format(folder, query))
    # query = query.lstrip(u'/')
    query = query.strip()
    files = []
    results = []
    for name, path in get_smart_folders():
        if name == folder:
            files = folder_contents(path)
            break
    # output = subprocess.check_output(['mdfind', '-s', folder]).decode('utf-8')
    # files = [path.strip() for path in output.split('\n') if path.strip()]
    log.debug(u'{} files in folder {}'.format(len(files), folder))
    for i, path in enumerate(files):
        name = os.path.basename(path)
        if query and not name.lower().startswith(query.lower()):
            continue

        item = alfred.Item(
                    {'uid': alfred.uid(u"%02d" % i),
                     'arg': path,
                     'valid': 'yes',
                     # 'autocomplete': path,
                     'type': 'file'},
                    name,
                    path,
                    icon=(path, {u'type' : u'fileicon'}))
        results.append(item)
        if len(results) == limit:
            break
    return results


def search_folders(query=None):
    """Search folder names/contents of folders

    Returns:
        list of alfred.Item instances
    """
    folders = get_smart_folders()
    results = []
    if query is None:
        results = make_folder_items(folders)
    else:
        query = query.lower()
        # query = query.rstrip(u'/')
        for (name, path) in folders:
            if query == name.lower():  # Exact match; show folder contents
                results = search_folder(name, u'')
                break
            elif query.startswith(name.lower()):  # search in folder
                query = query[len(name):]
                results = search_folder(name, query)
                break
        if not results:  # found no matching folder; filter folders
            results = make_folder_items([t for t in folders if
                                        t[0].lower().startswith(query)])
    return results


def main():
    args = docopt(__usage__, alfred.args())
    log.debug(u'args : {}'.format(args))
    if args.get(u'--helpfile'):
        open_help_file()
        return 0
    query = args.get(u'<query>')
    folder = args.get(u'--folder')
    results = []
    if folder is None:
        results = search_folders(query)
    else:
        if query is None:  # show list of contents of folder
            query = u''
        results = search_folder(folder, query)
    xml = alfred.xml(results, maxresults=MAX_RESULTS)
    log.debug(u'Returning {} results to Alfred'.format(len(results)))
    # log.debug('\n{}'.format(xml))
    alfred.write(xml)
    return 0

if __name__ == '__main__':
    sys.exit(main())