#!/usr/bin/env python3
"""
Website Scraper - Extracts all external domains from a website.

This script crawls a website, follows all internal links,
collects all external links, and saves their domains to a text file.
Configuration is loaded from a YAML config file.
Output filenames are automatically generated based on the crawled domain.
Uses multithreading for faster crawling.
"""

import yaml
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
import time
import logging
import uuid
import os
import concurrent.futures
import threading
import queue
from typing import Set, List, Dict
from collections import Counter

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Thread-safe structures
url_queue = queue.Queue()
visited_urls = set()
visited_urls_lock = threading.Lock()
external_domains = set()
external_domains_lock = threading.Lock()
page_count = 0
page_count_lock = threading.Lock()

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

def worker(base_domain: str, max_pages: int, request_delay: float):
    """
    Worker function for each thread.
    Processes URLs from the queue, extracts links, and updates shared state.
    """
    global page_count
    
    while True:
        try:
            # Check if we've reached the maximum number of pages
            with page_count_lock:
                if page_count >= max_pages:
                    break
            
            # Get the next URL from the queue with a timeout
            try:
                current_url = url_queue.get(timeout=1)
            except queue.Empty:
                # If the queue is empty, wait a moment and check again
                time.sleep(0.1)
                continue
            
            # Skip if already visited
            with visited_urls_lock:
                if current_url in visited_urls:
                    url_queue.task_done()
                    continue
                visited_urls.add(current_url)
            
            # Increment page count
            with page_count_lock:
                page_count += 1
                current_count = page_count
                if current_count > max_pages:
                    url_queue.task_done()
                    break
                logger.info(f"Crawling: {current_url} ({current_count}/{max_pages})")
            
            # Fetch and parse the page
            html = fetch_page(current_url)
            if not html:
                url_queue.task_done()
                continue
            
            # Extract links
            links = extract_links(html, current_url)
            
            # Process each link
            for link in links:
                # Internal link - add to the queue
                if is_internal_link(link, base_domain):
                    with visited_urls_lock:
                        if link not in visited_urls:
                            url_queue.put(link)
                # External link - add domain to results
                else:
                    external_domain = get_domain(link)
                    if external_domain:
                        with external_domains_lock:
                            external_domains.add(external_domain)
            
            # Be nice to the server
            time.sleep(request_delay)
            url_queue.task_done()
        
        except Exception as e:
            logger.error(f"Error in worker thread: {e}")
            url_queue.task_done()

def crawl_website(start_url: str, max_pages: int = 100, request_delay: float = 0.1, num_workers: int = 8) -> Set[str]:
    """
    Crawl a website using multiple threads, following internal links and collecting external domains.
    
    Args:
        start_url: URL to start crawling from
        max_pages: Maximum number of pages to crawl
        request_delay: Delay between requests in seconds
        num_workers: Number of worker threads to use
    
    Returns:
        Set of external domains found
    """
    global page_count, visited_urls, external_domains
    
    # Reset global variables
    with page_count_lock:
        page_count = 0
    with visited_urls_lock:
        visited_urls.clear()
    with external_domains_lock:
        external_domains.clear()
    
    # Get the base domain
    base_domain = get_domain(start_url)
    logger.info(f"Starting crawl of {base_domain} from {start_url} with {num_workers} workers")
    
    # Add the start URL to the queue
    url_queue.put(start_url)
    
    # Create and start worker threads
    with concurrent.futures.ThreadPoolExecutor(max_workers=num_workers) as executor:
        # Submit worker tasks
        futures = [
            executor.submit(worker, base_domain, max_pages, request_delay) 
            for _ in range(num_workers)
        ]
        
        # Wait for all tasks to complete or for max_pages to be reached
        for future in concurrent.futures.as_completed(futures):
            try:
                future.result()
            except Exception as e:
                logger.error(f"Worker thread error: {e}")
    
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
            'workers': 8,
            'request_delay': 0.1,
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
    request_delay = config.get('request_delay', 0.1)
    num_workers = config.get('workers', 8)
    
    # Validate URL
    parsed_url = urlparse(start_url)
    if not parsed_url.scheme or not parsed_url.netloc:
        logger.error(f"Invalid URL: {start_url}. Please include the scheme (http:// or https://)")
        return
    
    # Generate output filename
    output_file = generate_output_filename(start_url)
    
    # Crawl website and get external domains
    external_domains = crawl_website(start_url, max_pages, request_delay, num_workers)
    
    # Save domains to file
    save_domains_to_file(external_domains, output_file)

if __name__ == "__main__":
    main() 