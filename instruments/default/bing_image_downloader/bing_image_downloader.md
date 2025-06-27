# Bing Image Downloader Instrument

## Purpose
Downloads multiple images from Bing.com using a specified search query.

## Location
Instrument is located in `/a0/instruments/default/bing_image_downloader/`.
-   Main script: `download_bing_images.py`
-   Entry point: `bing_image_downloader.sh`

## Prerequisites
-   The `bing-image-downloader` Python library must be installed.
    Install using pip: `pip install bing-image-downloader`

## Usage
Execute via the `code_execution_tool` using the `terminal` runtime.

**Command Structure:**
`/a0/instruments/default/bing_image_downloader/bing_image_downloader.sh --query <search_term> [--limit <num>] [--output_dir <path>] [...]`

**Arguments:**
-   `--query <string>`: **(Required)** Search term for images.
-   `--limit <integer>`: (Optional, default: 10) Number of images to download.
-   `--output_dir <path>`: (Optional, default: `./downloaded_images`) Directory to save images.
-   `--adult_filter_off <boolean>`: (Optional, default: `True`) Disable adult filter.
-   `--force_replace <boolean>`: (Optional, default: `False`) Overwrite existing output directory.
-   `--timeout <integer>`: (Optional, default: 60) Download timeout in seconds.

## Example Execution
To download 15 images of 'vintage cars' to `/data/vintage_cars/`:

```bash
/a0/instruments/default/bing_image_downloader/bing_image_downloader.sh --query "vintage cars" --limit 15 --output_dir "/data/vintage_cars/"
```

## Tool Invocation Example (for Agent)

```json
{
    "thoughts": [
        "I need to download images of vintage cars.",
        "I will use the Bing Image Downloader instrument."
    ],
    "tool_name": "code_execution_tool",
    "tool_args": {
        "runtime": "terminal",
        "session": 0,
        "code": "/a0/instruments/default/bing_image_downloader/bing_image_downloader.sh --query 'vintage cars' --limit 15 --output_dir '/data/vintage_cars/'"
    }
}
```
