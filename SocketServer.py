import socket
import re


complete_injection_url_list = []
while True:
    # create socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # bind socket
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind(("localhost", 9000))

    # listen
    server_socket.listen(90)

    client_socket, client_address = server_socket.accept()
    alert = client_socket.recv(4096)


    urls_in_string = re.findall(r"http://[a-zA-z0-9.:/]+", str(alert))  # getting all urls found in the alert we receive
    complete_url_string = urls_in_string[0] + " " + urls_in_string[1] + " " + urls_in_string[2]

    if(complete_url_string not in complete_injection_url_list):
        print(alert.decode("utf-8"))
        complete_injection_url_list.append(complete_url_string)

    server_socket.close()  # restart socket
