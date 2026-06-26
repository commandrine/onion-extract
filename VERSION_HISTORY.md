# onion-extract Version History

A comprehensive guide to the major changes and improvements across versions of **onion-extract**, a lightweight Python tool for indexing and downloading files from onion URLs.

---

## Version 1.3

**Release Date:** June 11, 2026

### Major Features & Enhancements

v1.3 is a major overhaul introducing advanced features, improved reliability, and better user experience. This version includes **12 significant enhancements**:

#### 🔧 Core Features
- **Enhancement #1: Duplicate File Handling**
  - Automatically handles filename conflicts by appending incrementing numbers
  - Prevents accidental overwriting of existing files
  - Implements `get_unique_filename()` function

- **Enhancement #2: Connection Pooling & Retry Logic**
  - Added HTTP connection pooling with `HTTPAdapter`
  - Implements exponential backoff retry strategy for unreliable .onion networks
  - Automatically retries failed requests up to 3 times
  - Handles transient network errors (429, 500, 502, 503, 504)

- **Enhancement #3: File Size Limits**
  - New `--max-size` parameter to limit downloads (default: 500 MB)
  - Validates file size before downloading to prevent system overload
  - Blocks downloads that exceed the specified limit with error logging

- **Enhancement #4: Better Error Logging**
  - Dedicated `error_log.txt` for tracking failed downloads
  - Comprehensive error tracking with timestamps
  - Separate from success logging for easier debugging

#### 📊 User Experience
- **Enhancement #5: Resume Support**
  - Partial downloads can be resumed without starting over
  - Uses HTTP Range header for efficient resume capability
  - Supports append mode when resuming interrupted transfers

- **Enhancement #6: Configurable Timeouts**
  - New `--timeout` parameter (default: 60 seconds)
  - Prevents hanging on unresponsive .onion servers
  - Customizable per execution

- **Enhancement #7: Better URL Validation**
  - New `is_onion_url()` function validates .onion domains
  - Prevents accidental downloads from non-.onion addresses
  - Clear error messages for invalid URLs

- **Enhancement #8: Bandwidth Throttling**
  - New `--bandwidth-limit` parameter to cap download speed
  - Useful for limiting system impact during large downloads
  - Configurable in bytes/second

#### 🎯 Advanced Features
- **Enhancement #9: Configuration File Support**
  - New `--config` parameter to load settings from JSON file
  - Supports: `url`, `output`, `extensions`, `timeout`, `max_size`, `bandwidth_limit`
  - Configuration file: `onion-extract-config.json`
  - CLI arguments override configuration file settings

- **Enhancement #10: Progress Bar with tqdm**
  - Beautiful, real-time progress bars for each download
  - Shows download speed, ETA, and percentage completion
  - Replaces manual progress reporting with industry-standard tool

- **Enhancement #11: Expanded MIME Type Support**
  - Added support for: `image/gif`, `image/webp`, `text/html`, `application/json`, `application/x-tar`, `video/mp4`, `audio/mpeg`
  - Now supports broader media types beyond basic images/documents
  - Improves compatibility with diverse .onion content

- **Enhancement #12: Graceful Interrupt Handling**
  - Properly handles `Ctrl+C` (SIGINT) signals
  - Exits with proper status code (130)
  - Ensures clean shutdown without partial corrupted files

### Technical Changes
- **New Dependencies:** `tqdm` (for progress bars)
- **New Parameters:**
  ```
  --timeout <seconds>         Set request timeout (default: 60)
  --max-size <MB>            Maximum file size to download (default: 500 MB)
  --bandwidth-limit <B/s>    Throttle download speed
  --config <file>            Load configuration from JSON file
  ```

### Expanded MIME Types
```python
SAFE_MIME_TYPES = {
    'image/jpeg', 'image/png', 'image/gif', 'image/webp', 'image/jpg',
    'application/pdf', 'application/zip', 'application/x-tar',
    'text/plain', 'text/html', 'application/json',
    'video/mp4', 'audio/mpeg'
}
```

