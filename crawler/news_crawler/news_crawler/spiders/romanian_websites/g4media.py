import scrapy
from news_crawler.items import NewsCrawlerItem
from scrapy.spiders import SitemapSpider
from w3lib.html import remove_tags


class G4Media(SitemapSpider):
    name = 'G4Media'
    allowed_domains = ['g4media.ro']
    sitemap_urls = ['https://g4media.ro/sitemap-news.xml']

    def parse(self, response):
        item = NewsCrawlerItem()
        item['url'] = response.url
        item['title'] = response.xpath('//title/text()').get()
        item['date'] = response.css('time::attr(datetime)').get()

        text_nodes = response.css('div.post-content p ::text').getall()
        text_nodes = [text.replace('\xa0', ' ').replace('\n', ' ') for text in text_nodes]

        # Join the text nodes into a single string
        text = ''.join(text_nodes)

        item['content'] = text
        yield item

    def parse_sitemap(self, response, **kwargs):
        urls = response.xpath('//ns:urlset/ns:url/ns:loc/text()',
                              namespaces={'ns': 'http://www.google.com/schemas/sitemap-news/0.9'}).getall()

        for url in urls:
            if url.endswith('.xml'):
                # If the URL is a sitemap, follow it recursively
                yield scrapy.Request(url, callback=self.parse_sitemap)
            else:
                # If the URL is a regular page, extract the data from it
                yield scrapy.Request(url, callback=self.parse)
