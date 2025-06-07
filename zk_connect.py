import requests
import json
import time
import json
import pandas as pd

from pathlib import Path

from zk import ZK
from datetime import datetime
from collections import defaultdict

from pathlib import Path
# Configuration
PRODUCTION_URL = "https://hrm.boxleocourier.com/api/v1/syncZkteco"  # Your production URL
# response = requests.post(PRODUCTION_URL, data=payload, verify=False)
LOCAL_URL = "http://127.0.0.1:8000/api/v1/syncZkteco"  # Your local testing URL
ZKTECO_IP = "192.168.100.240"
ZKTECO_PORT = 4370
USE_PRODUCTION = False # Set to True when ready to send to production
USE_REAL_DEVICE = True  # Set to True when ready to use actual ZKTeco device
INTERVAL_MINUTES = 1

def log_message(message):
    """Log messages to file with timestamp"""
    with open("/home/engineer/Desktop/ZK/zkteco_debug.log", "a") as f:
        f.write(f"{datetime.now()}: {message}\n")

# def fetch_from_zkteco():
#     """Fetch attendance data from ZKTeco device"""
#     zk = ZK(ZKTECO_IP, port=ZKTECO_PORT, timeout=5)
#     try:
#         log_message("Connecting to ZKTeco device...")
#         conn = zk.connect()
#         conn.disable_device()

#         attendances = conn.get_attendance()
        
#         data = []
#         for record in attendances:
#             data.append({
#                 "user_id": record.user_id,
#                 # "name": record.name,
#                 "time": record.timestamp.strftime("%Y-%m-%d %H:%M:%S")
#             })
#          # Log the attendance data fetched
#         log_message(f"Attendance data: {json.dumps(data)}")    

#         conn.enable_device()
#         conn.disconnect()
        
#         log_message(f"Fetched {len(data)} attendance records from device")
#         return data
        
#     except Exception as e:
#         log_message(f"Error connecting to ZKTeco device: {str(e)}")
#         return None

def fetch_from_zkteco():
    """Fetch and structure attendance data from ZKTeco"""
    zk = ZK(ZKTECO_IP, port=ZKTECO_PORT, timeout=5)
    try:
        log_message("Connecting to ZKTeco device...")
        conn = zk.connect()
        conn.disable_device()

        attendances = conn.get_attendance()
        
        grouped = defaultdict(list)
        for record in attendances:
            user_id = str(record.user_id)
            date_str = record.timestamp.strftime("%Y-%m-%d")
            time_str = record.timestamp.strftime("%H:%M:%S")
            grouped[(user_id, date_str)].append(record.timestamp)

        structured_data = []
        for (user_id, date_str), punches in grouped.items():
            punches.sort()  # chronological order
            clock_in = punches[0].strftime("%H:%M:%S")
            clock_out = punches[-1].strftime("%H:%M:%S")
            final_clock = clock_out
            raw_punches = [p.strftime("%H:%M:%S") for p in punches]
            
            # Build in/out pairs
            in_out_pairs = []
            for i in range(0, len(punches) - 1, 2):
                in_time = punches[i].strftime("%H:%M:%S")
                out_time = punches[i + 1].strftime("%H:%M:%S") if i + 1 < len(punches) else None
                if out_time:
                    in_out_pairs.append({"in": in_time, "out": out_time})

            structured_data.append({
                "user_id": user_id,
                "date": date_str,
                "clock_in": clock_in,
                "clock_out": clock_out,
                "final_clock": final_clock,
                "raw_punches": raw_punches,
                "in_out_pairs": in_out_pairs
            })

        log_message(f"Structured attendance: {json.dumps(structured_data)}")
        
        
        
           # ✅ Save structured data to JSON and Excel for validation
      
        output_dir = Path("attendance_exports")
        output_dir.mkdir(exist_ok=True)

        # Save JSON
        json_path = output_dir / "attendance_data.json"
        with open(json_path, "w") as f:
            json.dump(structured_data, f, indent=4)
        log_message(f"Saved attendance data to JSON: {json_path}")

        # Save Excel
        excel_path = output_dir / "attendance_data.xlsx"
        rows = []
        for record in structured_data:
            for pair in record["in_out_pairs"]:
                rows.append({
                    "User ID": record["user_id"],
                    "Date": record["date"],
                    "Clock In": record["clock_in"],
                    "Clock Out": record["clock_out"],
                    "Final Clock": record["final_clock"],
                    "Raw Punches": ", ".join(record["raw_punches"]),
                    "In Time": pair["in"],
                    "Out Time": pair["out"]
                })
        df = pd.DataFrame(rows)
        df.to_excel(excel_path, index=False)
        log_message(f"Saved attendance data to Excel: {excel_path}")
        
        conn.enable_device()
        conn.disconnect()
        
        return structured_data

    except Exception as e:
        log_message(f"Error connecting to ZKTeco device: {str(e)}")
        return []

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
           {
            "user_id": "3", 
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