### Example Configuration File
Create `onion-extract-config.json`:
```json
{
  "url": "http://example.onion",
  "output": "downloads",
  "extensions": [".jpg", ".png", ".pdf"],
  "timeout": 120,
  "max_size": 1000000000,
  "bandwidth_limit": 1048576
}
```

### File Size: 11,405 bytes (↑ 77.8% from v1.2)

---

## Version 1.2

**Release Date:** November 30, 2025

### Major Features & Improvements

v1.2 focuses on **download progress visibility and enhanced user feedback**.

#### 📊 Progress Reporting
- **Real-time Download Progress Bar**
  - Displays download progress with percentage completion
  - Shows downloaded size vs. total size (e.g., "2.45 MB / 10.00 MB (24.50%)")
  - Uses carriage return (`\r`) for in-place terminal updates
  - Clears progress line before error messages

- **Enhanced Size Formatting**
  - Introduced `format_size()` function for human-readable file sizes
  - Formats: Bytes (B), Kilobytes (KB), Megabytes (MB), Gigabytes (GB)
  - Applied to both total file size and download progress

#### 🔧 Technical Improvements
- **Increased Timeout**
  - Changed from 30 seconds to 60 seconds for better reliability on unstable .onion networks
  - More forgiving for slow connections

- **Console Output Management**
  - Proper flushing using `sys.stdout.flush()`
  - Prevents output buffering issues during progress reporting
  - Cleans console lines to prevent visual artifacts (Enhancement over v1.1)

- **Better Error Handling**
  - Clears progress line before displaying error messages
  - Prevents overlapping error text with progress display

### New Capabilities
- Monitor real-time download progress during transfers
- Better visibility into download status for long-running operations
- Improved reliability on unstable Tor connections (60s timeout)

### Example Output
```
[↓] Downloading large_file.pdf (Total: 5.32 MB)...
    Progress: 1.58 MB / 5.32 MB (29.70%)
[✓] Downloaded: large_file.pdf
     └─ Source: http://example.onion/files/large_file.pdf
     └─ MIME: application/pdf
     └─ SHA256: a1b2c3d4e5f6...
     └─ Timestamp: 2025-11-30T16:00:17.123456 UTC
```

### File Size: 6,404 bytes (↑ 1.8% from v1.1)

---

## Version 1.1

**Release Date:** December 1, 2025

### Major Features

v1.1 introduces **security enhancements and comprehensive audit logging**.

#### 🔐 Security Features
- **File Extension Filtering**
  - Validates file extensions before downloading
  - Configurable with `-e` / `--extensions` parameter
  - Default safe extensions: `.jpg`, `.png`, `.pdf`, `.zip`, `.txt`

- **MIME Type Validation**
  - Validates Content-Type header from server responses
  - Only downloads files with whitelisted MIME types
  - Prevents malware or unexpected file types
  - Whitelisted MIME types:
    ```
    image/jpeg, image/png, application/pdf, application/zip,
    text/plain, image/jpg
    ```

#### 📋 Audit & Logging
- **SHA256 Hash Logging**
  - Calculates and logs SHA256 hash for every downloaded file
  - Useful for verifying file integrity and detecting tampering
  - Implemented `get_sha256()` function

- **Timestamped Audit Log**
  - Creates `download_log.txt` in the output folder
  - Logs timestamp (UTC), source URL, local path, MIME type, and SHA256 hash
  - Separates log entries with dashes for readability
  - Supports append mode for continuous logging

- **SSL Certificate Warnings Suppressed**
  - Disables SSL verification warnings for self-signed .onion certificates
  - Uses `urllib3.disable_warnings()` to reduce console clutter
  - Necessary for .onion sites that use self-signed certificates

#### 🔧 Technical Details
- **Tor Session Enhancement**
  - Added `session.verify = False` to disable SSL verification
  - Critical for .onion site compatibility

- **Console Output Enhancement**
  - More detailed per-file output showing:
    - Source URL
    - MIME type
    - SHA256 hash
    - UTC timestamp
  - Better formatted with tree-like indentation

