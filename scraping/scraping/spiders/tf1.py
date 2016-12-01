# -*- coding: utf-8 -*-
import scrapy
import sqlite3
import re
import locale
from scraping.items import SubjectItem
from datetime import datetime

class Tf1Spider(scrapy.Spider):
    name = "tf1"
    allowed_domains = ["lci.fr"]
    start_urls = (
        'http://www.lci.fr/emission/le-20h/',
        'http://www.lci.fr/emission/jt-13h/',
        'http://www.lci.fr/emission/jt-we/', # WE 20h
        'http://www.lci.fr/emission/jt-we-13h/'
    )

    def __init__(self):
        # try:
        #     locale.setlocale(locale.LC_ALL, 'fr_FR.UTF-8')
        # except Exception:
        #     raise SystemError("fr_FR.UTF-8 locale not installed. Please install it on your system")
        self.db = {}
        self.db['conn'] = sqlite3.connect('../transcript.db', timeout = 30)
        self.db['conn'].execute("PRAGMA busy_timeout = 30000") # set PRAGMA busy_timeout to 30s to avoid the 'sqlite3.OperationalError: database is locked' error
        self.db['cursor'] = self.db['conn'].cursor()

    def parse(self, response):
        urls_emissions = response.xpath('//ul[@class="topic-chronology-milestone-component"]/li/a/@href').extract()
        for url in urls_emissions:
            if url not in ['', None]: # skip empty URL 
                # don't save duplicates
                if not self.db['cursor'].execute("select * from emission where url = ?", (url,)).fetchone():
                    url = response.urljoin(url)
                    yield scrapy.Request(url, callback=self.parse_subject)
        url_list_next = response.xpath('//a[@class="pagination-link next"]/@href').extract_first()
        if url_list_next is not None:
            url_list_next = response.urljoin(url_list_next)
            yield scrapy.Request(url_list_next, callback=self.parse) # comment for debug
        
    # def parse_emission(self, response):
    #     title = response.xpath('//h1/text()').extract_first()
    #     # 
    #     # date
    #     try:
    #         date = re.search(r'(\d+)(?:er|e)?( (?:janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre) 20\d{2})', title, re.IGNORECASE) # extract date from title
    #         date_clean = (date.group(1)+date.group(2)).lower()
    #         date = datetime.strptime(date_clean, '%d %B %Y').date()
    #     except Exception:
    #         self.logger.error('Date not found in: '+str(title)+'; URL: '+response.url)
    #         date = None
    #     # type
    #     m = re.search('/jt-(.*?)/', response.url)
    #     if m is not None:
    #         type_emission = m.group(1)
    #     else:
    #         self.logger.error('Type not found in URL: '+response.url)
    #         type_emission = None
    #     if type_emission == "we": # we need to distinguish 13h and 20h
    #         m = re.search(r'(20|13) ?(?:heures|h)', title)
    #         if m is not None:
    #             type_emission = 'we'+m.group(1)+'h'
    #         else:
    #             type_emission = 'we'
    #     # speaker
    #     # try to extract speaker from description. Not specified each time.
    #     re_speaker = r'présentée? par (.+?)[. ]*$'
    #     speaker = response.xpath('//div[@class="footer"]/p[contains(@class, "description")]/text()').re_first(re_speaker)
    #     if speaker is None:
    #         speaker = response.xpath('//p[@itemprop="description"]/text()').re_first(re_speaker)
    #     # save emission
    #     content = {'url': response.url, 'title': title, 'date': date, 'channel': 'tf1', 'type': type_emission, 'speaker': speaker, 'date_scraping': datetime.now()}
    #     c = self.db['conn'].cursor()
    #     try:
    #         c.execute(
    #                     """insert into emission (url, title, channel, speaker, type, date, date_scraping)
    #                                             values (?, ?, ?, ?, ?, ?, ?)""",
    #                         (content['url'], content['title'], content['channel'], content['speaker'], content['type'], content['date'], content['date_scraping']))
    #     except sqlite3.IntegrityError as e:
    #         self.logger.error('sqlite3 error on emission: ('+str(content['channel'])+', '+str(content['type'])+', '+str(content['date'])+') at url: '+ str(response.url))
    #         raise e
    #     id_emission = c.lastrowid
    #     self.db['conn'].commit()
    #     if id_emission is None:
    #         raise ValueError("id of the emission missing in the DB")
    #     # extract subjects
    #     urls_subject = response.xpath('//ul/li/div/h3[contains(@class, "title")]/a/@href').extract()
    #     for url in urls_subject:
    #         # don't save duplicates
    #         if not self.db['cursor'].execute("select * from subject where url = ?", (url,)).fetchone():
    #             request = scrapy.Request(url, callback=self.parse_subject)
    #             request.meta['id_emission'] = id_emission
    #             yield request

    def parse_subject(self, response):
        title = response.xpath('//h1/text()').extract_first()
        title = re.sub(r'^JT ?(?:[0-9]{2}H|WE) - |^VIDÉO - ', '', title)

        # Don't save the summary of the emission.
        # TODO: Identified from the subject (examples delow gathered from a careful inspection of sujects with "topic=null" or "topic=replay")
        # New format: "Les titres du JT", "JT 20H - Les titres du 30 novembre 2016.", "Retrouvez les titres du JT de 20h du mercredi 30 novembre 2016."
        # ["Les titres du 20 heures du 18 juillet 2013", "Le 20 heures du 18 juillet 2013", "Les titres du journal de 20H du 18 juillet 2013", "Les titres du 20h de ce 18 juillet 2013", "Les titres du 11 avril 2016", "Les titres du journal de 20H du 1er février 2016",
        # "Les titres du journal de 20h jeudi 28 janvier 2016", "Retrouvez l'édition du 20 heures du mardi 15 mars 2016. ", "JT de 20h du 9 mars 2016", "Le journal de 20h du mardi 16 février 2016", "Les titres du 20h de ce mardi 19 avril", "Retrouvez l'édition du 20 heures du mardi 15 mars 2016. "]
        try:
            if re.search(r'Les titres du JT|Les titres du [0-3][0-9]|Retrouvez l(?:\'|’)édition du [0-9]+ ?h|Retrouvez les titres du JT', title, re.IGNORECASE):
                self.logger.info('Item not saved. Summary page: '+str(title)+'; URL: '+response.url)
                return None
        except Exception:
            self.logger.error('Item not saved. Impossible to search in: '+str(title)+'; URL: '+response.url)
            return None
        # try:
        #     if re.search(r'(?:^(?:Les titres|Le|Retrouvez l(?:\'|’)édition|JT de) (?:du |de ce )?(?:journal de |JT de )?(?:20|13) ?(?:h|H|heures)|^Les titres) (?:du |de ce )?(?:lundi|mardi|mercredi|jeudi|vendredi|samedi|dimanche)? ?\d+(?:er|e)? (?:janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)(?: 20\d{2})?',title): # re.IGNORECASE
        #         return None
        # except Exception:
        #     self.logger.error('Item not saved. Impossible to search in: '+str(title)+'; URL: '+response.url)
        #     return None

        xpath_sub_description = '//div[contains(@class, "article-block-paragraph")]/p/text()' # extract sub_description 

        # date
        date = response.xpath(xpath_sub_description).re_first(r'([0-3][0-9]/[01][0-9]/201[0-9])')
        if date is not None:
            date = datetime.strptime(date, '%d/%m/%Y').date()
        else:
            date = response.xpath('//time[contains(@class, "article-date-credit-block-date")]/@datetime').re_first(r'^(201[0-9]-[01][0-9]-[0-3][0-9])T')
            if date is not None:
                date = datetime.strptime(date, '%Y-%m-%d').date()
            else:
                self.logger.error('Item not saved. Date not found in URL: '+response.url)
                return None

        # type
        type_emission = response.xpath('//h2[@class="topic-title-component-title"]/a/text()').extract_first()
        if isinstance(type_emission, str):
            type_emission = type_emission.lower()
            type_emission = re.sub(r'^le |^jt ', '', type_emission)
        if type_emission not in ['13h', '20h', 'we 13h', 'we 20h']:
            # some subject don't have the type in this h2, example: http://www.lci.fr/societe/jt-13h-demantelement-de-calais-accueil-chaleureux-a-pessat-villeneuve-en-auvergne-2009946.html
            # extract from tags
            tags = response.xpath('//ul[contains(@class,"tag-list-block-list")]/li/a/text()').extract()
            tags = [x.lower() for x in tags if isinstance(x, str)] # convert to lower case
            if 'le 13h' in tags:
                type_emission = '13h'
            elif 'le 20h' in tags:
                type_emission = '20h'
            elif 'jt we 13h' in tags:
                type_emission = 'we 13h'
            elif 'jt we 20h' in tags:
                type_emission = 'we 20h'
            else:
                # TODO: extract from description or subdescription?
                self.logger.error('Item not saved. Type emission not found in URL: '+response.url)
                return None

        # id_emission
        # check if emission exists
        # TODO: save URL?
        content = {'url': response.url, 'title': None, 'date': date, 'channel': 'tf1', 'type': type_emission, 'speaker': None, 'date_scraping': datetime.now()}
        c = self.db['conn'].cursor()
        id_emission = c.execute("select id from emission where date = ? and channel = ? and type = ?",
            (content['date'], content['channel'], content['type'])).fetchone()
        if id_emission is None: # emission not saved in DB
            # speaker
            content['speaker'] = response.xpath(xpath_sub_description).re_first(r'présentée? par (.*) sur TF1')
            if content['speaker'] is None:
                self.logger.info('Speaker not found in URL: '+response.url)

            # save emission
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
        else:
            id_emission = id_emission[0]
            if c.execute("select speaker from emission where id = ?", (id_emission,)).fetchone() == (None,):
                # speaker can be None, then we try to store it from another subject of the same emission
                speaker = response.xpath(xpath_sub_description).re_first(r'présentée? par (.*) sur TF1')
                if speaker is not None:
                    self.logger.info('Import speaker again from URL: '+response.url)
                    try:
                        c.execute("update emission set speaker = ? where id = ?", (speaker, id_emission))
                        self.db['conn'].commit()
                    except Exception as e:
                        raise e

        if id_emission is None:
            raise ValueError("id of the emission missing in the DB")

        # topic
        m = re.search(r'^http://www\.lci\.fr(?:\:[0-9]+)/(.*?)/', response.url)
        if m is not None:
            topic = m.group(1)
        else:
            topic = None
            self.logger.error('Topic not found in URL: '+response.url)

        item = SubjectItem()
        item['url'] = response.url
        item['id_emission'] = id_emission
        item['title'] = title
        item['subtitle'] = None
        item['topic'] = topic
        item['duration'] = None
        # try:
        #     if duration is None:
        #         item['duration'] = None
        #     else:
        #         duration_parsed = re.search(r'(?:(\d+) ?(?:m|min|minutes?))?(?: (\d+) ?(?:s|sec|secondes?))?$', duration)
        #         if duration_parsed.group(1) is None:
        #             minutes = 0
        #         else:
        #             minutes = int(duration_parsed.group(1))
        #         if duration_parsed.group(2) is None:
        #             secondes = 0
        #         else:
        #             secondes = int(duration_parsed.group(2))
        #         item['duration'] = minutes*60 + secondes
        # except Exception:
        #     self.logger.error('Duration unknown: '+str(duration)+'; URL: '+response.url)

        description = response.xpath('//div[contains(@class, "article-chapo-block")]/div/span/text()').extract_first()
        if description is None:
            # other description path, for example in: http://lci.tf1.fr/jt-20h/videos/2016/sur-tf1-daniel-auteuil-revient-sur-son-dernier-role-dans-au-nom-8723010.html
            description = response.xpath(xpath_sub_description).extract_first() # description in sub description
            # check that we don't save the generic description of the JT
            if re.search(r'^Ce reportage est issu du journal télévisé', description):
                description = None
        if description is not None:
            description = re.sub(r'^JT (?:[0-9]{2}H|WE) - ', '', description)
            description = re.sub('ZOOM SUR', '', description)
        else:
            self.logger.error('Description is None: '+response.url)
        item['description'] = description
        item['date_scraping'] = datetime.now()
        yield item
