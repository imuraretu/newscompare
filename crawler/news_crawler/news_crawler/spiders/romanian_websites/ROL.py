import scrapy
from news_crawler.items import NewsCrawlerItem
from scrapy.spiders import SitemapSpider
from w3lib.html import remove_tags


class ROLSpider(SitemapSpider):
    name = 'ROL'
    allowed_domains = ['rol.ro']
    sitemap_urls = ['https://rol.ro/post-sitemap12.xml']

    def parse(self, response):
        item = NewsCrawlerItem()
        item['url'] = response.url
        item['title'] = response.xpath('//title/text()').get()
        item['date'] = response.css('meta[property="article:published_time"]::attr(content)').get()
        text_nodes = response.xpath(
            '//div[contains(@class, "entry-content")]//*[not(self::script)][not('
            'self::style)]/descendant-or-self::text()[normalize-space()]').get()

        # Join the text nodes into a single string
        text = text_nodes

        item['content'] = text
        yield item

    def parse_sitemap(self, response, **kwargs):
        urls = response.xpath('//ns:urlset/ns:url/ns:loc/text()', namespaces={'ns': 'http://www.sitemaps.org/schemas'
                                                                                    '/sitemap/0.9'}).getall()
        for url in urls:
            if url.endswith('.xml'):
                # If the URL is a sitemap, follow it recursively
                yield scrapy.Request(url, callback=self.parse_sitemap)
            else:
                # If the URL is a regular page, extract the data from it
                yield scrapy.Request(url, callback=self.parse)
