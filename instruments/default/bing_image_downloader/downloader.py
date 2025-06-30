import os, sys
import shutil
from pathlib import Path
import argparse # Added argparse

try:
    from bing import Bing
except ImportError:  # Python 3
    from .bing import Bing


def download(query, limit=100, output_dir='dataset', adult_filter_off=True, 
force_replace=False, timeout=60, filter="",resize=None, verbose=True):

    # engine = 'bing'
    if adult_filter_off:
        adult = 'off'
    else:
        adult = 'on'

    
    image_dir = Path(output_dir).joinpath(query).absolute()

    if force_replace:
        if Path.is_dir(image_dir):
            shutil.rmtree(image_dir)

    # check directory and create if necessary
    try:
        if not Path.is_dir(image_dir):
            Path.mkdir(image_dir, parents=True)

    except Exception as e:
        print('[Error]Failed to create directory.', e)
        sys.exit(1)
        
    print("[%] Downloading Images to {}".format(str(image_dir.absolute())))
    bing = Bing(query, limit, image_dir, adult, timeout, filter,resize, verbose)
    bing.run()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Bing Image Downloader')
    parser.add_argument('--query', type=str, required=True, help='Query string to be searched.')
    parser.add_argument('--limit', type=int, default=100, help='Number of images to download.')
    parser.add_argument('--output_dir', type=str, default='dataset', help='Name of output directory.')
    parser.add_argument('--adult_filter_off', action='store_true', help='Enable or disable adult filter.')
    parser.add_argument('--force_replace', action='store_true', help='Delete folder if present and start a fresh download.')
    parser.add_argument('--timeout', type=int, default=60, help='Timeout for connection.')
    parser.add_argument('--filter', type=str, default='', help='Filter for image type/color etc.')
    parser.add_argument('--resize', type=int, nargs=2, help='Resize images to specified width and height (e.g., 200 200).')
    parser.add_argument('--verbose', action='store_true', default=True, help='Print verbose output.')

    args = parser.parse_args()

    download(
        args.query,
        limit=args.limit,
        output_dir=args.output_dir,
        adult_filter_off=args.adult_filter_off,
        force_replace=args.force_replace,
        timeout=args.timeout,
        filter=args.filter,
        resize=args.resize,
        verbose=args.verbose
    )