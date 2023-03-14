import socket
import sys
import re
import random
import string

random_string = ''.join(random.choices(string.ascii_uppercase + string.ascii_lowercase, k=10))


# create socket
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# bind socket
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_socket.bind(("localhost", 9000))

# listen
server_socket.listen(1)
print("Inputs sent, user may now browse pages to trigger blind SSTI\n")
print("Server waiting for blind SSTI triggered connections\n")
print("Press enter at any time to finish testing for blind SSTI and close the server\n")

urls = sys.argv[1]
print("urls below")
print(urls)
urls_list = list(urls.split(" "))

user_input = 1
while True:
    client_socket, client_address = server_socket.accept()
    #print(f"Connection from {0}", client_address)
    alert = client_socket.recv(4096)

    urls_in_string = re.findall(r"http://[a-zA-z0-9.:/]+", str(alert))
    print(urls_in_string[2])
    print(str(alert))
    if not (urls_in_string[2] in str(alert)): # making sure that the third url (where injection occurs) is not a url that has been found through requests (not actually a blind area)
        print(type(urls_in_string[2]))
        print(urls_list)
        print(alert)

    user_input = input("Press enter if you have finished testing for blind SSTI: ")
    if(user_input == ""):
        print("Stopping tests for Blind SSTI")
        break
