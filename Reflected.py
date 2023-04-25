import re
import sys
import requests


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

    form_groups = re.findall(r"(action=[a-zA-Z0-9 _:;=./\"\-<>\s\S'\\\\]+<\/form>)+", html)
    link_groups = {}
    input_count = 0
    for group in form_groups:
        action_link = post_url(group)
        input_links, input_count = locate_input_points(group)
        link_groups[action_link] = input_links

    return link_groups, input_count


def test_reflected(urls):
    """
    Repeatedly sends POST requests to all forms in pages. If the result of 7*7 is found in the html then injection is confirmed
    """

    scan_result = []
    for url in urls:
        session = requests.session()
        front = session.get(url)

        try:
            token = get_token(front.text)
            cookies = session.cookies

            post_data = {}
            groups, input_no = get_forms(front.text)

            for group in groups:
                # Get the inputs for each form group iteratively
                inputs = groups[group]
                for inp in inputs:  # Give each input a value and add to dictionary
                    post_data[inp] = "ssti test {{7*7}}"

                post_data["_token"] = token  # Add token last
                req = requests.post(group, data=post_data, cookies=cookies)

                # Check that an error is not thrown due to GET route, skip rest of code execution
                if ("methodNotAllowed" in req.text):
                    scan_result.append("URL: " + url + " isVulnerable: Unable to test, only GET is supported")
                    continue

                if "ssti test 49" in req.text:
                    scan_result.append("URL: " + url + " Form link: " + group + " isVulnerable: True")
                else:
                    scan_result.append("URL: " + url + " Form link: " + group + " isVulnerable: False")
        except IndexError:  # A page had no inputs we could find
            scan_result.append("URL: " + url + " isVulnerable: Unable to test, no input points found")

    return scan_result


urls = sys.argv[1]
urls_list = list(urls.split(" "))
results = test_reflected(urls_list)

for result in results:  # print results
    print(result)
