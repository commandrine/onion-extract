# onion-extract

A Python command-line tool that scans links on a `.onion` page and downloads linked files with selected extensions through a local Tor service.

## Requirements

- Python 3
- Tor running locally with its SOCKS proxy at `127.0.0.1:9050`
- The v1.3 dependencies listed in `v1.3/requirements.txt`

## Installation

From the repository root, create and activate a virtual environment, then install the v1.3 requirements:

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r v1.3/requirements.txt
```

## Usage

Run the v1.3 script with a `.onion` URL:

```bash
python3 v1.3/onion-extract.py http://example.onion -o downloads
```

The output directory defaults to `downloads`. By default, the tool looks for links ending in `.jpg`, `.png`, `.pdf`, `.zip`, or `.txt`. For example, to preview matching links without downloading them:

```bash
python3 v1.3/onion-extract.py http://example.onion --dry-run
```

To choose extensions and adjust the timeout, maximum file size (in MB), or bandwidth limit (in bytes per second):

```bash
python3 v1.3/onion-extract.py http://example.onion \
  --extensions .jpg .png .pdf \
  --timeout 120 \
  --max-size 100 \
  --bandwidth-limit 1048576
```

Use `--help` to see all command-line options.

## Configuration file

The default configuration file is `onion-extract-config.json`. Pass `--config PATH` to use another file. Supported keys are `url`, `output`, `extensions`, `timeout`, `max_size` (MB), and `bandwidth_limit` (bytes per second). Values in the configuration file take precedence over the corresponding command-line values.

Example:

```json
{
  "url": "http://example.onion",
  "output": "downloads",
  "extensions": [".jpg", ".png", ".pdf"],
  "timeout": 120,
  "max_size": 100,
  "bandwidth_limit": 1048576
}
```

When `url` is provided in the configuration, the script still expects a positional URL argument; that configured URL is used in preference to the positional value.

## v1.3 features

- Filters linked files by extension and checks response MIME types.
- Shows per-download progress bars and computes SHA256 hashes.
- Avoids overwriting existing filenames by choosing a unique name.
- Retries selected transient HTTP errors and supports request timeouts.
- Offers a configurable file-size limit, bandwidth throttling, and dry-run mode.
- Writes successful downloads to `download_log.txt` and failures to `error_log.txt` in the output directory.
- Handles Ctrl+C with an exit status of 130.

## Notes

The tool only accepts `.onion` URLs and connects through the local Tor SOCKS proxy. It disables TLS certificate verification, so use it only with sources you trust. Downloads are limited to the MIME types allowed by the v1.3 script.
