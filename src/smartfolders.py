#!/usr/bin/env python3
#
# Copyright (c) 2023 deanishe@deanishe.net.
#
# MIT Licence. See http://opensource.org/licenses/MIT
#
# Created on 2023-06-05
#
"""Search smart folders."""

import argparse
import json
import os
import re
import sys
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Callable, Iterator, Optional, Union

MAX_RESULTS = 100
# UPDATE_SETTINGS = {'github_slug': 'deanishe/alfred-smartfolders'}
CACHE_AGE_FOLDERS = 20  # seconds
CACHE_AGE_CONTENTS = 10  # seconds

# HELPFILE = Path('.') / 'Help.html'

DELIMITER = '/'
HOME = os.getenv('HOME')
VERBOSE = os.getenv('alfred_debug') == '1'
BUNDLEID = os.getenv('alfred_workflow_bundleid')
TRIGGER_URL = f'alfred://runtrigger/{BUNDLEID}/{{name}}/?argument={{arg}}'

CACHE = Path(os.getenv('alfred_workflow_cache'))
LOCKFILE = CACHE / 'reload.lock'
FOLDER_LIST = CACHE / 'folders.txt'

ICON_ERROR = {'path': 'error.png'}
ICON_WARNING = {'path': 'warning.png'}
ICON_INFO = {'path': 'info.png'}
ICON_LOADING = {'path': 'loading.png'}
ICON_SYNC = {'path': 'sync.png'}


def shortpath(p: Union[Path, str]) -> str:
    """Pretty path."""
    p = str(p)
    if p.startswith(HOME):
        return '~' + p[len(HOME):]

    return p


@contextmanager
def timed(title: str) -> Iterator[None]:
    """Log execution time."""
    start = time.time()
    yield
    log('%s ⧖ %0.3fs', title, time.time() - start)


def make_matcher(query: str) -> Callable[[Path], bool]:
    """Make function that matches paths that match query."""
    flags = re.I if query.islower() else 0
    pat = '.*'.join(query.split())
    rx = re.compile(f'.*{pat}.*', flags)

    def _inner(p: Path) -> bool:
        return rx.match(p.name)

    return _inner


def cache_file(path: Union[Path, str]) -> Path:
    """Return cache key for `path`."""
    import hashlib
    h = hashlib.sha256(str(path).encode('utf-8'))
    name = f'folder-{h.hexdigest()[:12]}.txt'
    return CACHE / name


def get_folder(path: Path) -> list[Path]:
    """Get contents of folder."""
    import plistlib
    from subprocess import check_output

    log('reading plist "%s" ...', shortpath(path))
    with path.open('rb') as fp:
        data = plistlib.load(fp)

    params = data['RawQueryDict']
    query = data['RawQuery']
    locations = params['SearchScopes']
    cmd = ['mdfind']
    for p in locations:
        if p == 'kMDQueryScopeHome':
            p = str(Path('~').expanduser())
        elif p == 'kMDQueryScopeComputer' or not Path(p).exists():
            continue

        cmd.extend(['-onlyin', p])

    cmd.append(query)
    log('cmd=%r', cmd)

    out = check_output(cmd, text=True).strip()
    return [Path(s) for s in out.split('\n')]


def get_all_folders() -> list[Path]:
    """List of all smart folders on system."""
    from subprocess import check_output
    out = check_output([
        'mdfind',
        'kMDItemContentType == com.apple.finder.smart-folder',
    ],
                       text=True).strip()

    return [Path(s) for s in out.split('\n')]


def find_folder(name: str) -> Path:
    """Get path for folder."""
    folders, _ = load_folders()
    for p in folders:
        if p == Path(name) or p.stem == name:
            return p

    raise ValueError(f'Unknown folder: {name}')


def load_folder(folder: str) -> tuple[list[Path], bool]:
    """Load folder contents from cache."""
    cache = cache_file(find_folder(folder))
    if not cache.exists():
        return [], False

    fresh = time.time() - cache.stat().st_mtime < CACHE_AGE_CONTENTS
    paths = [Path(s) for s in cache.read_text().split('\n')]
    return paths, fresh


