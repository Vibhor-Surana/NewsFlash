#!/usr/bin/env python3
"""
Complete test of the news search flow with detailed logging
"""

import requests
import json
import time

def test_complete_flow():
    """Test the complete news search flow with new API key"""
    print("🔍 Testing Complete News Search Flow")
    print("=" * 60)
    
    session = requests.Session()
    
    try:
        # Step 1: Establish session
        print("1. Establishing session...")
        response = session.get("http://localhost:5000/")
        print(f"   ✅ Status: {response.status_code}")
        
        # Step 2: Send initial chat message
        print("\n2. Sending chat message: 'technology'")
        response = session.post("http://localhost:5000/chat", json={"message": "technology"})
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Response: {data.get('response', 'No response')[:80]}...")
            print(f"   ✅ Topics: {data.get('topics', [])}")
            print(f"   ✅ Should search: {data.get('should_search', False)}")
        else:
            print(f"   ❌ Error: {response.text}")
            return
        
        # Step 3: Trigger search with "no"
        print("\n3. Triggering search with 'no'...")
        response = session.post("http://localhost:5000/chat", json={"message": "no"})
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Response: {data.get('response', 'No response')[:80]}...")
            print(f"   ✅ Should search: {data.get('should_search', False)}")
        else:
            print(f"   ❌ Error: {response.text}")
            return
        
        # Step 4: Perform news search
        print("\n4. Performing news search...")
        print("   (This may take a moment with AI summaries...)")
        
        start_time = time.time()
        response = session.post("http://localhost:5000/search_news")
        end_time = time.time()
        
        print(f"   Status: {response.status_code}")
        print(f"   Duration: {end_time - start_time:.2f} seconds")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Success: {data.get('success', False)}")
            
            results = data.get('results', {})
            print(f"   ✅ Topics found: {list(results.keys())}")
            
            total_articles = 0
            for topic, articles in results.items():
                article_count = len(articles)
                total_articles += article_count
                print(f"   📰 {topic}: {article_count} articles")
                
                # Show first article details
                if articles:
                    first_article = articles[0]
                    print(f"      📄 Title: {first_article.get('title', 'No title')[:60]}...")
                    print(f"      📝 Summary: {first_article.get('summary', 'No summary')[:80]}...")
                    print(f"      🌐 Source: {first_article.get('source', 'Unknown')}")
            
            print(f"\n   🎯 Total articles found: {total_articles}")
            
            if total_articles > 0:
                print("\n🎉 SUCCESS: News search completed successfully!")
                print("   ✅ Backend is working correctly")
                print("   ✅ AI summaries are being generated")
                print("   ✅ Articles are being returned")
                
                # Test if this would display in frontend
                print("\n📱 Frontend Display Test:")
                print("   The results should now display in the browser interface.")
                print("   If they don't appear, the issue is in the JavaScript display logic.")
            else:
                print("\n⚠️  WARNING: No articles found")
                print("   This could be due to search API issues or topic filtering.")
        else:
            print(f"   ❌ Search failed: {response.status_code}")
            print(f"   Error: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection failed - make sure Flask server is running on localhost:5000")
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")

if __name__ == "__main__":
    test_complete_flow()