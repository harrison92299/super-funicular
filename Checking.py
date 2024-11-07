import socket
import csv
import sys
from datetime import datetime

def check_domain_status(domain):
    """Check if domain resolves to an IP"""
    try:
        ip = socket.gethostbyname(domain)
        return "registered" if ip else "available"
    except socket.gaierror:
        return "available"

def process_batch(input_file, output_file, status_file):
    """Process a batch of domains and track changes"""
    # Read previous status if exists
    previous_status = {}
    try:
        with open(status_file, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                previous_status[row['Domain']] = row['Status']
    except FileNotFoundError:
        previous_status = {}

    changes = []
    current_status = {}

    # Process domains
    with open(input_file, 'r') as f, open(output_file, 'w') as out:
        reader = csv.reader(f)
        writer = csv.writer(out)
        writer.writerow(['Domain', 'Status', 'Check_Time'])
        
        next(reader)  # Skip header if exists
        for row in reader:
            domain = row[0].strip()
            status = check_domain_status(domain)
            check_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            writer.writerow([domain, status, check_time])
            current_status[domain] = status
            
            # Check for status change
            if domain in previous_status and previous_status[domain] != status:
                changes.append({
                    'domain': domain,
                    'old_status': previous_status[domain],
                    'new_status': status,
                    'time': check_time
                })
            print(f"{domain}: {status}")

    # Save current status
    with open(status_file, 'w') as f:
        writer = csv.writer(f)
        writer.writerow(['Domain', 'Status'])
        for domain, status in current_status.items():
            writer.writerow([domain, status])

    return changes

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python Checking.py input_file output_file status_file")
        sys.exit(1)
        
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    status_file = sys.argv[3]
    
    changes = process_batch(input_file, output_file, status_file)
    
    # Print changes for GitHub Actions
    if changes:
        print("\nStatus Changes Detected:")
        for change in changes:
            print(f"::warning::Domain {change['domain']} changed from {change['old_status']} to {change['new_status']}")
