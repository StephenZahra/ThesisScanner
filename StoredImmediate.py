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


def locate_input_points(html):
    """
    Finds all text input tags and returns their names
    """

    # find all input tags including token
    input_collection = re.findall(r"(<input [a-zA-Z0-9 _=\"'\\\\]*>)+", str(html))
    print(input_collection)
    all_names = []  # array containing necessary input tags which will be used later
    for elem in input_collection:  # loop through inputs, remove token & submit input
        if "_token" in elem:
            input_collection.remove(elem)
        elif "type='submit'" in elem:
            input_collection.remove(elem)

    for inp in input_collection:  # filter through remaining valid inputs storing the names
        all_names = re.findall(r"(name=[\\\\'a-zA-Z0-9\"'\\\\']+)", inp)

    final_names = []
    for elem in all_names:  # Clean names
        temp_name = elem.replace("name=", "")
        temp_name = temp_name.replace("'", "")
        final_names.append(temp_name)
    return final_names


def test_stored_immediate(urls):
    """
    This function performs SSTI on a given target url for all forms, and checks each page to verify if any of it has
    executed
    """

    for url in urls:
        session = requests.session()
        front = session.get(url)

        token = re.findall(r'<input type="hidden" name="_token" value="(.*)"', front.text)[0]
        cookies = session.cookies

        inputs = locate_input_points(front.text)

        print(inputs)
        for name in inputs:
            data = {name: "{{7*7}}", "_token": token}
            req = requests.post(url, data=data, cookies=cookies)
            text = req.text
            print(text)


        # scan_result = {}
        # for next_url in urls:
        #     html = get_html(next_url)
        #
        #     if("49" in str(html)):
        #         scan_result[next_url] = True
        #     else:
        #         scan_result[next_url] = False

        #return scan_result


# Begin the scanning process
html = begin_scan()

# urls = get_page_urls(html)
#
# nested_links = check_nested_links(urls)
# filtered_urls = filter_links(urls+nested_links)
#stored_pos_results = \
test_stored_immediate(["http://127.0.0.1:8000/storedimm"])

# for result in stored_pos_results:  # print results
#    print("URL: " + result + " hasExecutedSSTI: " + str(stored_pos_results[result]))