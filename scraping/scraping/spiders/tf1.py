# -*- coding: utf-8 -*-
import scrapy
import sqlite3
import re
import locale
from scraping.items import SubjectItem
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
            raise SystemError("fr_FR.UTF-8 locale not installed. Please install it on your system")
        self.db = {}
        self.db['conn'] = sqlite3.connect('../transcript.db', timeout = 30)
        self.db['conn'].execute("PRAGMA busy_timeout = 30000") # set PRAGMA busy_timeout to 30s to avoid the 'sqlite3.OperationalError: database is locked' error
        self.db['cursor'] = self.db['conn'].cursor()

    def parse(self, response):
        urls_emissions = response.xpath('//a[@class="sz22 f1 c3"]/@href').extract()
        for url in urls_emissions:
            # don't save duplicates
            if not self.db['cursor'].execute("select * from emission where url = ?", (url,)).fetchone():
                url = response.urljoin(url)
                yield scrapy.Request(url, callback=self.parse_emission)
        url_list_next = response.xpath('//li[contains(@class, "suivante")]/a/@href').extract_first()
        if url_list_next is not None:
            url_list_next = response.urljoin(url_list_next)
            yield scrapy.Request(url_list_next, callback=self.parse) # comment for debug
        
    def parse_emission(self, response):
        title = response.xpath('//h1/text()').extract_first()
        try:
            # date
            date = re.search(r'(\d+)(?:er|e)?( (?:janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre) 20\d{2})', title, re.IGNORECASE) # extract date from title
            date_clean = (date.group(1)+date.group(2)).lower()
            date = datetime.strptime(date_clean, '%d %B %Y').date()
            # type
            m = re.search('/jt-(.*?)/', response.url)
            if m is not None:
                type_emission = m.group(1)
            else:
                self.logger.error('Type not found in URL: '+response.url)
                type_emission = None
            if type_emission == "we": # we need to distinguish 13h and 20h
                m = re.search(r'(20|13) ?(?:heures|h)', title)
                if m is not None:
                    type_emission = 'we'+m.group(1)+'h'
                else:
                    type_emission = 'we'
        except Exception:
            self.logger.error('Date not found in: '+str(title)+'; URL: '+response.url)
            date = None
        # save emission
        content = {'url': response.url, 'title': title, 'date': date, 'channel': 'tf1', 'type': type_emission, 'speaker': None, 'date_scraping': datetime.now()}
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
        urls_subject = response.xpath('//ul/li/div/h3[contains(@class, "title")]/a/@href').extract()
        for url in urls_subject:
            # don't save duplicates
            if not self.db['cursor'].execute("select * from subject where url = ?", (url,)).fetchone():
                request = scrapy.Request(url, callback=self.parse_subject)
                request.meta['id_emission'] = id_emission
                yield request

    def parse_subject(self, response):
        title = response.xpath('//h1/text()').extract_first()
        # Don't save the summary of the emission. Identified from the subject (examples delow gathered from a careful inspection of sujects with "topic=null")
        # ["Les titres du 20 heures du 18 juillet 2013", "Le 20 heures du 18 juillet 2013", "Les titres du journal de 20H du 18 juillet 2013", "Les titres du 20h de ce 18 juillet 2013", "Les titres du 11 avril 2016", "Les titres du journal de 20H du 1er février 2016",
        # "Les titres du journal de 20h jeudi 28 janvier 2016", "Retrouvez l'édition du 20 heures du mardi 15 mars 2016. ", "JT de 20h du 9 mars 2016", "Le journal de 20h du mardi 16 février 2016", "Les titres du 20h de ce mardi 19 avril", "Retrouvez l'édition du 20 heures du mardi 15 mars 2016. "]
        try:
            if re.search(r'(?:^(?:Les titres|Le|Retrouvez l(?:\'|’)édition|JT de) (?:du |de ce )?(?:journal de |JT de )?(?:20|13) ?(?:h|H|heures)|^Les titres) (?:du |de ce )?(?:lundi|mardi|mercredi|jeudi|vendredi|samedi|dimanche)? ?\d+(?:er|e)? (?:janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)(?: 20\d{2})?',title): # re.IGNORECASE
                return None
        except Exception:
            self.logger.error('Item not saved. Impossible to search in: '+str(title)+'; URL: '+response.url)
            return None
        item = SubjectItem()
        item['url'] = response.url
        item['id_emission'] = response.meta['id_emission']
        item['title'] = title
        item['subtitle'] = None
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
        #item['speaker'] = None #response.xpath('//div[@class="program-infos"]/div[contains(@class, "speaker")]/strong/text()').extract_first() #TODO: remove or parse from some descripton?
        description = response.xpath('//div[@class="footer"]/p[contains(@class, "description")]/text()').extract_first()
        if description is None:
            # other description path, for example in: http://lci.tf1.fr/jt-20h/videos/2016/sur-tf1-daniel-auteuil-revient-sur-son-dernier-role-dans-au-nom-8723010.html
            description = response.xpath('//p[@itemprop="description"]/text()').extract_first()
        if description is not None:
            item['description'] = re.sub('ZOOM SUR', '', description)
        else:
            self.logger.error('Description is None: '+response.url)
            item['description'] = None
        item['date_scraping'] = datetime.now()
        yield item