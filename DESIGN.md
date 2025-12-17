# Design Document: Daily Website Scraper with Diff Alerts

## 1. Problem Statement

**Objective**: Build a system that monitors websites for changes by performing full-domain crawls, detecting content modifications, and sending automated alerts.

**Key Challenges**:
- Crawl entire domains efficiently without overwhelming servers
- Detect meaningful changes (not just timestamps or ads)
- Store and compare large amounts of HTML content
- Schedule regular monitoring without manual intervention
- Respect website policies (robots.txt, rate limiting)
- Provide actionable insights through a user-friendly interface

**Success Criteria**:
- Correctly detect new, modified, and removed pages
- Handle rate limits and implement polite crawling
- Send timely email notifications
- Provide comprehensive analytics dashboard

## 2. Architecture & System Flow

### High-Level Architecture

```
┌───────────────────────────────────────────────────────────┐
│                  Web Dashboard (Flask)                    │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │   Home   │  │Analytics │  │ Changes  │  │ Profiles │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
└────────────────────────┬──────────────────────────────────┘
                         │
                         ▼
┌───────────────────────────────────────────────────────────┐
│                   Application Layer                       │
│  ┌────────────────────────────────────────────────────┐   │
│  │              APScheduler (Background Jobs)         │   │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐    │   │
│  │  │ Domain 1   │  │ Domain 2   │  │   Daily    │    │   │
│  │  │ (5 min)    │  │ (1 hour)   │  │   Digest   │    │   │
│  │  └────────────┘  └────────────┘  └────────────┘    │   │
│  └────────────────────────────────────────────────────┘   │
└────────────────────────┬──────────────────────────────────┘
                         │
                         ▼
┌───────────────────────────────────────────────────────────┐
│                    Core Components                        │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │ Crawler  │  │  Scraper │  │ Storage  │  │ Notifier │   │
│  │  (BFS)   │  │  (Core)  │  │  (JSON)  │  │ (Email)  │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
└────────────────────────┬──────────────────────────────────┘
                         │
                         ▼
┌───────────────────────────────────────────────────────────┐
│                    Data Storage                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ domains.json │  │  pages.json  │  │changes.json  │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│  ┌──────────────┐  ┌──────────────┐                       │
│  │   Snapshots  │  │ Attachments  │                       │
│  └──────────────┘  └──────────────┘                       │
└───────────────────────────────────────────────────────────┘
```

### Data Flow

```
1. User adds domain via Web UI
              ↓
2. Domain config saved to domains.json
              ↓
3. APScheduler creates periodic job
              ↓
4. Crawler performs BFS traversal
              ↓
5. Each page is scraped and hashed
              ↓
6. Storage compares with previous snapshot
              ↓
7. Changes detected and recorded
              ↓
8. Email notification sent
              ↓
9. Dashboard updated with new data
```

## 3. Tools & Libraries

### Core Technologies
┌──────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
|         Tool       |   Version   |        Purpose       |           Justification                            |
├──────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
| **Python**         |   3.7+      | Programming language | Rich ecosystem, excellent for web scraping         |
| **Flask**          |   2.3.0+    | Web framework        | Lightweight, easy to learn, perfect for dashboards |
| **APScheduler**    |   3.10.0+   | Task scheduling      | Reliable background job execution                  |
| **requests**       |   2.31.0+   | HTTP client          | Industry standard, robust                          |
| **BeautifulSoup**  |   4.12.0+   | HTML parsing         | Best Python HTML parser                            |
| **lxml**           |   4.9.0+    | XML/HTML parser      | Fast, efficient                                    |
├──────────────────────────────────────────────────────────────────────────────────────────────────────────────┤

### Why NOT Scrapy?

While Scrapy is powerful, we chose **requests + BeautifulSoup** because:
- Simpler learning curve
- More control over crawl logic
- Easier to implement custom BFS algorithm
- Sufficient for our use case
- Less overhead for small-scale scraping

