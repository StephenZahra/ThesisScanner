import socket
import multiprocessing
import time


# create socket
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# bind socket
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_socket.bind(("localhost", 9000))

# listen
server_socket.listen(1)
print("Server waiting for blind SSTI triggered connections")

while True:
    # accept connections below
    #t_end = time.time() + 15  # wait for 15 seconds
    #while time.time() < t_end:

    client_socket, client_address = server_socket.accept()
    #print(f"Connection from {0}", client_address)
    print(client_socket.recv(4096))
    # handle client requests here

    # close the connection
    #client_socket.close()

