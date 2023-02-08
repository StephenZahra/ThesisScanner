import re
import urllib.request
import requests


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

    all_names = []  # array containing necessary input tags which will be used later
    for elem in input_collection:  # loop through inputs, remove token & submit input
        if "_token" in elem:
            input_collection.remove(elem)
        elif "type=\\'submit\\'" in elem:
            input_collection.remove(elem)

    for inp in input_collection:  # filter through remaining valid inputs storing the names
        all_names = re.findall(r"(name=[\\\\'a-zA-Z\\\\']+)", inp)

    final_names = []
    for elem in all_names:  # Clean names
        temp_name = elem.replace("name=\\'", "")
        temp_name = temp_name.replace("\\'", "")
        final_names.append(temp_name)

    return final_names


def test_reflected(url, names):
    """
    Repeatedly sends POST requests to the page using previously acquired input tag names, returns dictionary
    with boolean values
    """

    session = requests.session()
    front = session.get(url)

    token = re.findall(r'<input type="hidden" name="_token" value="(.*)"', front.text)[0]
    cookies = session.cookies

    scan_result = {}  # dictionary to store results
    for name in names:
        data = {name: "{{7*7}}", "_token": token}
        req = requests.post(url, data=data, cookies=cookies)
        text = req.text

        if "49" in text:
            scan_result[name] = True
        else:
            scan_result[name] = False

    return scan_result


def filter_stored_posterior_urls(all_urls):
    """
    This function checks for duplicates in the total collection of links in the website and removes them
    """
    for x in all_urls:
        if(any(all_urls.count(x) > 1 for x in all_urls) == True):
            all_urls.remove(x)
    return all_urls


def test_stored_posterior(urls):
    """
    This function performs SSTI on a given target url for all forms, and checks each page to verify if any of it has
    executed
    """
    for url in urls:
        session = requests.session()
        front = session.get(url)

        token = re.findall(r'<input type="hidden" name="_token" value="(.*)"', front.text)[0]
        cookies = session.cookies

        inputs = locate_input_points(front)

        for name in inputs:
            data = {name: "{{7*7}}", "_token": token}
            requests.post(url, data=data, cookies=cookies)

        scan_result = {}
        for next_url in urls:
            html = get_html(next_url)

            if("49" in str(html)):
                scan_result[next_url] = True
            else:
                scan_result[next_url] = False

        return scan_result



# Begin the scanning process
html = begin_scan()

names = locate_input_points(html)
urls = get_page_urls(html)

#results = test_reflected(url, names)

#for result in results:  # print results
 #   print("Input name: " + result + " isVulnerable: " + str(results[result]))

nested_links = check_nested_links(urls)
filtered_urls = filter_stored_posterior_urls(urls+nested_links)
stored_pos_results = test_stored_posterior(filtered_urls)

for result in stored_pos_results:  # print results
   print("URL: " + result + " hasExecutedSSTI: " + str(stored_pos_results[result]))
