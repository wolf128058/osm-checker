#!/usr/bin/python3
# -*- coding: utf-8 -*-
# pylint: disable=missing-docstring, line-too-long

import xml.etree.ElementTree as ET
import os.path
import re
import argparse
import urllib
import sys
import requests
import progressbar
from progressbar import Bar, ETA, AdaptiveETA, Percentage

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:85.0) Gecko/20100101 Firefox/85.0',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'de,en-US;q=0.7,en;q=0.3',
    'Content-Type': 'application/json;charset=utf-8',
    'Connection': 'keep-alive',
    'DNT': '1',
    'Sec-GPC': '1',
    'Upgrade-Insecure-Requests': '1'
}


PARSER = argparse.ArgumentParser(
    description='Check osm-file for errors with facebook-entries')

PARSER.add_argument('-i', '--input', default='export.osm',
                    help=r'the file wich contains our input-data')
PARSER.add_argument('-e', '--export', default='result.osm',
                    help=r'the file we export our data to')
PARSER.add_argument('-l', '--limit', default=15,
                    help=r'finish loop at a number of n entries')
PARSER.add_argument('-o', '--offset', default=0,
                    help=r'start loop at entrynumber n')
PARSER.add_argument('-d', '--dryrun', default=0, action='store_true',
                    help=r'dry run: only stats of given entries, no parsing, no result-file')
ARGS = PARSER.parse_args()
ARGS.limit = int(ARGS.limit) + int(ARGS.offset)

if os.path.isfile(ARGS.input):
    FILE_CONTENT = open(ARGS.input, 'r').read()
    XML_ROOT = ET.fromstring(FILE_CONTENT)
    # make a copy without relations ways and nodes
    RESULT_ROOT = ET.fromstring(FILE_CONTENT)
    for stuff in RESULT_ROOT.findall('relation'):
        RESULT_ROOT.remove(stuff)
    for stuff in RESULT_ROOT.findall('way'):
        RESULT_ROOT.remove(stuff)
    for stuff in RESULT_ROOT.findall('node'):
        RESULT_ROOT.remove(stuff)

else:
    sys.exit('Input file "' + ARGS.input + '" not found.')

LIMIT_COUNTER = 0

