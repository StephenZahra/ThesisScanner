import re
import sys
import urllib.request

def begin_scan():
    """
    Begins the scanning process by getting the html for a given site
    """
    url = input()
    response = urllib.request.urlopen(url)
    html = response.read()

    return html


def get_page_urls(html):
    """
    This function gets all href data in <a> tags and verifies which of them are in the current domain and removes extra
    characters if so
    """
    link_collection = re.findall(r"(href[a-zA-Z0-9_=:.\"\-/'\\\\]*)+", str(html))

    required_links = []
    for link in link_collection:
        if (link.find(".test") != -1):#if (link.find("127.0.0.1:8000") != -1):
            modif_link = link.replace("href=\"", '')
            modif_link = modif_link.replace("\"", '')
            required_links.append(modif_link)

    return required_links


def check_nested_links(required_links):
    """
    Iterates through collected links and checks for new ones in them
    """

    nested_links = []
    for url in required_links:
        response = urllib.request.urlopen(url)
        html = response.read()
        link_collection = re.findall(r"(href[a-zA-Z0-9_=:.\"\-/'\\\\]*)+", str(html))

        for link in link_collection:
            if (link.find(".test") != -1):#if (link.find("127.0.0.1:8000") != -1):
                modif_link = link.replace("href=\"", '')
                modif_link = modif_link.replace("\"", '')
                nested_links.append(modif_link)
    return nested_links


def filter_links(all_urls):
    """
    This function checks for duplicates in the total collection of links in the website and removes them
    """

    output = ""
    all_urls = list(dict.fromkeys(all_urls))
    for url in all_urls:
        output += url + "|"
    return output


html = begin_scan()
urls = get_page_urls(html)

nested_links = check_nested_links(urls)
filtered_urls = filter_links(urls+nested_links)

print(filtered_urls)
sys.stdout.flush()
