import socket
import csv
import sys
from datetime import datetime, timedelta
import time

def check_domain_status(domain):
    """Check if domain resolves to an IP"""
    try:
        ip = socket.gethostbyname(domain)
        return "registered" if ip else "available"
    except socket.gaierror:
        return "available"

def process_domains(input_file, output_file):
    """Process domains that are due for checking"""
    current_time = datetime.now()
    changes = []
    domains_checked = 0
    
    # Read the entire CSV into memory
    with open(input_file, 'r') as f:
        reader = csv.DictReader(f)
        domains_data = list(reader)
    
    # Process domains
    for row in domains_data:
        domain = row['domain']
        
        # Check if domain was checked in the last 7 days
        if row['last_checked']:
            last_check = datetime.strptime(row['last_checked'], '%Y-%m-%d %H:%M:%S')
            if (current_time - last_check).days < 7:
                continue
        
        # Check domain status
        new_status = check_domain_status(domain)
        check_time = current_time.strftime('%Y-%m-%d %H:%M:%S')
        
        # Check for status change
        old_status = row['status'] if row['status'] else 'unknown'
        if old_status != new_status:
            changes.append({
                'domain': domain,
                'old_status': old_status,
                'new_status': new_status,
                'time': check_time
            })
            print(f"::warning::Domain {domain} changed from {old_status} to {new_status}")
        
        # Update row with new status and check time
        row['status'] = new_status
        row['last_checked'] = check_time
        
        domains_checked += 1
        print(f"Checked {domain}: {new_status}")
        
        time.sleep(1)  # Rate limiting
        
        # Stop after checking reasonable number of domains per run
        if domains_checked >= 1000:  # Adjust this number based on your needs
            break
    
    # Write all data back to CSV
    with open(input_file, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['domain', 'base_domain', 'generation_date', 'last_checked', 'status'])
        writer.writeheader()
        writer.writerows(domains_data)
    
    print(f"\nProcessed {domains_checked} domains")
    return changes

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python Checking.py domains.csv")
        sys.exit(1)
        
    input_file = sys.argv[1]
    process_domains(input_file, input_file)  # Using same file for input and output
