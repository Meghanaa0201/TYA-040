import requests
import hashlib
import time
import random
import os
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, urlunparse
from urllib.robotparser import RobotFileParser
from datetime import datetime
import difflib
import config
from scraper import storage

# Session management
def create_session():
    """Create requests session with custom headers"""
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    })
    return session

def polite_delay():
    """Random delay between requests"""
    time.sleep(random.uniform(config.MIN_DELAY, config.MAX_DELAY))

# Robots.txt handling
robot_parsers = {}

def get_robot_parser_for_domain(domain):
    """Get or create robot parser for domain"""
    if domain not in robot_parsers:
        rp = RobotFileParser()
        rp.set_url(f"https://{domain}/robots.txt")
        try:
            rp.read()
        except:
            pass
        robot_parsers[domain] = rp
    return robot_parsers[domain]

def allowed_by_robots(url):
    """Check if URL is allowed by robots.txt"""
    try:
        parsed = urlparse(url)
        domain = parsed.netloc
        rp = get_robot_parser_for_domain(domain)
        return rp.can_fetch("*", url)
    except:
        return True

# Content processing
def compute_hash(text):
    """Compute SHA256 hash of text"""
    return hashlib.sha256(text.encode('utf-8')).hexdigest()

def parse_html(html_content):
    """Parse HTML and extract text"""
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Remove script, style, noscript tags
    for tag in soup(['script', 'style', 'noscript']):
        tag.decompose()
    
    # Get title
    title = soup.title.string if soup.title else "No Title"
    
    # Get text content
    text = soup.get_text(separator='\n', strip=True)
    
    return title, text, soup

def short_unified_diff(old_text, new_text, max_lines=50):
    """Generate unified diff"""
    old_lines = old_text.splitlines(keepends=True)
    new_lines = new_text.splitlines(keepends=True)
    
    diff = difflib.unified_diff(old_lines, new_lines, lineterm='')
    diff_lines = list(diff)
    
    if len(diff_lines) > max_lines:
        diff_lines = diff_lines[:max_lines] + [f'\n... (truncated, {len(diff_lines) - max_lines} more lines)']
    
    return ''.join(diff_lines)

def calculate_similarity(old_text, new_text):
    """Calculate similarity ratio between two texts"""
    return difflib.SequenceMatcher(None, old_text, new_text).ratio()

# Helper functions
def normalize_url(url):
    """Normalize URL to avoid duplicates"""
    parsed = urlparse(url)
    # Remove fragment
    normalized = urlunparse((
        parsed.scheme,
        parsed.netloc,
        parsed.path,
        parsed.params,
        parsed.query,
        ''  # Remove fragment
    ))
    # Remove trailing slash
    if normalized.endswith('/') and normalized != parsed.scheme + '://' + parsed.netloc + '/':
        normalized = normalized[:-1]
    return normalized

def is_same_domain(url1, url2):
    """Check if two URLs are from the same domain"""
    domain1 = urlparse(url1).netloc.replace('www.', '')
    domain2 = urlparse(url2).netloc.replace('www.', '')
    return domain1 == domain2

def is_file_url(url):
    """Check if URL points to a downloadable file"""
    file_extensions = ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', 
                      '.zip', '.rar', '.tar', '.gz', '.jpg', '.jpeg', '.png', 
                      '.gif', '.svg', '.mp4', '.mp3', '.avi', '.mov',
                      '.txt', '.json', '.xml', '.csv']
    
    path = urlparse(url).path.lower()
    return any(path.endswith(ext) for ext in file_extensions)

def get_file_extension(url):
    """Get file extension from URL"""
    path = urlparse(url).path.lower()
    if '.' in path:
        return path.split('.')[-1]
    return None

