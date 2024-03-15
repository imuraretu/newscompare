import scrapy
from news_crawler.items import NewsCrawlerItem
from scrapy.spiders import SitemapSpider
from w3lib.html import remove_tags


class AlJazzeeraSpider(SitemapSpider):
    name = 'aljazzeera'
    allowed_domains = ['aljazeera.com']
    sitemap_urls = ['https://www.aljazeera.com/sitemaps/article-new/31-10-2023.xml']

    def parse(self, response):
        item = NewsCrawlerItem()
        item['url'] = response.url
        item['title'] = response.xpath('//title/text()').get()
        item['date'] = response.css(
            'meta[name="publishedDate"]::attr(content)').get()

        text_nodes = response.css('div.wysiwyg--all-content ::text').getall()
        text_nodes = [text.replace('\xa0', ' ').replace('\n', ' ') for text in text_nodes]

        # Join the text nodes into a single string
        text = ''.join(text_nodes)

        item['content'] = text
        print(item)
        yield item

    def _parse_sitemap(self, response):
        print("XxXxXxXxXxXxX")
        # urls = response.xpath('//ns:urlset/ns:url/ns:loc/text()',
        #                       namespaces={'ns': 'http://www.google.com/schemas/sitemap-news/0.9'}).getall()
        urls = response.xpath('//ns:url/ns:loc/text()', namespaces={'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9'}).extract()
        for url in urls:
            if url.endswith('.xml'):
                # If the URL is a sitemap, follow it recursively
                yield scrapy.Request(url, callback=self._parse_sitemap)
            else:
                # If the URL is a regular page, extract the data from it
                yield scrapy.Request(url, callback=self.parse)

