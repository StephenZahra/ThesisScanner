import re
import urllib.request
import requests


def getrequest():
    """
    Sends a get request to the page returning the url used and html page
    """

    url = input("Please enter a url: ")
    response = urllib.request.urlopen(url)
    text = response.read()

    return url, text


def locateinputpoints(html):
    """
    Finds all text input tags and returns their names
    """

    # find all input tags including token
    inputcollection = re.findall(r"(<input [a-zA-Z0-9 _=\"'\\\\]*>)+", str(html))

    allnames = []  # array containing necessary input tags which will be used later
    for elem in inputcollection:  # loop through inputs, remove token & submit input
        if "_token" in elem:
            inputcollection.remove(elem)
        elif "type=\\'submit\\'" in elem:
            inputcollection.remove(elem)

    for inp in inputcollection:  # filter through remaining valid inputs storing the names
        allnames = re.findall(r"(name=[\\\\'a-zA-Z\\\\']+)", inp)

    finalNames = []
    for elem in allnames:
        tempname = elem.replace("name=\\'", "")
        tempname = tempname.replace("\\'", "")
        finalNames.append(tempname)

    return finalNames


def sendpostrequest(url, names):
    """
    Repeatedly sends POST requests to the page using previously acquired input tag names, returns dictionary
    with boolean values
    """

    session = requests.session()
    front = session.get(url)

    token = re.findall(r'<input type="hidden" name="_token" value="(.*)"', front.text)[0]
    cookies = session.cookies

    scanResult = {}  # dictionary to store results
    for name in names:
        data = {name: "{{7*7}}", "_token": token}
        req = requests.post(url, data=data, cookies=cookies)
        text = req.text

        if "49" in text:
            scanResult[name] = True
        else:
            scanResult[name] = False

    return scanResult


url, text = getrequest()

names = locateinputpoints(text)

results = sendpostrequest(url, names)

for result in results:  # print results
    print("Input name: " + result + " isVulnerable: " + str(results[result]))
