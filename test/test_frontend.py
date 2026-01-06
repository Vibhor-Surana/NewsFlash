#!/usr/bin/env python3
"""
Test script to simulate frontend behavior and debug the news search issue
"""

import requests
import json
import time

# Base URL
BASE_URL = "http://localhost:5000"

def test_news_search():
    """Test the complete news search flow"""
    print("🔍 Testing News Search Flow")
    print("=" * 50)
    
    # Create a session
    session = requests.Session()
    
    # Step 1: Visit main page to establish session
    print("1. Establishing session...")
    response = session.get(f"{BASE_URL}/")
    if response.status_code == 200:
        print("✅ Session established successfully")
    else:
        print(f"❌ Failed to establish session: {response.status_code}")
        return
    
    # Step 2: Send chat message
    print("\n2. Sending chat message...")
    chat_data = {"message": "technology news"}
    response = session.post(f"{BASE_URL}/chat", json=chat_data)
    
    if response.status_code == 200:
        chat_result = response.json()
        print("✅ Chat message processed successfully")
        print(f"   Response: {chat_result.get('response', 'No response')}")
        print(f"   Topics: {chat_result.get('topics', [])}")
        print(f"   Should search: {chat_result.get('should_search', False)}")
    else:
        print(f"❌ Chat failed: {response.status_code}")
        print(f"   Error: {response.text}")
        return
    
    # Step 3: Search for news
    print("\n3. Searching for news...")
    response = session.post(f"{BASE_URL}/search_news")
    
    if response.status_code == 200:
        search_result = response.json()
        print("✅ News search completed successfully")
        print(f"   Success: {search_result.get('success', False)}")
        
        results = search_result.get('results', {})
        print(f"   Topics found: {list(results.keys())}")
        
        for topic, articles in results.items():
            print(f"   📰 {topic}: {len(articles)} articles")
            if articles:
                for i, article in enumerate(articles[:2]):  # Show first 2 articles
                    print(f"      {i+1}. {article.get('title', 'No title')[:80]}...")
    else:
        print(f"❌ News search failed: {response.status_code}")
        print(f"   Error: {response.text}")
        return
    
    print("\n🎉 Test completed successfully!")

if __name__ == "__main__":
    try:
        test_news_search()
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")