### Audit Log Format
```
2025-12-01T13:40:22.123456 UTC
  Source: http://example.onion/image.jpg
  Saved to: /downloads/image.jpg
  MIME type: image/jpeg
  SHA256: 3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d
----------------------------------------
```

### File Size: 6,284 bytes (↑ 10.2% from v1.0)

---

## Version 1.0

**Release Date:** October 28, 2025

### Initial Release

v1.0 is the **lightweight baseline** for onion URL indexing and file downloading.

#### 🎯 Core Features
- **Tor Integration**
  - Direct connection through Tor proxy (socks5h://127.0.0.1:9050)
  - Requires local Tor service to be running

- **Basic File Scraping**
  - Parses HTML pages using BeautifulSoup
  - Extracts all hyperlinks (`<a>` tags) from a given URL
  - Identifies files based on URL extension

- **Extension-based Filtering**
  - Downloads only files matching specified extensions
  - Default extensions: `.jpg`, `.png`, `.pdf`, `.zip`, `.txt`
  - Customizable via `-e` / `--extensions` parameter

- **Streaming Downloads**
  - Uses chunked streaming for efficient memory usage
  - Chunk size: 8 KB
  - Works with large files without loading entire file into memory

- **Dry-Run Mode**
  - `--dry-run` flag lists files without downloading
  - Useful for previewing what would be downloaded

- **Command-line Interface**
  - Simple argument parser with clear help text
  - Parameters:
    - `url`: Target onion URL (required)
    - `-o`, `--output`: Destination folder (default: "downloads")
    - `-e`, `--extensions`: File extensions to filter
    - `--dry-run`: Preview mode

### Basic Usage
```bash
python3 onion-extract.py -o downloads http://example.onion
```

### File Size: 6,164 bytes

---

## Comparison Summary

| Feature | v1.0 | v1.1 | v1.2 | v1.3 |
|---------|------|------|------|------|
| **Core Scraping** | ✅ | ✅ | ✅ | ✅ |
| **MIME Type Validation** | ❌ | ✅ | ✅ | ✅ |
| **SHA256 Hashing** | ❌ | ✅ | ✅ | ✅ |
| **Audit Logging** | ❌ | ✅ | ✅ | ✅ |
| **Progress Reporting** | ❌ | ❌ | ✅ | ✅ |
| **Connection Pooling** | ❌ | ❌ | ❌ | ✅ |
| **Retry Logic** | ❌ | ❌ | ❌ | ✅ |
| **File Size Limits** | ❌ | ❌ | ❌ | ✅ |
| **Resume Support** | ❌ | ❌ | ❌ | ✅ |
| **Bandwidth Throttling** | ❌ | ❌ | ❌ | ✅ |
| **Config File Support** | ❌ | ❌ | ❌ | ✅ |
| **Progress Bars (tqdm)** | ❌ | ❌ | ❌ | ✅ |
| **Error Logging** | ❌ | ✅ | ✅ | ✅ |
| **Graceful Interrupts** | ❌ | ❌ | ❌ | ✅ |

---

## Deployment Notes

### Version Requirements

- **Python:** 3.6+
- **Dependencies:**
  - `requests` (all versions)
  - `beautifulsoup4` (all versions)
  - `urllib3` (v1.1+)
  - `tqdm` (v1.3 only)

### Breaking Changes

- **v1.3:** Introduces strict `.onion` URL validation. Non-.onion URLs will be rejected.
- **v1.2 → v1.3:** New `tqdm` dependency required. Update requirements.txt accordingly.

### Migration Guide

**From v1.2 to v1.3:**
1. Update `requirements.txt` to include `tqdm`
2. Optional: Create `onion-extract-config.json` for common settings
3. Existing scripts will continue to work without modification

**From v1.1 to v1.2:**
1. No breaking changes
2. New timeout value (60s) applies automatically

**From v1.0 to v1.1:**
1. No breaking changes
2. File auditing logs automatically created

---

## Support & Updates

For issues or feature requests, please refer to the repository's issues page. Each version is maintained for backward compatibility where possible.

