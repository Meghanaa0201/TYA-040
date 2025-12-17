
import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

print("Attempting to import modules...")
try:
    from scraper import core
    print("✅ scraper.core imported")
    from scraper import crawler
    print("✅ scraper.crawler imported")
except Exception as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)

print("Attempting to run helpers...")
try:
    url = "https://example.com/file.pdf"
    if core.is_file_url(url):
        print("✅ is_file_url working")
    else:
        print("❌ is_file_url failed")
except Exception as e:
    print(f"❌ Helper error: {e}")

print("Attempting to dry-run crawl_domain...")
try:
    print("Running crawl_domain for real (expecting networking)...")
    
    # Test network first
    import requests
    try:
        print("Testing connection to target...")
        r = requests.get("https://the-internet.herokuapp.com/download", timeout=10)
        print(f"Connection status: {r.status_code}")
        print(f"Content length: {len(r.text)}")
        
        # Test link discovery manually
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(r.text, 'html.parser')
        links = soup.find_all('a')
        print(f"Found {len(links)} links on page")
        for l in links[:5]:
            print(f"Link: {l.get('href')}")
            
    except Exception as e:
        print(f"❌ Network error: {e}")
        
    print("Running crawler.crawl_domain...")
    stats = crawler.crawl_domain("https://the-internet.herokuapp.com/download", max_pages=5, max_depth=1)
    print(f"Stats: {stats}")
    print("✅ crawl_domain finished without exception")
except Exception as e:
    import traceback
    traceback.print_exc()
    print(f"❌ Crawler crashed: {e}")
except Exception as e:
    print(f"❌ Crawler error: {e}")
