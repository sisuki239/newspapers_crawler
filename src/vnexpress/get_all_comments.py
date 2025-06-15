import requests
import csv
import time
import re
import html
from bs4 import BeautifulSoup
import argparse
import os

def clean_html_content(content):
    """
    Removes HTML tags from content
    
    Args:
        content: Text that may contain HTML tags
        
    Returns:
        Cleaned text
    """
    # First unescape any HTML entities
    unescaped = html.unescape(content)
    
    # Use BeautifulSoup to remove all HTML tags
    soup = BeautifulSoup(unescaped, 'html.parser')
    clean_text = soup.get_text()
    
    # Remove excessive whitespace
    clean_text = re.sub(r'\s+', ' ', clean_text).strip()
    
    return clean_text

def fetch_comment_replies(article_id, parent_comment_id):
    """
    Fetch replies for a specific comment
    
    Args:
        article_id: ID of the article
        parent_comment_id: ID of the parent comment
        
    Returns:
        List of reply comments
    """
    reply_api_url = (
        f"https://usi-saas.vnexpress.net/index/getreplay?siteid=1000000&"
        f"objectid={article_id}&objecttype=1&id={parent_comment_id}&limit=12&"
        f"offset=0&sort_by=like"
    )
    
    try:
        response = requests.get(reply_api_url)
        response.raise_for_status()
        
        # Parse JSON response
        data = response.json()
        
        # Check if replies data exists
        if 'data' in data and 'items' in data['data']:
            return data['data']['items']
        
        return []
    except Exception as e:
        print(f"Error fetching replies for comment {parent_comment_id}: {e}")
        return []

def fetch_article_comments(article_id):
    """
    Fetch comments for an article using the API
    
    Args:
        article_id: ID of the article
        
    Returns:
        List of comments including replies
    """
    comment_api_url = (
        f"https://usi-saas.vnexpress.net/index/get?offset=0&limit=1000&"
        f"frommobile=0&sort_by=like&objectid={article_id}&objecttype=1&siteid=1000000&usertype=4"
    )
    
    all_comments = []
    
    try:
        response = requests.get(comment_api_url)
        response.raise_for_status()
        
        # Parse JSON response
        data = response.json()
        
        # Check if comments data exists
        if 'data' in data and 'items' in data['data']:
            comments = data['data']['items']
            
            for comment in comments:
                # Clean the comment content
                if 'content' in comment:
                    comment['content'] = clean_html_content(comment['content'])
                
                # Add the comment to our list
                all_comments.append(comment)
                
                # Check if this comment has replies
                if ('replys' in comment and 
                    'total' in comment['replys'] and 
                    comment['replys']['total'] > 0):
                    
                    # Get the parent comment ID
                    parent_id = comment.get('comment_id')
                    if parent_id:
                        print(f"  Fetching {comment['replys']['total']} replies for comment {parent_id}")
                        
                        # Fetch replies
                        replies = fetch_comment_replies(article_id, parent_id)
                        
                        # Clean and add replies to our list
                        for reply in replies:
                            if 'content' in reply:
                                reply['content'] = clean_html_content(reply['content'])
                            reply['is_reply'] = True  # Mark as reply
                            all_comments.append(reply)
                        
                        time.sleep(0.2)  # Small delay to avoid rate limiting
        
        return all_comments
    except Exception as e:
        print(f"Error fetching comments for article {article_id}: {e}")
        return []

