# -*- coding: utf-8 -*-
import scrapy
import sqlite3
import re
import locale
from scraping.items import Tf1Item
from datetime import datetime

class Tf1Spider(scrapy.Spider):
    name = "tf1"
    allowed_domains = ["tf1.fr"]
    start_urls = (
        'http://lci.tf1.fr/jt-20h/videos/video-integrale/',
        'http://lci.tf1.fr/jt-13h/videos/video-integrale/',
        'http://lci.tf1.fr/jt-we/videos/video-integrale/'
    )

    def __init__(self):
        try:
            locale.setlocale(locale.LC_ALL, 'fr_FR.UTF-8')
        except Exception:
            raise "French locale not supported"
        self.db = {}
        self.db['conn'] = sqlite3.connect('../transcript.db')
        self.db['cursor'] = self.db['conn'].cursor()

    def parse(self, response):
        urls_emissions = response.xpath('//a[@class="sz22 f1 c3"]/@href').extract()
        for url in urls_emissions:
            url = response.urljoin(url)
            yield scrapy.Request(url, callback=self.parse_emission)
        url_list_next = response.xpath('//li[contains(@class, "suivante")]/a/@href').extract_first()
        if url_list_next is not None:
            url_list_next = response.urljoin(url_list_next)
            yield scrapy.Request(url_list_next, callback=self.parse)
        
    def parse_emission(self, response):
        title = response.xpath('//h1/text()').extract_first()
        date = re.search(r'(\d+)(?:er)?( (?:janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre) 20\d{2})', title) # extract date from title
        try:
            date_clean = date.group(1)+date.group(2)
            date = datetime.strptime(date_clean, '%d %B %Y').date()
        except Exception:
            self.logger.error('Date not found in: '+title+'; URL: '+response.url)
            date = None
        urls_subject = response.xpath('//ul/li/div/h3[contains(@class, "title")]/a/@href').extract()
        for url in urls_subject:
            # don't save duplicates
            if not self.db['cursor'].execute("select * from subject where url = ?", (url,)).fetchone():
                request = scrapy.Request(url, callback=self.parse_subject)
                request.meta['date'] = date
                yield request

    def parse_subject(self, response):
        title = response.xpath('//h1/text()').extract_first()
        # Don't save the summary of the emission. Identified from the subject (examples delow gathered from a careful inspection of sujects with "topic=null")
        # ["Les titres du 20 heures du 18 juillet 2013", "Le 20 heures du 18 juillet 2013", "Les titres du journal de 20H du 18 juillet 2013", "Les titres du 20h de ce 18 juillet 2013", "Les titres du 11 avril 2016", "Les titres du journal de 20H du 1er février 2016",
        # "Les titres du journal de 20h jeudi 28 janvier 2016", "Retrouvez l'édition du 20 heures du mardi 15 mars 2016. ", "JT de 20h du 9 mars 2016", "Le journal de 20h du mardi 16 février 2016", "Les titres du 20h de ce mardi 19 avril", "Retrouvez l'édition du 20 heures du mardi 15 mars 2016. "]
        if re.search(r'(?:^(?:Les titres|Le|Retrouvez l(?:\'|’)édition|JT de) (?:du |de ce )?(?:journal de |JT de )?(?:20|13) ?(?:h|H|heures)|^Les titres) (?:du |de ce )?(?:lundi|mardi|mercredi|jeudi|vendredi|samedi|dimanche)? ?\d+(?:er)? (?:janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)(?: 20\d{2})?',title): # re.IGNORECASE
            return None
        item = Tf1Item()
        item['url'] = response.url
        item['title'] = title
        item['channel'] = 'tf1'
        item['topic'] = response.xpath('//div[@class="header"]/span[contains(@class, "topic")]/text()').extract_first()
        duration = response.xpath('//div[@class="header"]/span[@class="times"]/span[contains(@class, "duration")]/text()').extract_first()
        try:
            if duration is None:
                item['duration'] = None
            else:
                duration_parsed = re.search(r'(?:(\d+) ?(?:m|min|minutes?))?(?: (\d+) ?(?:s|sec|secondes?))?$', duration)
                if duration_parsed.group(1) is None:
                    minutes = 0
                else:
                    minutes = int(duration_parsed.group(1))
                if duration_parsed.group(2) is None:
                    secondes = 0
                else:
                    secondes = int(duration_parsed.group(2))
                item['duration'] = minutes*60 + secondes
        except Exception:
            self.logger.error('Duration unknown: '+str(duration)+'; URL: '+response.url)
        item['speaker'] = response.xpath('//div[@class="program-infos"]/div[contains(@class, "speaker")]/strong/text()').extract_first()
        m = re.search('/jt-(.*?)/', response.url)
        if m is not None:
            item['type'] = m.group(1)
        else:
            self.logger.error('Type not found in URL: '+response.url)
        item['date'] = response.meta['date']
        description = response.xpath('//div[@class="footer"]/p[contains(@class, "description")]/text()').extract_first()
        if description is None:
            # other description path, for example in: http://lci.tf1.fr/jt-20h/videos/2016/sur-tf1-daniel-auteuil-revient-sur-son-dernier-role-dans-au-nom-8723010.html
            description = response.xpath('//p[@itemprop="description"]/text()').extract_first()
        if description is not None:
            item['description'] = re.sub('ZOOM SUR', '', description)
        else:
            self.logger.error('Description is None: '+response.url)
        item['date_scraping'] = datetime.now()
        yield item