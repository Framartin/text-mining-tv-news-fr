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
        self.conn = sqlite3.connect('../transcript.db', timeout = 30)
        self.conn.execute("PRAGMA busy_timeout = 30000") # set PRAGMA busy_timeout to 30s to avoid the 'sqlite3.OperationalError: database is locked' error
        self.cursor = self.conn.cursor()

    def process_item(self, item, spider):
        try:
            self.cursor.execute(
                    """insert into subject (url, id_emission, title, subtitle, topic, duration, description, date_scraping)
                                            values (?, ?, ?, ?, ?, ?, ?, ?)""",
                        (item["url"], item['id_emission'], item["title"], item["subtitle"], item["topic"], item["duration"], item["description"], item["date_scraping"]))
            self.conn.commit()
        except Exception as e:
            raise e
        return item

    def close_spider(self, spider):
        self.conn.close()
 