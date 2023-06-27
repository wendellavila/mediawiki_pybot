import os
import json
import re
import requests
import time
from typing import List

SESSION = requests.Session()

def login(username: str, password: str, url:str) -> str:
    # Retrieve login token first
    LOGIN_TOKEN_PARAMS = {
        'action':"query",
        'meta':"tokens",
        'type':"login",
        'format':"json"
    }
    request = SESSION.get(url=url, params=LOGIN_TOKEN_PARAMS)
    data = request.json()
    LOGIN_TOKEN = data['query']['tokens']['logintoken']

    # Send a post request to login. Using the main account for login is not
    # supported. Obtain credentials via Special:BotPasswords
    # (https://www.mediawiki.org/wiki/Special:BotPasswords) for lgname & lgpassword
    LOGIN_PARAMS = {
        'action': "login",
        'lgname': username,
        'lgpassword': password,
        'lgtoken': LOGIN_TOKEN,
        'format': "json"
    }
    request = SESSION.post(url, data=LOGIN_PARAMS)
    data = request.json()
    if(data['login']['result'] == 'Success'):
        print(username + ": Login successful.")
    else:
        raise Exception("Login failed: Wrong credentials. Check your credentials and run 'mediawiki-pybot save' again.")
    
    # Step 3: GET request to fetch CSRF token
    CSRF_PARAMS = {
        "action": "query",
        "meta": "tokens",
        "format": "json"
    }
    request = SESSION.get(url=url, params=CSRF_PARAMS)
    data = request.json()
    CSRF_TOKEN = data['query']['tokens']['csrftoken']
    
    return CSRF_TOKEN

def set_request_limit(pagelist_source: str, pagelist_target: str, params: dict, limit: int):
    # max limit per request is 500
    QUERY_PROPS = ("linkshere", "fileusage", "images","links", "redirects", "templates", "transcludedin")

    if pagelist_source == 'category':
        params['cmlimit'] = limit
    elif pagelist_source == 'usercontribs':
        params['uclimit'] = limit
    elif pagelist_source == 'specialpage':
        if pagelist_target.lower() == 'newfiles':
            params['lelimit'] = limit
        elif pagelist_target.lower() == 'newpages':
            params['rclimit'] = limit
        else:
            params['qplimit'] = limit
    elif pagelist_source in QUERY_PROPS:
        if pagelist_source == 'linkshere':
            params['lhlimit'] = limit
        elif pagelist_source == 'fileusage':
            params['fulimit'] = limit
        elif pagelist_source == 'images':
            params['imlimit'] = limit
        elif pagelist_source == 'links':
            params['pllimit'] = limit
        elif pagelist_source == 'redirects':
            params['rdlimit'] = limit
        elif pagelist_source == 'templates':
            params['tllimit'] = limit
        elif pagelist_source == 'transcludedin':
            params['tilimit'] = limit

    return params
    
