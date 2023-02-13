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

    all_names = []  # array containing necessary input tags which will be used later
    for elem in input_collection:  # loop through inputs, remove token & submit input
        if "_token" in elem:
            input_collection.remove(elem)
        elif "type='submit'" in elem:
            input_collection.remove(elem)

    for inp in input_collection:  # filter through remaining valid inputs storing the names
        all_names = re.findall(r"(name=[\\\\'a-zA-Z0-9\"'\\\\']+)", str(inp))

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


def test_reflected(urls):
    """
    Repeatedly sends POST requests to the page using previously acquired input tag names, returns dictionary
    with boolean values
    """

    for url in urls:
        session = requests.session()
        front = session.get(url)

        token = re.findall(r'<input type="hidden" name="_token" value="(.*)"', front.text)[0]
        cookies = session.cookies

        inputs = locate_input_points(front.text)

        scan_result = {}  # dictionary to store results
        for name in inputs:
            data = {name: "{{7*7}}", "_token": token}
            req = requests.post(url, data=data, cookies=cookies)
            text = req.text

            if "49" in text:
                scan_result[name] = True
            else:
                scan_result[name] = False

        return scan_result


# Begin the scanning process
html = begin_scan()

urls = get_page_urls(html)

nested_links = check_nested_links(urls)
filtered_urls = filter_links(urls+nested_links)
results = test_reflected(filtered_urls)

for result in results:  # print results
    print("Input name: " + result + " isVulnerable: " + str(results[result]))
