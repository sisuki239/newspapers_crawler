import requests
from bs4 import BeautifulSoup
import csv
import time
import re
import argparse
from urllib.parse import quote
import sys
from tqdm import tqdm

def search_dantri(query, page=1):
    """
    Search for articles on Dantri.com.vn with the given query and page number
    
    Args:
        query: Search query
        page: Page number (default: 1)
        
    Returns:
        HTML content of the search results page and whether we've reached the last page
    """
    encoded_query = quote(query).replace("%20", "+")
    search_url = f"https://dantri.com.vn/tim-kiem/{encoded_query}.htm?date=165&pi={page}"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        response = requests.get(search_url, headers=headers)
        response.raise_for_status()
        
        # Check if we've reached the last page
        # If we're beyond the last page, the URL will redirect to the last page
        current_page_url = response.url
        current_page_match = re.search(r'pi=(\d+)', current_page_url)
        current_page = int(current_page_match.group(1)) if current_page_match else None
        
        is_last_page = current_page is not None and current_page < page
        
        return response.content, is_last_page
    except Exception as e:
        print(f"Error searching Dantri with query '{query}', page {page}: {e}")
        return None, True  # Assume it's the last page if an error occurs

def extract_article_id(url):
    """Extract the article ID from a Dantri article URL"""
    match = re.search(r'-(\d+)\.htm$', url)
    if match:
        return match.group(1)
    return None

def extract_articles(html_content, query):
    """
    Extract article information from Dantri search results page
    
    Args:
        html_content: HTML content of the search results page
        query: Search query to filter by relevance
        
    Returns:
        List of article dictionaries
    """
    if not html_content:
        return []
    
    articles = []
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Find all article elements
    article_elements = soup.find_all('article', class_='article-item')
    
    for article in article_elements:
        try:
            # Find the title and URL
            title_element = article.select_one('.article-title a')
            if not title_element:
                continue
            
            title = title_element.get_text(strip=True)
            url = title_element['href']
            if not url.startswith('http'):
                url = f"https://dantri.com.vn{url}"
            
            # Extract article ID
            article_id = extract_article_id(url)
            if not article_id:
                continue
            
            # Find the description
            description_element = article.select_one('.article-excerpt a')
            description = description_element.get_text(strip=True) if description_element else ""
            
            # Check if the query is in either the title or description
            query_terms = [term.strip() for term in query.split() if term.strip()]
            title_lower = title.lower()
            description_lower = description.lower()
            
            if all(term.lower() in title_lower or term.lower() in description_lower for term in query_terms):
                articles.append({
                    'article_id': article_id,
                    'url': url,
                    'title': title,
                    'description': description
                })
        except Exception as e:
            print(f"Error extracting article information: {e}")
            continue
    
    return articles

def save_to_csv(articles, filename):
    """
    Save articles to a CSV file
    
    Args:
        articles: List of article dictionaries
        filename: Output file name
    """
    if not articles:
        print("No articles to save.")
        return
    
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['article_id', 'url', 'title', 'description']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(articles)
    
    print(f"Saved {len(articles)} articles to {filename}")

def main():
    parser = argparse.ArgumentParser(description='Crawl news articles from Dantri.com.vn')
    parser.add_argument('--output', '-o', default='dantri_articles.csv', help='Output CSV file (default: dantri_articles.csv)')
    parser.add_argument('--delay', '-d', type=float, default=1.0, help='Delay between requests in seconds (default: 1.0)')
    
    args = parser.parse_args()
    
    # Search keywords
    search_queries = ["thuốc giả", "sữa giả", "thực phẩm chức năng giả"]
    
    all_articles = []
    
    # Search for each query
    for query in search_queries:
        print(f"Searching for articles with query: '{query}'")
        
        page = 1
        reached_last_page = False
        query_articles = []
        
        with tqdm(desc=f"Crawling pages for '{query}'") as pbar:
            while not reached_last_page:
                html_content, is_last_page = search_dantri(query, page)
                if is_last_page:
                    reached_last_page = True
                    print(f"Reached the last page ({page-1}) for query '{query}'")
                
                if html_content:
                    articles = extract_articles(html_content, query)
                    if articles:
                        query_articles.extend(articles)
                        print(f"Found {len(articles)} relevant articles on page {page} for query '{query}'")
                    else:
                        print(f"No relevant articles found on page {page} for query '{query}'")
                
                pbar.update(1)
                
                if not reached_last_page:
                    page += 1
                    time.sleep(args.delay)  # Be nice to the server
        
        print(f"Total relevant articles found for '{query}': {len(query_articles)}")
        all_articles.extend(query_articles)
    
    # Remove duplicates (same article may appear in different search results)
    unique_articles = {article['article_id']: article for article in all_articles}.values()
    unique_articles_list = list(unique_articles)
    
    print(f"Total unique articles found across all queries: {len(unique_articles_list)}")
    
    # Save results to CSV
    save_to_csv(unique_articles_list, args.output)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())