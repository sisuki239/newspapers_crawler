#!/usr/bin/env python3
import requests
import pandas as pd
import json
import time
import argparse
import sys
from tqdm import tqdm

def get_article_comments(article_id):
    """
    Fetch comments for a TuoiTre article
    
    Args:
        article_id: ID of the article
        
    Returns:
        List of comment dictionaries with id, content and reactions
    """
    url = f"https://id.tuoitre.vn/api/getlist-comment.api?pagesize=1000&objId={article_id}&objType=1&sort=2"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        
        data = response.json()
        comments_json = data.get('Data', '[]')
        
        # If the data is returned as a string (JSON), parse it
        if isinstance(comments_json, str):
            comments = json.loads(comments_json)
        else:
            comments = comments_json
            
        return comments
    except Exception as e:
        print(f"Error fetching comments for article {article_id}: {e}")
        return []

def calculate_total_reactions(reactions_dict):
    """
    Calculate the total number of reactions from the reactions dictionary
    
    Args:
        reactions_dict: Dictionary of reaction types and counts
        
    Returns:
        Total number of reactions
    """
    if not reactions_dict:
        return 0
    
    return sum(reactions_dict.values())

def process_article_comments(article_id, comments):
    """
    Process and format article comments
    
    Args:
        article_id: ID of the article
        comments: List of comment dictionaries
        
    Returns:
        List of dictionaries with article_id, content and reacts
    """
    result = []
    
    for comment in comments:
        content = comment.get('content', '')
        
        # Calculate total reactions
        reactions = comment.get('reactions', {})
        total_reactions = calculate_total_reactions(reactions)
        
        result.append({
            'article_id': article_id,
            'content': content,
            'reacts': total_reactions
        })
        
        # Process replies to this comment
        child_comments = comment.get('child_comments', [])
        if child_comments:
            for child in child_comments:
                child_content = child.get('content', '')
                child_reactions = child.get('reactions', {})
                child_total_reactions = calculate_total_reactions(child_reactions)
                
                result.append({
                    'article_id': article_id,
                    'content': child_content,
                    'reacts': child_total_reactions
                })
    
    return result

def main():
    parser = argparse.ArgumentParser(description='Crawl comments from TuoiTre articles')
    parser.add_argument('--input', '-i', required=True, help='Input CSV file with article data')
    parser.add_argument('--output', '-o', default='tuoitre_comments.csv', help='Output CSV file (default: tuoitre_comments.csv)')
    parser.add_argument('--delay', '-d', type=float, default=1.0, help='Delay between requests in seconds (default: 1.0)')
    
    args = parser.parse_args()
    
    try:
        # Read input CSV
        articles_df = pd.read_csv(args.input)
        
        if 'article_id' not in articles_df.columns:
            print("Error: Input CSV must contain 'article_id' column")
            return 1
        
        all_comments = []
        
        # Process each article
        print(f"Crawling comments for {len(articles_df)} articles...")
        for _, row in tqdm(articles_df.iterrows(), total=len(articles_df)):
            article_id = row['article_id']
            
            # Get comments for this article
            comments = get_article_comments(article_id)
            
            if comments:
                # Process and format comments
                processed_comments = process_article_comments(article_id, comments)
                all_comments.extend(processed_comments)
                
                print(f"Found {len(processed_comments)} comments for article {article_id}")
            else:
                print(f"No comments found for article {article_id}")
            
            # Add delay between requests
            time.sleep(args.delay)
        
        # Save results to CSV
        if all_comments:
            comments_df = pd.DataFrame(all_comments)
            comments_df.to_csv(args.output, index=False)
            print(f"Saved {len(all_comments)} comments to {args.output}")
        else:
            print("No comments found for any article.")
        
        return 0
            
    except Exception as e:
        print(f"Error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())