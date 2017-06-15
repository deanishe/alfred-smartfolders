
Smart Folders for Alfred
========================

Quick access to your Smart Folders (Saved Searches) in [Alfred 3](http://www.alfredapp.com/).

![](img/screenshot-1.png "Alfred Smart Folders")


Usage
-----

- `.sf [<query>]` to see or filter a list of your Smart Folders.
	- `⇥` on a Smart Folder to view its contents.
	- `↩` to open the Smart Folder in Finder.
- On Smart Folder contents:
	- `↩` will open a file/folder in its default app.
	- `⌘+↩` will reveal the item in the Finder.
- `.sfhelp` to view the help file.


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
