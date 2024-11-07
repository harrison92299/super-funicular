import socket
import csv
import sys
from datetime import datetime
import time
import logging
import requests
import os

# Get Telegram credentials from environment variables
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

def setup_logging():
    """Setup logging configuration"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('domain_checker.log')
        ]
    )

def send_telegram_message(message):
    """Send message to Telegram"""
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        data = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message,
            "parse_mode": "HTML",
            "disable_web_page_preview": False
        }
        requests.post(url, data=data)
    except Exception as e:
        logging.error(f"Failed to send Telegram message: {e}")

def check_domain_status(domain):
    """Check if domain resolves to an IP"""
    try:
        ip = socket.gethostbyname(domain)
        return "Registered" if ip else "Not Registered"
    except socket.gaierror:
        return "Not Registered"
    except Exception as e:
        logging.error(f"Error checking {domain}: {str(e)}")
        return "error"

def process_domains(input_file):
    """Process domains that are due for checking"""
    current_time = datetime.now()
    changes = []
    domains_checked = 0
    
    logging.info(f"Starting domain check run at {current_time}")
    
    try:
        # Read the entire CSV into memory
        with open(input_file, 'r') as f:
            reader = csv.DictReader(f)
            domains_data = list(reader)
        
        total_domains = len(domains_data)
        logging.info(f"Loaded {total_domains} domains from CSV")
        
        # Sort domains by last_checked date (None/empty values first)
        domains_data.sort(key=lambda x: datetime.strptime(x['last_checked'], '%Y-%m-%d %H:%M:%S') if x['last_checked'] else datetime.min)
        
        # Process domains
        for row in domains_data:
            domain = row['domain']
            
            # Check if we should process this domain
            if row['last_checked']:
                last_check = datetime.strptime(row['last_checked'], '%Y-%m-%d %H:%M:%S')
                if (current_time - last_check).days < 7:
                    continue
            
            try:
                # Check domain status
                new_status = check_domain_status(domain)
                check_time = current_time.strftime('%Y-%m-%d %H:%M:%S')
                
                # If domain is registered, send notification
                if new_status == "Registered":
                    message = (
                        f"🚨 <b>Registered Domain Found</b> 🚨\n"
                        f"Domain: {domain}\n"
                        f"URL: https://{domain}\n"
                        f"Time: {check_time}\n\n"
                        f"Check domain: https://whois.domaintools.com/{domain}"
                    )
                    send_telegram_message(message)
                    print(f"::warning::REGISTERED DOMAIN FOUND - {domain}")
                
                # Update row with new status and check time
                row['status'] = new_status
                row['last_checked'] = check_time
                
                domains_checked += 1
                logging.info(f"Domain {domain} status: {new_status}")
                
                if domains_checked % 100 == 0:
                    logging.info(f"Progress: Checked {domains_checked} domains")
                
                time.sleep(1)  # Rate limiting
                
                if domains_checked >= 7150:  # Adjusted to handle 200,000 domains weekly
                    break
                    
            except Exception as e:
                logging.error(f"Error processing domain {domain}: {str(e)}")
                continue
        
        # Write all data back to CSV
        with open(input_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['domain', 'base_domain', 'generation_date', 'last_checked', 'status'])
            writer.writeheader()
            writer.writerows(domains_data)
        
        logging.info(f"\nRun Summary:")
        logging.info(f"Total domains checked: {domains_checked}")
        
        return changes
        
    except Exception as e:
        logging.error(f"Critical error in process_domains: {str(e)}")
        raise

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python Checking.py domains.csv")
        sys.exit(1)
    
    input_file = sys.argv[1]
    setup_logging()
    
    try:
        process_domains(input_file)
    except Exception as e:
        logging.error(f"Script failed: {str(e)}")
        sys.exit(1)