def save_comments_to_csv(articles_with_comments, output_file):
    """
    Saves comments to a CSV file
    
    Args:
        articles_with_comments: Dict mapping article_id to comment list
        output_file: Path to save the CSV file
    """
    comments_data = []
    
    for article_id, comments in articles_with_comments.items():
        for comment in comments:
            try:
                comment_id = comment.get('comment_id', '')
                parent_id = comment.get('parent_id', comment_id)  # If same as comment_id, it's a top-level comment
                is_reply = comment.get('is_reply', False)
                content = comment.get('content', '').strip()
                # user_name = comment.get('full_name', '')
                like_count = comment.get('userlike', 0)
                # dislike_count = comment.get('userdilike', 0)
                # creation_time = comment.get('creation_time', '')
                # time_str = comment.get('time', '')
                
                comments_data.append({
                    'article_id': article_id,
                    'comment_id': comment_id,
                    'parent_id': parent_id,
                    'is_reply': 'Yes' if is_reply else 'No',
                    # 'user_name': user_name,
                    'content': content,
                    'likes': like_count,
                    # 'dislikes': dislike_count,
                    # 'creation_timestamp': creation_time,
                    # 'time_str': time_str
                })
            except Exception as e:
                print(f"Error processing comment: {e}")
    
    if not comments_data:
        print("No comments to save.")
        return 0
        
    with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['article_id', 'comment_id', 'parent_id', 'is_reply', 
                     'content', 'likes']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        for comment in comments_data:
            writer.writerow(comment)
    
    print(f"Saved {len(comments_data)} comments to {output_file}")
    return len(comments_data)

def read_articles_from_csv(input_file):
    """
    Read article data from CSV file
    
    Args:
        input_file: Path to the input CSV file
    
    Returns:
        List of article dictionaries
    """
    articles = []
    
    try:
        with open(input_file, 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                articles.append(row)
        
        print(f"Read {len(articles)} articles from {input_file}")
        return articles
    except Exception as e:
        print(f"Error reading articles from CSV: {e}")
        return []

def update_article_csv_with_comment_count(input_file, articles_with_comments, output_file=None):
    """
    Updates the article CSV with comment counts
    
    Args:
        input_file: Original CSV file path
        articles_with_comments: Dict mapping article_id to comment list
        output_file: Path for the updated CSV (if None, overwrites input)
    """
    if output_file is None:
        output_file = input_file
    
    articles = []
    
    # Read original file
    with open(input_file, 'r', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        fieldnames = reader.fieldnames
        
        # Make sure we have a comment_count field
        if 'comment_count' not in fieldnames:
            fieldnames.append('comment_count')
        
        for row in reader:
            article_id = row.get('article_id')
            if article_id in articles_with_comments:
                row['comment_count'] = len(articles_with_comments[article_id])
            else:
                row['comment_count'] = 0
            
            articles.append(row)
    
    # Write updated file
    with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(articles)
    
    print(f"Updated article CSV with comment counts: {output_file}")

def main():
    parser = argparse.ArgumentParser(description='Fetch comments for VnExpress articles from CSV')
    parser.add_argument('input_file', help='Input CSV file with article data')
    parser.add_argument('--output', '-o', help='Output file for comments (default: comments.csv)', default='comments.csv')
    parser.add_argument('--update-articles', '-u', action='store_true', help='Update input CSV with comment counts')
    parser.add_argument('--delay', '-d', type=float, default=0.5, help='Delay between requests in seconds (default: 0.5)')
    args = parser.parse_args()
    
    # Validate input file
    if not os.path.exists(args.input_file):
        print(f"Error: Input file '{args.input_file}' not found.")
        return
    
    # Read articles from CSV
    articles = read_articles_from_csv(args.input_file)
    if not articles:
        print("No articles found in input file. Exiting.")
        return
    
    # Dictionary to store article ID -> comments mapping
    articles_with_comments = {}
    
    # Process each article
    for i, article in enumerate(articles):
        article_id = article.get('article_id')
        if not article_id:
            print(f"Warning: Missing article_id in row {i+1}. Skipping.")
            continue
        
        print(f"[{i+1}/{len(articles)}] Fetching comments for article {article_id} ({article.get('headline', 'No headline')})")
        comments = fetch_article_comments(article_id)
        articles_with_comments[article_id] = comments
        print(f"  Found {len(comments)} comments (including replies)")
        
        # Apply delay between requests
        if i < len(articles) - 1:  # Don't delay after the last article
            time.sleep(args.delay)
    
    # Save comments to CSV
    total_comments = save_comments_to_csv(articles_with_comments, args.output)
    
    # Update the original article CSV with comment counts if requested
    if args.update_articles:
        update_article_csv_with_comment_count(args.input_file, articles_with_comments)
    
    print(f"Completed! Processed {len(articles)} articles and found {total_comments} comments.")

if __name__ == "__main__":
    main()