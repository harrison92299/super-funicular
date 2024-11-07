import socket
import csv
import sys
from datetime import datetime, timedelta
import time
import logging

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
                
                # Always log initial status
                old_status = row['status'] if row['status'] else 'unchecked'
                if old_status != new_status:
                    changes.append({
                        'domain': domain,
                        'old_status': old_status,
                        'new_status': new_status,
                        'time': check_time
                    })
                    print(f"::warning::Domain {domain} status: {new_status}")
                    logging.info(f"Domain {domain} status: {new_status}")
                
                # Update row with new status and check time
                row['status'] = new_status
                row['last_checked'] = check_time
                
                domains_checked += 1
                
                if domains_checked % 100 == 0:
                    logging.info(f"Progress: Checked {domains_checked} domains")
                
                time.sleep(1)  # Rate limiting
                
                # Stop after checking reasonable number of domains per run
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
        
        # Log summary
        logging.info(f"\nRun Summary:")
        logging.info(f"Total domains checked: {domains_checked}")
        logging.info(f"Status changes detected: {len(changes)}")
        logging.info(f"Completion time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        return changes
        
    except Exception as e:
        logging.error(f"Critical error in process_domains: {str(e)}")
        raise

def generate_summary(changes):
    """Generate a summary of changes"""
    if not changes:
        return "No domains checked in this run."
    
    registered_count = sum(1 for change in changes if change['new_status'] == 'Registered')
    not_registered_count = sum(1 for change in changes if change['new_status'] == 'Not Registered')
    
    summary = f"Domain Check Summary:\n"
    summary += f"Total domains checked: {len(changes)}\n"
    summary += f"Registered domains: {registered_count}\n"
    summary += f"Not Registered domains: {not_registered_count}\n\n"
    summary += "Registered Domains:\n"
    
    # List registered domains
    for change in changes:
        if change['new_status'] == 'Registered':
            summary += f"- {change['domain']}\n"
    
    return summary

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python Checking.py domains.csv")
        sys.exit(1)
    
    input_file = sys.argv[1]
    
    # Setup logging
    setup_logging()
    
    try:
        # Process domains and get changes
        changes = process_domains(input_file)
        
        # Generate and log summary
        summary = generate_summary(changes)
        logging.info("\nCheck Summary:\n" + summary)
        
    except Exception as e:
        logging.error(f"Script failed: {str(e)}")
        sys.exit(1)
