import requests
import json
import time
from zk import ZK
from datetime import datetime

# Configuration
PRODUCTION_URL = "https://hrm.boxleocourier.com/api/v1/syncZkteco"  # Your production URL
LOCAL_URL = "http://127.0.0.1:8000/api/v1/syncZkteco"  # Your local testing URL
ZKTECO_IP = "192.168.100.240"
ZKTECO_PORT = 4370
USE_PRODUCTION = True # Set to True when ready to send to production
USE_REAL_DEVICE = False  # Set to True when ready to use actual ZKTeco device
INTERVAL_MINUTES = 1

def log_message(message):
    """Log messages to file with timestamp"""
    with open("/home/engineer/Desktop/ZK/zkteco_debug.log", "a") as f:
        f.write(f"{datetime.now()}: {message}\n")

def fetch_from_zkteco():
    """Fetch attendance data from ZKTeco device"""
    zk = ZK(ZKTECO_IP, port=ZKTECO_PORT, timeout=5)
    try:
        log_message("Connecting to ZKTeco device...")
        conn = zk.connect()
        conn.disable_device()

        attendances = conn.get_attendance()
        
        data = []
        for record in attendances:
            data.append({
                "user_id": record.user_id,
                "name": record.name,
                "time": record.timestamp.strftime("%Y-%m-%d %H:%M:%S")
            })

        conn.enable_device()
        conn.disconnect()
        
        log_message(f"Fetched {len(data)} attendance records from device")
        return data
        
    except Exception as e:
        log_message(f"Error connecting to ZKTeco device: {str(e)}")
        return None

def get_test_data():
    """Get test data for development"""
    now = datetime.now()  # Define 'now' before using it

    return [
        {
            "user_id": "1",
            "name": "Raven Dudley",
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        },
        {
            "user_id": "2", 
            "name": "John Doe",
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        },
        
         {
            "user_id": "2", 
            "name": "John Doe",
            "time": (now.replace(hour=9, minute=0)).strftime("%Y-%m-%d %H:%M:%S")
        },
        {
            "user_id": "2", 
            "name": "John Doe",
            "time": (now.replace(hour=18, minute=0)).strftime("%Y-%m-%d %H:%M:%S")
        },
    ]

def send_to_server(data, url):
    """Send data to server"""
    try:
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        response = requests.post(url, json={"records": data}, headers=headers, timeout=30)
        
        log_message(f"Server response: {response.status_code} - {response.text}")
        return response.status_code == 200
        
    except requests.exceptions.RequestException as e:
        log_message(f"Request failed: {str(e)}")
        return False

def fetch_and_send():
    """Main function to fetch and send attendance data"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"\n[{timestamp}] Starting sync process...")
    
    # Determine data source
    if USE_REAL_DEVICE:
        print("Fetching data from ZKTeco device...")
        data = fetch_from_zkteco()
        if data is None:
            print("Failed to fetch from device, skipping this cycle")
            return
    else:
        print("Using test data...")
        data = get_test_data()
    
    if not data:
        print("No data to send")
        log_message("No attendance data to process")
        return
    
    print(f"Preparing to send {len(data)} records...")
    
    # Determine target URL
    target_url = PRODUCTION_URL if USE_PRODUCTION else LOCAL_URL
    server_type = "PRODUCTION" if USE_PRODUCTION else "LOCAL"
    
    print(f"Sending to {server_type} server: {target_url}")
    
    # Send data
    success = send_to_server(data, target_url)
    
    if success:
        print("✅ Data sent successfully!")
        log_message(f"Successfully sent {len(data)} records to {server_type}")
    else:
        print("❌ Failed to send data")
        log_message(f"Failed to send data to {server_type}")

def main():
    """Main execution function"""
    log_message("=" * 50)
    log_message("ZKTeco Sync Service Started")
    log_message(f"Configuration:")
    log_message(f"  - Production Mode: {USE_PRODUCTION}")
    log_message(f"  - Real Device: {USE_REAL_DEVICE}")
    log_message(f"  - Interval: {INTERVAL_MINUTES} minutes")
    log_message(f"  - Target URL: {PRODUCTION_URL if USE_PRODUCTION else LOCAL_URL}")
    log_message("=" * 50)
    
    print("🚀 ZKTeco Sync Service Starting...")
    print(f"📊 Configuration:")
    print(f"   • Mode: {'PRODUCTION' if USE_PRODUCTION else 'DEVELOPMENT'}")
    print(f"   • Data Source: {'ZKTeco Device' if USE_REAL_DEVICE else 'Test Data'}")
    print(f"   • Interval: {INTERVAL_MINUTES} minutes")
    print(f"   • Target: {PRODUCTION_URL if USE_PRODUCTION else LOCAL_URL}")
    print(f"⏰ Running every {INTERVAL_MINUTES} minutes. Press Ctrl+C to stop.\n")
    
    try:
        while True:
            fetch_and_send()
            print(f"⏳ Waiting {INTERVAL_MINUTES} minutes before next sync...")
            time.sleep(INTERVAL_MINUTES * 60)  # Convert minutes to seconds
            
    except KeyboardInterrupt:
        print("\n🛑 Service stopped by user")
        log_message("Service stopped by user")
    except Exception as e:
        print(f"\n💥 Unexpected error: {str(e)}")
        log_message(f"Unexpected error: {str(e)}")

if __name__ == "__main__":
    main()