# Website Domain Scraper

A Python tool for crawling a website, following all internal links, extracting all external links, and saving their domains to a text file.

## Features

- Follows all internal links on a website (up to a configurable maximum)
- Collects all external links and extracts their domains
- Saves the unique domains to a text file
- Respects server load with configurable delay between requests
- Command-line interface with customizable options

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

### Options

Both scripts support the following options:
- `--output`, `-o`: Specify an output file (default: domains.txt)
- `--max-pages`, `-m`: Set the maximum number of pages to crawl (default: 100)
- `--verbose`, `-v`: Enable verbose logging

Example with options:
```
python scraper.py https://example.com --output results.txt --max-pages 200 --verbose
```

## Notes

- The tool respects website load by waiting 0.5 seconds between requests
- It uses a breadth-first search approach to follow internal links
- External links are identified by comparing domains
- The tool uses a custom User-Agent to avoid being blocked

## License

MIT 