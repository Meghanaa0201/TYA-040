# Daily Website Scraper with Diff Alerts

A comprehensive web scraping solution that monitors websites for changes, performs full-domain crawls, detects content modifications, and sends automated email alerts.

## Project Overview

This project is a **full-featured website monitoring system** that:
- Crawls entire domains (including subdomains and linked pages)
- Downloads attached files (PDFs, documents, images)
- Detects new, modified, and removed pages
- Sends immediate email alerts and daily digest reports
- Provides a web dashboard for monitoring and analytics
- Respects robots.txt and implements polite crawling

## Key Features

### Core Functionality
- **Full Domain Crawling** - BFS-based crawler with configurable depth
- **Subdomain Discovery** - Automatically finds and crawls subdomains
- **File Downloads** - Downloads PDFs, docs, images, and other attachments
- **Change Detection** - Detects new, modified, and removed pages
- **Content Comparison** - SHA256 hashing + text similarity scoring
- **Email Notifications** - Immediate alerts + daily digest at 9 AM
- **Robots.txt Compliance** - Respects website crawling policies
- **Rate Limiting** - Polite delays between requests

### Advanced Features
- **DOM-Level Change Highlighting** - Shows exactly which HTML elements changed
- **Link Classification** - Categorizes links as internal/external/files
- **Per-Domain Profiles** - Detailed analytics for each monitored domain
- **Per-Page Tracking** - Individual page history and change tracking
- **Scheduled Crawling** - APScheduler with configurable intervals
- **Web Dashboard** - Flask-based UI with Chart.js visualizations

## Quick Start

### Prerequisites
- Python 3.7 or higher
- Gmail account (for email notifications)
- Internet connection

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/website-scraper.git
cd website-scraper
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Configure email settings**

Edit `config.py` and add your email credentials:
```python
EMAIL_FROM = "your-email@gmail.com"
EMAIL_PASSWORD = "your-app-password"  # Gmail App Password
EMAIL_TO = "recipient@gmail.com"
```

