import re
import sys
import urllib.request
from urllib.parse import urlparse

def begin_scan(url):
    """
    Begins the scanning process by getting the html for a given site
    """

    response = urllib.request.urlopen(url)
    html = response.read()

    return html


def get_page_urls(html):
    """
    This function gets all href data in <a> tags and verifies which of them are in the current domain and removes extra
    characters if so
    """

    a_tags = re.findall(r'href="([^"]*)"', str(html))
    vue_urls = re.findall(r'to="([^"]*)"', str(html))
    all_tags = a_tags + vue_urls

    required_links = []
    for link in all_tags:
        required_links.append(link)
    return required_links



def check_nested_links(required_links, hostname):
    """
    Iterates through collected links and checks for new ones in them
    """

    nested_links = []
    for url in required_links:
        try:
            joined_url = "http://"+hostname+url
            response = urllib.request.urlopen(joined_url)
            html = response.read()

            a_tags = re.findall(r'href="([^"]*)"', str(html))
            vue_urls = re.findall(r'to="([^"]*)"', str(html))
            all_tags = a_tags + vue_urls

            for link in all_tags:
                nested_links.append(link)
        except Exception:
            pass

    return nested_links


def filter_links(all_urls, hostname):
    """
    This function checks for duplicates in the total collection of links in the website and removes them
    """

    output = ""
    all_urls = list(dict.fromkeys(all_urls))
    temp_storage = []
    for url in all_urls:
        if(url != "#" or str(urlparse(url).hostname) == hostname):  # check that the url is not a # and
            temp_storage.append(url)

    for last_urls in temp_storage:  # This helps us remove unneeded urls and stay in session
        if(str(urlparse(last_urls).hostname) == hostname or str(urlparse(last_urls).hostname) == "None"):
            output += last_urls + "|"

    return output


url = input()
html = begin_scan(url)
urls = get_page_urls(html)

nested_links = check_nested_links(urls, str(urlparse(url).hostname))
filtered_urls = filter_links(urls+nested_links, str(urlparse(url).hostname))

print(filtered_urls)
sys.stdout.flush()
