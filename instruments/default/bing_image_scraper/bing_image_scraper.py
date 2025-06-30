import requests
from bs4 import BeautifulSoup
import json
import os
import sys
import argparse
import hashlib
import time

def scrape_bing_images_tool(query, output_dir, limit=100):
    print(f"Starting image scraping for query: '{query}' into directory: '{output_dir}'")
    
    # Encode query for URL safety
    encoded_query = requests.utils.quote(query)
    base_search_url = f'https://www.bing.com/images/search?q={encoded_query}'
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
    
    os.makedirs(output_dir, exist_ok=True)

    image_urls = []
    seen_urls = set()
    downloaded_count = 0
    first_param = 0 # Offset for pagination
    images_per_page = 30 # Approximate number of images per Bing page load

    while downloaded_count < limit:
        search_url = f"{base_search_url}&first={first_param}"
        print(f"Fetching search results from: {search_url}")

        try:
            response = requests.get(search_url, headers=headers, timeout=15)
            response.raise_for_status() 

            soup = BeautifulSoup(response.text, 'html.parser')
            current_page_urls = []

            for a_tag in soup.find_all('a', class_='iusc'):
                if a_tag.has_attr('m'):
                    try:
                        m_data = json.loads(a_tag['m'])
                        if 'murl' in m_data:
                            img_url = m_data['murl']
                            if img_url.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp')) and img_url not in seen_urls:
                                current_page_urls.append(img_url)
                                seen_urls.add(img_url)
                    except json.JSONDecodeError:
                        continue
            
            if not current_page_urls and first_param > 0: # If no new URLs on subsequent pages, stop
                print("No new image URLs found on this page. Ending search.")
                break

            image_urls.extend(current_page_urls)
            print(f"Found {len(current_page_urls)} new URLs on this page. Total unique URLs found: {len(image_urls)}")
            
            # Attempt to download images from the accumulated list
            # This inner loop ensures we always try to hit the limit with available URLs
            for img_url in current_page_urls:
                if downloaded_count >= limit:
                    print(f"Reached download limit of {limit} images.")
                    break

                original_file_name = os.path.basename(img_url).split('?')[0] 
                
                _, ext = os.path.splitext(original_file_name)
                if not ext:
                    if '.png' in img_url.lower(): ext = '.png'
                    elif '.gif' in img_url.lower(): ext = '.gif'
                    elif '.webp' in img_url.lower(): ext = '.webp'
                    else: ext = '.jpg'

                base_name = original_file_name.replace(ext, '')
                max_filename_len = 150 - len(ext) - 9 
                if len(base_name) > max_filename_len:
                    hash_suffix = hashlib.md5(img_url.encode('utf-8')).hexdigest()[:8] 
                    file_name = f"{base_name[:max_filename_len]}_{hash_suffix}{ext}"
                else:
                    file_name = original_file_name

                file_path = os.path.join(output_dir, file_name)
                
                if os.path.exists(file_path):
                    # print(f"Skipping existing file: {file_name}")
                    continue # Skip if file already exists

                try:
                    img_data = requests.get(img_url, stream=True, headers=headers, timeout=10)
                    img_data.raise_for_status()

                    with open(file_path, 'wb') as handler:
                        for chunk in img_data.iter_content(chunk_size=8192):
                            handler.write(chunk)
                    print(f"Downloaded: {file_name}")
                    downloaded_count += 1
                except requests.exceptions.RequestException as e:
                    print(f"Error downloading {img_url}: {e}")
                except Exception as e:
                    print(f"An unexpected error occurred while saving {file_name}: {e}")
            
            first_param += images_per_page # Move to the next page/offset
            time.sleep(1) # Be polite and avoid rapid fire requests

        except requests.exceptions.RequestException as e:
            print(f"Error fetching Bing search results from {search_url}: {e}")
            break # Stop if search page cannot be fetched
        except Exception as e:
            print(f"An unexpected error occurred during scraping loop: {e}")
            break

    print(f"Scraping complete. Downloaded {downloaded_count} images to {output_dir}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Scrape high-quality images from Bing.com.')
    parser.add_argument('--query', type=str, required=True, help='The search query for images.')
    parser.add_argument('--output_dir', type=str, default='./scraped_images', help='The directory to save downloaded images.')
    parser.add_argument('--limit', type=int, default=100, help='The maximum number of images to download.')
    
    args = parser.parse_args()
    
    scrape_bing_images_tool(args.query, args.output_dir, args.limit)
