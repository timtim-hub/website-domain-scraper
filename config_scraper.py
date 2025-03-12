#!/usr/bin/env python3
"""
Website Scraper - Extracts all external domains from a website.

This script crawls a website, follows all internal links,
collects all external links, and saves their domains to a text file.
Configuration is loaded from a YAML config file.
Output filenames are automatically generated based on the crawled domain.
"""

import yaml
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
import time
import logging
import uuid
import os
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

def crawl_website(start_url: str, max_pages: int = 100, request_delay: float = 0.5) -> Set[str]:
    """
    Crawl a website, following internal links and collecting external domains.
    
    Args:
        start_url: URL to start crawling from
        max_pages: Maximum number of pages to crawl
        request_delay: Delay between requests in seconds
    
    Returns:
        Set of external domains found
    """
    base_domain = get_domain(start_url)
    logger.info(f"Starting crawl of {base_domain} from {start_url}")
    
    visited_urls = set()
    to_visit = [start_url]
    external_domains = set()
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
                    external_domains.add(external_domain)
        
        # Be nice to the server
        time.sleep(request_delay)
    
    logger.info(f"Crawl completed. Visited {len(visited_urls)} pages. Found {len(external_domains)} unique external domains.")
    return external_domains

def generate_output_filename(start_url: str) -> str:
    """Generate an output filename based on the domain being scraped."""
    domain = get_domain(start_url)
    # Replace any dots with underscores to make a valid filename
    domain = domain.replace('.', '_')
    # Generate a short random string (first 8 chars of UUID)
    random_str = str(uuid.uuid4())[:8]
    # Combine domain and random string
    return f"{domain}_{random_str}.txt"

def save_domains_to_file(domains: Set[str], output_file: str) -> None:
    """Save a set of domains to a text file."""
    try:
        with open(output_file, 'w') as f:
            for domain in sorted(domains):
                f.write(f"{domain}\n")
        logger.info(f"Saved {len(domains)} domains to {output_file}")
    except IOError as e:
        logger.error(f"Error saving domains to file: {e}")

def load_config(config_file: str = 'config.yaml') -> Dict:
    """Load configuration from a YAML file."""
    try:
        with open(config_file, 'r') as f:
            config = yaml.safe_load(f)
            logger.info(f"Loaded configuration from {config_file}")
            return config
    except (yaml.YAMLError, IOError) as e:
        logger.error(f"Error loading config file {config_file}: {e}")
        logger.info("Using default configuration")
        return {
            'start_url': 'https://example.com',
            'max_pages': 100,
            'request_delay': 0.5,
            'verbose': False
        }

def main():
    """Main function to run the scraper."""
    # Load config from file
    config = load_config()
    
    # Set logging level
    if config.get('verbose', False):
        logger.setLevel(logging.DEBUG)
    
    # Get parameters from config
    start_url = config.get('start_url')
    max_pages = config.get('max_pages', 100)
    request_delay = config.get('request_delay', 0.5)
    
    # Validate URL
    parsed_url = urlparse(start_url)
    if not parsed_url.scheme or not parsed_url.netloc:
        logger.error(f"Invalid URL: {start_url}. Please include the scheme (http:// or https://)")
        return
    
    # Generate output filename
    output_file = generate_output_filename(start_url)
    
    # Crawl website and get external domains
    external_domains = crawl_website(start_url, max_pages, request_delay)
    
    # Save domains to file
    save_domains_to_file(external_domains, output_file)

if __name__ == "__main__":
    main() 