import os
import argparse
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import urllib3
import hashlib
from datetime import datetime
import sys  # Added for console output flushing and progress reporting

# Suppress SSL warnings for self-signed certs (common on .onion sites)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# MIME types considered safe for download
SAFE_MIME_TYPES = {
    'image/jpeg', 'image/png', 'application/pdf', 'application/zip',
    'text/plain', 'image/jpg'
}

def create_tor_session():
    session = requests.Session()
    session.proxies = {
        'http': 'socks5h://127.0.0.1:9050',
        'https': 'socks5h://127.0.0.1:9050'
    }
    session.verify = False  # Disable SSL verification for .onion
    return session

def is_valid_file(url, extensions):
    parsed = urlparse(url)
    return any(parsed.path.lower().endswith(ext) for ext in extensions)

def get_sha256(file_path):
    sha256 = hashlib.sha256()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            sha256.update(chunk)
    return sha256.hexdigest()

def log_download(dest_folder, info):
    log_path = os.path.join(dest_folder, "download_log.txt")
    with open(log_path, 'a') as log:
        log.write(f"{info['timestamp']} UTC\n")
        log.write(f"  Source: {info['url']}\n")
        log.write(f"  Saved to: {info['path']}\n")
        log.write(f"  MIME type: {info['mime']}\n")
        log.write(f"  SHA256: {info['hash']}\n")
        log.write("-" * 40 + "\n")

# Helper function for human-readable size formatting
def format_size(bytes_val):
    if bytes_val is None:
        return "Unknown Size"
    if bytes_val < 1024:
        return f"{bytes_val} B"
    elif bytes_val < 1024**2:
        return f"{bytes_val / 1024:.2f} KB"
    elif bytes_val < 1024**3:
        return f"{bytes_val / 1024**2:.2f} MB"
    else:
        return f"{bytes_val / 1024**3:.2f} GB"

def download_file(session, url, dest_folder, dry_run=False):
    # Determine the local filename
    parsed_url = urlparse(url)
    local_filename = os.path.join(dest_folder, os.path.basename(parsed_url.path))

    if dry_run:
        print(f"[DRY-RUN] Would download: {url} → {local_filename}")
        return
    
    try:
        # Start request with stream=True
        response = session.get(url, stream=True, timeout=60) # Increased timeout for safety
        response.raise_for_status()

        content_type = response.headers.get('Content-Type', '').split(';')[0].strip()
        if content_type not in SAFE_MIME_TYPES:
            print(f"[✗] Skipped {url} due to unsafe MIME type: {content_type}")
            return

        # Get total size from headers
        total_size = response.headers.get('Content-Length')
        if total_size is not None:
            total_size = int(total_size)
            total_size_formatted = format_size(total_size)
        else:
            total_size_formatted = "Unknown Size"
        
        # Initialize downloaded bytes counter
        downloaded_size = 0
        chunk_size = 8192
        
        print(f"[↓] Downloading {os.path.basename(local_filename)} (Total: {total_size_formatted})...")

        # Open file and start iterating through chunks for download
        with open(local_filename, 'wb') as f:
            for chunk in response.iter_content(chunk_size=chunk_size):
                if chunk: # filter out keep-alive new chunks
                    f.write(chunk)
                    downloaded_size += len(chunk)

                    # Progress Reporting Logic using carriage return (\r)
                    status_line = f"    Progress: {format_size(downloaded_size)}"
                    
                    if total_size:
                        percent = (downloaded_size / total_size) * 100
                        status_line += f" / {total_size_formatted} ({percent:.2f}%)"
                    
                    # Print and flush the line, overwriting the previous output
                    sys.stdout.write(status_line + ' ' * (70 - len(status_line)) + '\r')
                    sys.stdout.flush()
            
            # Print a final newline character to clean the console output
            sys.stdout.write('\n')
        
        # --- Post-download actions ---
        file_hash = get_sha256(local_filename)
        timestamp = datetime.utcnow().isoformat()

        print(f"[✓] Downloaded: {os.path.basename(local_filename)}")
        print(f"     └─ Source: {url}")
        print(f"     └─ MIME: {content_type}")
        print(f"     └─ SHA256: {file_hash}")
        print(f"     └─ Timestamp: {timestamp} UTC")

        log_download(dest_folder, {
            'timestamp': timestamp,
            'url': url,
            'path': local_filename,
            'mime': content_type,
            'hash': file_hash
        })

    except Exception as e:
        # Clear the progress line before printing the error message
        sys.stdout.write(' ' * 80 + '\r') 
        sys.stdout.flush()
        print(f"[✗] Failed to download {url}: {e}")

def scrape_onion(url, dest_folder, extensions, dry_run=False):
    session = create_tor_session()
    try:
        response = session.get(url, timeout=30)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        links = soup.find_all('a', href=True)
        os.makedirs(dest_folder, exist_ok=True)
        for link in links:
            file_url = urljoin(url, link['href'])
            if is_valid_file(file_url, extensions):
                download_file(session, file_url, dest_folder, dry_run)
    except Exception as e:
        print(f"[✗] Error accessing {url}: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download screenshots and files from an onion URL.")
    parser.add_argument("url", help="Target onion URL (e.g., http://xyz.onion)")
    parser.add_argument("-o", "--output", default="downloads", help="Destination folder")
    parser.add_argument("-e", "--extensions", nargs="+", default=[".jpg", ".png", ".pdf", ".zip", ".txt"], help="File extensions to download")
    parser.add_argument("--dry-run", action="store_true", help="List files without downloading")
    args = parser.parse_args()

    scrape_onion(args.url, args.output, args.extensions, args.dry_run)
