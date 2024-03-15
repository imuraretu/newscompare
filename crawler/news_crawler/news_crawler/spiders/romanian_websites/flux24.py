from datetime import date

import scrapy
from news_crawler.items import NewsCrawlerItem
from scrapy import Selector
from scrapy.spiders import SitemapSpider
from w3lib.html import remove_tags


class Flux24Spider(SitemapSpider):
    name = 'flux24'
    allowed_domains = ['flux24.ro']
    sitemap_urls = ['https://flux24.ro/sitemap_index.xml']

    def parse(self, response):
        item = NewsCrawlerItem()
        item['url'] = response.url
        item['title'] = response.xpath('//title/text()').get()
        item['date'] = response.css('time::attr(datetime)').get()

        text_nodes = response.css('div.data-app-meta-article p ::text').getall()
        text_nodes = [text.replace('\xa0', ' ').replace('\n', ' ') for text in text_nodes]

        # Join the text nodes into a single string
        text = ''.join(text_nodes)

        item['content'] = text
        print(item)
        pass
        # yield item

    def parse_sitemap(self, response, **kwargs):
        # urls = response.xpath('//ns:urlset/ns:url/ns:loc/text()', namespaces={'ns': 'http://www.google.com/schemas/sitemap-news/0.9'}).getall()
        urls = []
        for sitemap in Selector(response).xpath('//sitemap'):
            lastmod = sitemap.xpath('lastmod/text()').get()
            if lastmod and date.fromisoformat(lastmod) < date.today():
                urls.append(sitemap.xpath('loc/text()').get())
        print("--------------")
        print(urls)
        print("--------------")

        for url in urls:
            if url.endswith('.xml'):
                # If the URL is a sitemap, follow it recursively
                yield scrapy.Request(url, callback=self.parse_sitemap)
            else:
                # If the URL is a regular page, extract the data from it
                yield scrapy.Request(url, callback=self.parse)