### Why JSON instead of Database?

- **Simplicity**: No database setup required
- **Portability**: Easy to backup and transfer
- **Transparency**: Human-readable data
- **Sufficient**: Works well for moderate data volumes
- **Fast**: Direct file I/O is fast enough

## 4. Key Logic Explanation

### 4.1 BFS Crawler Algorithm

```python
def crawl_domain(start_url, max_depth, max_pages):
    """
    Breadth-First Search crawler
    
    Why BFS?
    - Ensures we crawl important pages first (closer to homepage)
    - Prevents getting stuck in deep link chains
    - Better for discovering site structure
    """
    queue = [(start_url, 0)]  # (url, depth)
    visited = set()
    pages_crawled = 0
    
    while queue and pages_crawled < max_pages:
        url, depth = queue.pop(0)
        
        if url in visited or depth > max_depth:
            continue
            
        visited.add(url)
        
        # Scrape page
        html, links = scrape_page(url)
        pages_crawled += 1
        
        # Add discovered links to queue
        if depth < max_depth:
            for link in links:
                if is_same_domain(link, start_url):
                    queue.append((link, depth + 1))
    
    return visited
```

**Key Design Decisions**:
1. **Queue-based**: FIFO ensures breadth-first traversal
2. **Depth limiting**: Prevents infinite crawling
3. **Page limiting**: Controls resource usage
4. **Same-domain check**: Stays within target domain

### 4.2 Change Detection

```python
def detect_changes(old_hash, new_hash, old_text, new_text):
    """
    Multi-level change detection
    
    Level 1: Hash comparison (fast)
    Level 2: Similarity scoring (detailed)
    Level 3: DOM diff (visual)
    """
    # Fast check
    if old_hash == new_hash:
        return None  # No change
    
    # Calculate similarity
    similarity = difflib.SequenceMatcher(
        None, old_text, new_text
    ).ratio()
    
    # Generate diff
    diff = difflib.unified_diff(
        old_text.splitlines(),
        new_text.splitlines()
    )
    
    return {
        'changed': True,
        'similarity': similarity,
        'diff': '\n'.join(diff)
    }
```

**Why this approach?**:
1. **Hash first**: O(1) comparison, very fast
2. **Similarity score**: Quantifies change magnitude
3. **Unified diff**: Shows exact changes
4. **Three levels**: Balance speed and detail

### 4.3 Polite Crawling

```python
def polite_crawl(url):
    """
    Implements polite crawling best practices
    """
    # 1. Check robots.txt
    if not can_fetch(url):
        return None
    
    # 2. Random delay (0.2-0.6 seconds)
    time.sleep(random.uniform(0.2, 0.6))
    
    # 3. Custom User-Agent
    headers = {'User-Agent': 'WebsiteMonitor/1.0'}
    
    # 4. Timeout protection
    response = requests.get(
        url, 
        headers=headers, 
        timeout=10
    )
    
    return response
```

**Best Practices**:
- Respect robots.txt
- Delay between requests
- Identify ourselves (User-Agent)
- Handle timeouts gracefully

### 4.4 Email Notification System

```python
def send_email_alert(changes, domain):
    """
    Two-tier notification system
    
    Tier 1: Immediate alerts (after each scrape)
    Tier 2: Daily digest (9 AM summary)
    """
    # Immediate alert
    if changes:
        send_change_email(changes, domain)
    
    # Daily digest (scheduled separately)
    @scheduler.scheduled_job('cron', hour=9)
    def daily_digest():
        all_changes = get_last_24h_changes()
        send_digest_email(all_changes)
```

**Design Rationale**:
- **Immediate**: Critical changes notified ASAP
- **Digest**: Prevents email spam, daily summary
- **HTML emails**: Better formatting, clickable links
- **Grouped by domain**: Organized presentation

### 4.5 Link Classification

