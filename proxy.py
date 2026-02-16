import socket
import select
import sys
import os
import time


# def convertURLToFileName(url):


def __main__ ():
    # Create socket list to monitor sockets
    socket_set = set()

    # create dict to map destination server socket to browser socket
    dest_browser_map = {}

    # create caches to store destination response and filenames
    dest_response_data = {}
    dest_cache_file = {}

    # Create a listening TCP server
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    socket_set.add(server)

    # Bind server socket to localhost:8888
    server_address = ('localhost', 8888)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(server_address)

    # Make server socket listen to incoming browsers
    server.listen(5)

    # while loop to allow proxy to handle many requests one after another
    while True:
        
            readable, _, _ = select.select(list(socket_set), [], []) # only needs sockets to check for readability
            for sock in readable:
                try:
                    if sock is server:
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

                        # check proxy first
                        filename = os.path.join(os.getcwd(), hostname + new_path.replace('/', '_'))
                        if os.path.exists(filename):
                            with open(filename, 'rb') as f:
                                content = f.read()
                                browser.sendall(content)
                                browser.close()

                        else: # filename is not in cache
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
                            socket_set.add(dest_socket) # add dest_socket to list of sockets to monitor
                            
                            # update destination - browser map
                            dest_browser_map[dest_socket] = browser

                            # save filename to write destination server response to
                            dest_cache_file[dest_socket] = filename

                            # build up destination server response
                            dest_response_data[dest_socket] = b""
                
                    else:

                        dest_socket = sock
                        browser = dest_browser_map[dest_socket]
                        response = dest_socket.recv(4096)
                        if response:
                            browser.sendall(response)
                            dest_response_data[dest_socket] += response

                        else: 
                            # all data has been written so write the response to file to cache
                            filename = dest_cache_file[dest_socket]
                            content = dest_response_data[dest_socket]
                            with open(filename, "wb") as f:
                                f.write(content)
                            browser.close()
                            dest_socket.close()
                            socket_set.remove(dest_socket)

                            # clear map entries
                            del dest_browser_map[dest_socket]
                            del dest_response_data[dest_socket]
                            del dest_cache_file[dest_socket]
                except Exception as e:
                    print(f"Error: {e}")      
                
if __name__ == "__main__":
    __main__()
        


        

        

