import scrapy
from news_crawler.items import NewsCrawlerItem
from scrapy.spiders import SitemapSpider
from dateutil.parser import parse



class CBSSpider(SitemapSpider):
    name = 'cbs'
    allowed_domains = ['cbsnews.com']
    sitemap_urls = ['https://www.cbsnews.com/xml-sitemap/news.xml']

    def parse(self, response):
        item = NewsCrawlerItem()
        item['url'] = response.url
        item['title'] = response.xpath('//title/text()').get().replace('\n', ' ')
        item['date'] = parse(response.css('time[datetime]::attr(datetime)').get()).isoformat()

        text_nodes = response.css('article.content p ::text').getall()
        text_nodes = [text.replace('\xa0', ' ').replace('\n', ' ') for text in text_nodes]

        # Join the text nodes into a single string
        text = ''.join(text_nodes)

        item['content'] = text
        print(item)
        yield item

    def _parse_sitemap(self, response):
        # urls = response.xpath('//ns:urlset/ns:url/ns:loc/text()',
        #                       namespaces={'ns': 'http://www.google.com/schemas/sitemap-news/0.9'}).getall()
        
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
