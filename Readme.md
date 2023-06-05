# Smart Folders for Alfred

Quick access to your Smart Folders (Saved Searches) in [Alfred](http://www.alfredapp.com/).

![](screenshot.png "Alfred Smart Folders")

## Download & Installation

Download the workflow from [GitHub releases][gh-releases] and double-click the `.alfredworkflow` file to install.

## Usage

-   `.sf [<query>]` to see or filter a list of your Smart Folders
    -   `⇥` on a Smart Folder to view its contents
    -   `↩` to open the Smart Folder in Finder
        -   `⌘↩` to reveal the Smart Folder in Finder
-   On Smart Folder contents:
    -   `↩` to open a file/folder in its default app
    -   `⌘+↩` to reveal the item in the Finder
-   `.sf reload` to refresh list of Smart Folders
-   `.sf help` to view the help file

## Custom searches

You can also set up keywords to go directly to the contents of a specific Smart Folder. To do this, copy the default `.sf` Script Filter and use the `-f` option to specify the name of your Smart Folder:

    ./smartfolders.py -f 'FOLDER_NAME' "$1"

where `FOLDER_NAME` is the name of the Saved Search whose contents you want to search.

There is an example Script Filter included in the workflow (marked red) to search a Smart Folder called "TODO".

## Third-party software, copyright etc.

The code in this workflow is released under the [MIT licence][mit].

[mit]: http://opensource.org/licenses/MIT
[gh-releases]: https://github.com/deanishe/alfred-smartfolders/releases/latest
