import time
import os
import wifi
import socketpool
import adafruit_requests
import rgbmatrix
import framebufferio
import displayio
import terminalio
from adafruit_display_text import label
import microcontroller
import json
import random

# ==============================================================================
# 1. DISPLAY INITIALIZATION
# ==============================================================================
displayio.release_displays()

# Read configurations from settings.toml
r1 = getattr(board, f"GP{os.getenv('PIN_R1', 2)}") if 'board' in globals() else None
# Wait, board needs to be imported!
import board

# Helper to fetch board pin objects dynamically from settings.toml
def get_pin(name, default):
    pin_num = os.getenv(name, default)
    return getattr(board, f"GP{pin_num}")

# Setup HUB75 Matrix pins
try:
    matrix = rgbmatrix.RGBMatrix(
        width=64,
        height=32,
        bit_depth=3,
        rgb_pins=[
            get_pin("PIN_R1", 2),
            get_pin("PIN_G1", 3),
            get_pin("PIN_B1", 6),
            get_pin("PIN_R2", 7),
            get_pin("PIN_G2", 8),
            get_pin("PIN_B2", 9),
        ],
        addr_pins=[
            get_pin("PIN_A", 10),
            get_pin("PIN_B", 11),
            get_pin("PIN_C", 12),
            get_pin("PIN_D", 13),
        ],
        clock_pin=get_pin("PIN_CLK", 14),
        latch_pin=get_pin("PIN_LAT", 15),
        output_enable_pin=get_pin("PIN_OE", 16)
    )
    display = framebufferio.FramebufferDisplay(matrix, rotation=0)
except Exception as e:
    print("Failed to initialize display. Check wiring and pin configurations:", e)
    # Fallback dummy display or print error
    display = None

# Create the display group and label
group = displayio.Group()
text_area = label.Label(
    terminalio.FONT,
    text="Booting...",
    color=0x00FF00, # Green
)
text_area.anchor_point = (0.0, 0.5)
text_area.anchored_position = (0, 16) # Centered vertically
group.append(text_area)

if display:
    display.root_group = group

# ==============================================================================
# 2. SCROLLING ENGINE
# ==============================================================================
def scroll_text(text, color=0xFFFFFF, speed=0.02):
    """Scrolls text smoothly from right to left across the matrix screen."""
    print("Scrolling:", text)
    text_area.text = text
    text_area.color = color
    
    # Start text fully off-screen to the right (x=64)
    x = 64
    text_area.anchored_position = (x, 16)
    
    # Bounding box width
    width = text_area.width
    
    # Scroll until the end of the text passes off-screen to the left
    while x > -width:
        x -= 1
        text_area.anchored_position = (x, 16)
        time.sleep(speed)

# Show boot message
scroll_text("Connecting WiFi...", color=0x00FFFF)

# ==============================================================================
# 3. WIFI CONNECTIVITY
# ==============================================================================
wifi_ssid = os.getenv("CIRCUITPY_WIFI_SSID")
wifi_pw = os.getenv("CIRCUITPY_WIFI_PASSWORD")

connected = False
try:
    if wifi_ssid and wifi_pw and wifi_ssid != "YOUR_WIFI_SSID":
        wifi.radio.connect(wifi_ssid, wifi_pw)
        print("Connected to Wi-Fi. IP:", wifi.radio.ipv4_address)
        connected = True
        scroll_text(f"Connected! IP: {wifi.radio.ipv4_address}", color=0x00FF00)
    else:
        print("WiFi Credentials not set in settings.toml")
        scroll_text("WiFi Not Configured", color=0xFF0000)
except Exception as e:
    print("WiFi Connection failed:", e)
    scroll_text("WiFi Conn Failed", color=0xFF0000)

# Create request session if connected
pool = socketpool.SocketPool(wifi.radio)
requests = adafruit_requests.Session(pool) if connected else None

# ==============================================================================
# 4. FILESYSTEM & OTA UPDATES
# ==============================================================================
# Check if write permissions are enabled on the Pico filesystem (GP22 open)
filesystem_writeable = False
try:
    with open("write_check.tmp", "w") as f:
        f.write("OK")
    os.remove("write_check.tmp")
    filesystem_writeable = True
    print("Filesystem is writeable by Pico W.")
except OSError:
    print("Filesystem is READ-ONLY to Pico W (GP22 is likely grounded). OTA updates disabled.")