def load_folders() -> tuple[list[Path], bool]:
    """Load folders from cache."""
    if not FOLDER_LIST.exists():
        return [], False

    fresh = time.time() - FOLDER_LIST.stat().st_mtime < CACHE_AGE_FOLDERS
    folders = [Path(s) for s in FOLDER_LIST.read_text().split('\n')]
    return folders, fresh


@contextmanager
def lock() -> Iterator[None]:
    """Context manager that creates then deletes LOCKFILE."""
    try:
        with LOCKFILE.open('w') as fp:
            fp.write(str(os.getpid()))
            yield
    finally:
        LOCKFILE.unlink(missing_ok=True)


def log(s, *args, **kwargs):
    """Log to STDERR."""
    if not VERBOSE:
        return

    if args:
        s = s % args
    elif kwargs:
        s = s % kwargs

    print(s, file=sys.stderr)


def run_trigger(name: str, arg: str = '') -> None:
    """Run external trigger."""
    from subprocess import check_call
    from urllib.parse import quote_plus
    url = TRIGGER_URL.format(name=name, arg=quote_plus(arg))
    check_call(['/usr/bin/open', url], text=True)


def print_items(*items: dict, **kwargs: dict[str, str]) -> None:
    """Send items to Alfred as JSON feedback."""
    feedback = {'items': items}
    if 'rerun' in kwargs and (v := kwargs.pop('rerun')):
        feedback['rerun'] = v

    if kwargs:
        feedback['variables'] = kwargs

    json.dump(feedback, sys.stdout, indent=2)


def info(title: str, subtitle: str = '') -> dict:
    """Info message as Alfred item."""
    return {'title': title, 'subtitle': subtitle, 'valid': False, 'icon': ICON_INFO}


def warning(title: str, subtitle: str = '') -> dict:
    """Warning message as Alfred item."""
    return {'title': title, 'subtitle': subtitle, 'valid': False, 'icon': ICON_WARNING}


def error(title: Union[str, Exception], subtitle: str = '') -> dict:
    """Error message as Alfred item."""
    return {'title': str(title), 'subtitle': subtitle, 'valid': False, 'icon': ICON_ERROR}


class Backup(Exception):  # noqa: N818
    """Raised when query ends with DELIMITER. Signals workflow to exit a folder."""


def do_config(_args: argparse.Namespace) -> None:
    """Show config."""


def do_cache(args: argparse.Namespace) -> None:
    """Cache folder(s)."""
    cache = None
    if args.folder:
        # log('caching folder "%s" ...', args.folder)
        path = find_folder(args.folder)
        cache = cache_file(path)
        files = get_folder(path)
        log('%d file(s) in folder "%s"', len(files), args.folder)
        tmp = cache.parent / f'{cache.name}.tmp'
        out = '\n'.join([str(p) for p in files])
        tmp.write_text(out)
        tmp.rename(cache)

    else:
        folders = get_all_folders()
        log('%d smart folder(s) found on system', len(folders))
        tmp = FOLDER_LIST.parent / f'{FOLDER_LIST.name}.tmp'
        out = '\n'.join([str(p) for p in folders])
        tmp.write_text(out)
        tmp.rename(FOLDER_LIST)

    # delete old files
    for p in CACHE.glob('folder-*.txt'):
        if p != cache:
            p.unlink()


def _parse_query(query: str) -> tuple[Optional[str], Optional[str]]:
    """Split query into (folder, query)."""
    if query.endswith(DELIMITER):
        raise Backup()

    i = query.find(DELIMITER)
    folder = None
    if i > -1:
        folder = query[:i].strip()
        query = query[i + len(DELIMITER):].strip()
    else:
        query = query.strip()

    return folder, query


