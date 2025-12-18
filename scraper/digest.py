"""
Daily digest email generator
Aggregates all changes from last 24 hours and sends a single email
"""

from datetime import datetime, timedelta
from scraper import storage, notifier
import config


def get_recent_changes(hours=24):
    """Get all changes from the last N hours"""
    cutoff_time = datetime.now() - timedelta(hours=hours)
    
    all_changes = storage.load_json(config.CHANGES_FILE).get('changes', [])
    
    recent = []
    for change in all_changes:
        detected_at = datetime.fromisoformat(change['detected_at'])
        if detected_at >= cutoff_time:
            recent.append(change)
    
    return recent


def generate_daily_digest():
    """
    Generate daily digest of all changes across all domains
    Returns dict with digest data
    """
    domains = storage.get_all_domains()
    changes = get_recent_changes(24)
    
    # Group changes by domain
    digest = {
        'date': datetime.now().strftime('%Y-%m-%d'),
        'total_changes': len(changes),
        'domains': []
    }
    
    for domain in domains:
        domain_pages = storage.get_domain_pages(domain['id'])
        page_ids = [p['id'] for p in domain_pages]
        
        domain_changes = [c for c in changes if c['page_id'] in page_ids]
        
        if domain_changes:
            stats = {
                'new': len([c for c in domain_changes if c['change_type'] == 'new']),
                'modified': len([c for c in domain_changes if c['change_type'] == 'modified']),
                'removed': len([c for c in domain_changes if c['change_type'] == 'removed'])
            }
            
            digest['domains'].append({
                'url': domain['url'],
                'email': domain.get('email', config.EMAIL_TO),
                'changes': domain_changes,
                'stats': stats
            })
    
    return digest


def format_digest_email(digest):
    """Format digest as HTML email"""
    html = f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; background: #f5f5f5; padding: 20px; }}
            .container {{ max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; }}
            h1 {{ color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px; }}
            h2 {{ color: #3498db; margin-top: 30px; }}
            .summary {{ background: #ecf0f1; padding: 15px; border-radius: 5px; margin: 20px 0; }}
            .stats {{ display: flex; gap: 20px; margin: 15px 0; }}
            .stat {{ background: white; padding: 10px 15px; border-radius: 5px; border-left: 4px solid; }}
            .stat.new {{ border-left-color: #27ae60; }}
            .stat.modified {{ border-left-color: #f39c12; }}
            .stat.removed {{ border-left-color: #e74c3c; }}
            .change-item {{ background: #f8f9fa; padding: 12px; margin: 8px 0; border-radius: 4px; border-left: 3px solid; }}
            .change-item.new {{ border-left-color: #27ae60; }}
            .change-item.modified {{ border-left-color: #f39c12; }}
            .change-item.removed {{ border-left-color: #e74c3c; }}
            .badge {{ display: inline-block; padding: 4px 10px; border-radius: 3px; font-size: 11px; font-weight: bold; }}
            .badge.new {{ background: #d4edda; color: #155724; }}
            .badge.modified {{ background: #fff3cd; color: #856404; }}
            .badge.removed {{ background: #f8d7da; color: #721c24; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>📊 Daily Website Scraper Digest</h1>
            <div class="summary">
                <strong>Date:</strong> {digest['date']}<br>
                <strong>Total Changes:</strong> {digest['total_changes']}
            </div>
    """
    
    if not digest['domains']:
        html += "<p>No changes detected in the last 24 hours.</p>"
    else:
        for domain_data in digest['domains']:
            stats = domain_data['stats']
            html += f"""
            <h2>🌐 {domain_data['url']}</h2>
            <div class="stats">
                <div class="stat new">
                    <strong>{stats['new']}</strong> New
                </div>
                <div class="stat modified">
                    <strong>{stats['modified']}</strong> Modified
                </div>
                <div class="stat removed">
                    <strong>{stats['removed']}</strong> Removed
                </div>
            </div>
            """
            
            for change in domain_data['changes'][:10]:  # Limit to 10 per domain
                page = storage.get_page_by_id(change['page_id'])
                page_url = page['url'] if page else 'Unknown'
                page_title = page.get('title', 'Unknown') if page else 'Unknown'
                
                similarity = ""
                if change.get('similarity_score'):
                    similarity = f" (Similarity: {change['similarity_score']*100:.1f}%)"
                
                html += f"""
                <div class="change-item {change['change_type']}">
                    <span class="badge {change['change_type']}">{change['change_type'].upper()}</span>
                    <strong>{page_title}</strong><br>
                    <small>{page_url}</small>{similarity}
                </div>
                """
            
            if len(domain_data['changes']) > 10:
                html += f"<p><em>...and {len(domain_data['changes']) - 10} more changes</em></p>"
    
    html += """
        </div>
    </body>
    </html>
    """
    
    return html


def send_daily_digest():
    """Send daily digest email to all unique email addresses"""
    digest = generate_daily_digest()
    
    if digest['total_changes'] == 0:
        print("No changes in last 24 hours, skipping daily digest")
        return
    
    # Get unique emails
    emails = set()
    for domain_data in digest['domains']:
        emails.add(domain_data['email'])
    
    # Send digest to each email
    html = format_digest_email(digest)
    subject = f"📊 Daily Digest - {digest['total_changes']} changes detected ({digest['date']})"
    
    for email in emails:
        try:
            notifier.send_email(email, subject, html)
            print(f"✅ Daily digest sent to {email}")
        except Exception as e:
            print(f"❌ Failed to send digest to {email}: {e}")