def check_ota_updates():
    """Checks GitHub for updates, downloads files, and restarts if code changed."""
    if not connected or not filesystem_writeable:
        return False
    
    username = os.getenv("GITHUB_USERNAME")
    repo = os.getenv("GITHUB_REPO")
    branch = os.getenv("GITHUB_BRANCH", "main")
    
    if not username or username == "your_github_username":
        print("GitHub configuration not set in settings.toml. Skipping OTA.")
        return False
    
    base_url = f"https://raw.githubusercontent.com/{username}/{repo}/{branch}"
    scroll_text("Checking OTA...", color=0xFFFF00)
    
    try:
        # Fetch GitHub version.json
        print("Fetching remote version.json...")
        res = requests.get(f"{base_url}/version.json")
        if res.status_code != 200:
            print("Failed to fetch remote version.json. Status:", res.status_code)
            return False
            
        remote_data = res.json()
        remote_ver = remote_data.get("version", 0.0)
        
        # Load local version.json
        local_ver = 0.0
        try:
            with open("version.json", "r") as f:
                local_data = json.load(f)
                local_ver = local_data.get("version", 0.0)
        except Exception:
            pass # Keep 0.0 if file is missing
            
        print(f"Local version: {local_ver} | Remote version: {remote_ver}")
        
        if remote_ver > local_ver:
            scroll_text(f"Updating v{local_ver} -> v{remote_ver}...", color=0x00FFFF)
            
            # Download new files
            for file_name in ["code.py", "quotes.json", "version.json", "config.json"]:
                print(f"Downloading {file_name}...")
                file_res = requests.get(f"{base_url}/{file_name}")
                if file_res.status_code == 200:
                    temp_path = f"{file_name}.tmp"
                    with open(temp_path, "w") as f:
                        f.write(file_res.text)
                else:
                    raise Exception(f"Failed download for {file_name}")
            
            # Atomic swap
            for file_name in ["code.py", "quotes.json", "version.json", "config.json"]:
                try:
                    os.remove(file_name)
                except OSError:
                    pass
                os.rename(f"{file_name}.tmp", file_name)
            
            scroll_text("Update complete! Rebooting...", color=0x00FF00)
            time.sleep(1)
            microcontroller.reset()
            return True
        else:
            print("System is up to date.")
            scroll_text("System up-to-date", color=0x00FF00)
            
    except Exception as e:
        print("OTA error:", e)
        scroll_text("OTA Update Error", color=0xFF0000)
    return False

# Run initial check at boot
check_ota_updates()

# ==============================================================================
# 5. DATA FETCHING METHODS
# ==============================================================================
def get_config_val(key, default=None):
    """Reads a configuration value from config.json, falling back to settings.toml (os.getenv)."""
    try:
        with open("config.json", "r") as f:
            data = json.load(f)
            if key in data:
                return data[key]
    except Exception:
        pass
    
    # Fallback to settings.toml (environment variable in uppercase)
    val = os.getenv(key.upper())
    if val is not None:
        return val
    return default

def fetch_railway_keys():
    """Fetches key counts from custom Railway backend PostgreSQL proxy."""
    if not connected:
        return "Offline"
    
    url = get_config_val("railway_api_url")
    if not url or "your-railway-app" in url:
        return "Railway Config Err"
        
    try:
        print("Fetching Railway count...")
        res = requests.get(url)
        if res.status_code == 200:
            count = res.json().get("count", 0)
            return f"Distinct Keys: {count}"
        return f"Railway HTTP {res.status_code}"
    except Exception as e:
        print("Railway DB fetch error:", e)
        return "Railway DB Error"

def fetch_stock_prices():
    """Fetches live stock quotes from Yahoo Finance charts API (No API key needed)."""
    if not connected:
        return "Offline"
        
    tickers = get_config_val("stock_tickers", "AAPL,MSFT").split(",")
    results = []
    headers = {"User-Agent": "Mozilla/5.0"}
    
    for ticker in tickers:
        ticker = ticker.strip()
        if not ticker:
            continue
        try:
            print(f"Fetching stock: {ticker}...")
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?interval=1d&range=1d"
            res = requests.get(url, headers=headers)
            if res.status_code == 200:
                data = res.json()
                meta = data["chart"]["result"][0]["meta"]
                price = meta["regularMarketPrice"]
                prev_close = meta["chartPreviousClose"]
                change = price - prev_close
                pct = (change / prev_close) * 100
                sign = "+" if change >= 0 else ""
                results.append(f"{ticker}: ${price:.2f} ({sign}{pct:.2f}%)")
            else:
                results.append(f"{ticker}: Err {res.status_code}")
        except Exception as e:
            print(f"Stock {ticker} fetch error:", e)
            results.append(f"{ticker}: Error")
        time.sleep(0.5) # Avoid hammering
        
    return " | ".join(results)

def get_random_quote():
    """Fetches a random quote from the local quotes.json database file."""
    try:
        with open("quotes.json", "r") as f:
            quotes = json.load(f)
        q = random.choice(quotes)
        return f"\"{q['text']}\" - {q['author']}"
    except Exception as e:
        print("Quote loading error:", e)
        return "Keep coding, keep building! - Pico W"

# ==============================================================================
# 6. MAIN APPLICATION LOOP
# ==============================================================================
cycle_count = 0

while True:
    print(f"--- Starting Display Cycle #{cycle_count} ---")
    
    # 1. Fetch data
    db_text = fetch_railway_keys()
    stock_text = fetch_stock_prices()
    quote_text = get_random_quote()
    
    # 2. Scroll the gathered data
    scroll_text(db_text, color=0x00FFFF)      # Cyan for database keys count
    scroll_text(stock_text, color=0xFFFF00)   # Yellow for stocks
    scroll_text(quote_text, color=0xFFFFFF)    # White for quotes
    
    cycle_count += 1
    
    # Check for updates and refresh Wi-Fi data every 10 cycles (approx 5-10 minutes)
    if cycle_count % 10 == 0:
        check_ota_updates()
        
    time.sleep(1)
