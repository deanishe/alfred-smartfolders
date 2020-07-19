
Smart Folders for Alfred
========================

Quick access to your Smart Folders (Saved Searches) in [Alfred](http://www.alfredapp.com/).

![](img/screenshot-1.png "Alfred Smart Folders")


Download & Installation
-----------------------

**NOTE:** Version 3 and later are only compatible with Alfred 4+. If you're still using Alfred 3, download [v2.2][v2.2].

Download the workflow from [GitHub releases][gh-releases] and double-click the `.alfredworkflow` file to install.


Usage
-----

- `.sf [<query>]` to see or filter a list of your Smart Folders
	- `⇥` on a Smart Folder to view its contents
	- `↩` to open the Smart Folder in Finder
    - `⌘↩` to reveal the Smart Folder in Finder
- On Smart Folder contents:
	- `↩` to open a file/folder in its default app
	- `⌘+↩` to reveal the item in the Finder
- `.sfhelp` to view the help file


Custom searches
---------------

You can also set up keywords to go directly to the contents of a specific Smart Folder.

See the included help file for more details (keyword `.sfhelp` to view it).


Third-party software, copyright etc.
------------------------------------

This workflow relies upon the following libraries:

- [Alfred-Workflow][aw], a library for building Alfred workflows.
- [docopt][docopt], a library for parsing command-line options.

Both libraries and the code in the workflow are released under the [MIT licence][mit]

[aw]: http://www.deanishe.net/alfred-workflow/
[mit]: http://opensource.org/licenses/MIT
[docopt]: http://docopt.org/
[gh-releases]: https://github.com/deanishe/alfred-smartfolders/releases/latest
[v2.2]: https://github.com/deanishe/alfred-smartfolders/releases/tag/v2.2.0