def get_pagelist(url: str, pagelist_source: str, pagelist_target: str, namespace: str = "*", limit: int = None) -> List[str]:
    if url is None:
        raise Exception("Unable to get pages: url is missing from saved credentials. " + 
        "Run 'mediawiki-pybot save' to save credentials.")
    pagelist_source = pagelist_source.lower()
    pagelist = []
    params = {
        'action': "query",
        'format': "json",
        'formatversion': 2
    }
    # https://www.mediawiki.org/wiki/API:Properties
    QUERY_PROPS = ("linkshere", "fileusage", "images","links", "redirects", "templates", "transcludedin")

    #to do: subcategories, recursive whatlinks here, recursive transcludedin
    if pagelist_source == 'category':
        # https://www.mediawiki.org/wiki/API:Categorymembers
        pagelist_target = pagelist_target[9:] if pagelist_target[0:9].lower() == "category:" else pagelist_target
        params['list'] = "categorymembers"
        params['cmprop'] = "title"
        params['cmtitle'] = "Category:" + pagelist_target
        params['cmnamespace'] = namespace
    elif pagelist_source == 'usercontribs':
        # https://www.mediawiki.org/wiki/API:Usercontribs
        pagelist_target = pagelist_target[6:] if pagelist_target[0:6].lower() == "user:" else pagelist_target
        params['list'] = "usercontribs"
        params['ucprop'] = "title"
        params['ucuser'] = pagelist_target
        params['ucnamespace'] = namespace
    elif pagelist_source == 'specialpage':
        # https://www.mediawiki.org/wiki/API:Querypage
        pagelist_target = pagelist_target[8:] if pagelist_target[0:8].lower() == "special:" else pagelist_target
        if pagelist_target.lower() == 'newfiles':
            # https://www.mediawiki.org/wiki/API:Logevents
            params['list'] = "logevents"
            params['letype'] = "upload"
            params['lenamespace'] = 6
        elif pagelist_target.lower() == 'newpages':
            # https://www.mediawiki.org/wiki/API:Logevents
            params['list'] = "logevents"
            params['letype'] = "create"
            params['lenamespace'] = 0
        else:
            params['list'] = "querypage"
            params['qppage'] = pagelist_target
    elif pagelist_source in QUERY_PROPS:
        # https://www.mediawiki.org/wiki/API:Properties
        params['titles'] = pagelist_target
        params['prop'] = pagelist_source
    else:
        raise Exception("Unsupported pagelist source.")
    
    # max limit per request is 500
    request_limit = 500 if limit is None or limit >= 500 else limit
    params = set_request_limit(pagelist_source, pagelist_target, params, request_limit)

    pagelist = []
    print("Getting pagelist...")
    while request_limit > 0:
        request = SESSION.get(url=url, params=params)
        data = request.json()
        if 'error' in data:
            raise Exception(data['error'])
        
        if pagelist_source == 'category':
            pagelist += [page['title'] for page in data['query']['categorymembers']]
        elif pagelist_source == 'usercontribs':
            pagelist += [page['title'] for page in data['query']['usercontribs']]
        elif pagelist_source == 'specialpage':
            if pagelist_target.lower() == 'newfiles' or pagelist_target.lower() == 'newimages':
                pagelist += [page['title'] for page in data['query']['logevents']]
            elif pagelist_target.lower() == 'newpages':
                pagelist += [page['title'] for page in data['query']['logevents']]
            else:
                pagelist += [page['title'] for page in data['query']['querypage']['results']]
        else:
            # QUERY_PROPS
            NAMESPACES = [int(ns) for ns in namespace.split('|') if ns.strip().isdigit()] if namespace != "*" else []
            if pagelist_source in data['query']['pages'][0]:
                for page in data['query']['pages'][0][pagelist_source]:
                    if namespace == "*":
                        pagelist.append(page['title'])
                    else:
                        if page['ns'] in NAMESPACES:
                            pagelist.append(page['title'])
        
        # https://www.mediawiki.org/wiki/API:Continue
        if 'continue' in data:
            params.update(data['continue'])
        elif 'qpoffset' in data:
            params.update(data['qpoffset'])
        elif 'rccontinue' in data:
            params.update(data['rccontinue'])
        elif 'lecontinue' in data:
            params.update(data['lecontinue'])
        elif 'lhcontinue' in data:
            params.update(data['lhcontinue'])
        elif 'fucontinue' in data:
            params.update(data['fucontinue'])
        elif 'imcontinue' in data:
            params.update(data['imcontinue'])
        elif 'plcontinue' in data:
            params.update(data['plcontinue'])
        elif 'rdcontinue' in data:
            params.update(data['rdcontinue'])
        elif 'tlcontinue' in data:
            params.update(data['tlcontinue'])
        elif 'ticontinue' in data:
            params.update(data['ticontinue'])
        else:
            break

        # reducing request limit when total of pages gets closer to user provided limit
        if limit is not None:
            request_limit = (limit - len(pagelist)) if (limit - len(pagelist)) < 500 else 500
            params = set_request_limit(pagelist_source, pagelist_target, params, request_limit)
    return pagelist

