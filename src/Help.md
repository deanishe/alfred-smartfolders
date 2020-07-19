Smart Folders for Alfred
========================

Browse your Saved Searches in Alfred 4+.

![](screenshot-1.png "Alfred Smart Folders")


Usage
-----

- `.sf [<query>]` to see or filter a list of your Smart Folders
    - `⇥` on a Smart Folder to view its contents
    - `↩` to open the Smart Folder in Finder
    - `⌘↩` to reveal the Smart Folder in Finder
- On Smart Folder contents:
    - `↩` to open a file/folder in its default app
    - `⌘+↩` to reveal the item in the Finder
- `.sfhelp` to view this help file


### Custom searches ###

You can also set up keywords to go directly to the contents of a specific Smart Folder. To do this, copy the default `.sf` Script Filter and use the `-f` option to specify the name of your Smart Folder:

    /usr/bin/python smartfolders.py -f 'FOLDER_NAME' "$1"

where `FOLDER_NAME` is the name of the Saved Search whose contents you want to search.

It should look something like this:

![](screenshot-config.png "Example custom search")

The above example is included in the workflow, but has no keyword.


Third-party software, copyright etc.
------------------------------------

- [Alfred-Workflow][aw], a library for building Alfred workflows.
- [docopt][docopt], a library for parsing command-line options.

Both libraries and the code in the workflow are released under the [MIT licence][mit].


More Info
---------

Smart Folders for Alfred is hosted on [GitHub](https://github.com/deanishe/alfred-smartfolders).

Feedback to <deanishe@deanishe.net>


[aw]: http://www.deanishe.net/alfred-workflow/
[mit]: http://opensource.org/licenses/MIT
[docopt]: http://docopt.org/
