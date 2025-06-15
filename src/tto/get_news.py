import requests
from bs4 import BeautifulSoup
import csv
import time
import re
from datetime import datetime
from urllib.parse import quote, urljoin
import argparse
import sys

def extract_article_id(url):
    """
    Extract article ID from a TuoiTre article URL
    
    Args:
        url: Article URL or path
        
    Returns:
        Article ID as string or None if not found
    """
    # Extract article ID from URL pattern like:
    # /phat-hien-thuoc-tri-hen-suyen-gia-chi-dat-6-3-ham-luong-20250529092525297.htm
    match = re.search(r'-(\d{14,})\.htm', url)
    if match:
        return match.group(1)
    return None

def extract_article_date(article_id):
    """
    Extract date from article ID (format: yyyymmdd...)
    
    Args:
        article_id: Article ID
        
    Returns:
        Datetime object or None if invalid
    """
    if not article_id or len(article_id) < 8:
        return None
    
    try:
        date_str = article_id[:8]  # Extract first 8 characters (yyyymmdd)
        return datetime.strptime(date_str, '%Y%m%d')
    except ValueError:
        return None

def search_tuoitre_articles(keyword, page_index, session=None):
    """
    Search for articles on TuoiTre with the given keyword and page index
    
    Args:
        keyword: Search keyword
        page_index: Page number
        session: Requests session (optional)
        
    Returns:
        List of article dictionaries and oldest date found on page
    """
    if session is None:
        session = requests
    
    # URL encode the keyword
    encoded_keyword = quote(keyword)
    search_url = f"https://tuoitre.vn/timeline-search.htm?keywords={encoded_keyword}&PageIndex={page_index}"
    
    articles = []
    oldest_date = None
    
    try:
        print(f"Fetching search results page {page_index} for keyword '{keyword}'...")
        response = session.get(search_url, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        response.raise_for_status()
        
        # Decode the content to string before parsing
        html_content = response.content.decode('utf-8')
        
        # Parse the HTML content
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Find all article items - use the correct selector based on the provided HTML structure
        article_items = soup.find_all('div', class_='box-category-item')
        
        if not article_items:
            print(f"No articles found on page {page_index}")
            return [], None
        
        print(f"Found {len(article_items)} articles on page {page_index}")
        
        for item in article_items:
            try:
                # Find the title and URL from the link within the box-category-link-title class
                title_tag = item.find('a', class_='box-category-link-title')
                if not title_tag:
                    continue
                
                article_href = title_tag.get('href')
                if not article_href:
                    continue
                
                # Build the full URL if it's a relative path
                if article_href.startswith('/'):
                    article_url = urljoin('https://tuoitre.vn', article_href)
                else:
                    article_url = article_href
                
                # Extract article ID
                article_id = extract_article_id(article_href)
                if not article_id:
                    continue
                
                # Get headline
                headline = title_tag.get_text(strip=True)
                
                # Get description/sapo
                desc_tag = item.find('p', {'data-type': 'sapo'})
                description = desc_tag.get_text(strip=True) if desc_tag else ""
                
                # Extract date from article ID
                article_date = extract_article_date(article_id)
                
                if article_date:
                    # Keep track of the oldest article date on this page
                    if oldest_date is None or article_date < oldest_date:
                        oldest_date = article_date
                
                articles.append({
                    'article_id': article_id,
                    'url': article_url,
                    'headline': headline,
                    'description': description,
                    'date': article_date
                })
                
            except Exception as e:
                print(f"Error processing article item: {e}")
        
        return articles, oldest_date
        
    except Exception as e:
        print(f"Error searching for articles on page {page_index}: {e}")
        return [], None

def save_to_csv(articles, output_file):
    """
    Save articles to CSV file
    
    Args:
        articles: List of article dictionaries
        output_file: Output file path
    """
    if not articles:
        print("No articles to save.")
        return
    
    with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['article_id', 'url', 'headline', 'description']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for article in articles:
            # Create a copy without the 'date' field which was only used internally
            row_data = {k: v for k, v in article.items() if k in fieldnames}
            writer.writerow(row_data)
    
    print(f"Saved {len(articles)} articles to {output_file}")

def main():
    parser = argparse.ArgumentParser(description='Crawl TuoiTre newspaper articles for a specific keyword')
    parser.add_argument('--keyword', '-k', default='thuốc giả', help='Search keyword (default: thuốc giả)')
    parser.add_argument('--output', '-o', default='tuoitre_articles.csv', help='Output CSV file (default: tuoitre_articles.csv)')
    parser.add_argument('--start-date', '-s', default='2025-01-01', help='Start date in YYYY-MM-DD format (default: 2025-01-01)')
    parser.add_argument('--end-date', '-e', default=datetime.now().strftime('%Y-%m-%d'), 
                       help=f'End date in YYYY-MM-DD format (default: today)')
    parser.add_argument('--delay', '-d', type=float, default=1.0, 
                       help='Delay between requests in seconds (default: 1.0)')
    parser.add_argument('--max-empty-pages', '-m', type=int, default=3,
                       help='Maximum number of consecutive empty pages before stopping (default: 3)')
    
    args = parser.parse_args()
    
    # Parse dates
    try:
        start_date = datetime.strptime(args.start_date, '%Y-%m-%d')
        end_date = datetime.strptime(args.end_date, '%Y-%m-%d')
    except ValueError as e:
        print(f"Error parsing date: {e}")
        print("Use format YYYY-MM-DD for dates")
        return 1
    
    # Validate date range
    if start_date > end_date:
        print(f"Error: Start date ({args.start_date}) is after end date ({args.end_date})")
        return 1
    
    print(f"Searching for articles with keyword: {args.keyword}")
    print(f"Date range: {args.start_date} to {args.end_date}")
    print(f"Will stop when articles older than {args.start_date} are found")
    
    # Create a session for better performance
    session = requests.Session()
    
    all_articles = []
    page_index = 1
    empty_pages_count = 0  # Count consecutive pages with no articles
    reached_start_date = False
    
    # Crawl pages until we reach articles older than our start date or hit too many empty pages
    while not reached_start_date and empty_pages_count < args.max_empty_pages:
        articles, oldest_date = search_tuoitre_articles(args.keyword, page_index, session)
        
        if not articles:
            # No articles found on this page, increment empty counter
            empty_pages_count += 1
            print(f"No articles found on page {page_index}. Empty page count: {empty_pages_count}/{args.max_empty_pages}")
            page_index += 1
            time.sleep(args.delay)
            continue
        
        # Reset empty pages counter since we found articles
        empty_pages_count = 0
        
        # Filter articles by date range
        filtered_articles = [
            article for article in articles 
            if article['date'] and start_date <= article['date'] <= end_date
        ]
        
        if filtered_articles:
            print(f"Found {len(filtered_articles)} articles in the date range on page {page_index}")
            all_articles.extend(filtered_articles)
        else:
            print(f"No articles in the date range on page {page_index}")
        
        # Check if we've reached or gone past our target start date
        if oldest_date and oldest_date < start_date:
            print(f"Found articles older than {args.start_date}. Stopping search.")
            reached_start_date = True
            break
        
        page_index += 1
        
        # Apply delay between requests
        time.sleep(args.delay)
    
    # Sort articles by date (newest first)
    all_articles.sort(key=lambda x: x['date'] if x['date'] else datetime.min, reverse=True)
    
    # Save results to CSV
    if all_articles:
        print(f"Total articles found in date range: {len(all_articles)}")
        save_to_csv(all_articles, args.output)
    else:
        print("No articles found in the specified date range.")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())