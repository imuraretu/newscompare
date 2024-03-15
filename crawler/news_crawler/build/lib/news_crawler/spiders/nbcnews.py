import scrapy
from news_crawler.items import NewsCrawlerItem
from scrapy.spiders import SitemapSpider
from dateutil.parser import parse
import json


class NBCNewsSpider(SitemapSpider):
    name = 'nbcnews'
    allowed_domains = ['nbcnews.com']
    sitemap_urls = ['https://nbcnews.com/sitemap/nbcnews/sitemap-news']

    def parse(self, response):
        item = NewsCrawlerItem()
        item['url'] = response.url
        item['title'] = response.xpath('//title/text()').get()
        json_string_date = response.css('script[type="application/ld+json"]::text').get()
        # Then, parse the JSON string
        date = json.loads(json_string_date)

        # Finally, get the 'datePublished' value from the parsed JSON
        date_published = date.get('datePublished')
        item['date'] = parse(date_published).isoformat()

        text_nodes = response.css('div.article-body__content p ::text').getall()
        text_nodes = [text.replace('\xa0', ' ').replace('\n', ' ') for text in text_nodes]

        # Join the text nodes into a single string
        text = ''.join(text_nodes)

        item['content'] = text
        print(item)
        yield item

    def _parse_sitemap(self, response):
        # urls = response.xpath('//ns:urlset/ns:url/ns:loc/text()',
        #                       namespaces={'ns': 'http://www.google.com/schemas/sitemap-news/0.9'}).getall()
        print("---------------------------------")
        ns = {
            'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9',
            'news': 'http://www.google.com/schemas/sitemap-news/0.9'
        }
        urls = response.xpath('//ns:url[news:news/news:publication/news:language/text()="en"]/ns:loc/text()', namespaces=ns).extract()
        print(urls)
        for url in urls:
            if url.endswith('.xml'):
                # If the URL is a sitemap, follow it recursively
                yield scrapy.Request(url, callback=self._parse_sitemap)
            else:
                # If the URL is a regular page, extract the data from it
                yield scrapy.Request(url, callback=self.parse)
