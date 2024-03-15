import scrapy
from news_crawler.items import NewsCrawlerItem
from scrapy.spiders import SitemapSpider
from dateutil.parser import parse


class ReutersSpider(SitemapSpider):
    name = 'reuters'
    allowed_domains = ['reuters.com']
    sitemap_urls = ['https://www.reuters.com/arc/outboundfeeds/news-sitemap-index/?outputType=xml']

    def parse(self, response):
        item = NewsCrawlerItem()
        item['url'] = response.url
        item['title'] = response.xpath('//title/text()').get().replace('\n', ' ')
        item['date'] = parse(response.css('meta[name="article:published_time"]::attr(content)').get()).isoformat()


        text_nodes = response.css('article p ::text').getall()
        text_nodes = [text.replace('\xa0', ' ').replace('\n', ' ') for text in text_nodes]

        # Join the text nodes into a single string
        text = ''.join(text_nodes)

        item['content'] = text
        print(item)
        yield item

    def _parse_sitemap(self, response):
        content_type = response.headers.get('Content-Type')
        if b'xml' in content_type:
            if response.xpath('/*[local-name()="sitemapindex"]'):
                # Handle sitemapindex logic (e.g., follow links to other sitemaps)
                sitemaps = response.xpath('//*[local-name()="sitemap"]/*[local-name()="loc"]/text()').extract()
                for sitemap_url in sitemaps:
                    yield scrapy.Request(sitemap_url, callback=self._parse_sitemap)

            # Check if it contains URLs to crawl
            elif response.xpath('/*[local-name()="urlset"]'):
                ns = {
                    'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9',
                    'news': 'http://www.google.com/schemas/sitemap-news/0.9'
                }
                urls = response.xpath('//ns:url[news:news/news:publication/news:language/text()="en"]/ns:loc/text()', namespaces=ns).extract()
        

                print(urls)
                for url in urls:
                    yield scrapy.Request(url, callback=self.parse)
        else:
            yield scrapy.Request(url, callback=self.parse)

