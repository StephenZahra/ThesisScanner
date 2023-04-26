import re
import sys
import urllib.request
import requests
from urllib.parse import urlparse
import selenium.common.exceptions
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By


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
    post_link = re.findall(r"action=([a-zA-Z0-9_:;=./\"\-'\\\\]+)", html)[0]

    #for link in post_links:
    formatted_link = re.findall(r"(http://[a-zA-Z0-9_:;=./\-\\\\]+)", post_link)[0]
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
            temp_name = temp_name.replace("\"", "")  # IMPORTANT
            final_names.append(temp_name)
        input_counter+=1

    return final_names, input_counter


def get_input_types(html):
    """
    This function takes form html and returns the types of inputs that are found sequentially
    """

    input_types = re.findall(r"type=\"([a-zA-Z]+)\"", html)
    input_types.remove("hidden")
    input_types.remove("submit")

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

    token = re.findall(r'<input type="hidden" name="_token" value="(.*)"', html)
    return token


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
        joined_url = url
        try:
            if (hostname not in joined_url):  # check if the url is not formatted properly
                joined_url = "http://" + hostname + url

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


def test_authenticated_stored_posterior(urls):
    login_found = False
    login_page_url = ""
    login_form_url = ""
    login_inputs = {}
    to_scan = []

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

        login_page = authenticated_session.get(login_page_url).text  # Get the login page html
        cookies = authenticated_session.cookies

        login_token = get_token(login_page)  # Extract the form token
        login_data["_token"] = login_token

        site_type = None
        if("vue" in login_page):
            site_type = "vue"

        hostname = urlparse(login_form_url).hostname  # Hostname to use later
        login_response = authenticated_session.post(login_form_url, login_data, cookies=cookies)  # Performing login

        if (login_response.status_code == 200):  # Login successful
            # We must start a new process of scanning for urls, getting forms, and testing them as authenticated users
            front = login_response.content
            new_urls = get_page_urls(front)

            nested_links = check_nested_links(new_urls, str(hostname))  # Check for links inside the new pages
            filtered_urls = filter_links(new_urls + nested_links, hostname)  # Form a collection of urls we've seen so far and new ones (not including urls variable as that has login and register that are not important)
            split_urls = list(filtered_urls.split("|"))  # split the filtered_urls string

            for unique_url in split_urls:
                if (unique_url not in urls):  # If the current URL is not present in the list of URLs we have already seen
                    if("http://" not in unique_url):  # Differentiate between vue and laravel urls
                        to_scan.append("http://" + str(hostname) + unique_url)
                    else:
                        to_scan.append(unique_url)
            to_scan.pop(-1)  # Removing the last element as it is an empty string

            chrome_options = Options()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--disable-gpu')


            browser = webdriver.Chrome(options=chrome_options)
            browser.get(login_page_url)
            browser.delete_all_cookies()
            selenium_cookies = authenticated_session.cookies.get_dict()
            for name, value in selenium_cookies.items():
                browser.add_cookie({'name': name, 'value': value})

            browser.add_cookie({'name': "domain", 'value': "." + str(hostname)})

            if(site_type == "vue"):
                for next_url in to_scan:
                    browser.get(next_url)
                    html = browser.page_source

                    form_groups = browser.find_elements(By.TAG_NAME, 'form')  # Get all forms

                    if(len(form_groups) == 0):
                        print(f"No forms detected on {next_url}. Moving on to next url")

                    for index in range(len(form_groups)):
                        form_groups = browser.find_elements(By.TAG_NAME, 'form')
                        current_form = form_groups[index]

                        if("new password" in current_form.get_attribute("innerHTML").lower()):
                            print("Found password reset form, skipping as Stored SSTI will not execute")
                            continue
                        else:
                            pass

                        all_inputs = current_form.find_elements(By.TAG_NAME, 'input')
                        all_dropdowns = current_form.find_elements(By.TAG_NAME, 'select')

                        if(len(all_inputs) == 1):  # Check if the input is just a hidden laravel token
                            if(all_inputs[0].get_attribute('type') == "hidden"):
                                continue

                        for dd_index in range(len(all_dropdowns)):  # Checking for any empty dropdowns, remove if so
                            if(all_dropdowns[dd_index].text == ""):
                                all_dropdowns.remove(all_dropdowns[dd_index])

                        visibility_status = True
                        # Check if any of the form elements are not visible
                        if any(not input_tag.is_displayed() for input_tag in all_inputs):
                            visibility_status = False

                        if(visibility_status == True):
                            fresh_inps = current_form.find_elements(By.TAG_NAME, 'input')
                            for indx in range(len(fresh_inps)):  # Loop through inputs
                                next_inp = fresh_inps[indx]

                                try:
                                    if(next_inp.get_attribute('type') == "search"):
                                        search_inject = "auth stored ssti test {{7*7}} " + next_url
                                        next_inp.clear()
                                        next_inp.send_keys(search_inject)
                                    elif(next_inp.get_attribute('type') == "text"):
                                        text_inject = "auth stored ssti test {{7*7}} " + next_url
                                        next_inp.clear()
                                        next_inp.send_keys(text_inject)
                                    elif(next_inp.get_attribute('type') == "number"):
                                        next_inp.clear()
                                        next_inp.send_keys("1234")
                                    elif(next_inp.get_attribute('type') == "email"):
                                        next_inp.clear()
                                        next_inp.send_keys("test@gmail.com")
                                    elif(next_inp.get_attribute('type') == "checkbox"):
                                        next_inp.clear()
                                        next_inp.send_keys("0")
                                    elif(next_inp.get_attribute('type') == ""):  # If the type isn't specified we assume that it is text
                                        text_inject = "auth stored ssti test {{7*7}} " + next_url
                                        next_inp.clear()
                                        next_inp.send_keys(text_inject)
                                except selenium.common.exceptions.ElementNotInteractableException:
                                    pass

                            form_buttons = current_form.find_elements(By.TAG_NAME, 'button')

                            for button_indx in range(len(form_buttons)):
                                form_buttons = current_form.find_elements(By.TAG_NAME, 'button')
                                next_btn = form_buttons[button_indx]

                                if(next_btn.get_attribute('type') == 'submit' and next_btn.is_displayed() == True):  # Found the submit button
                                    next_btn.click()
                        else:
                            print(f"\nSkipping form on {next_url} as it was not revealed")

                for next_url in to_scan:  # Re-check the urls to see where SSTI has been found
                    browser.get(next_url)
                    html = browser.page_source

                    found_ssti = re.search(r"auth stored ssti test 49 ([a-zA-Z0-9:/\-.]+)", html)
                    if (found_ssti):
                        print(f"On {next_url} - Found executed SSTI from {found_ssti.group(1)}")

            else:
                for next_url in urls:
                    browser.get(next_url)
                    html = browser.page_source

                    auth_groups, input_no = get_forms(html)

                    if(input_no > 0):  # We cannot do anything if there are no inputs to inject in
                        for auth_group in auth_groups:
                            # Gets the current form token
                            token = get_token(html)

                            # Get the inputs for each form group iteratively
                            inputs = auth_groups[auth_group]

                            types = get_input_types(html)

                            post_data = {}
                            input_counter = 0
                            if(input_no == len(inputs)):  # Check that the count of inputs found earlier is the same the count of "name=" values found
                                for index in range(len(inputs)):  # Cycle through inputs and fill in based on type
                                    if(types[index] == "text"):
                                        post_data[inputs[index]] = "auth stored ssti test {{7*7}} " + next_url + " " + auth_group
                                    elif(types[index] == "number"):
                                        post_data[inputs[index]] = 1234
                                    elif(types[index] == "email"):
                                        post_data[inputs[index]] = "test@gmail.com"
                                    elif(types[index] == "checkbox"):
                                        post_data[inputs[index]] = "0"

                                    input_counter+=1

                                post_data["_token"] = token[0]
                                authenticated_session.post(auth_group, post_data, cookies=cookies)
                            else:
                                print("Cannot test form ", auth_group, " on page: ", next_url, " due to one or more missing name= attribute/s")
                    else:
                        print(f"No form links found for url: {next_url}. Moving on to next url")

                #  Check all urls that were scanned again
                session_instance = requests.session()  # Create a session to be authenticated

                login_page = session_instance.get(login_page_url)  # Get the login page html
                cookies = session_instance.cookies

                login_token = get_token(login_page.text)  # Extract the form token
                login_data["_token"] = login_token
                login_response = session_instance.post(login_form_url, login_data, cookies=cookies)  # Performing login
                for nxt_url in to_scan:
                    site_data = session_instance.get(nxt_url)
                    html_to_inspect = site_data.text
                    found_vuln_pairs = []  # Variable to keep track of url pairs found to be vulnerable

                    if("auth stored ssti test 49" in html_to_inspect):  # Check if the url we are checking have executed ssti
                        for line in html_to_inspect.split("\n"):  # split new lines from html
                            if("auth stored ssti test 49" in line):
                                req_line = line  # Save line once found
                                line_urls = re.findall(r"(http://[a-zA-Z0-9_:;=./\-\\\\]+)", req_line)
                                if(line_urls[0] + " " + line_urls[1] not in found_vuln_pairs):  # Check if we haven't already found this pair of urls previously
                                    print("SSTI detected on page ", line_urls[0], " from form url: ", line_urls[1])

                                break  # Exit the inner for loop
        else:
            print("\n\nFailed to authenticate to perform authenticated scan. The scan will now stop")
            sys.exit()


urls = sys.argv[1]
urls_list = list(urls.split(" "))
test_authenticated_stored_posterior(urls_list)
