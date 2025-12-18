from flask import Blueprint, render_template, request, redirect, url_for, flash
from scraper import storage, scheduler
import config

routes_bp = Blueprint('routes', __name__)

@routes_bp.route('/')
def index():
    """Landing page with URL input and domain list"""
    domains = storage.get_all_domains()
    analytics = storage.get_analytics_data()
    return render_template('index.html', domains=domains, analytics=analytics)

@routes_bp.route('/websites')
def websites():
    """List of monitored websites"""
    domains = storage.get_all_domains()
    return render_template('websites.html', domains=domains)

@routes_bp.route('/add_domain', methods=['POST'])
def add_domain():
    """Add new domain to monitor"""
    url = request.form.get('url', '').strip()
    interval_minutes = int(request.form.get('interval_minutes', 60))
    email = request.form.get('email', '').strip()
    crawl_depth = int(request.form.get('crawl_depth', 2))
    max_pages = int(request.form.get('max_pages', 100))
    
    if not url:
        flash('URL is required', 'error')
        return redirect(url_for('routes.index'))
    
    # Add http:// if not present
    if not url.startswith('http'):
        url = 'https://' + url
    
    # Add domain with crawl settings
    domain = storage.add_domain(url, interval_minutes, email)
    storage.update_domain(domain['id'], {
        'crawl_depth': crawl_depth,
        'max_pages': max_pages
    })
    
    # Schedule scraping
    scheduler.schedule_domain(domain['id'], interval_minutes)
    
    # Trigger immediate first scrape
    scheduler.trigger_immediate_scrape(domain['id'])
    
    flash(f'Domain added and first scrape triggered! Will scrape every {interval_minutes} minutes.', 'success')
    return redirect(url_for('routes.index'))

@routes_bp.route('/domain/<domain_id>')
def domain_profile(domain_id):
    """Detailed profile page for a domain"""
    domain = storage.get_domain(domain_id)
    if not domain:
        flash('Domain not found', 'error')
        return redirect(url_for('routes.index'))
    
    pages = storage.get_domain_pages(domain_id)
    runs = storage.get_domain_runs(domain_id)
    changes = storage.get_domain_changes(domain_id)
    files = storage.get_domain_files(domain_id)
    
    # Calculate statistics
    active_pages = [p for p in pages if p.get('is_active', True)]
    removed_pages = [p for p in pages if not p.get('is_active', True)]
    
    stats = {
        'total_pages': len(pages),
        'active_pages': len(active_pages),
        'removed_pages': len(removed_pages),
        'total_changes': len(changes),
        'total_files': len(files),
        'total_runs': len(runs),
        'total_internal_links': 0,
        'total_external_links': 0,
        'total_file_links': 0,
        'top_external_domains': [],
        'successful_runs': len([r for r in runs if r['status'] == 'completed'])
    }
    
    # Calculate link statistics
    from collections import Counter
    external_domains = Counter()
    
    for page in pages:
        links = page.get('links', {})
        stats['total_internal_links'] += len(links.get('internal', []))
        stats['total_external_links'] += len(links.get('external', []))
        stats['total_file_links'] += len(links.get('files', []))
        
        # Count external domains
        for ext_link in links.get('external', []):
            ext_domain = ext_link.get('domain', '')
            if ext_domain:
                external_domains[ext_domain] += 1
    
    stats['top_external_domains'] = external_domains.most_common(10)
    
    # Sort pages by last checked
    pages.sort(key=lambda x: x.get('last_checked_at', ''), reverse=True)
    
    # Sort runs by started_at
    runs.sort(key=lambda x: x.get('started_at', ''), reverse=True)
    
    # Sort changes by detected_at
    changes.sort(key=lambda x: x.get('detected_at', ''), reverse=True)
    
    return render_template('domain_profile.html',
                         domain=domain,
                         pages=pages,
                         runs=runs,
                         changes=changes,
                         files=files,
                         stats=stats)

@routes_bp.route('/page/<page_id>')
def page_profile(page_id):
    """Detailed profile for a specific page/link"""
    page = storage.get_page_by_id(page_id)
    if not page:
        flash('Page not found', 'error')
        return redirect(url_for('routes.index'))
    
    # Get domain
    domain = storage.get_domain(page['domain_id'])
    
    # Get all changes for this page
    changes = storage.get_page_changes(page_id)
    changes.sort(key=lambda x: x.get('detected_at', ''), reverse=True)
    
    return render_template('page_profile.html',
                         page=page,
                         domain=domain,
                         changes=changes)

