#!/usr/bin/python3
# -*- coding: utf-8 -*-
# pylint: disable=missing-docstring, line-too-long

import xml.etree.ElementTree as ET
import os.path
import argparse
import urllib
import sys
import requests
import progressbar

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:85.0) Gecko/20100101 Firefox/85.0',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'de,en-US;q=0.7,en;q=0.3',
    'Content-Type': 'application/json;charset=utf-8',
    'Origin': '',
    'Connection': 'keep-alive',
    'Referer': '',
    'DNT': '1',
    'Sec-GPC': '1',
    'Upgrade-Insecure-Requests': '1'
}


PARSER = argparse.ArgumentParser(
    description='Check osm-file for errors with website-entries')

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


def check_website(elementtype, xml_root):
    global LIMIT_COUNTER, ARGS
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
                if tag.attrib['k'] == 'website' and tag.attrib['v'].find('http') != 1:
                    print(tag.attrib['v'])
                    initial_url = tag.attrib['v']

                    # test adding https:
                    https_status = False
                    try:
                        HEADERS['Origin'] = 'https://' + initial_url
                        HEADERS['Referer'] = 'https://' + initial_url
                        https_status = requests.get(
                            'https://' + initial_url, headers=HEADERS).status_code
                    except:
                        http_status = False

                    try:
                        HEADERS['Origin'] = 'https://' + initial_url
                        HEADERS['Referer'] = 'https://' + initial_url
                        http_status = requests.get(
                            'http://' + initial_url, headers=HEADERS).status_code
                    except:
                        http_status = False

                    if https_status == 200:
                        tag.attrib['v'] = 'https://' + initial_url
                    elif http_status == 200:
                        tag.attrib['v'] = 'http://' + initial_url

                    if int(https_status) > 200:
                        print('https-status: https://' +
                              initial_url + ' ' + str(https_status))
                    if int(http_status) > 200:
                        print('http-status: http://' +
                              initial_url + ' ' + str(http_status))

                    if not https_status and not http_status:
                        continue

                    # check for redirection
                    HEADERS['Origin'] = tag.attrib['v']
                    HEADERS['Referer'] = tag.attrib['v']
                    r = requests.get(tag.attrib['v'], headers=HEADERS)
                    if r.url != tag.attrib['v']:
                        redirection = r.url
                        if redirection.endswith('/'):
                            redirection = redirection[:-1]
                        # split url for analysing it later
                        r_parts = urllib.parse.urlparse(redirection)

                        # if new url is just a scheme and a domain we take it as replacement
                        if redirection == r_parts.scheme + '://' + r_parts.netloc:
                            tag.attrib['v'] = r_parts.scheme + \
                                '://' + r_parts.netloc

                    if tag.attrib['v'].endswith('/'):
                        tag.attrib['v'] = tag.attrib['v'][:-1]

                    if tag.attrib['v'] != initial_url:
                        element_changed = True
                        print('>>> ' + tag.attrib['v'])

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
    check_website('relation', XML_ROOT)

print(str(len(XML_ROOT.findall('way'))) + ' ways found.')
if not ARGS.dryrun:
    check_website('way', XML_ROOT)

print(str(len(XML_ROOT.findall('node'))) + ' nodes found.')
if not ARGS.dryrun:
    check_website('node', XML_ROOT)
    with open(ARGS.export, 'w') as f:
        f.write(ET.tostring(RESULT_ROOT, encoding='utf8').decode('utf8'))
