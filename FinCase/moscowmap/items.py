# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy
from scrapy.loader.processors import Compose, MapCompose, TakeFirst

def parse_params(params: list):
    params = list(map(lambda s: s.strip().strip(':'), params))
    result = dict(zip(params[::2], params[1::2]))
    return result

def parse_house(house: list):
    house = house[-1].split()
    result = {'number': house[0]}
    result.update(dict(zip(house[1::2], house[2::2])))
    return result


class MoscowmapItem(scrapy.Item):
    _id = scrapy.Field()
    street = scrapy.Field(
        input_processor=MapCompose(lambda s: s.strip().strip(',')),
        output_processor=TakeFirst()
    )

    house = scrapy.Field(
        input_processor=MapCompose(lambda s: s.strip()),
        output_processor=Compose(parse_house)
    )
    params_house = scrapy.Field(output_processor=Compose(parse_params))
    query = scrapy.Field(output_processor=TakeFirst())
    url = scrapy.Field(output_processor=TakeFirst())
