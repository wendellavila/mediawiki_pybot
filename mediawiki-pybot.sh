#!/usr/bin/env python
import argparse
import mw_api_functions
import json
import os
import sys

parser = argparse.ArgumentParser(
    prog='mediawiki-pybot',
    description='Command-line utility for performing mass edits on wikis using the MediaWiki API. Written in Python.')

subparsers = parser.add_subparsers(metavar='operation', help="allowed values: {save, pagelist, edit}", dest='operation')

parser_save = subparsers.add_parser('save', help="stores login credentials locally. for options see 'mediawiki-pybot save --help'.")
parser_save.add_argument('-u', '--username', action='store', help="bot account username")
parser_save.add_argument('-p', '--password', action='store', help="bot password (obtain credentials via Special:BotPasswords)")
parser_save.add_argument('--url', action='store', help="mediawiki api endpoint url")

parser_pagelist = subparsers.add_parser('pagelist',
help="generates list of pages to be edited. for options see 'mediawiki-pybot pagelist --help'.")
pagelist_choices = ['category','specialpage','linkshere','transcludedin','fileusage','images',
    'links','redirects','templates', 'usercontribs', 'newfiles', 'newpages']
parser_pagelist.add_argument(
    '-s', '--source', action='store', choices=pagelist_choices, metavar='SOURCE', required=True,
    help="Type of source for pagelist generation. " +
    "allowed values: {category, specialpage, linkshere, transcludedin, fileusage, images, links, redirects, templates, usercontribs} " + 
    "category: Get pages pertaining to a category. " +
    "specialpage: Uses a page in the Special: namespace to get a list of pages. " +
    "linkshere: WhatLinksHere - Get pages linking to a given page. " +
    "transcludedin: WhatTranscludesPage - Get pages that transclude a given page. " +
    "fileusage: Get pages currently using a given image or video. " +
    "images: Get images used in a given page. " +
    "links: Get pages linked from a given page. " +
    "redirects: Get pages that redirect to a given page. " +
    "templates: Get templates in use in a given page. " +
    "usercontribs: Get all contributions from a given user. ")
parser_pagelist.add_argument('-t', '--target', action='store', required=True,
    help="argument for pagelist generation (page name, category name, file path, etc.)")
parser_pagelist.add_argument('--no-reset', action='store_true',
    help="use this flag to increment an existing pagelist instead of resetting it")
parser_pagelist.add_argument('--save-path', action='store',
    help="save pagelist to a text file in a custom location")
parser_pagelist.add_argument('-l','--limit', action='store',
    help="limits the total number of pages to be returned", type=int)
parser_pagelist.add_argument('-n','--namespace', action='store',
    help="limits returned pages to certain namespaces. format= \"0|1|2|3\"")


parser_edit = subparsers.add_parser('edit',
    help="perform mass edits on pages from a pagelist. for options see 'mediawiki-pybot edit --help'.")
parser_edit.add_argument('-r', '--regex', action='store',
    help="regex string or file with regex list to be applied when editing pages")
parser_edit.add_argument('-a', '--append', action='store', help="string to be appended to pages when editing")
parser_edit.add_argument('-p', '--prepend', action='store', help="string to be prepended to pages when editing")
parser_edit.add_argument('--pagelist-path', action='store', help="loads a pagelist file from a custom location")
parser_edit.add_argument('--skip-if', action='store', help="pages that contains given string or regex won't be edited")
parser_edit.add_argument('--skip-ifnot', action='store', help="pages that doesn't contain given string or regex won't be edited")
parser_edit.add_argument('--delay', action='store', help="delay between each edit, in seconds (default=1)", type=int)

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
    #performing actions based on args
    if args.operation == "save":
        if os.path.exists("credentials.json"):
            with open('credentials.json') as input_file:
                credentials = json.load(input_file)
        else:
            credentials = {'username':None,'password':None,'url':None}

        credentials['username'] = args.username if args.username is not None else credentials['username']
        credentials['password'] = args.password if args.password is not None else credentials['password']
        credentials['url'] = args.url if args.url is not None else credentials['url']

        with open("credentials.json", "w") as output_file:
            json.dump(credentials, output_file)
        print("Credentials saved successfully.")
    elif args.operation == "pagelist":
        pagelist_path = args.save_path if args.save_path is not None else "pagelist.txt"
        pagelist_mode = "a" if args.no_reset else "w"
            
        if os.path.exists("credentials.json"):
            with open('credentials.json') as credentials_file:
                credentials = json.load(credentials_file)
                url = credentials['url']
        else:
            url = None
        with open(pagelist_path, pagelist_mode) as pagelist_file:
            pagelist = mw_api_functions.get_pagelist(url, args.source, args.target, args.namespace, args.limit)
            for pagename in pagelist:
                pagelist_file.write("{}\n".format(pagename))
            if len(pagelist) == 0:
                print("No pages found with given source and target.")
            else:
                print(f"{args.source.capitalize()}:{args.target} - {len(pagelist)} pages added to pagelist.")
    elif args.operation == "edit":
        if os.path.exists("credentials.json"):
            with open('credentials.json') as credentials_file:
                credentials = json.load(credentials_file)
            if credentials['username'] == None or credentials['password'] == None or credentials['url'] == None:
                raise Exception("Unable to login: Saved credentials partially missing. Run 'mediawiki-pybot save' to save credentials.")
            else:
                CSRF_TOKEN = ""
                #CSRF_TOKEN = mw_api_functions.login(credentials['username'], credentials['password'], credentials['url'])
        else:
            raise Exception("Unable to login: No saved credentials. Run 'mediawiki-pybot save' to save credentials.")
        
        pagelist_path = args.pagelist_path if args.pagelist_path is not None else "pagelist.txt"
        pagelist = []
        with open(pagelist_path, "r") as pagelist_file:
            for line in pagelist_file.readlines():
                pagelist.append(line)
        mw_api_functions.edit_pages(CSRF_TOKEN, pagelist, args.regex, args.append, args.prepend, args.skip_if, args.skip_ifnot, args.delay)
        
parser.exit()