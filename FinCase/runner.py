#!/usr/bin/env python

import requests

import logging

from scrapy.crawler import CrawlerProcess
from scrapy.settings import Settings

from moscowmap import settings
from moscowmap.spiders.spider_house import SpiderHouseSpider


def get_proxy(proxy_type='http'):
    """
    Get proxy from
            www.proxy-list.download
            pubproxy.com
            proxyscrape.com
            githubusercontent.com

    :proxy_type: http, http, https, socks4, socks5
    :returns: list proxy

    """

    headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:69.0) Gecko/20100101 Firefox/69.0'
        }

    urls = [
        f'https://www.proxy-list.download/api/v1/get?type={proxy_type}',
        f'http://pubproxy.com/api/proxy?type={proxy_type}&format=txt&user_agent=true&limit=5',
        f'https://api.proxyscrape.com/?request=getproxies&format=normal&proxytype={proxy_type}',
        f'https://raw.githubusercontent.com/clarketm/proxy-list/master/proxy-list-raw.txt'
           ]

    ip_proxies = set()

    for url in urls:
        response = requests.get(url, headers=headers)
        if response.ok:
            ip_proxies.update(set(response.text.splitlines()))

    proxy_list = list(map(lambda x: 'http' + '://' + x, ip_proxies))

    return proxy_list


if __name__ == "__main__":
    settings.PROXY_SETTINGS['list'] = get_proxy()

    crawler_settings = Settings()
    crawler_settings.setmodule(settings)

    with open('street.csv', 'r') as csvfile:
        queries = csvfile.read().splitlines()

    process = CrawlerProcess(settings=crawler_settings)
    process.crawl(SpiderHouseSpider, queries=queries)

    process.start()
