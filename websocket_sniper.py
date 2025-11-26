import websocket
import json
import requests
import hmac
import hashlib
import urllib.parse
import time
import threading
import os
import sys
from datetime import datetime

# Render.com loads from environment variables
API_KEY = os.environ.get('MEXC_API_KEY')
SECRET_KEY = os.environ.get('MEXC_SECRET_KEY')
BASE_URL = 'https://api.mexc.com'

# Global variables
SNIPE_LIST = {}
active_orders = {}
ws_connected = False

def log(message):
    """Render-optimized logging"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")
    sys.stdout.flush()  # Critical for Render logs

def load_snipe_list():
    """Load snipe list from file"""
    global SNIPE_LIST
    try:
        if os.path.exists('snipe_config.json'):
            with open('snipe_config.json', 'r') as f:
                SNIPE_LIST = json.load(f)
                log(f"📁 Loaded {len(SNIPE_LIST)} tokens from config")
        else:
            log("⚠️  snipe_config.json not found - creating default")
            # Create default config
            default_config = {"NSGUSDT": 2.0}
            with open('snipe_config.json', 'w') as f:
                json.dump(default_config, f, indent=2)
            SNIPE_LIST = default_config
            log("✅ Created default snipe_config.json")
    except Exception as e:
        log(f"❌ Error loading config: {e}")

def save_snipe_list():
    """Save snipe list to file"""
    try:
        with open('snipe_config.json', 'w') as f:
            json.dump(SNIPE_LIST, f, indent=2)
    except Exception as e:
        log(f"❌ Error saving config: {e}")

def place_market_order(symbol, quantity):
    """Market order placement with Render optimizations"""
    try:
        log(f"🚀 EXECUTING SNIPE: {symbol} for {quantity} USDT")
        
        endpoint = '/api/v3/order'
        timestamp = int(time.time() * 1000)
        
        params = {
            'symbol': symbol,
            'side': 'BUY',
            'type': 'MARKET',
            'quoteOrderQty': quantity,
            'timestamp': timestamp
        }
        
        # Create signature
        query_string = urllib.parse.urlencode(params)
        signature = hmac.new(SECRET_KEY.encode('utf-8'), query_string.encode('utf-8'), hashlib.sha256).hexdigest()
        params['signature'] = signature
        
        headers = {'X-MEXC-APIKEY': API_KEY}
        
        # Render-optimized timeout
        url = BASE_URL + endpoint
        response = requests.post(url, params=params, headers=headers, timeout=10)
        result = response.json()
        
        if 'orderId' in result:
            log(f"🎉 SNIPE SUCCESS! {symbol} - Order ID: {result['orderId']}")
            return True
        else:
            log(f"💥 SNIPE FAILED! {symbol} - Error: {result.get('msg', 'Unknown error')}")
            return False
            
    except Exception as e:
        log(f"🔥 ORDER ERROR {symbol}: {e}")
        return False

def on_message(ws, message):
    """WebSocket message handler"""
    global active_orders
    
    try:
        data = json.loads(message)
        
        # Check if this is a 24hr ticker stream
        if 'stream' in data and '24hrTicker' in data['stream']:
            stream_data = data['data']
            symbol = stream_data['s']  # Symbol like 'ABCUSDT'
            
            # Check if this is a token we want to snipe
            if symbol in SNIPE_LIST and symbol not in active_orders:
                # Check if trading has actually started (price > 0)
                if float(stream_data.get('c', 0)) > 0:
                    log(f"🎯 DETECTED TRADING START: {symbol}")
                    log(f"   Price: {stream_data.get('c')}")
                    log(f"   Volume: {stream_data.get('v')}")
                    
                    # MARK AS ACTIVE IMMEDIATELY to prevent duplicate orders
                    active_orders[symbol] = 'executing'
                    
                    # EXECUTE SNIPE IMMEDIATELY
                    amount = SNIPE_LIST[symbol]
                    success = place_market_order(symbol, amount)
                    
                    if success:
                        active_orders[symbol] = 'completed'
                        # Remove from snipe list after successful buy
                        del SNIPE_LIST[symbol]
                        save_snipe_list()
                        log(f"✅ Removed {symbol} from monitoring list")
                    else:
                        active_orders[symbol] = 'failed'
                        log(f"❌ Failed to buy {symbol}, will not retry")
        
    except Exception as e:
        log(f"WebSocket message error: {e}")

def on_error(ws, error):
    log(f"WebSocket error: {error}")

def on_close(ws, close_status_code, close_msg):
    global ws_connected
    ws_connected = False
    log("🔴 WebSocket connection closed")
    log(f"Close code: {close_status_code}, Message: {close_msg}")

def on_open(ws):
    global ws_connected
    ws_connected = True
    log("🟢 WebSocket connected successfully!")
    
    # Subscribe to 24hr ticker for ALL tokens in our snipe list
    streams = [f"{symbol.lower()}@24hrTicker" for symbol in SNIPE_LIST.keys()]
    
    if streams:
        subscribe_message = {
            "method": "SUBSCRIPTION",
            "params": streams
        }
        ws.send(json.dumps(subscribe_message))
        log(f"📡 Subscribed to {len(streams)} tokens for instant detection")
    else:
        log("⚠️  No tokens to monitor - add tokens to snipe_config.json")
    
    log("🎯 ACTIVE SNIPE TARGETS:")
    for symbol, amount in SNIPE_LIST.items():
        log(f"   {symbol}: {amount} USDT")
    log("⏳ Waiting for trading to start...")

def start_websocket():
    """Start WebSocket with Render optimizations"""
    websocket.enableTrace(False)
    
    ws_url = "wss://wbs.mexc.com/ws"
    
    ws = websocket.WebSocketApp(
        ws_url,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close,
        on_open=on_open
    )
    
    def run_forever():
        while True:
            try:
                log("🔄 Starting WebSocket connection...")
                ws.run_forever()
            except Exception as e:
                log(f"WebSocket crashed: {e}. Reconnecting in 10 seconds...")
                time.sleep(10)
    
    ws_thread = threading.Thread(target=run_forever, daemon=True)
    ws_thread.start()
    
    return ws

def main():
    """Main function optimized for Render.com"""
    log("🤖 MEXC ULTIMATE WEBSOCKET SNIPER BOT")
    log("🚀 RENDER.COM EDITION - Running 24/7 in Cloud")
    log("=" * 50)
    
    # Check environment variables
    if not API_KEY or not SECRET_KEY:
        log("❌ ERROR: MEXC_API_KEY and MEXC_SECRET_KEY environment variables not set!")
        log("💡 On Render.com: Go to Settings → Environment Variables")
        log("💡 Add: MEXC_API_KEY and MEXC_SECRET_KEY")
        return
    
    log("✅ API keys loaded successfully from environment")
    
    # Load snipe list
    load_snipe_list()
    
    if not SNIPE_LIST:
        log("⚠️  No tokens in snipe list! Bot is running but not monitoring anything.")
        log("💡 Add tokens by editing snipe_config.json file")
    else:
        log(f"🎯 Loaded {len(SNIPE_LIST)} snipe targets")
    
    log("🚀 Starting WebSocket sniper monitoring...")
    log("💚 Bot will run 24/7 and auto-restart if needed")
    
    # Start WebSocket
    start_websocket()
    
    # Keep main thread alive forever with heartbeat
    heartbeat_count = 0
    while True:
        time.sleep(60)
        heartbeat_count += 1
        log(f"💓 Bot heartbeat #{heartbeat_count} - Still monitoring {len(SNIPE_LIST)} tokens")

if __name__ == "__main__":
    main()