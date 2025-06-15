#!/usr/bin/env python3
import requests
from bs4 import BeautifulSoup
import csv
import re
import time
from urllib.parse import quote

def extract_article_id(url):
    """Extract article ID from VnExpress URL"""
    # Pattern for URLs like https://vnexpress.net/noi-lo-mua-phai-thuoc-gia-4891633.html
    pattern = r'\/(\d+)\.html'
    match = re.search(pattern, url)
    if match:
        return match.group(1)
    return None

def parse_search_results(html_content):
    """
    Parse VnExpress search results HTML and extract articles
    
    Args:
        html_content: HTML content of the search results page
        
    Returns:
        List of article dictionaries with id, url, title, and description
    """
    articles = []
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Find all article items
    article_items = soup.find_all('article', class_='item-news-common')
    
    for item in article_items:
        # Skip ad items
        if item.find('ins', class_='adsbyeclick'):
            continue
            
        try:
            # Get article URL and ID
            article_url = item.get('data-url')
            if not article_url:
                link = item.find('h3', class_='title-news').find('a')
                if link:
                    article_url = link.get('href')
            
            if not article_url:
                continue
                
            article_id = extract_article_id(article_url)
            
            # Get title
            title_element = item.find('h3', class_='title-news')
            title = title_element.find('a').get_text(strip=True) if title_element else ""
            
            # Get description
            desc_element = item.find('p', class_='description')
            description = desc_element.find('a').get_text(strip=True) if desc_element else ""
            
            if article_url and title:
                articles.append({
                    'article_id': article_id,
                    'url': article_url,
                    'title': title,
                    'description': description
                })
        except Exception as e:
            print(f"Error parsing article: {e}")
    
    return articles

def search_vnexpress(query, page):
    """
    Search VnExpress with given query and page number
    
    Args:
        query: Search query
        page: Page number
        
    Returns:
        HTML content of the search results page
    """
    # Base URL for VnExpress search
    base_url = "https://timkiem.vnexpress.net/"
    
    # Parameters
    params = {
        'q': query,
        'media_type': 'all',
        'fromdate': '1735664406',
        'todate': '1749952018',
        'latest': '',
        'cate_code': '',
        'search_f': 'title,tag_list',
        'date_format': 'all',
        'page': str(page)
    }
    
    # Construct query string
    query_string = '&'.join([f"{k}={quote(v) if k == 'q' else v}" for k, v in params.items()])
    
    # Full URL
    url = f"{base_url}?{query_string}"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.text
    except Exception as e:
        print(f"Error fetching search results for page {page}: {e}")
        return None

def save_to_csv(articles, filename):
    """
    Save articles to CSV file
    
    Args:
        articles: List of article dictionaries
        filename: Output file path
    """
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['article_id', 'url', 'title', 'description']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(articles)
    
    print(f"Saved {len(articles)} articles to {filename}")

def main():
    query = "thuốc giả"
    output_file = "vnexpress_articles.csv"
    all_articles = []
    
    # Crawl pages 1 to 4
    for page in range(1, 5):
        print(f"Fetching search results from page {page}...")
        html_content = search_vnexpress(query, page)
        
        if html_content:
            articles = parse_search_results(html_content)
            print(f"Found {len(articles)} articles on page {page}")
            all_articles.extend(articles)
        else:
            print(f"Failed to fetch page {page}")
        
        # Add delay between requests
        if page < 4:  # No need to delay after the last page
            time.sleep(1)
    
    # Save all articles to CSV
    save_to_csv(all_articles, output_file)
    print(f"Total articles found: {len(all_articles)}")

if __name__ == "__main__":
    main()