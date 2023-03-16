import socket
import sys
import re


print("Inputs sent, user may now browse pages to trigger blind SSTI\n")

urls = sys.argv[1]
urls_list = list(urls.split(" "))

while True:
    # create socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # bind socket
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind(("localhost", 9000))

    # listen
    server_socket.listen(90)

    print("Server waiting for blind SSTI triggered connections\n")
    client_socket, client_address = server_socket.accept()
    alert = client_socket.recv(4096)

    urls_in_string = re.findall(r"http://[a-zA-z0-9.:/]+", str(alert))  # getting all urls found in the alert we receive
    if not (urls_in_string[2] in urls_list):  # making sure that the third url (where injection occurs) is not a url that has been found through requests (not actually a blind area)
        print(alert)
    else:
        print("Connection received from page with reflected injection, this is not blind SSTI")

    user_input = input("Press 1 if you have finished browsing pages for blind SSTI: ")
    if(user_input == "1"):
        print("Stopping tests for Blind SSTI")
        break
    else:
        server_socket.close()  # restart socket