def file_item(path: Path, is_folder: bool = True) -> dict:
    """Make Alfred item for path."""
    s = str(path)
    auto = f'{path.stem} {DELIMITER} ' if is_folder else None
    return {
        'title': path.name,
        # 'autocomplete': f'{p.stem} {DELIMITER} ',
        'autocomplete': auto,
        'subtitle': f'~{s[len(HOME):]}' if s.startswith(HOME) else s,
        'arg': s,
        'uid': s,
        'type': 'file',
        'icon': {
            'path': s,
            'type': 'fileicon',
        },
    }


def do_search_in_folder(folder: str, query: str) -> None:
    """Search within a smart folder."""
    reloading = LOCKFILE.exists() or os.getenv('reloading')
    files, fresh = load_folder(folder)
    # log('loaded %d file(s) for folder "%s" (fresh=%r)', len(files), folder, fresh)
    if not fresh and not reloading:
        run_trigger('reload', folder)
        reloading = True

    rerun = 0.2 if reloading else 0

    if query:
        files = list(filter(make_matcher(query), files))
        log('%d file(s) match %r', len(files), query)

    items = [file_item(p) for p in files]
    if not items:
        items.append(warning('Nothing Found', 'Try a different query?'))

    print_items(*items, rerun=rerun)
    return


def _workflow_actions(query: str) -> list[dict]:
    """Special action items that match query."""
    if len(query) < 2:
        return []

    items = []
    if 'reload'.startswith(query) or 'refresh'.startswith(query):
        items.append({
            'title': 'Reload Folders',
            'subtitle': 'Reload list of smart folders',
            'arg': ['action', 'reload'],
            'uid': 'reload',
            'icon': ICON_LOADING,
        })

    if 'help'.startswith(query):
        items.append({
            'title': 'View Help',
            'subtitle': 'Open help in your browser',
            'arg': ['action', 'help'],
            'uid': 'help',
            'icon': ICON_INFO,
        })

    return items


def do_search(args: argparse.Namespace) -> None:
    """Search (in) folder."""
    if args.folder:
        return do_search_in_folder(args.folder, args.query)

    try:
        folder, query = _parse_query(args.query)
    except Backup:
        run_trigger('search')
        return None

    log('folder=%r, query=%r', folder, query)
    if folder:
        return do_search_in_folder(folder, query)

    reloading = LOCKFILE.exists() or os.getenv('reloading')
    folders, fresh = load_folders()
    # log('loaded %d folder(s) (fresh=%r)', len(folders), fresh)
    if not fresh and not reloading:
        run_trigger('reload')
        reloading = True

    rerun = 0.2 if reloading else 0

    if query:
        folders = list(filter(make_matcher(query), folders))
        # log('%d folder(s) match %r', len(folders), query)

    items = _workflow_actions(query)
    items.extend([file_item(p, True) for p in folders])

    if not items:
        items.append(warning('Nothing Found', 'Try a different query?'))

    print_items(*items, rerun=rerun)
    return None


def parse_args() -> argparse.Namespace:
    """Handle CLI arguments."""
    p = argparse.ArgumentParser(description=__doc__)

    g = p.add_mutually_exclusive_group()
    g.add_argument('--config',
                   dest='func',
                   action='store_const',
                   const=do_config,
                   help='view workflow configuration')
    g.add_argument('--cache',
                   dest='func',
                   action='store_const',
                   const=do_cache,
                   help='cache folder(s)')

    p.add_argument('-f', '--folder', type=str, help='only this folder')

    p.add_argument('query', metavar='<query>', nargs='?', help='search query')

    p.set_defaults(func=do_search)
    return p.parse_args()


def main():
    """Run script."""
    CACHE.mkdir(0o755, parents=True, exist_ok=True)
    args = parse_args()
    log('🍺')
    log('args=%r', args)
    # load_config()
    args.func(args)


if __name__ == '__main__':
    try:
        main()
    except Exception as err:
        from traceback import print_exc
        print_exc(file=sys.stderr)
        print_items(error(err))
        sys.exit(1)
