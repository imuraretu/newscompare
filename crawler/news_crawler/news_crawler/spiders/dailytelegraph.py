import scrapy
from news_crawler.items import NewsCrawlerItem
from scrapy.spiders import SitemapSpider
from dateutil.parser import parse



class DailytelegraphSpider(SitemapSpider):
    name = 'dailytelegraph'
    allowed_domains = ['dailytelegraph.com.au']
    sitemap_urls = ['https://www.dailytelegraph.com.au/news-sitemap.xml']
    custom_settings = {
        "USER_AGENT": "Mozilla/5.0 (Macintosh; Intel Mac OS X 12_6_2) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.3 Safari/605.1.15",
    }
    def parse(self, response):
        item = NewsCrawlerItem()
        item['url'] = response.url
        item['title'] = response.xpath('//title/text()').get()
        item['date'] = parse(response.css('meta[property="article:published_time"]::attr(content)').get()).isoformat()

        text_nodes = response.css('div#story-wrapper p ::text').getall()
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
