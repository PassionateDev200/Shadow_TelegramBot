#!/usr/bin/env python3
"""
Script to view all stored data in the liquidity rebalance bot
"""
import json
import os
from datetime import datetime
from utils.state import load_state, STATE_FILE

def format_pool_data(pool):
    """Format a single pool's data for display"""
    print(f"  📊 Pool: {pool.get('link', 'N/A')}")
    print(f"     Range: {pool.get('range', 'N/A')}")
    print(f"     Token: {pool.get('token', 'N/A')}")
    print(f"     Amount: {pool.get('amount', 'N/A')}")
    print(f"     Owner Chat ID: {pool.get('owner_chat_id', 'N/A')}")
    print(f"     Last Status: {pool.get('last_status', 'N/A')}")
    print(f"     Metadata: {pool.get('meta', {})}")
    print()

def view_all_data():
    """Display all stored data in a readable format"""
    print("=" * 60)
    print("🤖 LIQUIDITY REBALANCE BOT - DATA VIEWER")
    print("=" * 60)
    print()
    
    # Check if state file exists
    if not os.path.exists(STATE_FILE):
        print("❌ No state file found at:", STATE_FILE)
        print("   The bot hasn't saved any data yet.")
        return
    
    # Get file info
    stat_info = os.stat(STATE_FILE)
    file_size = stat_info.st_size
    last_modified = datetime.fromtimestamp(stat_info.st_mtime)
    
    print(f"📂 State file: {STATE_FILE}")
    print(f"📏 File size: {file_size} bytes")
    print(f"⏰ Last modified: {last_modified.strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Load and display data
    try:
        state = load_state()
        
        # Display settings
        print("⚙️  SETTINGS:")
        settings = state.get("settings", {})
        if settings:
            for key, value in settings.items():
                print(f"   {key}: {value}")
        else:
            print("   No settings stored")
        print()
        
        # Display pools
        pools = state.get("pools", [])
        print(f"🏊 POOLS ({len(pools)} total):")
        if pools:
            for i, pool in enumerate(pools, 1):
                print(f"\n  Pool #{i}:")
                format_pool_data(pool)
        else:
            print("   No pools stored")
        
        # Display raw JSON for reference
        print("📄 RAW JSON DATA:")
        print("-" * 40)
        print(json.dumps(state, indent=2))
        
    except Exception as e:
        print(f"❌ Error reading state file: {e}")
        print("   The file might be corrupted.")

def view_logs():
    """Display recent log files"""
    print("\n" + "=" * 60)
    print("📋 RECENT LOG FILES")
    print("=" * 60)
    
    logs_dir = os.path.join(os.path.dirname(__file__), "logs")
    if not os.path.exists(logs_dir):
        print("❌ No logs directory found")
        return
    
    log_files = [f for f in os.listdir(logs_dir) if f.endswith('.log')]
    if not log_files:
        print("❌ No log files found")
        return
    
    # Sort by modification time (newest first)
    log_files.sort(key=lambda f: os.path.getmtime(os.path.join(logs_dir, f)), reverse=True)
    
    for log_file in log_files[:5]:  # Show only last 5 log files
        file_path = os.path.join(logs_dir, log_file)
        stat_info = os.stat(file_path)
        file_size = stat_info.st_size
        last_modified = datetime.fromtimestamp(stat_info.st_mtime)
        
        print(f"📄 {log_file}")
        print(f"   Size: {file_size} bytes")
        print(f"   Modified: {last_modified.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Show last few lines of the log
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                if lines:
                    print(f"   Last few lines:")
                    for line in lines[-3:]:
                        print(f"     {line.strip()}")
        except Exception as e:
            print(f"   Error reading file: {e}")
        print()

if __name__ == "__main__":
    view_all_data()
    view_logs()
