# standard library imports
import argparse
import os
import sys
# custom modules
from lib import libmediawiki
from lib import utils

parser = argparse.ArgumentParser(
    prog='mediawiki_pybot',
    description='Command-line utility for performing mass edits on wikis using the MediaWiki API. Made with Python.')

subparsers = parser.add_subparsers(metavar='operation', help="allowed values: {save, pagelist, edit, create}", dest='operation')

parser_save = subparsers.add_parser('save', help="stores login credentials locally. for options see 'mediawiki_pybot save --help'.")
parser_save.add_argument('-u', '--username', action='store', help="bot account username")
parser_save.add_argument('-p', '--password', action='store', help="bot password (obtain credentials via Special:BotPasswords)")
parser_save.add_argument('--url', action='store', help="mediawiki api endpoint url")

parser_pagelist = subparsers.add_parser('pagelist',
help="generates list of pages to be edited. for options see 'mediawiki_pybot pagelist --help'.")
pagelist_choices = ['category','fileusage','images','links','linkshere','manual','newfiles','newpages',
                    'redirects','specialpage','templates','transcludedin','usercontribs', 'search']
parser_pagelist.add_argument(
    '-s', '--source', action='store', choices=pagelist_choices, metavar='SOURCE', required=True, type=str.lower,
    help="Type of source for pagelist generation. " +
    "allowed values: {category, fileusage, images, links, linkshere, manual, newfiles, newpages, redirects, specialpage, templates, transcludedin, usercontribs, search} " +
    "category: Get pages pertaining to a category. " +
    "fileusage: Get pages currently using a given image or video. " +
    "images: Get images used in a given page. " +
    "links: Get pages linked from a given page. " +
    "linkshere: WhatLinksHere - Get pages linking to a given page. " +
    "manual: Add pages to the list manually by providing a list of comma separated pagenames. " +
    "newfiles: Get the most recent files uploaded to a wiki. " +
    "newpages: Get the most recent pages created in a wiki. " +
    "redirects: Get pages that redirect to a given page. " +
    "specialpage: Uses a page in the Special: namespace to get a list of pages. " +
    "templates: Get templates in use in a given page. " +
    "transcludedin: WhatTranscludesPage - Get pages that transclude a given page. " +
    "usercontribs: Get all contributions from a given user. " +
    "search: Performs a textual search.")
parser_pagelist.add_argument('-t', '--target', action='store', required=True,
    help="argument for pagelist generation (page name, category name, etc.)")
parser_pagelist.add_argument('--clear', action='store_true',
    help="if set, pagelist will be overwritten instead of incremented")
parser_pagelist.add_argument('--save-path', action='store',
    help="save pagelist to a text file in a custom location")
parser_pagelist.add_argument('-l','--limit', action='store',
    help="max number of pages to be returned", type=int)
parser_pagelist.add_argument('-n','--namespace', action='store',
    help="only return pages in certain namespaces. Use comma separated numbers: \"0,1,2,3\"")


parser_edit = subparsers.add_parser('edit',
    help="perform mass edits on pages from a pagelist. for options see 'mediawiki_pybot edit --help'.")
parser_edit.add_argument('-s', '--substitution', action='store',
    help="path to a text file containing a list of text/regex substitutions to be applied when editing pages. See substitution_example.txt for usage.")
parser_edit.add_argument('-a', '--append', action='store', help="string to be appended to pages when editing")
parser_edit.add_argument('-p', '--prepend', action='store', help="string to be prepended to pages when editing")
parser_edit.add_argument('--summary', action='store', help="edit summary")
parser_edit.add_argument('--pagelist-path', action='store', help="loads a pagelist file from a custom location")
parser_edit.add_argument('--skip-if', action='store', help="pages that contain given string or regex won't be edited")
parser_edit.add_argument('--skip-ifnot', action='store', help="pages that doesn't contain given string or regex won't be edited")
parser_edit.add_argument('-d', '--delay', action='store', help="delay between each edit, in seconds", type=int)

parser_create = subparsers.add_parser('create', help="mass create pages. for options see 'mediawiki_pybot create --help'.")
parser_create.add_argument('-c', '--content', action='store', help="content to be added to each page", required=True)
parser_create.add_argument('-p', '--pagelist-path', action='store', help="loads a pagelist file from a custom location")
parser_create.add_argument('-s', '--summary', action='store', help="edit summary")
parser_create.add_argument('-d', '--delay', action='store', help="delay between each edit, in seconds", type=int)

args = parser.parse_args(args=None if sys.argv[1:] else ['--help'])

if len(sys.argv)==2:
    #print subparser help when args are insufficient
    if args.operation == "save":
        parser_save.print_help()
    elif args.operation == "pagelist":
        parser_pagelist.print_help()
    elif args.operation == "edit":
        parser_edit.print_help()
    else:
        parser.print_help()
else:
    DIR_PATH = os.path.dirname(os.path.realpath(__file__))
    DEFAULT_PATHS = {
        'credentials': DIR_PATH + "/cache/credentials.json",
        'pagelist': DIR_PATH + "/cache/pagelist.txt"
    }
    try:
        #performing actions based on args
        if args.operation == "save":
            utils.save_credentials(DEFAULT_PATHS['credentials'], username=args.username, password=args.password, url=args.url)
            print("Credentials saved successfully.")
        elif args.operation == "pagelist":
            PAGELIST_PATH = args.save_path if args.save_path is not None else DEFAULT_PATHS['pagelist']
            PAGELIST_MODE = "w" if args.clear else "a"
            URL = libmediawiki.get_url(DEFAULT_PATHS['credentials'])
            pagelist = libmediawiki.generate_pagelist(url=URL, pagelist_source=args.source, pagelist_target=args.target,
            namespace=args.namespace, limit=args.limit)
            if len(pagelist) == 0:
                print("No pages found with given parameters.")
            else:
                utils.write_pagelist(pagelist, PAGELIST_PATH, PAGELIST_MODE)
                print(f"{args.source.capitalize()}:{args.target} - {len(pagelist)} pages added to pagelist.")
        elif args.operation == "edit":
            CSRF_TOKEN = libmediawiki.get_token(DEFAULT_PATHS['credentials'])
            URL = libmediawiki.get_url(DEFAULT_PATHS['credentials'])
            PAGELIST_PATH = args.pagelist_path if args.pagelist_path is not None else DEFAULT_PATHS['pagelist']
            libmediawiki.edit_pages(csrf_token=CSRF_TOKEN, url=URL, pagelist_path=PAGELIST_PATH, summary=args.summary,
            substitution_path=args.substitution, append=args.append,
            prepend=args.prepend, skip_if=args.skip_if, skip_ifnot=args.skip_ifnot, delay=args.delay)
        elif args.operation == "create":
            CSRF_TOKEN = libmediawiki.get_token(DEFAULT_PATHS['credentials'])
            URL = libmediawiki.get_url(DEFAULT_PATHS['credentials'])
            PAGELIST_PATH = args.pagelist_path if args.pagelist_path is not None else DEFAULT_PATHS['pagelist']
            libmediawiki.create_pages(csrf_token=CSRF_TOKEN, url=URL, content=args.content, pagelist_path=PAGELIST_PATH,
            summary=args.summary, delay=args.delay)
    except Exception as e:
        print(e)
        
parser.exit()