#!/usr/bin/env python3.6
# -*- coding: utf-8 -*-
#
# Copyright 2017 Prasanna Venkadesh
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, see <http://www.gnu.org/licenses/>.

import asyncio
import ujson
import socket
import uvloop

from aiohttp import ClientSession, TCPConnector
from bs4 import BeautifulSoup


def count_active_months(all_anchors):
    '''Counts the number of months in each year
       the list was active.

       :param str all_years: list of <td>s
       :return: year wise active month count
       :rtype: dict
    '''
    year_wise_count = {}
    for each_a in all_anchors:
        if each_a.text:
            year = each_a.text.split('-')[-1]
            if year in year_wise_count.keys():
                year_wise_count[year] += 1
            else:
                year_wise_count[year] = 1
    return year_wise_count

def month_wise_stat(html_content):
    month_soup = BeautifulSoup(html_content, "html.parser")
    month = month_soup.find('h1').text.split(', ')[-1]
    email_threads = month_soup.select('div')[3].select('ul > li')
    no_of_emails = len(email_threads)

    senders = {}
    for email_thread in email_threads:
        if email_thread.text:
            sender = email_thread.text.split('-')[-1]
            if sender in senders.keys():
                senders[sender] += 1
            else:
                senders[sender] = 1
    return {month: {"total_emails": no_of_emails, "senders": senders}}

async def hit_url(url, session):
    '''Get request to url and returns response back.

       :param str url: url to perform a get request
       :param object session: aiohttp ClientSession object
       :return: http response
       :rtype: str
    '''
    print(f"Hitting {url}")
    async with session.get(url) as response:
        response_content = await response.read()
    return response_content

async def main(list_name, loop):
    try:
        url = BASE_URL.format(list_name)
        output = {}
        connector = TCPConnector(family=socket.AF_INET, verify_ssl=False)
        async with ClientSession(loop=loop, connector=connector) as session:
            home_page = await hit_url(url, session)
            
            soup = BeautifulSoup(home_page, "html.parser")
            table = soup.find("table")
            all_anchors = table.find_all("a")

            # count all active months in each year
            output['years'] = count_active_months(all_anchors)

            # fetch all year, all months data
            tasks = [asyncio.ensure_future(hit_url(url+"/"+each_a.text, session)) 
                     for each_a in all_anchors if each_a]
            responses = await asyncio.gather(*tasks)

            # fetch total values for each month
            output['months'] = [month_wise_stat(month_page) for month_page in responses]

        # write the output to a json file
        print(f"Writing to {list_name}.json")
        with open(f'{list_name}.json', 'w', encoding="utf-8") as out_file:
            ujson.dump(output, out_file)
    except Exception as ex:
        print (ex)


if __name__ == "__main__":

    BASE_URL = "https://www.freelists.org/archive/{}"
    list_name = input("list name as per freelists.org: ")
    
    loop = uvloop.new_event_loop()
    asyncio.set_event_loop(loop)
    
    loop.run_until_complete(main(list_name, loop))
