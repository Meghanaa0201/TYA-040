import json
import os
import uuid
from datetime import datetime
from typing import Dict, List, Optional
import config

import threading

# Global lock for file operations
file_lock = threading.Lock()

def load_json(filepath: str) -> Dict:
    """Load JSON file, return empty structure if not exists"""
    with file_lock:
        if not os.path.exists(filepath):
            return {}
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading {filepath}: {e}")
            return {}

def save_json(filepath: str, data: Dict):
    """Save data to JSON file with atomic write and thread locking"""
    import time
    
    with file_lock:
        max_retries = 3
        for i in range(max_retries):
            try:
                # Write to unique temporary file first
                temp_file = f"{filepath}.{uuid.uuid4()}.tmp"
                with open(temp_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                
                # Rename to actual file (atomic on most systems)
                if os.path.exists(filepath):
                    try:
                        os.remove(filepath)
                    except OSError:
                        pass # Maybe already removed or locked, retry rename
                
                os.rename(temp_file, filepath)
                return # Success
            except Exception as e:
                # Clean up temp file if it exists
                if 'temp_file' in locals() and os.path.exists(temp_file):
                    try:
                        os.remove(temp_file)
                    except:
                        pass
                        
                if i == max_retries - 1:
                    print(f"Error saving {filepath}: {e}")
                else:
                    time.sleep(0.1) # Small delay before retry

# Domain operations
def add_domain(url: str, interval_minutes: int = 60, email: str = None) -> Dict:
    """Add new domain, return domain dict"""
    data = load_json(config.DOMAINS_FILE)
    if 'domains' not in data:
        data['domains'] = []
    
    domain_id = str(uuid.uuid4())
    domain = {
        'id': domain_id,
        'url': url,
        'interval_minutes': interval_minutes,
        'email': email or config.EMAIL_TO,
        'is_active': True,
        'created_at': datetime.now().isoformat(),
        'last_scraped_at': None
    }
    
    data['domains'].append(domain)
    save_json(config.DOMAINS_FILE, data)
    return domain

def get_all_domains() -> List[Dict]:
    """Get all domains"""
    data = load_json(config.DOMAINS_FILE)
    return data.get('domains', [])

def get_domain(domain_id: str) -> Optional[Dict]:
    """Get domain by ID"""
    data = load_json(config.DOMAINS_FILE)
    for domain in data.get('domains', []):
        if domain['id'] == domain_id:
            return domain
    return None

def update_domain(domain_id: str, updates: Dict):
    """Update domain fields"""
    data = load_json(config.DOMAINS_FILE)
    for domain in data.get('domains', []):
        if domain['id'] == domain_id:
            domain.update(updates)
            save_json(config.DOMAINS_FILE, data)
            return True
    return False

def delete_domain(domain_id: str):
    """Delete domain"""
    data = load_json(config.DOMAINS_FILE)
    data['domains'] = [d for d in data.get('domains', []) if d['id'] != domain_id]
    save_json(config.DOMAINS_FILE, data)

# Scrape run operations
def create_scrape_run(domain_id: str) -> Dict:
    """Create new scrape run, return run dict"""
    data = load_json(config.RUNS_FILE)
    if 'runs' not in data:
        data['runs'] = []
    
    run_id = str(uuid.uuid4())
    run = {
        'id': run_id,
        'domain_id': domain_id,
        'status': 'running',
        'started_at': datetime.now().isoformat(),
        'completed_at': None,
        'pages_crawled': 0,
        'pages_changed': 0,
        'pages_new': 0,
        'error_message': None,
        'current_url': None
    }
    
    data['runs'].append(run)
    save_json(config.RUNS_FILE, data)
    return run

def update_scrape_run(run_id: str, updates: Dict):
    """Update run status/stats"""
    data = load_json(config.RUNS_FILE)
    for run in data.get('runs', []):
        if run['id'] == run_id:
            run.update(updates)
            save_json(config.RUNS_FILE, data)
            return True
    return False

def get_scrape_run(run_id: str) -> Optional[Dict]:
    """Get scrape run by ID"""
    data = load_json(config.RUNS_FILE)
    for run in data.get('runs', []):
        if run['id'] == run_id:
            return run
    return None

def get_domain_runs(domain_id: str) -> List[Dict]:
    """Get all runs for a domain"""
    data = load_json(config.RUNS_FILE)
    return [r for r in data.get('runs', []) if r['domain_id'] == domain_id]

# Page operations
def add_page(domain_id: str, url: str, title: str, content_hash: str, status_code: int, links: Optional[Dict] = None) -> Dict:
    """Add or update page"""
    data = load_json(config.PAGES_FILE)
    if 'pages' not in data:
        data['pages'] = []
    
    # Check if page exists
    for page in data['pages']:
        if page['domain_id'] == domain_id and page['url'] == url:
            # Update existing page
            page['title'] = title
            page['content_hash'] = content_hash
            page['status_code'] = status_code
            page['last_checked_at'] = datetime.now().isoformat()
            if links is not None:
                page['links'] = links
            save_json(config.PAGES_FILE, data)
            return page
    
    # Create new page
    page_id = str(uuid.uuid4())
    page = {
        'id': page_id,
        'domain_id': domain_id,
        'url': url,
        'title': title,
        'content_hash': content_hash,
        'status_code': status_code,
        'first_seen': datetime.now().isoformat(),
        'last_scraped': datetime.now().isoformat(),
        'is_active': True,
        'links': links if links is not None else {
            'internal': [],
            'external': [],
            'files': []
        }
    }
    
    data['pages'].append(page)
    save_json(config.PAGES_FILE, data)
    return page

def get_page_by_url(domain_id: str, url: str) -> Optional[Dict]:
    """Get page by domain and URL"""
    data = load_json(config.PAGES_FILE)
    for page in data.get('pages', []):
        if page['domain_id'] == domain_id and page['url'] == url:
            return page
    return None

# Change operations
def add_change(page_id: str, run_id: str, change_type: str, old_snapshot: str = None, 
               new_snapshot: str = None, diff_path: str = None, similarity: float = None) -> Dict:
    """Record detected change"""
    data = load_json(config.CHANGES_FILE)
    if 'changes' not in data:
        data['changes'] = []
    
    change_id = str(uuid.uuid4())
    change = {
        'id': change_id,
        'page_id': page_id,
        'run_id': run_id,
        'change_type': change_type,
        'old_snapshot': old_snapshot,
        'new_snapshot': new_snapshot,
        'diff_path': diff_path,
        'similarity_score': similarity,
        'detected_at': datetime.now().isoformat(),
        'notified': False
    }
    
    data['changes'].append(change)
    save_json(config.CHANGES_FILE, data)
    return change

def get_recent_changes(limit: int = 50) -> List[Dict]:
    """Get recent changes"""
    data = load_json(config.CHANGES_FILE)
    changes = data.get('changes', [])
    # Sort by detected_at descending
    changes.sort(key=lambda x: x.get('detected_at', ''), reverse=True)
    return changes[:limit]

def get_run_changes(run_id: str) -> List[Dict]:
    """Get all changes for a run"""
    data = load_json(config.CHANGES_FILE)
    return [c for c in data.get('changes', []) if c['run_id'] == run_id]

def mark_change_notified(change_id: str):
    """Mark change as notified"""
    data = load_json(config.CHANGES_FILE)
    for change in data.get('changes', []):
        if change['id'] == change_id:
            change['notified'] = True
            save_json(config.CHANGES_FILE, data)
            return True
    return False

def mark_changes_notified(change_ids: List[str]):
    """Mark multiple changes as notified in one operation"""
    data = load_json(config.CHANGES_FILE)
    updated = False
    for change in data.get('changes', []):
        if change['id'] in change_ids:
            change['notified'] = True
            updated = True
    
    if updated:
        save_json(config.CHANGES_FILE, data)
        return True
    return False

# Analytics
def get_analytics_data() -> Dict:
    """Compute analytics from JSON files"""
    domains = get_all_domains()
    runs_data = load_json(config.RUNS_FILE)
    pages_data = load_json(config.PAGES_FILE)
    changes_data = load_json(config.CHANGES_FILE)
    
    total_runs = len(runs_data.get('runs', []))
    completed_runs = len([r for r in runs_data.get('runs', []) if r['status'] == 'completed'])
    total_pages = len(pages_data.get('pages', []))
    total_changes = len(changes_data.get('changes', []))
    
    return {
        'total_domains': len(domains),
        'active_domains': len([d for d in domains if d.get('is_active', True)]),
        'total_runs': total_runs,
        'completed_runs': completed_runs,
        'total_pages': total_pages,
        'total_changes': total_changes,
        'recent_changes': get_recent_changes(10)
    }

# Domain-specific queries
def get_domain_pages(domain_id: str) -> List[Dict]:
    """Get all pages for a domain"""
    data = load_json(config.PAGES_FILE)
    return [p for p in data.get('pages', []) if p['domain_id'] == domain_id]

def get_domain_changes(domain_id: str) -> List[Dict]:
    """Get all changes for a domain"""
    pages = get_domain_pages(domain_id)
    page_ids = [p['id'] for p in pages]
    
    changes_data = load_json(config.CHANGES_FILE)
    return [c for c in changes_data.get('changes', []) 
            if c['page_id'] in page_ids]

def get_page_changes(page_id: str) -> List[Dict]:
    """Get all changes for a specific page"""
    changes_data = load_json(config.CHANGES_FILE)
    return [c for c in changes_data.get('changes', []) if c['page_id'] == page_id]

# Removed pages detection
def mark_page_removed(page_id: str):
    """Mark a page as removed"""
    data = load_json(config.PAGES_FILE)
    for page in data.get('pages', []):
        if page['id'] == page_id:
            page['is_active'] = False
            page['removed_at'] = datetime.now().isoformat()
            save_json(config.PAGES_FILE, data)
            return True
    return False

def detect_removed_pages(domain_id: str, current_urls: List[str]) -> List[Dict]:
    """
    Detect pages that were previously seen but not in current crawl
    """
    all_pages = get_domain_pages(domain_id)
    active_pages = [p for p in all_pages if p.get('is_active', True)]
    
    removed = []
    for page in active_pages:
        if page['url'] not in current_urls:
            mark_page_removed(page['id'])
            removed.append(page)
    
    return removed

# File tracking
def add_file(domain_id: str, url: str, file_path: str, file_type: str, file_size: int) -> Dict:
    """Track downloaded file"""
    data = load_json(config.SETTINGS_FILE)
    if 'files' not in data:
        data['files'] = []
    
    file_id = str(uuid.uuid4())
    file_record = {
        'id': file_id,
        'domain_id': domain_id,
        'url': url,
        'file_path': file_path,
        'file_type': file_type,
        'file_size': file_size,
        'downloaded_at': datetime.now().isoformat()
    }
    
    data['files'].append(file_record)
    save_json(config.SETTINGS_FILE, data)
    return file_record

# Maintenance / Fix functions
def fix_notification_statuses() -> int:
    """Fix 'notified' status for changes"""
    data = load_json(config.CHANGES_FILE)
    count = 0
    updated = False
    
    for change in data.get('changes', []):
        if not change.get('notified'):
            change['notified'] = True
            updated = True
            count += 1
            
    if updated:
        save_json(config.CHANGES_FILE, data)
        
    return count

def fix_missing_titles() -> int:
    """Generate titles for pages missing them"""
    from urllib.parse import urlparse
    
    data = load_json(config.PAGES_FILE)
    count = 0
    updated = False
    
    for page in data.get('pages', []):
        if not page.get('title') or page.get('title') == 'No Title':
            # Generate title from URL
            url = page['url']
            path = urlparse(url).path
            if not path or path == '/':
                new_title = url
            else:
                segment = path.strip('/').split('/')[-1]
                if not segment:
                    new_title = url
                else:
                    if '.' in segment:
                        segment = segment.rsplit('.', 1)[0]
                    new_title = segment.replace('-', ' ').replace('_', ' ').title()
            
            if new_title != page.get('title'):
                page['title'] = new_title
                updated = True
                count += 1
    
    if updated:
        save_json(config.PAGES_FILE, data)
        
    return count

def get_domain_files(domain_id: str) -> List[Dict]:
    """Get all files for a domain"""
    data = load_json(config.SETTINGS_FILE)
    return [f for f in data.get('files', []) if f['domain_id'] == domain_id]

def get_page_by_id(page_id: str) -> Optional[Dict]:
    """Get page by ID"""
    data = load_json(config.PAGES_FILE)
    for page in data.get('pages', []):
        if page['id'] == page_id:
            return page
    return None

