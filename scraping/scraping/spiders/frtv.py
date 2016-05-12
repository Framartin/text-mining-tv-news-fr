# -*- coding: utf-8 -*-
import scrapy
import sqlite3
import re
from scraping.items import Tf1Item
from datetime import datetime

class Tf1Spider(scrapy.Spider):
    name = "frtv"
    allowed_domains = ["francetvinfo.fr"]
    start_urls = (
        'http://www.francetvinfo.fr/replay-jt/france-2/8-heures/',
        'http://www.francetvinfo.fr/replay-jt/france-2/13-heures/',
        'http://www.francetvinfo.fr/replay-jt/france-2/20-heures/',
        'http://www.francetvinfo.fr/replay-jt/france-3/12-13/',
        'http://www.francetvinfo.fr/replay-jt/france-3/19-20/',
        'http://www.francetvinfo.fr/replay-jt/france-3/soir-3/'
    )

    def __init__(self):
        self.db = {}
        self.db['conn'] = sqlite3.connect('../transcript.db')
        self.db['cursor'] = self.db['conn'].cursor()

    def parse(self, response):
        urls_emissions = response.xpath('//div[@id="middleColumn"]/section/a[@class="img"]/@href').extract() # first emission
        other_urls = response.xpath('//div[@id="middleColumn"]/article/a[@class="img"]/@href').extract() # other emissions
        if other_urls is not None:
            urls_emissions = urls_emissions + other_urls
        for url in urls_emissions:
            url = response.urljoin(url)
            yield scrapy.Request(url, callback=self.parse_emission)
        url_list_next = response.xpath('//a[@class="page next"]/@href').extract_first()
        if url_list_next is not None:
            url_list_next = response.urljoin(url_list_next)
            #yield scrapy.Request(url_list_next, callback=self.parse)
        
    def parse_emission(self, response):
        date_row = response.xpath('//p[contains(@class, "schedule")]/span/text()').re_first('(\d+/\d+/20\d{2})')
        try:
            date = datetime.strptime(date_row, '%d/%m/%Y').date()
        except Exception:
            self.logger.error('Date not found in: '+str(date_row)+'; URL: '+response.url)
            date = None
        speaker = response.xpath('//p[contains(@class, "presenter")]/span[contains(@class, "by")]/text()').extract_first()
        #type
        m = re.search(r'/(\d+)-heures/|/12-(13)|19-(20)|(soir)-3/', response.url)
        if m is not None:
            if m.group(1) is not None:
                type_jt = m.group(1)+'h'
            elif m.group(2) is not None:
                type_jt = m.group(2)+'h'
            elif m.group(3) is not None:
                type_jt = m.group(3)+'h'
            else:
                type_jt = m.group(4)
        else:
            self.logger.error('Type not found in URL: '+response.url)
            type_jt = None
        #channel
        m = re.search(r'/france-(\d)/', response.url)
        if m is not None:
            channel = 'fr'+m.group(1)
        else:
            self.logger.error('Channel not found in URL: '+response.url)
            channel = None
        urls_subject = response.xpath('//ul[contains(@class, "subjects-list")]/li/a[contains(@class, "title")]/@href').extract()
        for url in urls_subject:
            url = response.urljoin(url)
            # don't save duplicates
            if not self.db['cursor'].execute("select * from subject where url = ?", (url,)).fetchone():
                request = scrapy.Request(url, callback=self.parse_subject)
                request.meta['date'] = date
                request.meta['speaker'] = speaker
                request.meta['type'] = type_jt
                request.meta['channel'] = channel
                yield request

    def parse_subject(self, response):
        #channel
        m = re.search(r'^http://www\.francetvinfo\.fr/(.*?)/', response.url)
        if m is not None:
            topic = m.group(1)
        else:
            self.logger.error('Topic not found in URL: '+response.url)
            topic = None
        item = Tf1Item()
        item['url'] = response.url
        item['title'] = response.xpath('//h1/text()').extract_first()
        item['topic'] = topic
        item['duration'] = None
        item['date'] = response.meta['date']
        item['speaker'] = response.meta['speaker']
        item['type'] = response.meta['type']
        item['channel'] = response.meta['channel']
        description = response.xpath('//div[contains(@itemprop, "articleBody")]/p[descendant-or-self::text()]').extract()
        if description is not None:
            description = ''.join(description) # join the element of text separated by h2 titles
            item['description'] = re.sub('<.*?>', '', description) # remove HTML elements
        else:
            self.logger.error('Description error on: '+response.url)
            item['description'] = None
        item['date_scraping'] = datetime.now()
        yield item