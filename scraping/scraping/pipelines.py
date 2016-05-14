# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html

import sqlite3

class ScrapingPipeline(object):
    def process_item(self, item, spider):
        return item

class SqliteItemExporter(object):

    def open_spider(self, spider):
        self.conn = sqlite3.connect('../transcript.db')
        self.cursor = self.conn.cursor()

    def process_item(self, item, spider):
        self.cursor.execute(
                """insert into subject (url, title, subtitle, channel, topic, duration, speaker, type, date, description, date_scraping)
                                        values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (item["url"], item["title"], item["subtitle"], item["channel"], item["topic"], item["duration"], item["speaker"], item["type"], item["date"], item["description"], item["date_scraping"]))
        self.conn.commit()
        return item

    def close_spider(self, spider):
        self.conn.close()
 