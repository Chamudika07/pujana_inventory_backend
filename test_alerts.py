#!/usr/bin/env python3
"""
Test script for Low Stock Alert System
Run this after setup to verify everything works
"""

import requests
import json
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8000"
TEST_EMAIL = "test@example.com"
TEST_PASSWORD = "test123456"
TEST_PHONE = "+919876543210"
TEST_ALERT_EMAIL = "alerts@example.com"

# Global token storage
TOKEN = None

def print_section(title):
    """Print a formatted section header"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")

def print_result(status, message):
    """Print result with status indicator"""
    indicator = "✅" if status else "❌"
    print(f"{indicator} {message}")

def test_1_user_registration():
    """Test 1: User Registration"""
    print_section("TEST 1: User Registration")
    
    try:
        response = requests.post(
            f"{BASE_URL}/users/register",
            json={
                "email": TEST_EMAIL,
                "password": TEST_PASSWORD
            }
        )
        
        if response.status_code == 201:
            data = response.json()
            print_result(True, f"User registered: {data['email']}")
            return True
        else:
            print_result(False, f"Registration failed: {response.text}")
            return False
    except Exception as e:
        print_result(False, f"Error: {str(e)}")
        return False

def test_2_user_login():
    """Test 2: User Login"""
    print_section("TEST 2: User Login")
    
    global TOKEN
    
    try:
        response = requests.post(
            f"{BASE_URL}/users/login",
            data={
                "username": TEST_EMAIL,
                "password": TEST_PASSWORD
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            TOKEN = data['access_token']
            print_result(True, f"Login successful. Token: {TOKEN[:20]}...")
            return True
        else:
            print_result(False, f"Login failed: {response.text}")
            return False
    except Exception as e:
        print_result(False, f"Error: {str(e)}")
        return False

def test_3_update_preferences():
    """Test 3: Update Alert Preferences"""
    print_section("TEST 3: Update Alert Preferences")
    
    try:
        response = requests.put(
            f"{BASE_URL}/alerts/preferences/update",
            headers={"Authorization": f"Bearer {TOKEN}"},
            json={
                "phone_number": TEST_PHONE,
                "notification_email": TEST_ALERT_EMAIL,
                "notification_enabled": True,
                "alert_threshold": 5
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            print_result(True, "Preferences updated")
            print(f"  Phone: {data['phone_number']}")
            print(f"  Email: {data['notification_email']}")
            print(f"  Threshold: {data['alert_threshold']}")
            return True
        else:
            print_result(False, f"Update failed: {response.text}")
            return False
    except Exception as e:
        print_result(False, f"Error: {str(e)}")
        return False

def test_4_get_preferences():
    """Test 4: Get Alert Preferences"""
    print_section("TEST 4: Get Alert Preferences")
    
    try:
        response = requests.get(
            f"{BASE_URL}/alerts/preferences/get",
            headers={"Authorization": f"Bearer {TOKEN}"}
        )
        
        if response.status_code == 200:
            data = response.json()
            print_result(True, "Preferences retrieved")
            print(f"  Phone: {data['phone_number']}")
            print(f"  Email: {data['notification_email']}")
            print(f"  Enabled: {data['notification_enabled']}")
            print(f"  Threshold: {data['alert_threshold']}")
            return True
        else:
            print_result(False, f"Failed: {response.text}")
            return False
    except Exception as e:
        print_result(False, f"Error: {str(e)}")
        return False

def test_5_create_category():
    """Test 5: Create Category"""
    print_section("TEST 5: Create Category")
    
    global CATEGORY_ID
    
    try:
        response = requests.post(
            f"{BASE_URL}/categories/",
            headers={"Authorization": f"Bearer {TOKEN}"},
            json={"name": "Test Category"}
        )
        
        if response.status_code == 201:
            data = response.json()
            CATEGORY_ID = data['id']
            print_result(True, f"Category created: {data['name']} (ID: {CATEGORY_ID})")
            return True
        else:
            print_result(False, f"Failed: {response.text}")
            return False
    except Exception as e:
        print_result(False, f"Error: {str(e)}")
        return False

def test_6_create_item():
    """Test 6: Create Item"""
    print_section("TEST 6: Create Item")
    
    global ITEM_ID
    
    try:
        response = requests.post(
            f"{BASE_URL}/items/",
            headers={"Authorization": f"Bearer {TOKEN}"},
            json={
                "name": "Test Resistor 1K",
                "quantity": 100,
                "buying_price": 0.50,
                "selling_price": 1.00,
                "description": "1K Ohm Resistor",
                "model_number": "RES-1K",
                "category_id": CATEGORY_ID
            }
        )
        
        if response.status_code == 201:
            data = response.json()
            ITEM_ID = data['id']
            print_result(True, f"Item created: {data['name']} (ID: {ITEM_ID})")
            print(f"  Quantity: {data['quantity']}")
            return True
        else:
            print_result(False, f"Failed: {response.text}")
            return False
    except Exception as e:
        print_result(False, f"Error: {str(e)}")
        return False

def test_7_trigger_low_stock_alert():
    """Test 7: Trigger Low Stock Alert by Updating Quantity"""
    print_section("TEST 7: Trigger Low Stock Alert")
    
    print("Updating item quantity from 100 to 3 (below threshold of 5)...")
    print("This should trigger email and WhatsApp notifications!")
    print()
    
    try:
        response = requests.put(
            f"{BASE_URL}/items/{ITEM_ID}",
            headers={"Authorization": f"Bearer {TOKEN}"},
            json={
                "name": "Test Resistor 1K",
                "quantity": 3,  # Below threshold of 5!
                "buying_price": 0.50,
                "selling_price": 1.00,
                "description": "1K Ohm Resistor",
                "model_number": "RES-1K",
                "category_id": CATEGORY_ID
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            print_result(True, f"Item updated successfully")
            print(f"  New Quantity: {data['quantity']}")
            print()
            print("📧 Email should be sent to:", TEST_ALERT_EMAIL)
            print("💬 WhatsApp should be sent to:", TEST_PHONE)
            print()
            print("⏳ Waiting 5 seconds for notifications to be sent...")
            import time
            time.sleep(5)
            return True
        else:
            print_result(False, f"Failed: {response.text}")
            return False
    except Exception as e:
        print_result(False, f"Error: {str(e)}")
        return False

def test_8_get_alerts():
    """Test 8: Get Alerts"""
    print_section("TEST 8: Get Alerts")
    
    try:
        response = requests.get(
            f"{BASE_URL}/alerts/",
            headers={"Authorization": f"Bearer {TOKEN}"}
        )
        
        if response.status_code == 200:
            data = response.json()
            print_result(True, f"Alerts retrieved: {len(data)} alert(s)")
            
            if len(data) > 0:
                for alert in data:
                    print(f"\n  Alert ID: {alert['id']}")
                    print(f"  Item: {alert['item']['name']}")
                    print(f"  Quantity: {alert['quantity_at_alert']}")
                    print(f"  Type: {alert['alert_type']}")
                    print(f"  Resolved: {alert['is_resolved']}")
                    print(f"  Created: {alert['created_at']}")
            return True
        else:
            print_result(False, f"Failed: {response.text}")
            return False
    except Exception as e:
        print_result(False, f"Error: {str(e)}")
        return False

def test_9_get_alert_stats():
    """Test 9: Get Alert Statistics"""
    print_section("TEST 9: Get Alert Statistics")
    
    try:
        response = requests.get(
            f"{BASE_URL}/alerts/stats",
            headers={"Authorization": f"Bearer {TOKEN}"}
        )
        
        if response.status_code == 200:
            data = response.json()
            print_result(True, "Statistics retrieved")
            print(f"  Total Alerts: {data['total_alerts']}")
            print(f"  Active Alerts: {data['active_alerts']}")
            print(f"  Resolved Alerts: {data['resolved_alerts']}")
            print(f"  Low Stock Items: {data['low_stock_items']}")
            return True
        else:
            print_result(False, f"Failed: {response.text}")
            return False
    except Exception as e:
        print_result(False, f"Error: {str(e)}")
        return False

def test_10_trigger_check():
    """Test 10: Manual Trigger Low Stock Check"""
    print_section("TEST 10: Manual Trigger Low Stock Check")
    
    try:
        response = requests.post(
            f"{BASE_URL}/alerts/trigger-check",
            headers={"Authorization": f"Bearer {TOKEN}"}
        )
        
        if response.status_code == 200:
            data = response.json()
            print_result(True, "Check triggered successfully")
            print(f"  Items Checked: {data['items_checked']}")
            print(f"  Alerts Sent: {data['alerts_sent']}")
            return True
        else:
            print_result(False, f"Failed: {response.text}")
            return False
    except Exception as e:
        print_result(False, f"Error: {str(e)}")
        return False

def main():
    """Run all tests"""
    print("""
    ╔═══════════════════════════════════════════════════════════╗
    ║   Low Stock Alert System - Test Suite                    ║
    ║                                                           ║
    ║   This script tests all functionality of the alert       ║
    ║   system. Make sure the FastAPI server is running!       ║
    ║                                                           ║
    ║   Run: uvicorn app.main:app --reload                    ║
    ╚═══════════════════════════════════════════════════════════╝
    """)
    
    input("Press Enter to start tests...")
    
    results = {
        "Test 1: Registration": test_1_user_registration(),
        "Test 2: Login": test_2_user_login(),
        "Test 3: Update Preferences": test_3_update_preferences(),
        "Test 4: Get Preferences": test_4_get_preferences(),
        "Test 5: Create Category": test_5_create_category(),
        "Test 6: Create Item": test_6_create_item(),
        "Test 7: Trigger Alert": test_7_trigger_low_stock_alert(),
        "Test 8: Get Alerts": test_8_get_alerts(),
        "Test 9: Statistics": test_9_get_alert_stats(),
        "Test 10: Manual Check": test_10_trigger_check(),
    }
    
    # Summary
    print_section("TEST SUMMARY")
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        indicator = "✅" if result else "❌"
        print(f"{indicator} {test_name}")
    
    print(f"\n{'='*60}")
    print(f"Result: {passed}/{total} tests passed")
    print(f"{'='*60}")
    
    if passed == total:
        print("\n🎉 All tests passed! Your alert system is working!")
        print("\n✅ Next: Check your email and WhatsApp for notifications")
    else:
        print("\n⚠️ Some tests failed. Check the errors above.")
        print("See LOW_STOCK_ALERT_SYSTEM.md for troubleshooting")

if __name__ == "__main__":
    # Global variables for test data
    CATEGORY_ID = None
    ITEM_ID = None
    ALERT_ID = None
    
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nTests cancelled by user")
    except Exception as e:
        print(f"\n\nFatal error: {str(e)}")