@routes_bp.route('/edit_domain/<domain_id>', methods=['GET', 'POST'])
def edit_domain(domain_id):
    """Edit domain settings"""
    domain = storage.get_domain(domain_id)
    if not domain:
        flash('Domain not found', 'error')
        return redirect(url_for('routes.index'))
    
    if request.method == 'POST':
        # Update settings
        interval_minutes = int(request.form.get('interval_minutes', 60))
        email = request.form.get('email', '').strip()
        crawl_depth = int(request.form.get('crawl_depth', 2))
        max_pages = int(request.form.get('max_pages', 100))
        
        storage.update_domain(domain_id, {
            'interval_minutes': interval_minutes,
            'email': email,
            'crawl_depth': crawl_depth,
            'max_pages': max_pages
        })
        
        # Reschedule if active
        if domain.get('is_active', True):
            scheduler.unschedule_domain(domain_id)
            scheduler.schedule_domain(domain_id, interval_minutes)
        
        flash('Domain settings updated!', 'success')
        return redirect(url_for('routes.domain_profile', domain_id=domain_id))
    
    return render_template('edit_domain.html', domain=domain)


@routes_bp.route('/delete_domain/<domain_id>')
def delete_domain(domain_id):
    """Delete domain"""
    scheduler.unschedule_domain(domain_id)
    storage.delete_domain(domain_id)
    flash('Domain deleted', 'success')
    return redirect(url_for('routes.index'))

@routes_bp.route('/toggle_domain/<domain_id>')
def toggle_domain(domain_id):
    """Toggle domain active status"""
    domain = storage.get_domain(domain_id)
    if domain:
        new_status = not domain.get('is_active', True)
        storage.update_domain(domain_id, {'is_active': new_status})
        
        if new_status:
            scheduler.schedule_domain(domain_id, domain['interval_minutes'])
            flash('Domain activated', 'success')
        else:
            scheduler.unschedule_domain(domain_id)
            flash('Domain paused', 'info')
    
    return redirect(url_for('routes.index'))

@routes_bp.route('/scrape_now/<domain_id>')
def scrape_now(domain_id):
    """Trigger immediate scrape"""
    scheduler.trigger_immediate_scrape(domain_id)
    flash('Scrape triggered!', 'success')
    return redirect(url_for('routes.index'))

@routes_bp.route('/dashboard')
def dashboard():
    """Analytics dashboard"""
    analytics = storage.get_analytics_data()
    domains = storage.get_all_domains()
    return render_template('dashboard.html', analytics=analytics, domains=domains)

@routes_bp.route('/changes')
def changes():
    """View recent changes"""
    recent_changes = storage.get_recent_changes(50)
    
    # Enrich changes with page and domain info
    pages_data = storage.load_json(config.PAGES_FILE)
    domains_data = storage.load_json(config.DOMAINS_FILE)
    
    for change in recent_changes:
        # Find page
        for page in pages_data.get('pages', []):
            if page['id'] == change['page_id']:
                change['page_url'] = page['url']
                change['page_title'] = page['title']
                
                # Find domain
                for domain in domains_data.get('domains', []):
                    if domain['id'] == page['domain_id']:
                        change['domain_url'] = domain['url']
                        break
                break
    
    return render_template('changes.html', changes=recent_changes)

@routes_bp.route('/download/<file_id>')
def download_file(file_id):
    """Download a scraped file"""
    import os
    from flask import send_file, abort
    
    # Get file record
    # Note: storage.get_file_by_id isn't implemented explicitly, but we can search for it
    # Ideally should implement get_file_by_id in storage.py, but for now we load settings
    
    # Simple search in settings.json
    settings = storage.load_json(config.SETTINGS_FILE)
    file_record = None
    for f in settings.get('files', []):
        if f['id'] == file_id:
            file_record = f
            break
            
    if not file_record:
        flash('File not found', 'error')
        return redirect(url_for('routes.index'))
        
    file_path = file_record['file_path']
    if not os.path.exists(file_path):
        flash('File missing on disk', 'error')
        return redirect(url_for('routes.index'))
        
    # Serve file
    filename = os.path.basename(file_path)
    return send_file(file_path, as_attachment=True, download_name=filename)


@routes_bp.route('/fix_data', methods=['POST'])
def fix_data():
    """Run data repair scripts"""
    try:
        # Run notifications fix
        count_notif = storage.fix_notification_statuses()
        
        # Run titles fix
        count_titles = storage.fix_missing_titles()
        
        message = f"✅ Data repaired! Fixed {count_notif} notifications"
        if count_titles > 0:
            message += f" and {count_titles} titles"
        message += "."
        flash(message, 'success')
    except Exception as e:
        flash(f'⚠️ Repair failed: {e}', 'error')
        print(f"Repair error: {e}")
        
    return redirect(request.referrer or url_for('routes.dashboard'))

