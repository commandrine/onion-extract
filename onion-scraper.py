import os
import argparse
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

def create_tor_session():
    session = requests.Session()
    session.proxies = {
        'http': 'socks5h://127.0.0.1:9050',
        'https': 'socks5h://127.0.0.1:9050'
    }
    return session

def is_valid_file(url, extensions):
    parsed = urlparse(url)
    return any(parsed.path.lower().endswith(ext) for ext in extensions)

def download_file(session, url, dest_folder, dry_run=False):
    local_filename = os.path.join(dest_folder, os.path.basename(urlparse(url).path))
    if dry_run:
        print(f"[DRY-RUN] Would download: {url} → {local_filename}")
        return
    try:
        response = session.get(url, stream=True, timeout=30)
        response.raise_for_status()
        with open(local_filename, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        print(f"[✓] Downloaded: {local_filename}")
    except Exception as e:
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