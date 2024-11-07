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
    
    # Read existing status file if it exists
    try:
        with open(output_file, 'r') as f:
            reader = csv.DictReader(f)
            status_data = list(reader)
            status_dict = {row['Domain']: row for row in status_data}
    except FileNotFoundError:
        status_dict = {}
    
    # Process domains
    updated_status = []
    with open(input_file, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            domain = row['Domain']
            
            # Check if domain exists in status file and when it was last checked
            if domain in status_dict:
                last_check = datetime.strptime(status_dict[domain]['Last_Checked'], '%Y-%m-%d %H:%M:%S')
                if (current_time - last_check).days < 7:  # Skip if checked less than 7 days ago
                    updated_status.append(status_dict[domain])
                    continue
            
            # Check domain status
            status = check_domain_status(domain)
            check_time = current_time.strftime('%Y-%m-%d %H:%M:%S')
            
            # Check for status change
            if domain in status_dict and status_dict[domain]['Status'] != status:
                changes.append({
                    'domain': domain,
                    'old_status': status_dict[domain]['Status'],
                    'new_status': status,
                    'time': check_time
                })
                print(f"::warning::Domain {domain} changed from {status_dict[domain]['Status']} to {status}")
            
            # Update status
            updated_status.append({
                'Domain': domain,
                'Status': status,
                'Last_Checked': check_time
            })
            
            domains_checked += 1
            print(f"Checked {domain}: {status}")
            
            time.sleep(1)  # Rate limiting
            
            # Stop after checking reasonable number of domains per run
            if domains_checked >= 1000:  # Adjust this number based on your needs
                break
    
    # Write updated status to file
    with open(output_file, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['Domain', 'Status', 'Last_Checked'])
        writer.writeheader()
        writer.writerows(updated_status)
    
    print(f"\nProcessed {domains_checked} domains")
    return changes

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python Checking.py input_file output_file")
        sys.exit(1)
        
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    
    process_domains(input_file, output_file)
