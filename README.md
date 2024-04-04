# mediawiki_pybot
Command-line utility for performing mass edits on wikis using the MediaWiki API. Made with Python, inspired by AutoWikiBrowser.

## Dependencies
* [Python](https://www.python.org/downloads/) (>= 3.9)
* [requests](https://pypi.org/project/requests/)

## How to run
### Clone repository
```sh
git clone git@github.com:wendellavila/mediawiki_pybot.git
# or
git clone https://github.com/wendellavila//mediawiki_pybot.git
```

### cd into repository
```sh
cd mediawiki_pybot
```
### Run script with python3
```sh
python3 mediawiki_pybot.py
```
### Or run with sh
```sh
# make file executable
chmod +x mediawiki_pybot.sh
# run
./mediawiki_pybot.sh
```
## Usage
### See --help for usage
```sh
python3 mediawiki_pybot.sh --help
```
```
usage: mediawiki_pybot [-h] operation ...

Command-line utility for performing mass edits on wikis using the MediaWiki API.
Written with Python.

positional arguments:
  operation   allowed values: {save, pagelist, edit, create}
    save      stores login credentials locally. for options see 'mediawiki_pybot
              save --help'.
    pagelist  generates list of pages to be edited. for options see 'mediawiki_
              pybot pagelist --help'.
    edit      perform mass edits on pages from a pagelist. for options see
              'mediawiki_pybot edit --help'.
    create    mass create pages. for options see 'mediawiki_pybot create
              --help'.

options:
  -h, --help  show this help message and exit
```
### save
```sh
python3 mediawiki_pybot.sh save --help
```
```
usage: mediawiki_pybot save [-h] [-u USERNAME] [-p PASSWORD] [--url URL]

options:
  -h, --help            show this help message and exit
  -u USERNAME, --username USERNAME
                        bot account username
  -p PASSWORD, --password PASSWORD
                        bot password (obtain credentials via
                        Special:BotPasswords)
  --url URL             mediawiki api endpoint url
```
### pagelist
```sh
python3 mediawiki_pybot.sh pagelist --help
```
```
usage: mediawiki_pybot pagelist [-h] -s SOURCE -t TARGET [--clear]
                                [--save-path SAVE_PATH] [-l LIMIT]
                                [-n NAMESPACE]

options:
  -h, --help            show this help message and exit
  -s SOURCE, --source SOURCE
                        Type of source for pagelist generation. allowed values:
                        {category, specialpage, linkshere, transcludedin,
                        fileusage, images, links, redirects, templates,
                        usercontribs} category: Get pages pertaining to a
                        category. specialpage: Uses a page in the Special:
                        namespace to get a list of pages. linkshere:
                        WhatLinksHere - Get pages linking to a given page.
                        transcludedin: WhatTranscludesPage - Get pages that
                        transclude a given page. fileusage: Get pages currently
                        using a given image or video. images: Get images used in
                        a given page. links: Get pages linked from a given page.
                        redirects: Get pages that redirect to a given page.
                        templates: Get templates in use in a given page.
                        usercontribs: Get all contributions from a given user.
  -t TARGET, --target TARGET
                        argument for pagelist generation (page name, category
                        name, etc.)
  --clear               if set, pagelist will be overwritten instead of
                        incremented
  --save-path SAVE_PATH
                        save pagelist to a text file in a custom location
  -l LIMIT, --limit LIMIT
                        max number of pages to be returned
  -n NAMESPACE, --namespace NAMESPACE
                        only return pages in certain namespaces. format=
                        "0|1|2|3"
```
### edit
```sh
python3 mediawiki_pybot.sh edit --help
```
```
usage: mediawiki_pybot edit [-h] [-s SUBSTITUTION] [-a APPEND] [-p PREPEND]
                            [--summary SUMMARY] [--pagelist-path PAGELIST_PATH]
                            [--skip-if SKIP_IF] [--skip-ifnot SKIP_IFNOT]
                            [-d DELAY]

options:
  -h, --help            show this help message and exit
  -s SUBSTITUTION, --substitution SUBSTITUTION
                        path to a text file containing a list of text/regex
                        substitutions to be applied when editing pages. See
                        substitution_example.txt for usage.
  -a APPEND, --append APPEND
                        string to be appended to pages when editing
  -p PREPEND, --prepend PREPEND
                        string to be prepended to pages when editing
  --summary SUMMARY     edit summary
  --pagelist-path PAGELIST_PATH
                        loads a pagelist file from a custom location
  --skip-if SKIP_IF     pages that contain given string or regex won't be edited
  --skip-ifnot SKIP_IFNOT
                        pages that doesn't contain given string or regex won't
                        be edited
  -d DELAY, --delay DELAY
                        delay between each edit, in seconds
```
### create
```sh
python3 mediawiki_pybot.sh create --help
```
```
usage: mediawiki_pybot create [-h] -c CONTENT [-p PAGELIST_PATH] [-s SUMMARY] [-d DELAY]

options:
  -h, --help            show this help message and exit
  -c CONTENT, --content CONTENT
                        content to be added to each page
  -p PAGELIST_PATH, --pagelist-path PAGELIST_PATH
                        loads a pagelist file from a custom location
  -s SUMMARY, --summary SUMMARY
                        edit summary
  -d DELAY, --delay DELAY
                        delay between each edit, in seconds
```

## Examples
### Saving credentials
First, make sure you have a bot account with permission to edit in the desired wiki.<br>
You can get your bot username and password by going to Special:BotPasswords in the wiki you're editing.<br> For more information on bot accounts and bot passwords, see: [Help:Bots on FANDOM Community Central](https://community.fandom.com/wiki/Help:Bots).<br>
Then run:
```sh
python3 mediawiki_pybot.py save --username myusername --password mypassword --url https://mywiki.fandom.com/api.php
```
### Editing pages
Generating a list of pages to edit
```sh
# Getting all pages in Category:Bands
python3 mediawiki_pybot.py pagelist --source category --target Bands
```
Editing pages
```sh
# Using the substitution patterns configured in substitution_example.txt and appending a category to the page
python3 mediawiki_pybot.py edit --substitution substitution_example.txt --append "[[Category:My Edits]]" --summary "Editing pages with mediawiki_pybot"
```
### Creating pages
Generating a list of pages to create
```sh
# Getting all pages in Special:WantedCategories
python3 mediawiki_pybot.py pagelist --source specialpage --target WantedCategories
```
Creating pages
```sh
# Creating pages with wikitext content
python3 mediawiki_pybot.py create --content "==Description==
This is a category page." --summary "Creating pages with MediaWiki Pybot"
```
