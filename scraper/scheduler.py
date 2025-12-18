from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
from scraper import core, storage, notifier
import config

scheduler = BackgroundScheduler()
active_jobs = {}

def scrape_domain_job(domain_id):
    """Background job to scrape entire domain"""
    print(f"\n{'='*60}")
    print(f"🕐 Scheduled scrape starting for domain: {domain_id}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}\n")
    
    domain = storage.get_domain(domain_id)
    if not domain or not domain.get('is_active'):
        print(f"Domain {domain_id} not found or inactive")
        return
    
    url = domain['url']
    email = domain.get('email', config.EMAIL_TO)
    crawl_depth = domain.get('crawl_depth', config.DEFAULT_CRAWL_DEPTH)
    max_pages = domain.get('max_pages', config.DEFAULT_MAX_PAGES)
    
    # Create scrape run
    run = storage.create_scrape_run(domain_id)
    run_id = run['id']
    
    try:
        # Import crawler
        from scraper import crawler
        
        # Use full domain crawler
        print(f"Crawling: {url}")
        print(f"Settings: depth={crawl_depth}, max_pages={max_pages}")
        
        result = crawler.crawl_domain(
            base_url=url,
            max_depth=crawl_depth,
            max_pages=max_pages,
            domain_id=domain_id,
            run_id=run_id
        )
        
        # Detect removed pages
        removed = storage.detect_removed_pages(domain_id, result['urls'])
        
        # Record removed pages as changes
        for page in removed:
            storage.add_change(
                page_id=page['id'],
                run_id=run_id,
                change_type='removed',
                old_snapshot=None,
                new_snapshot=None,
                diff_path=None,
                similarity=None
            )
        
        # Update run stats
        stats = {
            'status': 'completed',
            'completed_at': datetime.now().isoformat(),
            'pages_crawled': result['pages_crawled'],
            'pages_changed': result['pages_modified'],
            'pages_new': result['pages_new'],
            'pages_removed': len(removed),
            'files_downloaded': result.get('files_downloaded', 0)
        }
        
        storage.update_scrape_run(run_id, stats)
        
        # Update domain last scraped time
        storage.update_domain(domain_id, {'last_scraped_at': datetime.now().isoformat()})
        
        # Send email notification if changes detected
        total_changes = result['pages_new'] + result['pages_modified'] + len(removed)
        
        if total_changes > 0:
            changes = storage.get_run_changes(run_id)
            
            # Enrich changes with page URL
            for change in changes:
                page_id = change.get('page_id')
                page = storage.get_page_by_id(page_id)
                if page:
                    change['page_url'] = page['url']
                    change['page_title'] = page.get('title', 'Unknown')
            
            if changes:
                subject = f"🔔 {total_changes} changes detected on {url}"
                notifier.send_email_alert(email, subject, changes, url)
                
                # Mark changes as notified
                change_ids = [c['id'] for c in changes]
                storage.mark_changes_notified(change_ids)
        else:
            # Send completion notification (no changes)
            notifier.send_scrape_complete_notification(email, url, stats)
        
        print(f"\n✅ Scrape completed for {url}")
        print(f"   Pages crawled: {result['pages_crawled']}")
        print(f"   New: {result['pages_new']}, Modified: {result['pages_modified']}, Removed: {len(removed)}")
        print(f"   Files: {result.get('files_downloaded', 0)}\n")
        
    except Exception as e:
        print(f"❌ Error scraping {url}: {e}")
        import traceback
        traceback.print_exc()
        storage.update_scrape_run(run_id, {
            'status': 'failed',
            'completed_at': datetime.now().isoformat(),
            'error_message': str(e)
        })


def init_scheduler():
    """Initialize scheduler"""
    if not scheduler.running:
        scheduler.start()
        print("✅ Scheduler started")
        
        # Schedule daily digest at 9 AM
        from scraper import digest
        scheduler.add_job(
            digest.send_daily_digest,
            trigger=CronTrigger(hour=9, minute=0),
            id='daily_digest',
            name='Daily Digest Email'
        )
        print("✅ Daily digest scheduled for 9:00 AM")

def schedule_domain(domain_id, interval_minutes):
    """Schedule periodic scraping for a domain"""
    job_id = f"domain_{domain_id}"
    
    # Remove existing job if any
    if job_id in active_jobs:
        scheduler.remove_job(job_id)
    
    # Add new job
    trigger = IntervalTrigger(minutes=interval_minutes)
    job = scheduler.add_job(
        scrape_domain_job,
        trigger=trigger,
        args=[domain_id],
        id=job_id,
        replace_existing=True
    )
    
    active_jobs[job_id] = job
    print(f"✅ Scheduled domain {domain_id} to scrape every {interval_minutes} minutes")
    
    return job

def unschedule_domain(domain_id):
    """Remove scheduled job for a domain"""
    job_id = f"domain_{domain_id}"
    
    if job_id in active_jobs:
        scheduler.remove_job(job_id)
        del active_jobs[job_id]
        print(f"✅ Unscheduled domain {domain_id}")

def trigger_immediate_scrape(domain_id):
    """Trigger immediate scrape for a domain"""
    print(f"🚀 Triggering immediate scrape for domain {domain_id}")
    scrape_domain_job(domain_id)

def get_scheduled_jobs():
    """Get all scheduled jobs"""
    return scheduler.get_jobs()

def shutdown_scheduler():
    """Shutdown scheduler"""
    if scheduler.running:
        scheduler.shutdown()
        print("Scheduler stopped")
