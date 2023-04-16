import re
import sys
import urllib.request
import requests
from urllib.parse import urlparse
from urllib.parse import urljoin


def get_html(url):
    """
    This function acquires the html for any given url
    """

    response = urllib.request.urlopen(url)
    html = response.read()

    return html


def post_url(html):
    """
    This function finds all form action links in given html
    """

    post_link = re.findall(r"action=([a-zA-Z0-9 _:;=./\"'\\\\]+)", html)[0]

    #for link in post_links:
    formatted_link = re.findall(r"(http://[a-zA-Z0-9_:;=./\\\\]+)", post_link)[0]
    #formatted_links.append(formatted_link[0])

    return formatted_link


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


def get_input_types(html):
    """
    This function takes form html and returns the types of inputs that are found sequentially
    """

    input_types = re.findall(r"type=\"([a-zA-Z])\"+", html)
    print("input_types: ", input_types)
    return input_types


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


def get_token(html):
    """
    This function grabs the token for each given form
    """

    token = re.findall(r'<input type="hidden" name="_token" value="(.*)"', html)[0]
    return token


def get_page_urls(html):
    """
    This function gets all href data in <a> tags and verifies which of them are in the current domain and removes extra
    characters if so
    """

    a_tags = re.findall(r'href="([^"]*)"', str(html))
    vue_urls = re.findall(r'to="([^"]*)"', str(html))
    all_tags = a_tags + vue_urls
    #link_collection = re.findall(r"(href[a-zA-Z0-9_=:.\"/'\\\\]*)+", str(html))
    required_links = []
    for link in all_tags:
        parsed_link = urlparse(link)
        #if (link.find("127.0.0.1:8000") != -1):  # This helps us stay in session  (not going to different websites)
        if(parsed_link.hostname == "localhost" or parsed_link.hostname == None):  # This helps us stay in session  (not going to different websites)
            # modif_link = link.replace("href=\"", '')
            # modif_link = modif_link.replace("\"", '')
            required_links.append(link)

    return required_links


def check_nested_links(required_links):
    """
    Iterates through collected links and checks for new ones in them
    """

    nested_links = []
    for url in required_links:
        full_url = urllib.parse.urljoin("http://127.0.0.1:8000", url)
        response = urllib.request.urlopen(full_url)
        html = response.read()

        a_tags = re.findall(r'href="([^"]*)"', str(html))
        vue_urls = re.findall(r'to="([^"]*)"', str(html))
        all_tags = a_tags + vue_urls

        #link_collection = re.findall(r"(href[a-zA-Z0-9_=:.\"/'\\\\]*)+", str(html))

        for link in all_tags:
            parsed_link = urlparse(link)
            if (parsed_link.hostname == "localhost" or parsed_link.hostname == None):  # This helps us stay in session  (not going to different websites)
                #modif_link = link.replace("href=\"", '')
                #modif_link = modif_link.replace("\"", '')
                nested_links.append(link)
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


def test_authenticated_stored_posterior(urls):
    login_found = False
    login_page_url = ""
    login_form_url = ""
    login_inputs = {}

    #  Loop through all URLs to find login form
    try:
        for url in urls:
            session = requests.session()
            front = session.get(url)

            groups, input_no = get_forms(front.text)
            if(login_found == False):
                login_form_url, login_inputs, login_page_url, login_found = check_login_form(groups, url)
            else:
                break
    except Exception:
        pass

    if(login_found != True):  # Login form not found, thus scan cannot continue
        print("\n\nLogin form was not found, stopping scan...")
        sys.exit()
    else:
        # Perform login
        cred_names = sys.argv[2]  # Getting the login credentials inputted at the beginning
        cred_vals = sys.argv[3]

        name_array = cred_names.split(" ")
        val_array = cred_vals.split(" ")

        login_data = {}

        input_count = 0
        for inpt in login_inputs:  # For each input found in the login form
            login_data[name_array[input_count]] = val_array[input_count]  # use cred name & val arrays to get inputted names and values
            input_count += 1

        authenticated_session = requests.session()  # Create a session to be authenticated

        login_page = authenticated_session.get(login_page_url)  # Get the login page html
        cookies = authenticated_session.cookies

        login_token = get_token(login_page.text)  # Extract the form token
        login_data["_token"] = login_token

        login_response = authenticated_session.post(login_form_url, login_data, cookies)  # Performing login

        if (login_response.status_code == 200):  # Login successful
            # We must start a new process of scanning for urls, getting forms, and testing them as authenticated users
            front = login_response.content
            new_urls = get_page_urls(front)

            nested_links = check_nested_links(new_urls)  # Check for links inside the new pages
            filtered_urls = filter_links(new_urls + nested_links)  # Form a collection of urls we've seen so far and new ones (not including urls variable as that has login and register that are not important)
            split_urls = list(filtered_urls.split("|"))  # split the filtered_urls string

            to_scan = []
            for unique_url in split_urls:
                if (unique_url not in urls):  # If the current URL is not present in the list of URLs we have already seen
                    to_scan.append(unique_url)
            to_scan.pop(-1)  # Removing the last element as it is an empty string

            for next_url in to_scan:
                try:
                    page_html = authenticated_session.get(next_url)

                    groups, input_no = get_forms(page_html)

                    for group in groups:
                        # Gets the current form token
                        token = get_token(group)

                        # Get the inputs for each form group iteratively
                        inputs = groups[group]

                        types = get_input_types(group)
                        post_data = {}
                        input_counter = 0
                        if(input_no == len(inputs)):  # Check that the count of inputs found earlier is the same the count of "name=" values found
                            for inp in inputs:  # Cycle through inputs and fill in based on type
                                if(types[input_counter] == "text"):
                                    post_data[inp] = "ssti test {{7*7}} " + next_url + " " + group
                                elif(types[input_counter] == "number"):
                                    post_data[inp] = 1234567890
                                elif(types[input_counter] == "email"):
                                    post_data[inp] = "test@gmail.com"
                                elif(types[input_counter] == "checkbox"):
                                    post_data[inp] = "1"

                                input_counter+=1

                            post_data["_token"] = token
                            requests.post(group, post_data, cookies)
                        else:
                            print("\n\nCannot test form ", group, " on page: ", next_url, " due to one or more missing name= attribute/s")
                except Exception:
                    continue

            #  Check all urls that were scanned again
            for next_url  in to_scan:
                html_to_inspect = str(get_html(next_url))
                req_line = ""
                found_vuln_pairs = []  # Variable to keep track of url pairs found to be vulnerable

                if("ssti test 49" in html_to_inspect):  # Check if the url we are checking have executed ssti
                    for line in html_to_inspect.split("\n"):  # split new lines from html
                        if("ssti test 49" in line):
                            req_line = line  # Save line once found
                            req_line.replace("ssti test 49 ", "")  # Format the string and split below
                            line_urls = list(req_line.split(" "))
                            if(line_urls[0] + " " + line_urls[1] not in found_vuln_pairs):  # Check if we haven't already found this pair of urls previously
                                print("SSTI detected on page ", line_urls[0], " from form url: ", line_urls[1])
                                found_vuln_pairs.append(line_urls[0] + " " + line_urls[1])

                            break  # Exit the inner for loop
        else:
            print("\n\nFailed to authenticate to perform authenticated scan. The scan will now stop")
            sys.exit()


urls = sys.argv[1]
urls_list = list(urls.split(" "))
test_authenticated_stored_posterior(urls_list)