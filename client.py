import socket
from urllib.parse import quote


HOST = '127.0.0.1'
PORT = 4000

def receive_response(sock):
    """Receive complete response from server, handling multi-line responses."""
    response = ""
    buffer = b""
    
    # Set timeout to avoid hanging indefinitely
    sock.settimeout(5.0)
    
    try:
        while True:
            chunk = sock.recv(4096)
            if not chunk:
                break
            buffer += chunk
            
            # Try to decode what we have so far
            try:
                response = buffer.decode('utf-8')
                # Check if we have a complete response
                if response.endswith("END\n") or response.endswith("OK bye\n") or \
                   response.startswith("ERROR") or response.startswith("OK app_server ready"):
                    break
            except UnicodeDecodeError:
                continue
    except socket.timeout:
        # If timeout, return what we have
        if buffer:
            response = buffer.decode('utf-8', errors='ignore')
    finally:
        # Reset to blocking mode
        sock.settimeout(None)
    
    return response

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((HOST, PORT))
    
    # Receive and display welcome message
    welcome = receive_response(s)
    print(welcome.strip())
    print()
    
    # Command loop
    while True:
        command = input("Enter command (LIST, SEARCH, or QUIT): ").strip().upper()
        
        if command == "SEARCH":
            # Retry loop for city input
            while True:
                city = input("City (e.g., Long Beach, San Diego): ").strip()
                price = input("Max Price: ").strip()
                
                # Validate inputs
                if not city:
                    print("Error: City cannot be empty. Please try again.\n")
                    continue
                
                try:
                    price_int = int(price)
                    if price_int <= 0:
                        print("Error: Price must be a positive number. Please try again.\n")
                        continue
                except ValueError:
                    print("Error: Price must be a valid number. Please try again.\n")
                    continue
                
                # Format the SEARCH command with parameters (URL-encode city for spaces)
                full_command = f"SEARCH city={quote(city)} max_price={price}\n"
                
                # Send command to server
                s.sendall(full_command.encode('utf-8'))
                
                # Receive and display response
                response = receive_response(s)
                print("\n" + response)
                
                # Check if no results were found
                if "OK RESULT 0" in response:
                    retry = input("No listings found for that city. Try again? (y/n): ").strip().lower()
                    if retry == 'y' or retry == 'yes':
                        continue  # Retry city input
                    else:
                        break  # Exit retry loop, go back to command prompt
                else:
                    break  # Success, exit retry loop
            
        elif command == "LIST":
            full_command = "LIST\n"
            # Send command to server
            s.sendall(full_command.encode('utf-8'))
            
            # Receive and display response
            response = receive_response(s)
            print("\n" + response)
            
        elif command == "QUIT":
            full_command = "QUIT\n"
            # Send command to server
            s.sendall(full_command.encode('utf-8'))
            
            # Receive and display response
            response = receive_response(s)
            print("\n" + response)
            
            # Exit gracefully
            print("Closing connection...")
            try:
                s.shutdown(socket.SHUT_RDWR)  # Graceful shutdown
            except OSError:
                pass  # Socket may already be closed
            break
            
        else:
            print("Invalid command. Use LIST, SEARCH, or QUIT.")