def edit_pages(csrf_token: str, url: str, pagelist: List[str], substitution_path: str = None, append: str = None, prepend: str = None,
skip_if: str = None, skip_ifnot: str = None, delay: int = None, summary: str = None):
    if substitution_path == None and append == None and prepend == None:
        raise Exception("No modifications to be performed.")

    substitution_list = []
    if substitution_path is not None and os.path.exists(substitution_path):
        with open(substitution_path) as substitution_file:
            for line in substitution_file.readlines():
                match = re.search(r'^"(.*)" "(.*)"', line)
                if match:
                    substitution_list.append((match.group(1), match.group(2)))

    total_page_count = len(pagelist)
    page_saved_count = 0
    page_skipped_count = 0
    page_count = 0
    page_error_count = 0
    pages_with_error = []
    print("Editing pages...")
    
    # https://www.mediawiki.org/wiki/API:Revisions
    getpage_params = {
        'action': "query",
        'format': "json",
        'formatversion': 2,
        'prop': "revisions",
        'rvprop': "ids|timestamp|content",
        'rvslots': "main",
        'rvlimit': 1,
        'curtimestamp': True
    }
    # https://www.mediawiki.org/wiki/API:Edit
    sendpage_params = {
        'action': "edit",
        'format': "json",
        'formatversion': 2,
        'title': "",
        'text': "",
        'summary': "",
        'bot': True,
        'recreate': False,
        'nocreate': True,
        'watchlist': "watch",
        'token': csrf_token
    }
    
    for pagename in pagelist:
        getpage_params['titles'] = pagename
        sendpage_params['title'] = pagename
        # navigating through redirects if redirect is found
        while True:  
            request = SESSION.get(url=url, params=getpage_params)
            data = request.json()
            if 'missing' in data['query']['pages'][0]:
                page_error_count += 1
                pages_with_error.append((pagename, "Page doesn't exist."))
            else:
                latest_revision = data['query']['pages'][0]['revisions'][0]
                page_content = latest_revision['slots']['main']['content']

                # checking if content is redirect
                redirect_search = re.search("#REDIRECT \[\[(.*?)\]\]", page_content)
                if bool(redirect_search):
                    getpage_params['titles'] = redirect_search.group(1)
                    sendpage_params['title'] = redirect_search.group(1)
                else:
                    #if page_content contains "skip_if", skip page
                    skip = bool(re.search(skip_if, page_content)) if skip_if is not None else False
                    if not skip:
                        # if page content doesn't contain "skip_ifnot", skip page
                        skip = not bool(re.search(skip_ifnot, page_content)) if skip_ifnot is not None else False
                        
                    if skip:
                        page_skipped_count += 1
                    else:
                        page_content_edited = page_content
                        for substitution in substitution_list:
                            page_content_edited = re.sub(substitution[0], substitution[1], page_content_edited)
                        if append is not None:
                            page_content_edited = append + "\n" + page_content_edited
                        if prepend is not None:
                            page_content_edited = page_content_edited + "\n" + prepend

                        if page_content_edited == page_content:
                            page_skipped_count += 1
                        else:
                            sendpage_params['text'] = page_content_edited
                            sendpage_params['starttimestamp'] = data['curtimestamp']
                            sendpage_params['basetimestamp'] = latest_revision['timestamp']
                            sendpage_params['baserevid'] = latest_revision['revid']
                            sendpage_params['contentformat'] = latest_revision['slots']['main']['contentformat']
                            sendpage_params['contentmodel'] = latest_revision['slots']['main']['contentmodel']
                            if summary is not None:
                                sendpage_params['summary'] = summary
                            request = SESSION.post(url=url, data=sendpage_params)
                            data = request.json()
                            if("error" in data):
                                page_error_count += 1
                                pages_with_error.append((pagename, data['error']['info']))
                                print(f"\nPage: {pagename}  Status: Error - {data['error']['info']}")
                            else:
                                print(f"\nPage: {pagename}  Status: {data['edit']['result']}")
                            if delay is not None:
                                time.sleep(delay)

                        page_saved_count += 1
                    #end else skip
                    break
                #end else redirect_search
            #end else missing
            page_count += 1
        #end while
        
        print(f"Edited: {page_saved_count}  Skipped: {page_skipped_count}  Errors: {page_error_count}  " + 
              f"Remaining: {total_page_count - page_count}  Completed: {(page_count / len(pagelist) * 100):.2f}%")
    if pages_with_error:
        print("Pages with errors:")
        for (pagename, error) in pages_with_error:
            print(f"{pagename}:  Error: {error}")