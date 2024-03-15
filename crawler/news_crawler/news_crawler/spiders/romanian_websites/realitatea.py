import scrapy
from news_crawler.items import NewsCrawlerItem
from scrapy.spiders import SitemapSpider


class RealitateaSpider(SitemapSpider):
    name = 'realitatea'
    allowed_domains = ['realitatea.net']
    sitemap_urls = ['https://www.realitatea.net/share/news_sitemaps/sitemap.xml']

    def parse(self, response):
        item = NewsCrawlerItem()
        item['url'] = response.url
        item['title'] = response.xpath('//title/text()').get()
        item['date'] = response.css('meta[property="article:published_time"]::attr(content)').get()

        text_nodes = response.css('div.realitatea-article-content-box p::text').getall()
        text_nodes = [text.replace('\xa0', ' ').replace('\n', ' ') for text in text_nodes]
        # Join the text nodes into a single string
        text = ''.join(text_nodes)

        item['content'] = text
        yield item

    def parse_sitemap(self, response, **kwargs):
        urls = response.xpath('//ns:urlset/ns:url/ns:loc/text()', namespaces={'ns': 'http://www.google.com/schemas'
                                                                                    '/sitemap-news/0.9'}).getall()

        for url in urls:
            if url.endswith('.xml'):
                # If the URL is a sitemap, follow it recursively
                yield scrapy.Request(url, callback=self.parse_sitemap)
            else:
                # If the URL is a regular page, extract the data from it
                yield scrapy.Request(url, callback=self.parse)
