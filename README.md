# Mini Housing Search Service

A three-tier client-server application for searching housing listings. The system consists of a data server, application server, and client that communicate via TCP sockets.

## Architecture

```
Client ←→ App Server ←→ Data Server ←→ listings.json
(Port 4000)      (Port 3000)
```

- **Data Server**: Manages housing data from `listings.json` and handles raw data queries
- **App Server**: Middleware layer that processes client requests, ranks results, and formats responses
- **Client**: Interactive command-line interface for users to search listings

## Prerequisites

- Python 3.x
- The following files in the same directory:
  - `data_server.py`
  - `app_server.py`
  - `client.py`
  - `listings.json`

## How to Run

### Step 1: Start the Data Server

Open a terminal and run:

```bash
python3 data_server.py
```

**Output:** `Connected by ('127.0.0.1', <port>)`

The data server listens on `127.0.0.1:3000` and waits for the app server to connect.

### Step 2: Start the App Server

Open a **new terminal** and run:

```bash
python3 app_server.py
```

**Output:** `app_server listening on 127.0.0.1:4000`

The app server:
- Connects to the data server at port 3000
- Listens for client connections at port 4000
- Logs all events to `app_server.log`

### Step 3: Start the Client

Open a **new terminal** and run:

```bash
python3 client.py
```

**Output:** Welcome message with available commands

You're now ready to interact with the housing search service!

## Client Commands

### LIST
Retrieves all housing listings.

**Usage:**
```
Enter command (LIST, SEARCH, or QUIT): LIST
```

**Response:**
```
OK RESULT 10
1 | Long Beach | 123 Ocean Blvd | $2200 | 2 bd
2 | Pasadena | 789 Colorado Blvd | $2800 | 2 bd
...
END
```

Results are automatically ranked by:
1. Price (lowest first)
2. Number of bedrooms (most first)

---

### SEARCH
Search for listings by city and maximum price.

**Usage:**
```
Enter command (LIST, SEARCH, or QUIT): SEARCH
City (e.g., Long Beach, San Diego): Long Beach
Max Price: 2500
```

**Parameters:**
- **City**: Case-insensitive, spaces allowed (e.g., "Long Beach", "san diego", "IRVINE")
- **Max Price**: Positive integer representing maximum monthly rent

**Response:**
```
OK RESULT 2
1 | Long Beach | 123 Ocean Blvd | $2200 | 2 bd
7 | Long Beach | 222 Shoreline Dr | $2400 | 1 bd
END
```

**Error Handling:**
- If city is empty: "Error: City cannot be empty. Please try again."
- If price is invalid: "Error: Price must be a valid number. Please try again."
- If no results found: "No listings found for that city. Try again? (y/n)"

---

### QUIT
Closes the connection gracefully.

**Usage:**
```
Enter command (LIST, SEARCH, or QUIT): QUIT
```

**Response:**
```
OK bye

Closing connection...
Connection closed.
```

## Logs

The app server creates `app_server.log` with timestamped events:
- Client connections/disconnections
- Request forwarding to data server
- Response summaries
- Cache hits and misses

**Example log entries:**
```
[2026-02-17 14:23:45] CONNECT ('127.0.0.1', 54321)
[2026-02-17 14:23:50] REQUEST ('127.0.0.1', 54321): SEARCH city=Long%20Beach max_price=2500
[2026-02-17 14:23:50] CACHE MISS ('127.0.0.1', 54321): SEARCH:Long Beach:2500
[2026-02-17 14:23:50] FORWARD ('127.0.0.1', 54321): RAW_SEARCH city=Long Beach max_price=2500
[2026-02-17 14:23:50] RESPONSE ('127.0.0.1', 54321): OK RESULT 2
[2026-02-17 14:23:55] REQUEST ('127.0.0.1', 54321): SEARCH city=Long%20Beach max_price=2500
[2026-02-17 14:23:55] CACHE HIT ('127.0.0.1', 54321): SEARCH:Long Beach:2500
[2026-02-17 14:23:55] RESPONSE ('127.0.0.1', 54321): OK RESULT 2
[2026-02-17 14:24:00] DISCONNECT ('127.0.0.1', 54321)
```

## Caching

The app server implements response caching to reduce load on the data server and improve performance.

### Cache Configuration

Edit `app_server.py` to configure caching behavior:

```python
# Cache settings
CACHE_ENABLED = True  # Set to False to disable caching
CACHE = {}
CACHE_TTL = 60  # seconds
```

**Settings:**
- **CACHE_ENABLED**: Set to `True` to enable caching, `False` to disable
- **CACHE_TTL**: Time-to-live in seconds (default: 60)

### How Caching Works

- Each `LIST` and `SEARCH` request is cached with a unique key
- Cache entries expire after `CACHE_TTL` seconds
- Cache hits return immediately without querying the data server
- Cache misses forward the request to the data server and store the result
- Error responses are also cached to prevent repeated failed queries

### Enabling/Disabling Cache

**To disable caching:**
1. Open `app_server.py`
2. Change `CACHE_ENABLED = True` to `CACHE_ENABLED = False`
3. Restart the app server

**To enable caching:**
1. Open `app_server.py`
2. Change `CACHE_ENABLED = False` to `CACHE_ENABLED = True`
3. Restart the app server

**Note:** Changes require restarting the app server to take effect.

## Stopping the Services

1. **Client**: Type `QUIT` or press `Ctrl+C`
2. **App Server**: Press `Ctrl+C` in the terminal
3. **Data Server**: Press `Ctrl+C` in the terminal

**Note:** Always stop in this order to avoid connection errors.

## Troubleshooting

### Connection refused

Ensure servers are started in order:
1. Data server first (port 3000)
2. App server second (port 4000)
3. Client last


## Example Session

```bash
# Terminal 1
$ python3 data_server.py
Connected by ('127.0.0.1', 50234)

# Terminal 2
$ python3 app_server.py
app_server listening on 127.0.0.1:4000
client: ('127.0.0.1', 50235)

# Terminal 3
$ python3 client.py
OK app_server ready. Commands: LIST | SEARCH city=<City> max_price=<Int> | QUIT

Enter command (LIST, SEARCH, or QUIT): SEARCH
City (e.g., Long Beach, San Diego): long beach
Max Price: 2500

OK RESULT 2
1 | Long Beach | 123 Ocean Blvd | $2200 | 2 bd
7 | Long Beach | 222 Shoreline Dr | $2400 | 1 bd
END

Enter command (LIST, SEARCH, or QUIT): QUIT

OK bye

Closing connection...
Connection closed.
```

