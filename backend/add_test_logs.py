#!/usr/bin/env python3
"""
Script to add test log data to the database for testing the logs filtering functionality.
"""

import asyncio
import asyncpg
import os
from datetime import datetime, timedelta
import random

# Database configuration - adjust these values to match your setup
DB_CONFIG = {
    'host': os.getenv('DB_HOST', '192.168.10.12'),
    'port': int(os.getenv('DB_PORT', 5432)),
    'user': os.getenv('DB_USER', 'netmonitor_user'),
    'password': os.getenv('DB_PASSWORD', 'netmonitor_password'),
    'database': os.getenv('DB_NAME', 'netmonitor_db')
}

# Test log data
TEST_LOGS = [
    # WiFi/Network logs
    {'process_name': 'hostapd', 'log_level': 'INFO', 'message': 'wlan0: STA 00:11:22:33:44:55 IEEE 802.11: authenticated'},
    {'process_name': 'hostapd', 'log_level': 'INFO', 'message': 'wlan0: STA 00:11:22:33:44:55 IEEE 802.11: associated'},
    {'process_name': 'hostapd', 'log_level': 'WARNING', 'message': 'wlan0: STA 00:11:22:33:44:55 IEEE 802.11: disassociated'},
    {'process_name': 'hostapd', 'log_level': 'ERROR', 'message': 'wlan0: STA 00:11:22:33:44:55 IEEE 802.11: deauthenticated'},
    {'process_name': 'hostapd', 'log_level': 'CRITICAL', 'message': 'wlan0: Authentication failure - possible attack'},
    
    # System logs
    {'process_name': 'systemd', 'log_level': 'INFO', 'message': 'Started Network Manager'},
    {'process_name': 'systemd', 'log_level': 'WARNING', 'message': 'High memory usage detected'},
    {'process_name': 'systemd', 'log_level': 'ERROR', 'message': 'Service nginx failed to start'},
    {'process_name': 'systemd', 'log_level': 'CRITICAL', 'message': 'System running out of disk space'},
    
    # Web server logs
    {'process_name': 'nginx', 'log_level': 'INFO', 'message': 'GET /api/v1/health 200'},
    {'process_name': 'nginx', 'log_level': 'WARNING', 'message': 'High number of 404 errors'},
    {'process_name': 'nginx', 'log_level': 'ERROR', 'message': 'Connection timeout to upstream server'},
    {'process_name': 'nginx', 'log_level': 'CRITICAL', 'message': 'Server overloaded - too many connections'},
    
    # Database logs
    {'process_name': 'postgresql', 'log_level': 'INFO', 'message': 'Database connection established'},
    {'process_name': 'postgresql', 'log_level': 'WARNING', 'message': 'Slow query detected'},
    {'process_name': 'postgresql', 'log_level': 'ERROR', 'message': 'Connection pool exhausted'},
    {'process_name': 'postgresql', 'log_level': 'CRITICAL', 'message': 'Database corruption detected'},
    
    # Security logs
    {'process_name': 'sshd', 'log_level': 'INFO', 'message': 'Accepted password for user admin'},
    {'process_name': 'sshd', 'log_level': 'WARNING', 'message': 'Failed password for user admin'},
    {'process_name': 'sshd', 'log_level': 'ERROR', 'message': 'Too many authentication failures'},
    {'process_name': 'sshd', 'log_level': 'CRITICAL', 'message': 'Brute force attack detected'},
    
    # Application logs
    {'process_name': 'mcp_service', 'log_level': 'INFO', 'message': 'Agent WiFiAgent started successfully'},
    {'process_name': 'mcp_service', 'log_level': 'WARNING', 'message': 'Model performance degradation detected'},
    {'process_name': 'mcp_service', 'log_level': 'ERROR', 'message': 'Failed to connect to Redis'},
    {'process_name': 'mcp_service', 'log_level': 'CRITICAL', 'message': 'System critical failure - shutting down'},
    
    # Firewall logs
    {'process_name': 'iptables', 'log_level': 'INFO', 'message': 'Packet accepted from 192.168.1.100'},
    {'process_name': 'iptables', 'log_level': 'WARNING', 'message': 'Suspicious traffic from 10.0.0.50'},
    {'process_name': 'iptables', 'log_level': 'ERROR', 'message': 'Firewall rule violation'},
    {'process_name': 'iptables', 'log_level': 'CRITICAL', 'message': 'DDoS attack detected - blocking IP range'},
]

async def add_test_logs():
    """Add test log entries to the database."""
    try:
        # Connect to the database
        conn = await asyncpg.connect(**DB_CONFIG)
        
        print("Connected to database successfully")
        
        # Check if log_entries table exists
        table_exists = await conn.fetchval(
            "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'log_entries')"
        )
        
        if not table_exists:
            print("Creating log_entries table...")
            await conn.execute("""
                CREATE TABLE log_entries (
                    id SERIAL PRIMARY KEY,
                    device_id VARCHAR(50),
                    device_ip VARCHAR(45),
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    log_level VARCHAR(20),
                    process_name VARCHAR(100),
                    message TEXT,
                    raw_message TEXT,
                    structured_data JSONB,
                    pushed_to_ai BOOLEAN DEFAULT FALSE,
                    pushed_at TIMESTAMP,
                    push_attempts INTEGER DEFAULT 0,
                    last_push_error TEXT
                )
            """)
            print("log_entries table created")
        
        # Generate timestamps for the last 24 hours
        now = datetime.now()
        timestamps = []
        for i in range(len(TEST_LOGS)):
            # Spread logs over the last 24 hours
            hours_ago = random.uniform(0, 24)
            timestamp = now - timedelta(hours=hours_ago)
            timestamps.append(timestamp)
        
        # Insert test logs
        print(f"Inserting {len(TEST_LOGS)} test log entries...")
        
        for i, log_data in enumerate(TEST_LOGS):
            await conn.execute("""
                INSERT INTO log_entries (
                    device_id, device_ip, timestamp, log_level, process_name, 
                    message, raw_message, structured_data, pushed_to_ai
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            """, 
            f"device_{random.randint(1, 5)}",  # device_id
            f"192.168.1.{random.randint(1, 254)}",  # device_ip
            timestamps[i],  # timestamp
            log_data['log_level'],  # log_level
            log_data['process_name'],  # process_name
            log_data['message'],  # message
            log_data['message'],  # raw_message (same as message for simplicity)
            {},  # structured_data (empty JSON object)
            False  # pushed_to_ai
            )
        
        # Verify the data was inserted
        count = await conn.fetchval("SELECT COUNT(*) FROM log_entries")
        print(f"Successfully inserted test logs. Total log entries: {count}")
        
        # Show some sample data
        sample_logs = await conn.fetch("""
            SELECT process_name, log_level, message, timestamp 
            FROM log_entries 
            ORDER BY timestamp DESC 
            LIMIT 5
        """)
        
        print("\nSample log entries:")
        for log in sample_logs:
            print(f"  {log['timestamp']} [{log['log_level']}] {log['process_name']}: {log['message']}")
        
        await conn.close()
        print("\nTest logs added successfully!")
        
    except Exception as e:
        print(f"Error adding test logs: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(add_test_logs()) 