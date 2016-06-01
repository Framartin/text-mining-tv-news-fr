# -*- coding: utf-8 -*-
import scrapy
import sqlite3
import re
from scraping.items import SubjectItem
from datetime import datetime

class FrTvSpider(scrapy.Spider):
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
        self.db['conn'] = sqlite3.connect('../transcript.db', timeout = 30)
        self.db['conn'].execute("PRAGMA busy_timeout = 30000") # set PRAGMA busy_timeout to 30s to avoid the 'sqlite3.OperationalError: database is locked' error
        self.db['cursor'] = self.db['conn'].cursor()

    def parse(self, response):
        urls_emissions = response.xpath('//div[@id="middleColumn"]/section/a[@class="img"]/@href').extract() # first emission
        other_urls = response.xpath('//div[@id="middleColumn"]/div/article/a[@class="img"]/@href').extract() # other emissions
        if other_urls is not None:
            urls_emissions = urls_emissions + other_urls
        for url in urls_emissions:
            url = response.urljoin(url)
            # don't save duplicates
            if not self.db['cursor'].execute("select * from emission where url = ?", (url,)).fetchone():
                yield scrapy.Request(url, callback=self.parse_emission)
        url_list_next = response.xpath('//a[@class="page next"]/@href').extract_first()
        if url_list_next is not None:
            url_list_next = response.urljoin(url_list_next)
            yield scrapy.Request(url_list_next, callback=self.parse) # comment for debug
        
    def parse_emission(self, response):
        title = response.xpath('//h1/text()').extract_first()
        date_row = response.xpath('//p[contains(@class, "schedule")]/span/text()').re_first('(\d+/\d+/20\d{2})')
        try:
            date = datetime.strptime(date_row, '%d/%m/%Y').date()
        except Exception:
            self.logger.error('Date not found in: '+str(date_row)+'; URL: '+response.url)
            date = None
        speaker = response.xpath('//p[contains(@class, "presenter")]/span[contains(@class, "by")]/text()').extract_first()
        #type
        m = re.search(r'/(\d+)-heures/|/12-(13)/|/19-(20)/|/(soir)-3/', response.url)
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
        # save emission
        content = {'url': response.url, 'title': title, 'date': date, 'channel': channel, 'type': type_jt, 'speaker': speaker, 'date_scraping': datetime.now()}
        c = self.db['conn'].cursor()
        try:
            c.execute(
                        """insert into emission (url, title, channel, speaker, type, date, date_scraping)
                                                values (?, ?, ?, ?, ?, ?, ?)""",
                            (content['url'], content['title'], content['channel'], content['speaker'], content['type'], content['date'], content['date_scraping']))
        except sqlite3.IntegrityError as e:
            self.logger.error('sqlite3 error on emission: ('+str(content['channel'])+', '+str(content['type'])+', '+str(content['date'])+') at url: '+ str(response.url))
            raise e
        id_emission = c.lastrowid
        self.db['conn'].commit()
        if id_emission is None:
            raise ValueError("id of the emission missing in the DB")
        # extract subjects
        urls_subject = response.xpath('//ul[contains(@class, "subjects-list")]/li/a[contains(@class, "title")]/@href').extract()
        for url in urls_subject:
            url = response.urljoin(url)
            # don't save duplicates
            if not self.db['cursor'].execute("select * from subject where url = ?", (url,)).fetchone():
                request = scrapy.Request(url, callback=self.parse_subject)
                request.meta['id_emission'] = id_emission
                yield request

    def parse_subject(self, response):
        #channel
        m = re.search(r'^http://www\.francetvinfo\.fr/(.*?)/', response.url)
        if m is not None:
            topic = m.group(1)
        else:
            self.logger.error('Topic not found in URL: '+response.url)
            topic = None
        item = SubjectItem()
        item['url'] = response.url
        item['id_emission'] = response.meta['id_emission']
        item['title'] = response.xpath('//h1/text()').extract_first()
        item['subtitle'] = response.xpath('//h2/text()').extract_first()
        item['topic'] = topic
        item['duration'] = None
        description = response.xpath('//div[contains(@itemprop, "articleBody")]/p[descendant-or-self::text()]').extract()
        h2_title = response.xpath('//div[contains(@itemprop, "articleBody")]/h2/text()').extract() # TODO
        if description is not None:
            description = ''.join(description) # join the element of text separated by h2 titles
            item['description'] = re.sub('<.*?>', ' ', description) # remove HTML elements
        else:
            self.logger.error('Description error on: '+response.url)
            item['description'] = None
        if h2_title is not None: # merge H2 title with description
            h2_title = ''.join(h2_title)
            description = description+' '+h2_title
        item['date_scraping'] = datetime.now()
        yield item