def check_facebookcontact(elementtype, xml_root):
    global LIMIT_COUNTER, ARGS
    list_suffix2kill = ['about', 'community', 'info',
                        'posts', 'reviews', 'services', 'timeline', ]
    list_subdomains2kill = ['m', 'web', 'b-m', 'da-dk', 'de-de', 'el-gr', 'en-gb',
                            'es-es', 'fr-fr', 'he-il', 'hr-hr', 'is-is', 'it-it', 'nl-nl', 'pl-pl', 'si-si']
    bar_max = len(xml_root.findall(elementtype))
    if int(ARGS.limit) > 0:
        bar_max = int(ARGS.limit)

    with progressbar.ProgressBar(max_value=bar_max, redirect_stdout=True) as p_bar:
        for element in xml_root.findall(elementtype):
            element_changed = False

            # save file and exit if limit is reached
            if int(ARGS.limit) > 0 and LIMIT_COUNTER >= int(ARGS.limit):
                with open(ARGS.export, 'w') as f:
                    f.write(ET.tostring(xml_root, encoding='utf8').decode('utf8'))
                break

            # iterate throug elements
            for tag in element.findall('tag'):

                # if we have found a website-tag with facebook in the url we move it to the contact:facebook-tag
                if tag.attrib['k'] == 'website' and tag.attrib['v'].find('facebook') >= 0:
                    tag.attrib['k'] = 'contact:facebook'
                    element_changed = True

                if tag.attrib['k'] == 'contact:facebook':
                    # save initial url-value to variable: current_url
                    current_url = tag.attrib['v']
                    # load initial url into variable for substitute-url
                    sub_url = current_url

                    # apply-subdomain-replacement
                    for subdomain in list_subdomains2kill:
                        sub_url = sub_url.replace(
                            subdomain + '.facebook.com', 'www.facebook.com')

                    # fix: urls starting with //
                    sub_url = re.sub(r"^\/\/(www\.|)facebook(\.com|\.de|\.pl)\/", "https://www.facebook.com/", sub_url, 0)
                    # fix: urls starting with www.facebook* or facebook*
                    sub_url = re.sub(r"^(www\.|)facebook(\.com|\.de|\.pl)\/", "https://www.facebook.com/", sub_url, 0)
                    # fix: replace http(s)://facebook* by https://www.facebook.com
                    sub_url = re.sub(r"http(|s)\:\/\/facebook(\.com|\.de|\.pl)\/", "https://www.facebook.com/", sub_url, 0)

                    # fix: cut the category-part out of the url
                    sub_url = re.sub(r"^https\:\/\/(www\.|)facebook\.com\/pages\/category\/[0-9a-zA-Z-]+\/", "https://www.facebook.com/pages/", sub_url, 0)

                    # test: if url is a redirection find its final target and use this as substitute-url
                    if requests.get(sub_url).status_code != 200:
                        test_url = re.sub(
                            r"^https\:\/\/www\.facebook\.com\/pages\/", "https://www.facebook.com/", sub_url, 0)
                        if requests.get(test_url).status_code == 200:
                            sub_url = test_url

                    # if the url does not contain photo/media-parts we do not need any get parameters
                    if sub_url.find('profile.php') == -1 and sub_url.find('/media/set/') == -1 and sub_url.find('/photo/') == -1:
                        sub_url = re.findall(r"^([^?]+)", sub_url)[0]


                    # if we got a new url so far, we tag this element as changed
                    if str(current_url) != str(sub_url):
                        print(current_url + ' > ' + sub_url)
                        tag.attrib['v'] = sub_url
                        element_changed = True

                    # sometimes we get redirected via the login-page. in this case we will have to html-decrypt the next-param and replay the get-param-removal
                    r = requests.get(tag.attrib['v'])
                    if r.url != tag.attrib['v']:
                        login_url = re.findall(
                            r"https:\/\/www\.facebook\.com\/login\/\?next\=(.*)", r.url)
                        if login_url:
                            decoded_url = urllib.parse.unquote(login_url[0])
                            if decoded_url.find('profile.php') == -1 and decoded_url.find('/media/set/') == -1 and decoded_url.find('/photo/') == -1:
                                decoded_url = re.findall(
                                    r"^([^?]+)", decoded_url)[0]
                            if current_url != decoded_url:
                                tag.attrib['v'] = decoded_url

                        else:
                            if current_url != r.url:
                                # if we can reach that url we take it as replacement otherwise remove it
                                if r.status_code == 200:
                                    tag.attrib['v'] = r.url
                                if r.status_code == 404:
                                    tag.attrib['v'] = ''
                                    print(r.url + ' >> DELETED because of 404')

                    # kill all suffixes from url
                    for suffix in list_suffix2kill:
                        if tag.attrib['v'].endswith('/' + suffix):
                            tag.attrib['v'] = tag.attrib['v'][:-(len(suffix) + 1)]
                        if tag.attrib['v'].endswith('/' + suffix + '/'):
                            tag.attrib['v'] = tag.attrib['v'][:-(len(suffix) + 2)]

                    # replay login-redirection fix
                    if tag.attrib['v'] != current_url:
                        # print(current_url + ' >>> ' + tag.attrib['v'])
                        if tag.attrib['v'].find('profile.php') == -1 and tag.attrib['v'].find('/media/set/') == -1 and tag.attrib['v'].find('/photo/') == -1 and re.findall(r"^([^?]+)", tag.attrib['v']):
                            tag.attrib['v'] = re.findall(
                                r"^([^?]+)", tag.attrib['v'])[0]
                        if tag.attrib['v'] != '' and requests.get(tag.attrib['v']).status_code == 404:
                            tag.attrib['v'] = ''                       
                        print(current_url + ' >> ' + tag.attrib['v'])

            if element_changed:
                if LIMIT_COUNTER + 1 > int(ARGS.offset) or (LIMIT_COUNTER == 0 and int(ARGS.offset) == 0):
                    # set modify-tag if element is in range
                    element.attrib['action'] = 'modify'
                    empty_tags = element.findall("tag[@v='']")
                    if empty_tags:
                        for empty_tag in empty_tags:
                            element.remove(empty_tag)
                    RESULT_ROOT.append(element)
                LIMIT_COUNTER += 1
                p_bar.update(LIMIT_COUNTER)                
    # end

print(str(len(XML_ROOT.findall('relation'))) + ' relations found.')
if not ARGS.dryrun:
    check_facebookcontact('relation', XML_ROOT)

print(str(len(XML_ROOT.findall('way'))) + ' ways found.')
if not ARGS.dryrun:
    check_facebookcontact('way', XML_ROOT)

print(str(len(XML_ROOT.findall('node'))) + ' nodes found.')
if not ARGS.dryrun:
    check_facebookcontact('node', XML_ROOT)
    with open(ARGS.export, 'w') as f:
        f.write(ET.tostring(RESULT_ROOT, encoding='utf8').decode('utf8'))
