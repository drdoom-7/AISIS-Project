# Bing Image Scraper Instrument

This instrument allows you to scrape high-quality images from Bing.com based on a given search query.
It supports downloading images in JPG, JPEG, PNG, GIF, and WebP formats.

## Usage

To use this instrument, you can call the `bing_scrape.sh` script located in this directory via the `code_execution_tool`.

### Parameters:

*   `--query <search_query>` (Required): The search term for the images you want to download.
*   `--output_dir <directory_path>` (Optional): The full path to the directory where images will be saved. Defaults to `./scraped_images` if not provided.
*   `--limit <number_of_images>` (Optional): The maximum number of images to download. Defaults to 100 if not provided.

### Example using `code_execution_tool`:

```json
{
    "thoughts": [
        "Initiating Bing Image Scraper to download cat pictures."
    ],
    "tool_name": "code_execution_tool",
    "tool_args": {
        "runtime": "terminal",
        "session": 0,
        "code": "/a0/instruments/default/bing_image_scraper/bing_scrape.sh --query \"cute kittens high resolution\" --output_dir \"/root/my_kitten_pics\" --limit 30"
    }
}
```

Replace `"cute kittens high resolution"` with your desired search query and `"/root/my_kitten_pics"` with your preferred output directory. Adjust the `limit` as needed.