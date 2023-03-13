import re
import urllib.request
import requests
import numpy


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
        all_names += re.findall(r"(name=[\\\\'a-zA-Z0-9\"'\\\\']+)", str(inp))

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


def post_url(html):
    """
    This function finds all form action links in a page, and returns only the required form action links
    """
    post_link = re.findall(r"action=([a-zA-Z0-9 _:;=./\"'\\\\]+)", html)[0]
    #formatted_links = []

    #for link in post_links:
    formatted_link = re.findall(r"(http://[a-zA-Z0-9_:;=./\\\\]+)", post_link)[0]
    #formatted_links.append(formatted_link[0])

    return formatted_link


def get_token(html):
    """
    This function grabs the token for each given form
    """
    token = re.findall(r'<input type="hidden" name="_token" value="(.*)"', html)[0]
    return token


def get_forms(html):
    """
    This function takes html and finds all forms and their encapsulated html. It will extract action links and their inputs
    and pair them together.
    """
    form_groups = re.findall(r"(action=[a-zA-Z0-9 _:;=./\"\-<>\s'\\\\]+</form>)+", html)

    link_groups = {}
    for group in form_groups:
        action_link = post_url(group)
        input_links = locate_input_points(group)
        link_groups[action_link] = input_links

    return link_groups


def test_reflected(urls):
    """
    Repeatedly sends POST requests to the page using previously acquired input tag names, returns array with
    test results
    """

    scan_result = []
    for url in urls:
        session = requests.session()
        front = session.get(url)

        try:
            token = get_token(front.text)
            cookies = session.cookies

            post_data = {}
            groups = get_forms(front.text)

            for group in groups:
                # Get the inputs for each form group iteratively
                inputs = groups[group]
                for inp in inputs:  # Give each input a value and add to dictionary
                    post_data[inp] = "{{7*7}}"

                post_data["_token"] = token  # Add token last
                req = requests.post(group, data=post_data, cookies=cookies)

                # Check that an error is not thrown due to GET route, skip rest of code execution
                if ("methodNotAllowed" in req.text):
                    scan_result.append("URL: " + url + " isVulnerable: Unable to test, only GET is supported")
                    continue

                if "49" in req.text:
                    scan_result.append("URL: " + url + " Form link: " + group + " isVulnerable: True")
                else:
                    scan_result.append("URL: " + url + " Form link: " + group + " isVulnerable: False")
        except IndexError:  # A page had no inputs we could find
            scan_result.append("URL: " + url + " isVulnerable: Unable to test, no input points found")

    return scan_result


# Begin the scanning process
html = begin_scan()

urls = get_page_urls(html)

nested_links = check_nested_links(urls)
filtered_urls = filter_links(urls+nested_links)
results = test_reflected(filtered_urls)

for result in results:  # print results
    print(result)
