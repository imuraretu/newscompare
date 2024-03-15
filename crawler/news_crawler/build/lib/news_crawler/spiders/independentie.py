import scrapy
from news_crawler.items import NewsCrawlerItem
from scrapy.spiders import SitemapSpider
from dateutil.parser import parse
import json

class IndependentIeSpider(SitemapSpider):
    name = 'independentie'
    allowed_domains = ['independent.ie']
    sitemap_urls = ['https://www.independent.ie/sitemap/sitemap_googlenews.xml']
    custom_settings = {
        "USER_AGENT": "Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/27.0.1453.93 Safari/537.36",
    }
    
    def parse(self, response):
        item = NewsCrawlerItem()
        item['url'] = response.url
        item['title'] = response.xpath('//title/text()').get().replace('\n', ' ')
        json_string_date = response.css('script[type="application/ld+json"]::text').get()
        # Then, parse the JSON string
        date = json.loads(json_string_date)
        print(date)
        # Finally, get the 'datePublished' value from the parsed JSON
        date_published = date.get('datePublished')
        print(date_published)
        item['date'] = parse(date_published).isoformat()

        text_nodes = response.css('div[data-fragment-name="articleDetail"] p ::text').getall()
        text_nodes = [text.replace('\xa0', ' ').replace('\n', ' ') for text in text_nodes]

        # Join the text nodes into a single string
        text = ''.join(text_nodes)

        item['content'] = text
        print(item)
        #yield item

    def _parse_sitemap(self, response):
        ns = {
            'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9',
            'news': 'http://www.google.com/schemas/sitemap-news/0.9'
        }
        print("---------------------------")
        urls = response.xpath('//ns:url[news:news/news:publication/news:language/text()="EN"]/ns:loc/text()', namespaces=ns).extract()
        print(urls)
        print("---------------------------")
        for url in urls:
            if url.endswith('.xml'):
                # If the URL is a sitemap, follow it recursively
                yield scrapy.Request(url, callback=self._parse_sitemap)
            else:
                # If the URL is a regular page, extract the data from it
                yield scrapy.Request(url, callback=self.parse)
