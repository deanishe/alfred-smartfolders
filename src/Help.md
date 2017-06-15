title: Smart Folders for Alfred Help
author: Dean Jackson <deanishe@deanishe.net>
date: 2017-06-15


Smart Folders for Alfred Help
=============================

Browse your Saved Searches in Alfred 3.

![](screenshot-1.png "Alfred Smart Folders")


Usage
-----

- `.sf [<query>]` to see or filter a list of your Smart Folders.
    - `⇥` on a Smart Folder to view/search its contents.
    - `↩` to open the Smart Folder in Finder.
- On Smart Folder contents:
    - `↩` will open a file/folder in its default app.
    - `⌘+↩` will reveal the item in the Finder.
- `.sfhelp` to view the help file.


### Custom searches ###

You can also set up keywords to go directly to the contents of a specific Smart Folder. To do this, copy the default `.sf` Script Filter and use the `-f` option to specify the name of your Smart Folder:

    /usr/bin/python smartfolders.py -f 'FOLDER_NAME' "$1"

where `FOLDER_NAME` is the name of the Saved Search whose contents you want to search.

It should look something like this:

![](screenshot-config.png "Example custom search")

The above example is included in the workflow, but has no keyword.


Third-party software, copyright etc.
------------------------------------

* All my code is covered by the [MIT licence](http://opensource.org/licenses/MIT).
* [docopt](http://docopt.org/) is covered by the [MIT licence](http://opensource.org/licenses/MIT).
* I don't know what licensing [alfred.py](https://github.com/nikipore/alfred-python) uses.


More Info
---------

Smart Folders for Alfred is hosted on [GitHub](https://github.com/deanishe/alfred-smartfolders).

Feedback to <deanishe@deanishe.net>
