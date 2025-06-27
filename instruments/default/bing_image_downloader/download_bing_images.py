#!/usr/bin/env python3

import argparse
from bing_image_downloader import downloader
import os

def main():
    parser = argparse.ArgumentParser(description='Download images from Bing.')
    parser.add_argument('--query', type=str, required=True, help='The search query for images.')
    parser.add_argument('--limit', type=int, default=10, help='Number of images to download.')
    parser.add_argument('--output_dir', type=str, default='./downloaded_images', help='Directory to save the downloaded images.')
    parser.add_argument('--adult_filter_off', type=bool, default=True, help='Enable or disable adult content filter.')
    parser.add_argument('--force_replace', type=bool, default=False, help='Delete folder if present and start a fresh download.')
    parser.add_argument('--timeout', type=int, default=60, help='Timeout for download in seconds.')

    args = parser.parse_args()

    # Create the output directory if it doesn't exist
    if not os.path.exists(args.output_dir):
        os.makedirs(args.output_dir)

    print(f"[INFO] Starting download for query: '{args.query}' with limit: {args.limit}")
    print(f"[INFO] Images will be saved to: {args.output_dir}")
    
    try:
        downloader.download(
            query=args.query,
            limit=args.limit,
            output_dir=args.output_dir,
            adult_filter_off=args.adult_filter_off,
            force_replace=args.force_replace,
            timeout=args.timeout
        )
        print(f"[INFO] Successfully downloaded {args.limit} images for '{args.query}'.")
    except Exception as e:
        print(f"[ERROR] An error occurred during download: {e}")
        
if __name__ == '__main__':
    main()