def classify_links(html_content, base_url):
    """
    Classify all links found in HTML content
    Returns dict with internal, external, and file links
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    
    classification = {
        'internal': [],
        'external': [],
        'files': []
    }
    
    base_domain = urlparse(base_url).netloc
    
    for tag in soup.find_all('a', href=True):
        href = tag['href']
        
        # Skip anchors and javascript
        if href.startswith('#') or href.startswith('javascript:'):
            continue
        
        # Make absolute URL
        absolute_url = urljoin(base_url, href)
        normalized = normalize_url(absolute_url)
        
        # Classify
        if is_file_url(normalized):
            file_type = get_file_extension(normalized)
            classification['files'].append({
                'url': normalized,
                'type': file_type,
                'text': tag.get_text(strip=True)[:100]
            })
        elif is_same_domain(normalized, base_url):
            classification['internal'].append({
                'url': normalized,
                'text': tag.get_text(strip=True)[:100]
            })
        else:
            classification['external'].append({
                'url': normalized,
                'text': tag.get_text(strip=True)[:100],
                'domain': urlparse(normalized).netloc
            })
    
    return classification

# Main scraping function
def scrape_url(url, domain_id=None, run_id=None, session=None):
    """
    Scrape a single URL and detect changes
    Returns dict with status, changes, etc.
    """
    if session is None:
        session = create_session()
    
    result = {
        'url': url,
        'status': 'success',
        'status_code': None,
        'title': None,
        'content_hash': None,
        'changed': False,
        'is_new': False,
        'error': None,
        'change_id': None
    }
    
    try:
        # Check robots.txt
        if not allowed_by_robots(url):
            result['status'] = 'blocked'
            result['error'] = 'Blocked by robots.txt'
            return result
        
        # Polite delay
        polite_delay()
        
        # Fetch URL
        response = session.get(url, timeout=config.DEFAULT_TIMEOUT)
        result['status_code'] = response.status_code
        
        if response.status_code != 200:
            result['status'] = 'error'
            result['error'] = f'HTTP {response.status_code}'
            return result
        
        # Parse HTML
        title, text_content, soup = parse_html(response.text)
        result['title'] = title
        
        # Classify links
        link_classification = classify_links(response.text, url)
        result['link_classification'] = link_classification
        
        # Compute hash
        content_hash = compute_hash(text_content)
        result['content_hash'] = content_hash
        
        # Save snapshot
        domain_name = urlparse(url).netloc.replace(':', '_')
        snapshot_dir = os.path.join(config.SNAPSHOT_DIR, domain_name)
        os.makedirs(snapshot_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        snapshot_txt = os.path.join(snapshot_dir, f'{timestamp}.txt')
        snapshot_html = os.path.join(snapshot_dir, f'{timestamp}.html')
        
        with open(snapshot_txt, 'w', encoding='utf-8') as f:
            f.write(text_content)
        
        with open(snapshot_html, 'w', encoding='utf-8') as f:
            f.write(response.text)
        
        # Check for changes if domain_id provided
        if domain_id:
            existing_page = storage.get_page_by_url(domain_id, url)
            
            if existing_page is None:
                # New page
                result['is_new'] = True
                result['changed'] = True
                
                # Add page to storage
                page = storage.add_page(
                    domain_id=domain_id,
                    url=url,
                    title=title,
                    content_hash=content_hash,
                    status_code=response.status_code,
                    links=link_classification
                )
                
                # Record change
                if run_id:
                    change = storage.add_change(
                        page_id=page['id'],
                        run_id=run_id,
                        change_type='new',
                        new_snapshot=snapshot_txt,
                        similarity=None
                    )
                    result['change_id'] = change['id']
                    
            elif existing_page['content_hash'] != content_hash:
                # Content changed
                result['changed'] = True
                
                # Find old snapshot
                old_snapshots = sorted([f for f in os.listdir(snapshot_dir) if f.endswith('.txt')])
                old_snapshot_path = None
                if len(old_snapshots) >= 2:
                    old_snapshot_path = os.path.join(snapshot_dir, old_snapshots[-2])
                
                # Calculate similarity
                similarity = None
                diff_path = None
                if old_snapshot_path and os.path.exists(old_snapshot_path):
                    with open(old_snapshot_path, 'r', encoding='utf-8') as f:
                        old_text = f.read()
                    
                    similarity = calculate_similarity(old_text, text_content)
                    
                    # Generate text diff
                    diff_content = short_unified_diff(old_text, text_content)
                    
                    # Generate DOM-level diff
                    from scraper.dom_diff import compare_dom_structures, generate_dom_diff_html
                    try:
                        old_html_content = ""
                        if old_html_snapshot_path and os.path.exists(old_html_snapshot_path):
                            with open(old_html_snapshot_path, 'r', encoding='utf-8') as f:
                                old_html_content = f.read()

                        dom_changes = compare_dom_structures(old_html_content, response.text)
                        dom_diff_html = generate_dom_diff_html(dom_changes)
                        
                        # Save DOM diff
                        # Ensure page_id is available for naming
                        page_id_for_dom_diff = existing_page['id'] if existing_page else 'unknown'
                        dom_diff_path = os.path.join(
                            config.ALERTS_DIR,
                            domain_name,
                            f"dom_diff_{page_id_for_dom_diff}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
                        )
                        os.makedirs(os.path.dirname(dom_diff_path), exist_ok=True)
                        with open(dom_diff_path, 'w', encoding='utf-8') as f:
                            f.write(dom_diff_html)
                    except Exception as e:
                        print(f"⚠️ Could not generate DOM diff: {e}")
                        dom_diff_path = None
                    
                    # Save text diff
                    diff_path = os.path.join(config.ALERTS_DIR, f'{domain_name}_{timestamp}_diff.txt')
                    os.makedirs(os.path.dirname(diff_path), exist_ok=True) # Ensure directory exists
                    with open(diff_path, 'w', encoding='utf-8') as f:
                        f.write(diff_content)
                
                # Update page
                storage.add_page(domain_id, url, title, content_hash, response.status_code, links=link_classification)
                
                # Record change
                if run_id:
                    change = storage.add_change(
                        page_id=existing_page['id'],
                        run_id=run_id,
                        change_type='modified',
                        old_snapshot=old_snapshot_path,
                        new_snapshot=snapshot_txt,
                        diff_path=diff_path,
                        similarity=similarity
                    )
                    result['change_id'] = change['id']
            else:
                # No change
                storage.add_page(domain_id, url, title, content_hash, response.status_code, links=link_classification)
        
        return result
        
    except Exception as e:
        result['status'] = 'error'
        result['error'] = str(e)
        return result
