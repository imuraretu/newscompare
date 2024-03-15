# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html
import json

# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
import couchdb
from scrapy.utils.project import get_project_settings


class CouchDBPipeline:
    def __init__(self):
        self.settings = get_project_settings()
        self.server = couchdb.Server(self.settings['COUCHDB_SERVER'])
        self.db = self.server[self.settings['COUCHDB_DATABASE']]

    def process_item(self, item, spider):
        # Convert item to a JSON-compatible format
        item_dict = dict(item)
        item_json = json.dumps(item_dict)

        query = {
            'selector': {
                'url': item['url']
            },
            'limit': 1
        }
        existing_docs = self.db.find(query)
        if len(list(existing_docs)) == 0:
            # Save item to CouchDB
            doc_id, doc_rev = self.db.save(json.loads(item_json))
        return item
