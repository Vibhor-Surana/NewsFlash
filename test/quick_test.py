#!/usr/bin/env python3
"""
Quick test to verify news search works without AI summaries
"""

import requests
import json

def test_news_search():
    session = requests.Session()
    
    # Step 1: Get session
    print("1. Getting session...")
    response = session.get("http://localhost:5000/")
    print(f"   Status: {response.status_code}")
    
    # Step 2: Send chat message
    print("2. Sending chat message...")
    response = session.post("http://localhost:5000/chat", json={"message": "technology"})
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"   Topics: {data.get('topics', [])}")
    
    # Step 3: Send "no" to trigger search
    print("3. Triggering search...")
    response = session.post("http://localhost:5000/chat", json={"message": "no"})
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"   Should search: {data.get('should_search', False)}")
    
    # Step 4: Search news
    print("4. Searching news...")
    response = session.post("http://localhost:5000/search_news")
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"   Success: {data.get('success', False)}")
        results = data.get('results', {})
        for topic, articles in results.items():
            print(f"   {topic}: {len(articles)} articles")
            if articles:
                print(f"      First article: {articles[0].get('title', 'No title')[:60]}...")
    else:
        print(f"   Error: {response.text}")

if __name__ == "__main__":
    test_news_search()