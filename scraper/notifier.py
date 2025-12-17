import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime
import config

def send_email_alert(recipient: str, subject: str, changes: list, domain_url: str):
    """Send email digest of detected changes"""
    if not config.EMAIL_ENABLED:
        print("Email notifications disabled")
        return False
    
    try:
        # Create message
        msg = MIMEMultipart('alternative')
        msg['From'] = config.EMAIL_FROM
        msg['To'] = recipient
        msg['Subject'] = subject
        
        # Create HTML content
        html_content = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                          color: white; padding: 20px; border-radius: 8px; }}
                .content {{ padding: 20px; background: #f9f9f9; border-radius: 8px; margin-top: 20px; }}
                .change {{ background: white; padding: 15px; margin: 10px 0; border-left: 4px solid #667eea; 
                          border-radius: 4px; }}
                .change-type {{ font-weight: bold; color: #667eea; text-transform: uppercase; }}
                .url {{ color: #666; font-size: 0.9em; word-break: break-all; }}
                .footer {{ margin-top: 20px; padding-top: 20px; border-top: 1px solid #ddd; 
                          color: #666; font-size: 0.9em; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h2>🔔 Website Change Alert</h2>
                <p>Changes detected on: <strong>{domain_url}</strong></p>
                <p>Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>
            
            <div class="content">
                <h3>Detected Changes ({len(changes)})</h3>
        """
        
        for change in changes:
            change_type = change.get('change_type', 'unknown')
            page_url = change.get('page_url', 'Unknown URL')
            similarity = change.get('similarity_score')
            
            similarity_text = ""
            if similarity is not None:
                similarity_pct = similarity * 100
                similarity_text = f"<br><small>Similarity: {similarity_pct:.1f}%</small>"
            
            html_content += f"""
                <div class="change">
                    <div class="change-type">{change_type}</div>
                    <div class="url">{page_url}</div>
                    {similarity_text}
                </div>
            """
        
        html_content += """
            </div>
            
            <div class="footer">
                <p>This is an automated alert from your Website Scraper.</p>
                <p>Check your dashboard for detailed diff views.</p>
            </div>
        </body>
        </html>
        """
        
        # Attach HTML content
        msg.attach(MIMEText(html_content, 'html'))
        
        # Send email
        server = smtplib.SMTP(config.SMTP_SERVER, config.SMTP_PORT)
        server.starttls()
        server.login(config.SMTP_USERNAME, config.SMTP_PASSWORD)
        server.send_message(msg)
        server.quit()
        
        print(f"✅ Email sent to {recipient}")
        return True
        
    except Exception as e:
        print(f"❌ Failed to send email: {e}")
        return False

def send_scrape_complete_notification(recipient: str, domain_url: str, stats: dict):
    """Send notification when scrape completes"""
    subject = f"Scrape Complete: {domain_url}"
    
    changes_count = stats.get('pages_changed', 0) + stats.get('pages_new', 0)
    
    if changes_count == 0:
        # No changes detected
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif;">
            <div style="background: #4CAF50; color: white; padding: 20px; border-radius: 8px;">
                <h2>✅ Scrape Complete - No Changes</h2>
                <p><strong>{domain_url}</strong></p>
                <p>Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>
            <div style="padding: 20px; background: #f9f9f9; margin-top: 20px; border-radius: 8px;">
                <p>Pages crawled: {stats.get('pages_crawled', 0)}</p>
                <p>No changes detected since last scrape.</p>
            </div>
        </body>
        </html>
        """
    else:
        # Changes detected
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif;">
            <div style="background: #FF9800; color: white; padding: 20px; border-radius: 8px;">
                <h2>🔔 Scrape Complete - Changes Detected</h2>
                <p><strong>{domain_url}</strong></p>
                <p>Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>
            <div style="padding: 20px; background: #f9f9f9; margin-top: 20px; border-radius: 8px;">
                <p>Pages crawled: {stats.get('pages_crawled', 0)}</p>
                <p>New pages: {stats.get('pages_new', 0)}</p>
                <p>Changed pages: {stats.get('pages_changed', 0)}</p>
            </div>
        </body>
        </html>
        """
    
    try:
        msg = MIMEMultipart('alternative')
        msg['From'] = config.EMAIL_FROM
        msg['To'] = recipient
        msg['Subject'] = subject
        msg.attach(MIMEText(html_content, 'html'))
        
        server = smtplib.SMTP(config.SMTP_SERVER, config.SMTP_PORT)
        server.starttls()
        server.login(config.SMTP_USERNAME, config.SMTP_PASSWORD)
        server.send_message(msg)
        server.quit()
        
        print(f"✅ Completion email sent to {recipient}")
        return True
        
    except Exception as e:
        print(f"❌ Failed to send completion email: {e}")
        return False

def send_email(to_email, subject, html_content):
    """
    Generic function to send HTML email
    Used by digest module
    """
    try:
        msg = MIMEMultipart('alternative')
        msg['From'] = config.EMAIL_FROM
        msg['To'] = to_email
        msg['Subject'] = subject
        
        msg.attach(MIMEText(html_content, 'html'))
        
        server = smtplib.SMTP(config.SMTP_SERVER, config.SMTP_PORT) # Use config for SMTP server
        server.starttls()
        server.login(config.SMTP_USERNAME, config.SMTP_PASSWORD) # Use config for login credentials
        server.send_message(msg)
        server.quit()
        
        print(f"✅ Email sent to {to_email}") # Added print statement for success
        return True
    except Exception as e:
        print(f"❌ Error sending email: {e}")
        return False
