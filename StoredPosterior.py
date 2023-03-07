import re
import urllib.request
import requests
import random
import string

# Generate a random string to uniquely identify every instance of Stored Posterior SSTI generated from this script
random_string = ''.join(random.choices(string.ascii_uppercase + string.ascii_lowercase, k=10))

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


def locate_input_points(html):
    """
    Finds all text input tags and returns their names
    """

    # find all input tags including token
    input_collection = re.findall(r"(<input [a-zA-Z0-9 _=\"'\\\\]*>)+", str(html))
    textarea_collection = re.findall(r"(<textarea [a-zA-Z0-9 _:;=\"'\\\\]*>)+", str(html))
    total_inputs = input_collection+textarea_collection

    all_names = []  # array containing necessary input tags which will be used later
    for elem in total_inputs:  # loop through inputs, remove token & submit input
        if "_token" in elem:
            total_inputs.remove(elem)
        elif "type='submit'" in elem:
            total_inputs.remove(elem)

    for inp in total_inputs:  # filter through remaining valid inputs storing the names
        all_names = re.findall(r"(name=[\\\\'a-zA-Z0-9\"'\\\\']+)", inp)

    final_names = []
    for elem in all_names:  # Clean names
        temp_name = elem.replace("name=", "")
        temp_name = temp_name.replace("'", "")
        final_names.append(temp_name)

    return final_names


def filter_links(all_urls):
    """
    This function checks for duplicates in the total collection of links in the website and removes them
    """

    all_urls = list(dict.fromkeys(all_urls))
    return all_urls


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


def test_stored_posterior(urls):
    """
    This function performs SSTI on a given target url for all forms, and checks each page to verify if any of it has
    executed
    """

    scan_result = []

    # Here we make post requests to send data only
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
                    # data = {name: url+" {{7*7}} "+random_string, "_token": token}
                    # requests.post(post_link, data=data, cookies=cookies)
                    data = {name: post_url + " {{7*7}} " + random_string, "_token": token}
                    requests.post(post_url, data=data, cookies=cookies)
        except:
            continue


    # Here we check all the urls to try and find the data we posted previously
    for next_url in urls:
        html_to_inspect = str(get_html(next_url))
        req_line = ''
        origin_url = ''

        try:

            # Check if the randomly generated string at the beginning is in the HTML
            if(random_string in html_to_inspect):
                for line in html_to_inspect.split("\n"):
                    if(random_string in line):
                        req_line = line  # Save line once found

                # Find all URLS on a page that are equal to req_line (the URL we are looking for)
                origin_url = re.findall(r"(http://[a-zA-Z0-9_:;=./\'\\\\]+)", req_line)
                if("49" in req_line):
                    scan_result.append("SSTI succeeded, Origin From: " + str(origin_url[0]) + " Executed on: " + str(next_url))
                else:
                    scan_result.append("SSTI tested from: " + str(origin_url[0]) + " was unsuccessful")
        except IndexError:
            scan_result.append("URL: " + next_url + " isVulnerable: Unable to test, no input points found")
            continue

    return scan_result



# Begin the scanning process
html = begin_scan()

urls = get_page_urls(html)

nested_links = check_nested_links(urls)
filtered_urls = filter_links(urls+nested_links)
stored_pos_results = test_stored_posterior(filtered_urls)

for result in stored_pos_results:  # print results
    print(result)
