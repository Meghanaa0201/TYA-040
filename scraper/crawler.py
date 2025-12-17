import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, urlunparse
from collections import deque
import os
from datetime import datetime
import config
from scraper import core, storage



def discover_links(html_content, base_url):
    """
    Extract all links from HTML content
    Returns list of normalized URLs
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    links = set()
    
    # Find all <a> tags
    for tag in soup.find_all('a', href=True):
        href = tag['href']
        
        # Skip anchors, javascript, mailto, etc.
        if href.startswith('#') or href.startswith('javascript:') or href.startswith('mailto:'):
            continue
        
        # Convert relative URLs to absolute
        absolute_url = urljoin(base_url, href)
        
        # Normalize URL
        normalized = core.normalize_url(absolute_url)
        
        # Only include same-domain links
        if core.is_same_domain(normalized, base_url):
            links.add(normalized)
    
    return list(links)

def download_file(url, domain_id, session):
    """Download a file from URL and save to attachments directory"""
    try:
        # Polite delay
        core.polite_delay()
        
        # Download file
        response = session.get(url, timeout=config.DEFAULT_TIMEOUT, stream=True)
        
        if response.status_code != 200:
            return None
        
        # Get filename
        domain_name = urlparse(url).netloc.replace(':', '_')
        file_ext = core.get_file_extension(url)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Create filename
        filename = f"{timestamp}.{file_ext}" if file_ext else f"{timestamp}.bin"
        
        # Create directory
        file_dir = os.path.join(config.ATTACHMENTS_DIR, domain_name)
        os.makedirs(file_dir, exist_ok=True)
        
        # Save file
        file_path = os.path.join(file_dir, filename)
        
        with open(file_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        # Get file size
        file_size = os.path.getsize(file_path)
        
        # Track in storage
        storage.add_file(domain_id, url, file_path, file_ext or 'unknown', file_size)
        
        print(f"  📎 Downloaded file: {filename} ({file_size} bytes)")
        
        return file_path
        
    except Exception as e:
        print(f"  ❌ Failed to download file {url}: {e}")
        return None

def crawl_domain(base_url, max_depth=2, max_pages=100, domain_id=None, run_id=None, progress_callback=None):
    """
    Crawl entire domain using BFS (Breadth-First Search)
    
    Args:
        base_url: Starting URL
        max_depth: Maximum depth to crawl
        max_pages: Maximum number of pages to crawl
        domain_id: Domain ID for storage
        run_id: Scrape run ID
        progress_callback: Optional callback function(current, total, url)
    
    Returns:
        dict with crawl statistics
    """
    print(f"\n{'='*60}")
    print(f"🕷️  Starting full domain crawl: {base_url}")
    print(f"   Max depth: {max_depth}, Max pages: {max_pages}")
    print(f"{'='*60}\n")
    
    # Create session
    session = core.create_session()
    
    # Track visited URLs and queue
    visited = set()
    queue = deque([(base_url, 0)])  # (url, depth)
    
    # Statistics
    stats = {
        'pages_crawled': 0,
        'pages_new': 0,
        'pages_modified': 0,
        'pages_unchanged': 0,
        'pages_error': 0,
        'files_downloaded': 0,
        'urls': []
    }
    
    while queue and len(visited) < max_pages:
        url, depth = queue.popleft()
        
        # Skip if already visited
        if url in visited:
            continue
        
        # Mark as visited
        visited.add(url)
        stats['urls'].append(url)
        
        # Progress callback
        if progress_callback:
            progress_callback(len(visited), max_pages, url)
        
        print(f"[{len(visited)}/{max_pages}] Depth {depth}: {url}")
        
        # Check if it's a file
        if core.is_file_url(url):
            print(f"  📎 Detected file URL")
            download_file(url, domain_id, session)
            stats['files_downloaded'] += 1
            continue
        
        # Scrape the page
        result = core.scrape_url(url, domain_id=domain_id, run_id=run_id, session=session)
        
        # Update statistics
        stats['pages_crawled'] += 1
        
        if result['status'] == 'success':
            if result['is_new']:
                stats['pages_new'] += 1
                print(f"  ✨ NEW page")
            elif result['changed']:
                stats['pages_modified'] += 1
                similarity = result.get('similarity', 0)
                print(f"  🔄 MODIFIED (similarity: {similarity*100:.1f}%)")
            else:
                stats['pages_unchanged'] += 1
                print(f"  ✓ No changes")
            
            # Discover links if we haven't reached max depth
            if depth < max_depth:
                # Get HTML content from last scrape
                try:
                    # Read the HTML snapshot
                    domain_name = urlparse(url).netloc.replace(':', '_')
                    snapshot_dir = os.path.join(config.SNAPSHOT_DIR, domain_name)
                    
                    # Get most recent HTML file
                    html_files = sorted([f for f in os.listdir(snapshot_dir) if f.endswith('.html')])
                    if html_files:
                        latest_html = os.path.join(snapshot_dir, html_files[-1])
                        with open(latest_html, 'r', encoding='utf-8') as f:
                            html_content = f.read()
                        
                        # Discover new links
                        new_links = discover_links(html_content, url)
                        
                        print(f"  🔗 Found {len(new_links)} links")
                        
                        # Add to queue
                        for link in new_links:
                            if link not in visited and link not in [u for u, d in queue]:
                                queue.append((link, depth + 1))
                
                except Exception as e:
                    print(f"  ⚠️  Error discovering links: {e}")
        
        else:
            stats['pages_error'] += 1
            error_msg = result.get('error', 'Unknown')
            print(f"  ❌ Error: {error_msg}")
            with open('error.log', 'a') as f:
                f.write(f"Error scraping {url}: {error_msg}\n")
        
        # Update run progress
        if run_id:
            storage.update_scrape_run(run_id, {
                'pages_crawled': stats['pages_crawled'],
                'current_url': url
            })
    
    print(f"\n{'='*60}")
    print(f"✅ Crawl completed!")
    print(f"   Pages crawled: {stats['pages_crawled']}")
    print(f"   New: {stats['pages_new']}, Modified: {stats['pages_modified']}, Unchanged: {stats['pages_unchanged']}")
    print(f"   Files downloaded: {stats['files_downloaded']}")
    print(f"   Errors: {stats['pages_error']}")
    print(f"{'='*60}\n")
    
    return stats

def discover_subdomains(domain):
    """
    Discover common subdomains
    Returns list of active subdomains
    """
    common_subdomains = ['www', 'blog', 'api', 'dev', 'staging', 'test', 
                        'mail', 'ftp', 'admin', 'portal', 'shop', 'store']
    
    active_subdomains = []
    session = core.create_session()
    
    for subdomain in common_subdomains:
        url = f"https://{subdomain}.{domain}"
        try:
            response = session.head(url, timeout=5)
            if response.status_code < 400:
                active_subdomains.append(url)
                print(f"  ✓ Found subdomain: {url}")
        except:
            pass
    
    return active_subdomains



