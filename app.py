from flask import Flask
from web.routes import routes_bp
from scraper import scheduler
import config

app = Flask(__name__)
app.config.from_object(config)
app.secret_key = config.SECRET_KEY

# Register blueprints
app.register_blueprint(routes_bp)

# Initialize scheduler
if config.SCHEDULER_ENABLED:
    scheduler.init_scheduler()
    
    # Re-schedule existing active domains on startup
    from scraper import storage
    domains = storage.get_all_domains()
    for domain in domains:
        if domain.get('is_active', True):
            scheduler.schedule_domain(domain['id'], domain['interval_minutes'])
            print(f"Re-scheduled domain: {domain['url']}")

if __name__ == '__main__':
    print("\n" + "="*60)
    print("🚀 Website Scraper Dashboard Starting...")
    print("="*60)
    print(f"📧 Email notifications: {'ENABLED' if config.EMAIL_ENABLED else 'DISABLED'}")
    print(f"📬 Sending to: {config.EMAIL_TO}")
    print(f"🔄 Scheduler: {'ENABLED' if config.SCHEDULER_ENABLED else 'DISABLED'}")
    print("="*60)
    print("\n🌐 Open your browser and go to: http://localhost:5000")
    print("\n")
    
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)
