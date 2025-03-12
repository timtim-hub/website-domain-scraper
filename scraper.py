#!/usr/bin/env python3
"""
Website Scraper - Extracts all external domains from a website.

This script crawls a website, follows all internal links,
collects all external links, and saves their domains to a text file.
"""

import argparse
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
import time
import logging
from typing import Set, List, Dict
from collections import Counter

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_domain(url: str) -> str:
    """Extract domain from a URL."""
    parsed_url = urlparse(url)
    domain = f"{parsed_url.netloc}"
    return domain

def is_internal_link(url: str, base_domain: str) -> bool:
    """Check if a URL is internal (same domain)."""
    url_domain = get_domain(url)
    return url_domain == base_domain or not url_domain

def fetch_page(url: str) -> str:
    """Fetch a webpage and return its HTML content."""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.text
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching {url}: {e}")
        return ""

def extract_links(html: str, base_url: str) -> List[str]:
    """Extract all links from an HTML document."""
    soup = BeautifulSoup(html, 'html.parser')
    links = []
    
    for anchor in soup.find_all('a', href=True):
        href = anchor['href']
        absolute_url = urljoin(base_url, href)
        links.append(absolute_url)
    
    return links

def crawl_website(start_url: str, max_pages: int = 100) -> Dict[str, int]:
    """
    Crawl a website, following internal links and collecting external domains.
    
    Args:
        start_url: URL to start crawling from
        max_pages: Maximum number of pages to crawl
    
    Returns:
        Dictionary of external domains and their occurrence counts
    """
    base_domain = get_domain(start_url)
    logger.info(f"Starting crawl of {base_domain} from {start_url}")
    
    visited_urls = set()
    to_visit = [start_url]
    external_domains = Counter()
    page_count = 0
    
    while to_visit and page_count < max_pages:
        current_url = to_visit.pop(0)
        
        # Skip if already visited
        if current_url in visited_urls:
            continue
        
        logger.info(f"Crawling: {current_url} ({page_count+1}/{max_pages})")
        visited_urls.add(current_url)
        page_count += 1
        
        # Fetch and parse the page
        html = fetch_page(current_url)
        if not html:
            continue
        
        # Extract links
        links = extract_links(html, current_url)
        
        # Process each link
        for link in links:
            # Internal link - add to the queue
            if is_internal_link(link, base_domain):
                if link not in visited_urls and link not in to_visit:
                    to_visit.append(link)
            # External link - add domain to results
            else:
                external_domain = get_domain(link)
                if external_domain:
                    external_domains[external_domain] += 1
        
        # Be nice to the server
        time.sleep(0.5)
    
    logger.info(f"Crawl completed. Visited {len(visited_urls)} pages. Found {len(external_domains)} unique external domains.")
    return external_domains

def save_domains_to_file(domain_counts: Dict[str, int], output_file: str) -> None:
    """Save a dictionary of domains and their counts to a text file."""
    try:
        with open(output_file, 'w') as f:
            f.write("# Domain\tCount\n")
            for domain, count in sorted(domain_counts.items(), key=lambda x: (-x[1], x[0])):
                f.write(f"{domain}\t{count}\n")
        logger.info(f"Saved {len(domain_counts)} domains to {output_file}")
    except IOError as e:
        logger.error(f"Error saving domains to file: {e}")

def main():
    """Main function to run the scraper."""
    parser = argparse.ArgumentParser(description='Website scraper to extract external domains')
    parser.add_argument('start_url', help='URL to start crawling from')
    parser.add_argument('--output', '-o', default='domains.txt', help='Output file path (default: domains.txt)')
    parser.add_argument('--max-pages', '-m', type=int, default=100, help='Maximum number of pages to crawl (default: 100)')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose logging')
    
    args = parser.parse_args()
    
    if args.verbose:
        logger.setLevel(logging.DEBUG)
    
    # Validate URL
    parsed_url = urlparse(args.start_url)
    if not parsed_url.scheme or not parsed_url.netloc:
        logger.error("Invalid URL. Please include the scheme (http:// or https://)")
        return
    
    # Crawl website and get external domains
    external_domains = crawl_website(args.start_url, args.max_pages)
    
    # Save domains to file
    save_domains_to_file(external_domains, args.output)

if __name__ == "__main__":
    main() 