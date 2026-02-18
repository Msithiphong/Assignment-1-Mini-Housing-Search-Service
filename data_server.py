import socket
import json
import os
from urllib.parse import unquote

# Host and Port to listen on
HOST = '127.0.0.1'
PORT = 3000

DB_FILE = "listings.json"

def load_listings():
    """ Opens listings.json """

    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as file:
            return json.load(file)
    else:
        return {}

    
def save_listings(listings):
    """ Saves listings to listings.json """
    with open(DB_FILE, "w") as file:
        json.dump(listings, file, indent=4)

    
listings_array = load_listings()
if not listings_array:
    print("listings failed to load or listings.json does not exist")

def RAW_LIST():
    """ Returns all listings in an array """
    
    return listings_array
    

def RAW_SEARCH(city, max_price):
    """ Filters listings by city and max price and returns them as a json object """
    
    searched_listings = []
    for listing in listings_array:
        # Case-insensitive comparison
        if (listing["city"].lower() == city.lower()) and (int(listing["price"]) <= max_price):
            searched_listings.append(listing)
    
    return searched_listings
    
def parse_command(cmd_str):
    """ Parses command string """ 

    keywords = cmd_str.strip().split()
    
    if not keywords:
        return None, {}

    command = keywords[0]
    parameters = {}

    for word in keywords[1:]:
        if '=' in word:
            key, value = word.split('=', 1)
            parameters[key] = value

    return command, parameters


        
        
        
    



with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.bind((HOST, PORT))
    s.listen()
    conn, addr = s.accept() # Wait for connection
    with conn:
        print(f'Connected by {addr}')
        while True:
            data = conn.recv(1024)
            if not data:
                break
            
            # Decode the data received
            message = data.decode('utf-8')
            print(f"Data Server received:  {message}")

            # Parse the command
            command, parameters = parse_command(message)
            
                
            if command == "RAW_SEARCH":
                city = unquote(parameters.get('city', '')) # URL-decode city name
                max_price = int(parameters.get('max_price', 0)) #  returns 0 if 'max_price' not found
                search = RAW_SEARCH(city, max_price)
                response = json.dumps(search)
                conn.sendall(response.encode('utf-8')) # encode and send to app_server
            elif command == "RAW_LIST":
               raw_list = RAW_LIST()
               response = json.dumps(raw_list)
               conn.sendall(response.encode('utf-8')) 
            else:
                error_msg = json.dumps({"error": "Unknown command"})
                conn.sendall(error_msg.encode('utf-8'))