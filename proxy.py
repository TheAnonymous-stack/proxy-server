import socket
import select
import sys
import os
import time

# Create a listening TCP server
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Bind server socket to localhost:8888
server_address = ('localhost', 8888)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind(server_address)

# Make server socket listen to incoming browsers
server.listen(1)

# while loop to allow proxy to handle many requests one after another
while True:
    try:
        # Make server accept incoming browser
        browser, client_address = server.accept()
        data = browser.recv(4096)
        decoded_data = data.decode()
        lines = decoded_data.split('\r\n')
        request_line = lines[0]
        method, path, http_version = request_line.split(" ")
        path = path.lstrip('/')  # get rid of the starting forward slash
        path_components = path.split('/', 1)
        hostname = path_components[0]
        new_path = '/' + path_components[1] if len(path_components) > 1 else '/'
        
        # modify url path
        lines[0] = f"GET {new_path} {http_version}"

        for i in range(1, len(lines)):

            # modify host
            if lines[i].startswith("Host:"):
                lines[i] = f"Host: {hostname}"

            # modify connection type to close because once proxy receives response
            # from destination server, there is no need to keep the connection alive
            elif lines[i].startswith("Connection:"):
                lines[i] = f"Connection: close"

        # encode the new request back to bytes
        new_req = "\r\n".join(lines).encode()

        # Create forwarding socket
        dest_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        dest_server_address = (hostname, 80)
        dest_socket.connect(dest_server_address)
        
        # forward the new request to destination server
        dest_socket.sendall(new_req)

        # relay response from destination server back to browser
        while True:
            response = dest_socket.recv(4096)
            if response:
                browser.sendall(response)
            else:
                break
        
        # finish relaying response from destination server to browser
        # can close both browser and dest_socket now
        dest_socket.close()
        browser.close()
    except Exception as e:
        print(f"Error: {e}")
    finally:
        browser.close()


    

    