```python
def classify_links(html, base_url):
    """
    Categorizes links for analytics
    
    Categories:
    - Internal: Same domain
    - External: Different domain
    - Files: PDFs, docs, images
    """
    soup = BeautifulSoup(html, 'html.parser')
    
    classification = {
        'internal': [],
        'external': [],
        'files': []
    }
    
    for link in soup.find_all('a', href=True):
        url = urljoin(base_url, link['href'])
        
        if is_file(url):
            classification['files'].append(url)
        elif is_same_domain(url, base_url):
            classification['internal'].append(url)
        else:
            classification['external'].append(url)
    
    return classification
```

**Benefits**:
- **SEO insights**: Internal linking structure
- **External dependencies**: Track outbound links
- **File tracking**: Monitor downloadable content

## 5. Database Schema (JSON)

### domains.json
```json
{
  "domains": [
    {
      "id": "uuid",
      "url": "string",
      "interval_minutes": "integer",
      "crawl_depth": "integer",
      "max_pages": "integer",
      "email": "string",
      "is_active": "boolean",
      "created_at": "datetime",
      "last_scraped_at": "datetime"
    }
  ]
}
```

### pages.json
```json
{
  "pages": [
    {
      "id": "uuid",
      "domain_id": "uuid (FK)",
      "url": "string",
      "title": "string",
      "content_hash": "string (SHA256)",
      "first_seen": "datetime",
      "last_scraped": "datetime",
      "is_active": "boolean",
      "links": {
        "internal": ["array"],
        "external": ["array"],
        "files": ["array"]
      }
    }
  ]
}
```

### changes.json
```json
{
  "changes": [
    {
      "id": "uuid",
      "page_id": "uuid (FK)",
      "change_type": "enum (new|modified|removed)",
      "detected_at": "datetime",
      "similarity_score": "float (0-1)",
      "diff_path": "string (file path)",
      "notified": "boolean"
    }
  ]
}
```

## 6. Security Considerations

1. **Email Credentials**: Stored in config.py (not in git)
2. **Input Validation**: URL validation before crawling
3. **Rate Limiting**: Prevents server overload
4. **Robots.txt**: Respects website policies
5. **Timeout Protection**: Prevents hanging requests

## 7. Performance Optimizations

1. **Hash-based comparison**: O(1) change detection
2. **BFS algorithm**: Efficient crawling
3. **JSON storage**: Fast read/write
4. **Background jobs**: Non-blocking execution
5. **Configurable limits**: Prevents resource exhaustion

## 8. Scalability Considerations

**Current Limitations**:
- JSON storage (not ideal for 1000+ domains)
- Single-threaded crawling
- In-memory scheduling

**Future Improvements**:
- PostgreSQL/MongoDB for storage
- Celery for distributed task queue
- Redis for caching
- Multi-threaded crawling

## 9. Testing Strategy

1. **Unit Tests**: Core functions (scraping, hashing, diff)
2. **Integration Tests**: End-to-end workflows
3. **Mock Tests**: External dependencies (HTTP, email)
4. **Edge Cases**: Empty pages, timeouts, errors

## 10. Deployment Considerations

**Development**:
```bash
python app.py  # Runs on localhost:5000
```

**Production** (recommendations):
- Use Gunicorn/uWSGI
- Nginx reverse proxy
- Systemd for process management
- Environment variables for secrets
- Log rotation

## 11. Monitoring & Logging

- **Application logs**: Scrape results, errors
- **Email logs**: Notification status
- **Scheduler logs**: Job execution
- **Error tracking**: Failed scrapes, timeouts

## 12. Future Enhancements

1. **Slack integration**: Alternative to email
2. **Webhook support**: Custom integrations
3. **API endpoints**: Programmatic access
4. **Mobile app**: iOS/Android notifications
5. **Machine learning**: Predict important changes
6. **Screenshot comparison**: Visual diff
7. **JavaScript rendering**: Puppeteer/Selenium
8. **Multi-user support**: User authentication

---

**Last Updated**: 2025-12-17 
**Author**: Meghana A
