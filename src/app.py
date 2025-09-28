import json
import os
import requests
import boto3  # ⬅️ IMPORT: AWS SDK for DynamoDB
from bs4 import BeautifulSoup

# --- CONFIGURATION ---
NLP_API_KEY = os.environ.get("NLP_API_KEY")
NLP_API_URL = "https://api.nlpcloud.io/v1/bart-large-cnn/summarization"

# Initialize DynamoDB outside the handler for connection reuse
DYNAMODB = boto3.resource('dynamodb')
# Note: Table name must match the one defined in template.yaml
CACHE_TABLE = DYNAMODB.Table('NewsSummaryCache')

# Global constant for text size limits
MAX_INPUT_CHARS = 2000 # Max input size for NLP API payload fix
MIN_EXTRACT_CHARS = 200 # Minimum text length to qualify as an article

def extract_main_text(url):
    """Fetches the URL and extracts text by targeting article paragraphs."""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'html.parser')

        # Robust heuristic to find the main article container
        article_body = soup.find(['article', 'main', 'div'], class_=['article-body', 'article-content', 'main-content'])

        if not article_body:
            article_body = soup.find('body')
        if not article_body:
            return None

        # Clean out noise tags
        for script_or_style in article_body(['script', 'style', 'header', 'footer', 'nav']):
            script_or_style.decompose()

        # Extract text ONLY from paragraph tags
        paragraphs = article_body.find_all('p')
        main_content = []
        for p in paragraphs:
            text = p.get_text(strip=True)
            if len(text) > 50:
                main_content.append(text)

        clean_text = ' '.join(main_content)
        
        # Check minimum required length
        if len(clean_text) < MIN_EXTRACT_CHARS:
             print(f"Warning: Only found {len(clean_text)} characters, returning None.")
             return None

        return clean_text
    
    except Exception as e:
        print(f"Error extracting content from URL: {e}")
        return None

def lambda_handler(event, context):
    """The main Lambda function handler."""
    try:
        body = json.loads(event['body']) 
        news_url = body.get('url')

        if not news_url:
            return {'statusCode': 400, 'body': json.dumps({'error': 'Missing "url" in request body'})}
        
        print(f"Received request to summarize: {news_url}")

        # 🚀 1. BONUS: CHECK CACHE 
        try:
            cache_response = CACHE_TABLE.get_item(Key={'ArticleUrl': news_url})
            if 'Item' in cache_response:
                summary = cache_response['Item']['Summary']
                print("Cache hit! Returning stored summary.")
                return {
                    'statusCode': 200,
                    'body': json.dumps({'url': news_url, 'summary': summary, 'cached': True}),
                    'headers': {'Content-Type': 'application/json'}
                }
        except Exception as e:
            print(f"DynamoDB cache check failed: {e}") 
            # Continue execution if cache check fails

        # 2. Extract text (Only runs if cache misses)
        article_text = extract_main_text(news_url)

        if not article_text:
            return {'statusCode': 400, 'body': json.dumps({'error': 'Could not extract enough text from the provided URL'})}

        # Truncate input text to MAX_INPUT_CHARS for API limits
        if len(article_text) > MAX_INPUT_CHARS:
            article_text = article_text[:MAX_INPUT_CHARS]
            print(f"Truncated article to {MAX_INPUT_CHARS} characters for API limits.")
        
        # 3. Call NLP Cloud API
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Token {NLP_API_KEY}' 
        }
        payload = {
            "text": article_text,
            "max_length": 150 # Concise summary length
        }

        nlp_response = requests.post(NLP_API_URL, headers=headers, json=payload, timeout=30)
        nlp_response.raise_for_status()
        summary_data = nlp_response.json()
        summary_text = summary_data.get('summary_text', 'Error: Summary not generated.')

        # 💾 4. BONUS: WRITE CACHE
        try:
            CACHE_TABLE.put_item(
                Item={'ArticleUrl': news_url, 'Summary': summary_text}
            )
            print("Successfully stored new summary in cache.")
        except Exception as e:
            print(f"DynamoDB cache write failed: {e}")

        # 5. Return the result
        return {
            'statusCode': 200,
            'body': json.dumps({
                'url': news_url,
                'summary': summary_text,
                'cached': False 
            }),
            'headers': {'Content-Type': 'application/json'}
        }

    except Exception as e:
        print(f"An error occurred: {e}")
        details = str(e)
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Internal server error', 'details': details})
        }