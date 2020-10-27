import argparse
import concurrent.futures
import requests
from lxml.etree import fromstring
import re
import logging

# yibudak@altinkaya


def load_url(url, timeout):
    response = requests.get(url, timeout=timeout)
    return response.text


def get_urls(html, oldstyle=False):
    url_list = []
    xmlstring = re.sub(' xmlns="[^"]+"', '', html, count=1)
    encoded_sitemap = fromstring(xmlstring.encode('utf-8'))
    if "sitemapindex" in xmlstring:  # TODO: find a better way
        iter = encoded_sitemap.xpath('/sitemapindex/sitemap/loc')
    else:
        iter = encoded_sitemap.xpath('/urlset/url/loc')
        oldstyle=True
    for element in iter:
        url_list.append(element.text)
    if oldstyle == True:
        walk_around_urls(url_list)
    else:
        return url_list

def walk_around_urls(urls):
    count = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=15) as executor:
        future_to_url = {executor.submit(load_url, url, 15): url for url in
                         urls}
        for future in concurrent.futures.as_completed(future_to_url):
            try:
                url = future_to_url[future]
                count += 1
            except Exception as exc:
                logging.info('%r generated an exception: %s' % (url, exc))
    logging.info('[Walked around %s urls successfully]', count)
    exit()


def main(url):
    url_list = get_urls(load_url(url, 15))
    links = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        future_to_url = {executor.submit(load_url, url, 15): url for url in
                         url_list}
        for future in concurrent.futures.as_completed(future_to_url):
            try:
                url = future_to_url[future]
                links.extend(get_urls(future.result()))
            except Exception as exc:
                logging.info('%r generated an exception: %s' % (url, exc))
    walk_around_urls(links)


if __name__ == '__main__':
    logging.basicConfig(filename='status.log', level=logging.INFO,
                        format='%(asctime)s %(message)s')
    parser = argparse.ArgumentParser(
        description='Shorten URLs on the terminal')
    # TODO: add user agent option
    parser.add_argument('--url', default="google.com",
                        help="The URL to cache warming format='http://example.com/sitemap.xml'")
    args = vars(parser.parse_args())
    main(url=args['url'])
