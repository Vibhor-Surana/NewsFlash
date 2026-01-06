#!/usr/bin/env python3
"""
Quick test of live API functionality
"""
import requests
import json

def test_live_api():
    """Test the live API endpoints"""
    print("🔍 Testing Live API Functionality")
    print("=" * 50)
    
    try:
        # Test 1: Main site
        print("1. Testing main site...")
        r = requests.get('http://localhost:5000/')
        print(f"   Status: {r.status_code}")
        print("   ✅ Main site accessible" if r.status_code == 200 else "   ❌ Main site not accessible")
        
        # Test 2: Language API
        print("\n2. Testing language API...")
        r = requests.get('http://localhost:5000/get-languages')
        print(f"   Status: {r.status_code}")
        if r.status_code == 200:
            data = r.json()
            print(f"   ✅ Languages available: {list(data['languages'].keys())}")
            print(f"   ✅ Current language: {data['current_language']}")
        else:
            print(f"   ❌ Error: {r.text[:100]}")
        
        # Test 3: Search API
        print("\n3. Testing search API...")
        r = requests.post('http://localhost:5000/search', json={
            'query': 'technology',
            'language': 'en',
            'max_results': 1
        })
        print(f"   Status: {r.status_code}")
        if r.status_code == 200:
            data = r.json()
            print(f"   ✅ Search successful: {data.get('success', False)}")
            print(f"   ✅ Language: {data.get('language', 'unknown')}")
            print(f"   ✅ Articles found: {len(data.get('articles', []))}")
        else:
            print(f"   ❌ Error: {r.text[:100]}")
        
        # Test 4: Language setting
        print("\n4. Testing language setting...")
        session = requests.Session()
        r = session.post('http://localhost:5000/set-language', json={'language': 'hi'})
        print(f"   Status: {r.status_code}")
        if r.status_code == 200:
            data = r.json()
            print(f"   ✅ Language set to: {data.get('language', 'unknown')}")
            
            # Verify language was set
            r2 = session.get('http://localhost:5000/get-languages')
            if r2.status_code == 200:
                data2 = r2.json()
                print(f"   ✅ Verified current language: {data2.get('current_language', 'unknown')}")
        else:
            print(f"   ❌ Error: {r.text[:100]}")
        
        print("\n🎉 Live API testing completed!")
        
    except requests.exceptions.ConnectionError:
        print("❌ Connection failed - make sure Flask server is running on localhost:5000")
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")

if __name__ == "__main__":
    test_live_api()