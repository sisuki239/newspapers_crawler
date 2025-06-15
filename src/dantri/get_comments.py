import requests
import pandas as pd
import time
import argparse
import sys
from tqdm import tqdm

def get_article_comments(article_id):
    """
    Fetch comments for a Dantri article
    
    Args:
        article_id: ID of the article
        
    Returns:
        List of comments for the article
    """
    url = f"https://webapi.dantri.com.vn/listcomment?objectId={article_id}&objectType=1&offset=0&limit=10000&orderBy=popular"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        
        data = response.json()
        return data.get('items', [])
    except Exception as e:
        print(f"Error fetching comments for article {article_id}: {e}")
        return []

def get_comment_replies(comment_id):
    """
    Fetch replies for a specific comment
    
    Args:
        comment_id: ID of the comment
        
    Returns:
        List of replies to the comment
    """
    url = f"https://webapi.dantri.com.vn/listcomment?objectId={comment_id}&objectType=1&offset=0&limit=10000&orderBy=popular&isReply=True"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        
        data = response.json()
        return data.get('items', [])
    except Exception as e:
        print(f"Error fetching replies for comment {comment_id}: {e}")
        return []

def process_comments(article_id, comments):
    """
    Process comments and their replies
    
    Args:
        article_id: ID of the article
        comments: List of comment dictionaries
        
    Returns:
        List of dictionaries with processed comments and replies
    """
    result = []
    
    for comment in comments:
        comment_id = comment.get('commentId')
        parent_id = comment.get('parentId')
        content = comment.get('commentContent', '')
        
        # Calculate total reactions
        reactions = comment.get('reactions', {})
        total_likes = reactions.get('total', 0) if reactions else 0
        
        # Add comment to result
        result.append({
            'article_id': article_id,
            'comment_id': comment_id,
            'parent_id': parent_id if parent_id else '',
            'is_reply': False if parent_id is None else True,
            'content': content,
            'likes': total_likes
        })
        
        # Check if comment has replies
        reply_count = comment.get('replyCount', 0)
        if reply_count > 0:
            # Fetch replies for this comment
            replies = get_comment_replies(comment_id)
            
            for reply in replies:
                reply_id = reply.get('commentId')
                content = reply.get('commentContent', '')
                
                # Calculate total reactions for reply
                reply_reactions = reply.get('reactions', {})
                reply_likes = reply_reactions.get('total', 0) if reply_reactions else 0
                
                # Add reply to result
                result.append({
                    'article_id': article_id,
                    'comment_id': reply_id,
                    'parent_id': comment_id,
                    'is_reply': True,
                    'content': content,
                    'likes': reply_likes
                })
    
    return result

def main():
    parser = argparse.ArgumentParser(description='Crawl comments from Dantri articles')
    parser.add_argument('--input', '-i', default='dantri_articles.csv', help='Input CSV file with article data')
    parser.add_argument('--output', '-o', default='dantri_comments.csv', help='Output CSV file (default: dantri_comments.csv)')
    parser.add_argument('--delay', '-d', type=float, default=1.0, help='Delay between requests in seconds (default: 1.0)')
    
    args = parser.parse_args()
    
    try:
        # Read input CSV
        print(f"Reading articles from {args.input}...")
        articles_df = pd.read_csv(args.input)
        
        if 'article_id' not in articles_df.columns:
            print("Error: Input CSV must contain 'article_id' column")
            return 1
        
        all_comments = []
        article_count = len(articles_df)
        
        # Process each article
        print(f"Crawling comments from {article_count} articles...")
        for index, row in tqdm(articles_df.iterrows(), total=article_count):
            article_id = row['article_id']
            
            # Get comments for this article
            comments = get_article_comments(article_id)
            
            if comments:
                # Process comments and their replies
                processed_comments = process_comments(article_id, comments)
                all_comments.extend(processed_comments)
                
                comment_count = len(processed_comments)
                print(f"Found {comment_count} comments/replies for article {article_id}")
            else:
                print(f"No comments found for article {article_id}")
            
            # Add delay between requests
            time.sleep(args.delay)
        
        # Save results to CSV
        if all_comments:
            comments_df = pd.DataFrame(all_comments)
            
            # Ensure columns are in the desired order
            ordered_columns = ['article_id', 'comment_id', 'parent_id', 'is_reply', 'content', 'likes']
            comments_df = comments_df[ordered_columns]
            
            comments_df.to_csv(args.output, index=False)
            print(f"Saved {len(all_comments)} comments/replies to {args.output}")
        else:
            print("No comments found for any article.")
        
        return 0
            
    except Exception as e:
        print(f"Error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())