**Note:** For Gmail, you need to create an [App Password](https://support.google.com/accounts/answer/185833):
- Go to Google Account → Security → 2-Step Verification → App passwords
- Generate a new app password for "Mail"
- Use this password in `config.py`

4. **Run the application**
```bash
python app.py
```

5. **Access the dashboard**

Open your browser and navigate to:
```
http://localhost:5000
```

## Project Structure

```
website-scraper/
├── app.py                      # Flask application entry point
├── config.py                   # Configuration settings
├── requirements.txt            # Python dependencies
├── README.md                   # This file
├── DESIGN.md                   # Design document
├── tests/                      # Unit tests
│   ├── test_core.py           # Core scraping tests
│   ├── test_crawler.py        # Crawler tests
│   └── test_storage.py        # Storage tests
├── scraper/                    # Core scraping logic
│   ├── __init__.py
│   ├── core.py                # Single URL scraping
│   ├── crawler.py             # Full domain crawler
│   ├── storage.py             # JSON data storage
│   ├── scheduler.py           # APScheduler integration
│   ├── notifier.py            # Email notifications
│   ├── digest.py              # Daily digest system
│   └── dom_diff.py            # DOM-level comparison
├── web/                        # Web interface
│   ├── __init__.py
│   └── routes.py              # Flask routes
├── templates/                  # HTML templates
│   ├── base.html              # Base template
│   ├── index.html             # Main page
│   ├── dashboard.html         # Analytics
│   ├── changes.html           # Changes list
│   ├── domain_profile.html    # Domain details
│   ├── page_profile.html      # Page details
│   └── edit_domain.html       # Settings editor
├── data/                       # JSON storage (auto-created)
│   ├── domains.json           # Domain configurations
│   ├── pages.json             # All pages data
│   ├── changes.json           # Change history
│   ├── scrape_runs.json       # Scrape run logs
│   └── settings.json          # Files and settings
└── scraped_websites/           # Scraped data (auto-created)
    ├── snapshots/             # HTML/text snapshots
    ├── alerts/                # Diff files
    └── attachments/           # Downloaded files
```

## Libraries Used

| Library | Version | Purpose |
|---------|---------|---------|
| Flask | 2.3.0+ | Web framework for dashboard |
| APScheduler | 3.10.0+ | Scheduled crawling |
| requests | 2.31.0+ | HTTP requests |
| beautifulsoup4 | 4.12.0+ | HTML parsing |
| lxml | 4.9.0+ | XML/HTML parser |

**Why these libraries?**
- **Flask**: Lightweight web framework, easy to use
- **APScheduler**: Reliable background job scheduling
- **requests**: Industry-standard HTTP library
- **BeautifulSoup**: Best Python HTML parser
- **lxml**: Fast XML/HTML processing

## Usage Guide

### 1. Add a Website to Monitor

1. Go to http://localhost:5000
2. Fill in the form:
   - **Website URL**: `https://example.com`
   - **Scraping Interval**: Choose frequency (5 min - daily)
   - **Crawl Depth**: How deep to follow links (1-5 levels)
   - **Maximum Pages**: Limit pages to crawl (10-1000)
   - **Email**: Your email for alerts
3. Click "Start Monitoring"

### 2. View Analytics

- Click **Analytics** in navigation
- See domain overview, recent activity
- View statistics and charts

### 3. Check Changes

- Click **Changes** in navigation
- See all detected changes (new/modified/removed)
- View similarity scores and timestamps

### 4. Domain Profile

- Click on any domain URL
- See detailed analytics:
  - Total pages, changes, files
  - Link classification statistics
  - Change trends charts
  - Recent changes and scrape history

### 5. Page Profile

- Click "View Details" on any page
- See page-specific information:
  - URL, title, status
  - First seen, last checked
  - Change history
  - Content hash

## Sample Data Explanation

The application stores data in JSON files:

### domains.json
```json
{
  "domains": [
    {
      "id": "uuid-here",
      "url": "https://example.com",
      "interval_minutes": 60,
      "crawl_depth": 2,
      "max_pages": 100,
      "email": "user@example.com",
      "is_active": true,
      "last_scraped_at": "2025-12-13T20:00:00"
    }
  ]
}
```

### pages.json
```json
{
  "pages": [
    {
      "id": "page-uuid",
      "domain_id": "domain-uuid",
      "url": "https://example.com/page",
      "title": "Page Title",
      "content_hash": "sha256-hash",
      "first_seen": "2025-12-13T10:00:00",
      "last_scraped": "2025-12-13T20:00:00",
      "is_active": true,
      "links": {
        "internal": [...],
        "external": [...],
        "files": [...]
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
      "id": "change-uuid",
      "page_id": "page-uuid",
      "change_type": "modified",
      "detected_at": "2025-12-13T20:00:00",
      "similarity_score": 0.85,
      "notified": true
    }
  ]
}
```

## Running Tests

```bash
# Run all tests
pytest tests/

# Run specific test file
pytest tests/test_core.py

# Run with coverage
pytest --cov=scraper tests/

# Verbose output
pytest -v tests/
```

## Configuration Options

Edit `config.py` to customize:

```python
# Email Settings
EMAIL_FROM = "your-email@gmail.com"
EMAIL_PASSWORD = "your-app-password"
EMAIL_TO = "default-recipient@gmail.com"

# SMTP Settings
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

# Crawling Settings
DEFAULT_TIMEOUT = 10  # seconds
USER_AGENT = "WebsiteMonitor/1.0"

# Storage Paths
DATA_DIR = "data"
SNAPSHOTS_DIR = "scraped_websites/snapshots"
ALERTS_DIR = "scraped_websites/alerts"
ATTACHMENTS_DIR = "scraped_websites/attachments"
```

## Email Notifications

### Immediate Alerts
Sent after each scrape run with changes detected:
- Subject: "X changes detected on [domain]"
- Contains: New/Modified/Removed pages with details

### Daily Digest
Sent at 9:00 AM every day:
- Subject: " Daily Digest - X changes detected"
- Contains: Summary of last 24 hours across all domains

## Demo Video

A 5-10 minute demo video is included showing:
1. Project setup and configuration
2. Adding a website to monitor
3. Viewing the dashboard and analytics
4. Checking detected changes
5. Domain and page profiles
6. Email notifications

## Design Document

See [DESIGN.md](DESIGN.md) for detailed architecture and design decisions.

## Troubleshooting

### Email not sending
- Verify Gmail App Password is correct
- Check 2-Step Verification is enabled
- Ensure "Less secure app access" is OFF (use App Password instead)

### Crawl not working
- Check robots.txt allows crawling
- Verify internet connection
- Check domain URL is accessible

### Data not persisting
- Ensure `data/` directory exists
- Check file permissions
- Verify JSON files are not corrupted

## Contributing

This project was developed for a campus drive demonstration. For educational purposes only.

## License

MIT License - Free to use for educational purposes.

## Author

- Email: meghanaa1315@gmail.com
- GitHub: [@Meghanaa0201](https://github.com/Meghanaa0201)


**Note**: This project demonstrates full-stack development skills including:
- Web scraping and crawling
- Data persistence and management
- Scheduled task execution
- Email integration
- Web dashboard development
- RESTful API design
- Testing and documentation
