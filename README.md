# Website Domain Scraper

A Python tool for crawling a website, following all internal links, extracting all external links, and saving their domains to a text file.

## Features

- Follows all internal links on a website (up to a configurable maximum)
- Collects all external links and extracts their domains
- Saves the unique domains to a text file
- Multithreaded crawling for high performance (configurable worker count)
- Respects server load with configurable delay between requests
- Multiple configuration options (command-line, config file)
- Automatic output file naming

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/timtim-hub/website-domain-scraper.git
   cd website-domain-scraper
   ```

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

## Usage

### Config File Version (Recommended)

The easiest way to use the scraper is with the config file:

1. Edit the `config.yaml` file to set your desired URL and options:
   ```yaml
   # URL to start crawling from (required)
   start_url: https://example.com
   
   # Maximum number of pages to crawl (default: 100)
   max_pages: 100
   
   # Number of worker threads for parallel crawling (default: 8)
   workers: 8
   
   # Delay between requests in seconds (default: 0.1)
   request_delay: 0.1
   
   # Enable verbose logging (default: false)
   verbose: false
   ```

2. Run the scraper without any arguments:
   ```
   python config_scraper.py
   ```

The script will automatically generate an output filename based on the domain being crawled plus a random string (e.g., `example_com_a1b2c3d4.txt`).

### Standard Version (with domain counts)

Basic usage:
```
python scraper.py https://example.com
```

This will crawl the website starting from the provided URL and save all found external domains with their occurrence counts to `domains.txt` in the current directory.

### Domains-Only Version

If you only want the domain names without the occurrence counts:
```
python domains_only_scraper.py https://example.com
```

This works the same way as the standard version but outputs only the domain names without counts.

### Command-Line Options

The command-line versions support the following options:
- `--output`, `-o`: Specify an output file (default: domains.txt)
- `--max-pages`, `-m`: Set the maximum number of pages to crawl (default: 100)
- `--verbose`, `-v`: Enable verbose logging

Example with options:
```
python scraper.py https://example.com --output results.txt --max-pages 200 --verbose
```

## Performance

The config-based version uses multithreading with configurable workers (default: 8) to significantly speed up crawling. This allows it to process more pages in less time compared to the single-threaded versions.

## Notes

- The tool respects website load by using a configurable delay between requests (default: 0.1 seconds)
- It uses a breadth-first search approach to follow internal links
- External links are identified by comparing domains
- The tool uses a custom User-Agent to avoid being blocked
- Using too many worker threads or too small a delay might overload some servers - adjust according to the website's capacity

## License

MIT 