# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class SubjectItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    title = scrapy.Field()
    subtitle = scrapy.Field()
    url = scrapy.Field()
    channel = scrapy.Field()
    topic = scrapy.Field()
    duration = scrapy.Field()
    speaker = scrapy.Field()
    type = scrapy.Field()
    date = scrapy.Field()
    description = scrapy.Field()
    date_scraping = scrapy.Field()
