import re
import sys
import urllib.request
import requests
import random
import string

# Generate a random string to uniquely identify every instance of Stored Posterior SSTI generated from this script
random_string = ''.join(random.choices(string.ascii_uppercase + string.ascii_lowercase, k=10))


def get_html(url):
    """
    This function acquires the html for any given url
    """

    response = urllib.request.urlopen(url)
    html = response.read()

    return html


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
    total_inputs = input_collection+textarea_collection

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


def filter_links(all_urls):
    """
    This function checks for duplicates in the total collection of links in the website and removes them
    """

    all_urls = list(dict.fromkeys(all_urls))
    return all_urls


def post_url(html):
    """
    This function finds all form action links in given html
    """

    post_link = re.findall(r"action=([a-zA-Z0-9 _:;=./\"'\\\\]+)", html)[0]

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


def test_stored_posterior(urls):
    """
    This function performs SSTI on all forms in pages, and checks each page to verify if any of it has
    executed
    """

    scan_result = []

    # Here we make post requests to send data only
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
                    post_data[inp] = url + " " + group + "ssti test {{7*7}} " + random_string

                post_data["_token"] = token  # Add token last
                requests.post(group, data=post_data, cookies=cookies)
        except:
            continue


    # Here we check all the urls to try and find the data we posted previously
    for next_url in urls:
        html_to_inspect = str(get_html(next_url))
        req_line = ''

        try:
            #Check if the randomly generated string at the beginning is in the HTML
            if(random_string in html_to_inspect):
                for line in html_to_inspect.split("\n"):  # split new lines from html
                    if(random_string in line):
                        req_line = line  # Save line once found

                # Find all URLS on a page that are equal to req_line (the URL we are looking for)
                origin_urls = re.findall(r"(http://[a-zA-Z0-9_:;=./\'\\\\]+)", req_line)
                if("ssti test 49" in req_line):
                    scan_result.append("SSTI succeeded, Origin Page: " + str(origin_urls[1]) + " Origin Form: " + str(origin_urls[0]) + " Executed on: " + str(next_url))
                else:
                    scan_result.append("SSTI tested from: " + str(origin_urls[0]) + " was unsuccessful")
            elif (html_to_inspect.find(random_string) == -1 and html_to_inspect.find("49") == -1):  # If we find no unique string or 49 in the html
                scan_result.append("SSTI tested from: " + next_url + " was unsuccessful")
        except IndexError:
            scan_result.append("URL: " + next_url + " isVulnerable: Unable to test, no input points found")
            continue

    return scan_result


urls = sys.argv[1]
urls_list = list(urls.split(" "))
stored_pos_results = test_stored_posterior(urls_list)

for result in stored_pos_results:  # print results
    print(result)
