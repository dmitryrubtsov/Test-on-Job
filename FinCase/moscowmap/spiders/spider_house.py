# -*- coding: utf-8 -*-
import scrapy
from scrapy.http import HtmlResponse
from scrapy.loader import ItemLoader

import requests
from lxml import html
import logging

from moscowmap.items import MoscowmapItem
from moscowmap import settings

from scrapy.utils.response import open_in_browser

log = logging.getLogger('scrapy.search_site')

class SpiderHouseSpider(scrapy.Spider):
    name = 'spider_house'
    allowed_domains = ['moscowmap.ru']
    start_urls = 'https://www.moscowmap.ru/imap_search.shtml'

    def __init__(self, queries: list):
        self.queries = queries


    def start_requests(self):
        params = {
            'type': 'address',
            'sid': '0',
            'sval': '',  # street name
            'hval': '',  # number of house
        }
        for query in self.queries:
            log.info(f'Searching for {query}')
            params['sval'] = query
            request = requests.post(self.start_urls, data=params)
            html_body = html.fromstring(request.text)
            html_body.make_links_absolute(self.start_urls)
            urls = html_body.xpath(
                    '//div[@class="text-wrapper left-text-shift fs14 subtitle-top"]//a/@href'
                )
            log.debug(f'Found urls for "{query}": {len(urls)}')
            if urls:
                for url in urls:
                    yield scrapy.Request(
                        url=url,
                        callback=self.parse_street,
                        meta={'query': query}
                    )

    def parse_street(self, response: HtmlResponse):
        urls_house = response.css(
            'div.house a.link-basic::attr(href)'
        ).extract()

        for url in urls_house:
            yield response.follow(
                url=url,
                callback=self.parse_house,
                meta={'query': response.meta['query']}
            )

    def parse_house(self, response: HtmlResponse):
        loader = ItemLoader(item=MoscowmapItem(), response=response)

        loader.add_css('street', 'h1 ::text')
        loader.add_css('house', 'h1 ::text')
        loader.add_css('params_house', 'div[class*="extinfo"] p ::text')
        loader.add_value('query', response.meta['query'])
        loader.add_value('url', response.url)

        yield loader.load_item()
