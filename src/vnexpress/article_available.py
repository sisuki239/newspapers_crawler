import requests
from bs4 import BeautifulSoup
import csv
import time
import re

def extract_article_id(url):
    """
    Extract article ID from a VnExpress URL
    
    Args:
        url: The article URL
        
    Returns:
        Article ID as string or None if not found
    """
    # Use regular expression to find the ID pattern at the end of the URL
    match = re.search(r'-(\d+)\.html$', url)
    if match:
        return match.group(1)
    return None

def scrape_vnexpress_topic(topic_base_url, max_pages):
    """
    Scrapes article information from VnExpress topic pages
    
    Args:
        topic_base_url: Base URL pattern for the topic
        max_pages: Maximum number of pages to scrape
    
    Returns:
        List of dictionaries containing article data
    """
    all_articles = []
    
    for page_num in range(1, max_pages + 1):
        url = topic_base_url.format(i=page_num)
        print(f"Scraping page {page_num}: {url}")
        
        try:
            # Send HTTP request
            response = requests.get(url)
            response.raise_for_status()
            
            # Parse HTML
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find the list-news container
            list_news = soup.find('div', id='list-news')
            if not list_news:
                print(f"No list-news div found on page {page_num}.")
                continue
            
            # Find all articles within the container
            articles = list_news.find_all('article')
            print(f"Found {len(articles)} articles on page {page_num}")
            
            for article in articles:
                try:
                    # Get the main link
                    link_tag = article.find('div').find('a', href=True)
                    if not link_tag:
                        continue
                    
                    article_url = link_tag['href']
                    
                    # Extract article ID from URL
                    article_id = extract_article_id(article_url)
                    
                    # Get headline
                    headline_tag = article.find(class_='title-news')
                    headline = headline_tag.get_text().strip() if headline_tag else "No headline found"
                    
                    # Get description
                    desc_tag = article.find(class_='description')
                    description = desc_tag.get_text().strip() if desc_tag else "No description found"
                    
                    all_articles.append({
                        'article_id': article_id,
                        'url': article_url,
                        'headline': headline,
                        'description': description
                    })
                except Exception as e:
                    print(f"Error extracting article data: {e}")
            
            # Be nice to the server
            time.sleep(1)
            
        except Exception as e:
            print(f"Error scraping page {page_num}: {e}")
    
    return all_articles

def save_to_csv(articles, output_file):
    """
    Saves article data to CSV file
    
    Args:
        articles: List of article dictionaries
        output_file: Path to save the CSV file
    """
    if not articles:
        print("No articles to save.")
        return
    
    with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['article_id', 'url', 'headline', 'description']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        for article in articles:
            writer.writerow(article)
    
    print(f"Saved {len(articles)} articles to {output_file}")

def main():
    # The base URL with a placeholder for the page number
    topic_url = "https://vnexpress.net/topic/truy-quet-buon-lau-hang-gia-28080-p{i}"
    
    # Number of pages to scrape
    num_pages = 4
    
    # Output file name
    output_file = "truy_quet_buon_lau_hang_gia_articles.csv"
    
    # Scrape articles
    articles = scrape_vnexpress_topic(topic_url, num_pages)
    print(f"Total articles scraped: {len(articles)}")
    
    # Save to CSV
    save_to_csv(articles, output_file)

if __name__ == "__main__":
    main()