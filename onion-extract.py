import os
import argparse
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import urllib3
import hashlib
from datetime import datetime
import sys
import json
import time
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from tqdm import tqdm

# Suppress SSL warnings for self-signed certs (common on .onion sites)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configuration defaults
MAX_FILE_SIZE = 500 * 1024 * 1024  # 500 MB limit
DEFAULT_CONFIG_FILE = "onion-extract-config.json"

# MIME types considered safe for download (expanded list - Enhancement #11)
SAFE_MIME_TYPES = {
    'image/jpeg', 'image/png', 'image/gif', 'image/webp', 'image/jpg',
    'application/pdf', 'application/zip', 'application/x-tar',
    'text/plain', 'text/html', 'application/json',
    'video/mp4', 'audio/mpeg'
}

def create_tor_session(max_retries=3):
    """
    Create a Tor session with connection pooling and retry logic.
    Enhancement #2: Connection Pooling & Retry Logic
    """
    session = requests.Session()
    session.proxies = {
        'http': 'socks5h://127.0.0.1:9050',
        'https': 'socks5h://127.0.0.1:9050'
    }
    session.verify = False  # Disable SSL verification for .onion
    
    # Add retry strategy for unstable .onion networks
    retry_strategy = Retry(
        total=max_retries,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
        backoff_factor=1
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session

def is_valid_file(url, extensions):
    """Check if URL ends with one of the allowed extensions."""
    parsed = urlparse(url)
    return any(parsed.path.lower().endswith(ext) for ext in extensions)

def is_onion_url(url):
    """
    Verify URL is a .onion address.
    Enhancement #7: Better URL Validation
    """
    parsed = urlparse(url)
    return parsed.netloc.endswith('.onion')

def get_sha256(file_path):
    """Calculate SHA256 hash of a file."""
    sha256 = hashlib.sha256()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            sha256.update(chunk)
    return sha256.hexdigest()

def get_unique_filename(dest_folder, filename):
    """
    Ensure unique filename by appending incrementing number if needed.
    Enhancement #1: Duplicate File Handling
    """
    path = os.path.join(dest_folder, filename)
    if not os.path.exists(path):
        return path
    
    name, ext = os.path.splitext(filename)
    counter = 1
    while os.path.exists(os.path.join(dest_folder, f"{name}_{counter}{ext}")):
        counter += 1
    return os.path.join(dest_folder, f"{name}_{counter}{ext}")

def log_download(dest_folder, info):
    """Log successful download to download_log.txt."""
    log_path = os.path.join(dest_folder, "download_log.txt")
    with open(log_path, 'a') as log:
        log.write(f"{info['timestamp']} UTC\n")
        log.write(f"  Source: {info['url']}\n")
        log.write(f"  Saved to: {info['path']}\n")
        log.write(f"  MIME type: {info['mime']}\n")
        log.write(f"  SHA256: {info['hash']}\n")
        log.write("-" * 40 + "\n")

def log_error(dest_folder, url, error_msg):
    """
    Log errors to error_log.txt.
    Enhancement #4: Better Error Logging
    """
    log_path = os.path.join(dest_folder, "error_log.txt")
    with open(log_path, 'a') as log:
        timestamp = datetime.utcnow().isoformat()
        log.write(f"{timestamp} UTC - {url}\n")
        log.write(f"  Error: {error_msg}\n")
        log.write("-" * 40 + "\n")

def format_size(bytes_val):
    """Convert bytes to human-readable format."""
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

def load_config(config_file):
    """
    Load configuration from JSON file.
    Enhancement #9: Configuration File Support
    """
    if os.path.exists(config_file):
        try:
            with open(config_file, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            print(f"[!] Warning: Invalid JSON in {config_file}, using defaults")
            return {}
    return {}

def download_file(session, url, dest_folder, dry_run=False, timeout=60, 
                  max_size=MAX_FILE_SIZE, bandwidth_limit=None):
    """
    Download a file from the given URL with enhanced features.
    
    Enhancement #1: Duplicate File Handling
    Enhancement #3: File Size Limits
    Enhancement #5: Resume Support (Torrent/Resume)
    Enhancement #8: Bandwidth Throttling
    Enhancement #10: Progress Bar with tqdm
    """
    # Determine the local filename with duplicate handling
    parsed_url = urlparse(url)
    filename = os.path.basename(parsed_url.path)
    local_filename = get_unique_filename(dest_folder, filename)

    if dry_run:
        print(f"[DRY-RUN] Would download: {url} → {local_filename}")
        return
    
    try:
        # Check if file partially exists and support resume
        resume_header = None
        if os.path.exists(local_filename):
            resume_header = {'Range': f'bytes={os.path.getsize(local_filename)}-'}
            response = session.get(url, stream=True, timeout=timeout, headers=resume_header)
        else:
            response = session.get(url, stream=True, timeout=timeout)
        
        response.raise_for_status()

        content_type = response.headers.get('Content-Type', '').split(';')[0].strip()
        if content_type not in SAFE_MIME_TYPES:
            msg = f"Unsafe MIME type: {content_type}"
            print(f"[✗] Skipped {url} due to {msg}")
            log_error(dest_folder, url, msg)
            return

        # Get total size from headers
        total_size = response.headers.get('Content-Length')
        if total_size is not None:
            total_size = int(total_size)
        
        # Check file size limit (Enhancement #3)
        if total_size and total_size > max_size:
            msg = f"Exceeds size limit ({format_size(total_size)} > {format_size(max_size)})"
            print(f"[✗] Skipped {url}: {msg}")
            log_error(dest_folder, url, msg)
            return
        
        total_size_formatted = format_size(total_size) if total_size else "Unknown Size"
        chunk_size = 8192
        
        print(f"[↓] Downloading {os.path.basename(local_filename)} (Total: {total_size_formatted})...")

        # Use tqdm for progress tracking (Enhancement #10)
        mode = 'ab' if os.path.exists(local_filename) else 'wb'
        with open(local_filename, mode) as f:
            with tqdm(total=total_size, unit='B', unit_scale=True, desc=os.path.basename(local_filename), leave=False) as pbar:
                for chunk in response.iter_content(chunk_size=chunk_size):
                    if chunk:
                        f.write(chunk)
                        pbar.update(len(chunk))
                        
                        # Bandwidth throttling (Enhancement #8)
                        if bandwidth_limit:
                            time.sleep(len(chunk) / bandwidth_limit)
        
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
        error_msg = str(e)
        print(f"[✗] Failed to download {url}: {error_msg}")
        log_error(dest_folder, url, error_msg)

def scrape_onion(url, dest_folder, extensions, dry_run=False, timeout=60, 
                 max_size=MAX_FILE_SIZE, bandwidth_limit=None):
    """
    Scrape an onion site and download files matching the given extensions.
    Enhancement #7: Better URL Validation
    """
    # Validate .onion URL
    if not is_onion_url(url):
        print("[✗] Error: URL must be a .onion address (e.g., http://xyz.onion)")
        return
    
    session = create_tor_session()
    try:
        response = session.get(url, timeout=timeout)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        links = soup.find_all('a', href=True)
        os.makedirs(dest_folder, exist_ok=True)
        
        if not links:
            print(f"[!] No links found on {url}")
            return
        
        for link in links:
            file_url = urljoin(url, link['href'])
            if is_valid_file(file_url, extensions):
                download_file(session, file_url, dest_folder, dry_run, timeout, max_size, bandwidth_limit)
    
    except KeyboardInterrupt:
        # Handle Ctrl+C gracefully (Enhancement #12)
        print("\n[!] Interrupted by user")
        sys.exit(130)
    except Exception as e:
        error_msg = str(e)
        print(f"[✗] Error accessing {url}: {error_msg}")
        log_error(dest_folder, url, error_msg)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download screenshots and files from an onion URL.")
    parser.add_argument("url", help="Target onion URL (e.g., http://xyz.onion)")
    parser.add_argument("-o", "--output", default="downloads", help="Destination folder")
    parser.add_argument("-e", "--extensions", nargs="+", default=[".jpg", ".png", ".pdf", ".zip", ".txt"], help="File extensions to download")
    parser.add_argument("--dry-run", action="store_true", help="List files without downloading")
    parser.add_argument("--timeout", type=int, default=60, help="Request timeout in seconds (Enhancement #6)")
    parser.add_argument("--max-size", type=int, default=500, help="Max file size in MB (Enhancement #3)")
    parser.add_argument("--bandwidth-limit", type=float, default=None, help="Bandwidth limit in bytes/second (Enhancement #8)")
    parser.add_argument("--config", default=DEFAULT_CONFIG_FILE, help="Config file path (Enhancement #9)")
    
    args = parser.parse_args()
    
    # Load config file if available (Enhancement #9)
    config = load_config(args.config)
    
    # Override args with config values if present
    url = config.get('url', args.url)
    output = config.get('output', args.output)
    extensions = config.get('extensions', args.extensions)
    timeout = config.get('timeout', args.timeout)
    max_size = config.get('max_size', args.max_size * 1024 * 1024)  # Convert MB to bytes
    bandwidth_limit = config.get('bandwidth_limit', args.bandwidth_limit)
    
    try:
        scrape_onion(url, output, extensions, args.dry_run, timeout, max_size, bandwidth_limit)
    except KeyboardInterrupt:
        # Handle Ctrl+C gracefully (Enhancement #12)
        print("\n[!] Interrupted by user")
        sys.exit(130)
