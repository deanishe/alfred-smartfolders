#!/usr/bin/env python
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

from __future__ import print_function

import sys
import os
import subprocess
import plistlib

import alfred
from docopt import docopt
from log import logger, LOG_CONFIG

__usage__ = u"""Search smart folders

Usage:
    smartfolders [-f <folder>|--folder=<folder>] [<query>]
    smartfolders (-h|--help)
    smartfolders --helpfile
    smartfolders --dellog
    smartfolders --openlog
    smartfolders --log
    smartfolders --nolog

Options:
    -f, --folder=<folder>   Search contents of named folder
                            Specify the folder name, not the path
    -h, --help              Show this message
    --helpfile              Open the enclosed help file in your web browser
    --dellog                Delete the debug log
    --openlog               Open the debug log in Console
    --log                   Turn logging on
    --nolog                 Turn logging off
"""

MAX_RESULTS = 50
HELPFILE = os.path.join(os.path.dirname(__file__), u'Help.html')
DELIMITER = u'⟩'
# DELIMITER = u'⦊'



log = logger(u'smartfolders')


def open_help_file():
    subprocess.call([u'open', HELPFILE])


def make_folder_items(folders):
    """Make alfred.Item for smart folders `folders`

    Returns:
        list of alfred.Item instances
    """
    items = []
    for folder in folders:
        folder, path = folder
        item = alfred.Item(
            {'uid': path,
             'arg': path,
             'valid': 'yes',
             'autocomplete': folder + u' {} '.format(DELIMITER),
             # 'path': path
             },
            folder,
            path,
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
    log.debug(u'Querying mds ...')
    output = subprocess.check_output([u'mdfind',
            u'kMDItemContentType == com.apple.finder.smart-folder']).decode(u'utf-8')
    paths = [path.strip() for path in output.split(u'\n') if path.strip()]
    for path in paths:
        name = os.path.splitext(os.path.basename(path))[0]
        results.append((name, path))
        log.debug(u'smartfolder : {}'.format(path))
    log.debug(u'{} smartfolders found'.format(len(results)))
    return results


def folder_contents(path):
    """Return files in smart folder at path

    Returns:
        list of paths
    """
    log.debug(u'Retrieving contents of smartfolder : {} ...'.format(path))
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
            if path == u'kMDQueryScopeHome':
                path = os.path.expanduser(u'~/')
            elif path == u'kMDQueryScopeComputer':
                continue
            elif not os.path.exists(path):
                continue
            command.extend([u'-onlyin', path])
        command.append(query)
    log.debug(u'command : {}'.format(command))
    output = subprocess.check_output(command).decode(u"utf-8")
    files = [path.strip() for path in output.split('\n') if path.strip()]
    log.debug(u"{} files in folder '{}'".format(len(files), path))
    return files


def filter_objects(objects, key, query=None, limit=0):
    """Filter objects by comparing query with key(object)"""
    log.debug(u'Filter: {} objects, query {!r}'.format(len(objects), query))
    if not query:  # return everything up to limit
        if limit > len(objects):
            return objects[:limit]
        return objects
    # search
    hits = []
    items = [(key(obj), obj) for obj in objects]
    for k, obj in items:
        if k.startswith(query):
            hits.append((0, obj))
        elif query in k:
            hits.append((1, obj))
    hits.sort()
    if limit and len(hits) > limit:
        hits = hits[:limit]
    return [t[1] for t in hits]


def search_folder(folder, query, limit=MAX_RESULTS):
    """Return list of items in `folder` matching `query`

    Returns:
        list of alfred.Item instances
    """
    log.debug(u'folder : {!r} query : {!r}'.format(folder, query))
    # query = query.lstrip(u'/')
    query = query.strip().lower()
    files = []
    hits = []
    items = []
    for name, path in get_smart_folders():
        if name == folder:
            files = folder_contents(path)
            break
    log.debug(u'{} files in folder {}'.format(len(files), folder))
    files = [(os.path.basename(path), path) for path in files]
    hits = filter_objects(files, lambda t: t[0].lower(), query, limit)
    log.debug(u"{}/{} items match '{}'".format(len(hits), len(files), query))
    if len(hits) > MAX_RESULTS:
        hits = hits[:MAX_RESULTS]
        log.debug(u'Trimmed result count to MAX_RESULTS ({})'.format(
                  MAX_RESULTS))
    for name, path in hits:
        log.debug(u'{!r}'.format(path))
        items.append(alfred.Item(
                    {'uid': path,
                     'arg': path,
                     'valid': 'yes',
                     # 'autocomplete': path,
                     'type': 'file'},
                    name,
                    path,
                    icon=(path, {u'type' : u'fileicon'}))
        )
    return items


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
                query = query[len(name):].strip(u' {}'.format(DELIMITER))
                results = search_folder(name, query)
                break
        if not results:  # found no matching folder; filter folders
            # results = make_folder_items([t for t in folders if
            #                             t[0].lower().startswith(query)])
            results = make_folder_items(filter_objects(folders,
                                        lambda t: t[0].lower(),
                                        query))
    return results


def main():
    args = docopt(__usage__, alfred.args())
    log.debug(u'args : {}'.format(args))
    if args.get(u'--dellog'):
        if os.path.exists(LOG_CONFIG.log_path):
            os.unlink(LOG_CONFIG.log_path)
        return 0
    elif args.get(u'--openlog'):
        if os.path.exists(LOG_CONFIG.log_path):
            subprocess.check_call([u'open', LOG_CONFIG.log_path])
        else:
            print(u'Logfile does not exist', file=sys.stderr)
        return 0
    elif args.get(u'--helpfile'):
        open_help_file()
        return 0
    elif args.get(u'--log'):
        LOG_CONFIG.logging = True
        print(u'Turned logging on', file=sys.stderr)
        return 0
    elif args.get(u'--nolog'):
        LOG_CONFIG.logging = False
        print(u'Turned logging off', file=sys.stderr)
        return 0
    query = args.get(u'<query>')
    if query is None:
        query = u''
    else:
        query = query.strip(u' {}'.format(DELIMITER))
    folder = args.get(u'--folder')
    results = []
    if folder is None:
        results = search_folders(query)
    else:
        results = search_folder(folder, query)
    xml = alfred.xml(results, indent=True)
    log.debug(u'Returning {} result(s) to Alfred'.format(len(results)))
    log.debug('XML output : \n{}'.format(xml))
    alfred.write(xml)
    return 0

if __name__ == '__main__':
    sys.exit(main())