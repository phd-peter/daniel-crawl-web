import os
from openai import OpenAI
from typing import Dict, List, Optional
import json
from scraper import scrape_article_content

# Initialize OpenAI client
client = OpenAI()

def summarize_article(article_url: str, title: str) -> Optional[Dict]:
    """
    Summarize an article using OpenAI GPT.
    Returns dict with summary, keywords, and bible verses.
    """
    try:
        # First, scrape the article content
        content = scrape_article_content(article_url)
        if not content:
            print(f"Could not scrape content for article: {article_url}")
            return None

        # Create the prompt for summarization
        prompt = f"""
다음은 다니엘기도회 관련 기사입니다:
이 기사를 다음 형식으로 요약해주세요:

1. 요약: 기사를 약 300단어로 요약해주세요. 기사의 핵심 내용과 메시지를 포함하세요.

2. 키워드: 기사의 주요 키워드 3-5개를 추출해주세요.

3. 성경 구절: 이 기사에서 언급된 성경 구절 1-2개를 추천해주세요. 없다면 작성하지 마세요.

제목: {title}

본문: {content}

응답은 다음 JSON 형식으로 해주세요:
{{
  "summary": "300단어 요약문",
  "keywords": ["키워드1", "키워드2", "키워드3"],
  "bible_verses": ["구절1", "구절2"]
}}
"""

        # Call OpenAI API
        response = client.responses.create(
            model="gpt-5-mini-2025-08-07",
            input=prompt
        )

        

        # Parse the response
        if hasattr(response, 'output') and response.output and len(response.output) > 1:
            result_text = response.output[1].content[0].text

            # Parse the JSON response directly
            try:
                result = json.loads(result_text)

                # Validate the result structure
                if all(key in result for key in ['summary', 'keywords', 'bible_verses']):
                    return {
                        'summary': result['summary'],
                        'keywords': result['keywords'] if isinstance(result['keywords'], list) else [],
                        'bible_verses': result['bible_verses'] if isinstance(result['bible_verses'], list) else []
                    }
                else:
                    print(f"Missing required keys in response: {result.keys()}")
            except json.JSONDecodeError as e:
                print(f"JSON parsing error: {e}")
                print(f"Response text: {result_text}")

        print(f"Invalid response format from OpenAI for article: {article_url}")
        return None

    except Exception as e:
        print(f"Error summarizing article {article_url}: {e}")
        return None

def summarize_top_articles(limit: int = 3) -> List[Dict]:
    """
    Summarize the top N most recent articles.
    Returns list of summary dictionaries.
    """
    from db import get_all_links

    try:
        # Get the most recent articles
        articles = get_all_links(limit=limit)
        summaries = []

        for article in articles:
            # Check if summary already exists
            from db import get_article_summary
            existing_summary = get_article_summary(article['url'])

            if existing_summary:
                # Use existing summary
                summaries.append({
                    'article_url': article['url'],
                    'title': article['title'],
                    **existing_summary
                })
            else:
                # Generate new summary
                print(f"Generating summary for: {article['title']}")
                summary_data = summarize_article(article['url'], article['title'])

                if summary_data:
                    # Save to database
                    from db import save_article_summary
                    save_article_summary(
                        article['url'],
                        summary_data['summary'],
                        summary_data['keywords'],
                        summary_data['bible_verses']
                    )

                    summaries.append({
                        'article_url': article['url'],
                        'title': article['title'],
                        **summary_data
                    })

        return summaries

    except Exception as e:
        print(f"Error in summarize_top_articles: {e}")
        return []

def test_summarizer():
    """Test the summarizer with a sample article."""
    from db import get_all_links

    articles = get_all_links(limit=1)
    if articles:
        article = articles[0]
        print(f"Testing summarizer with article: {article['title']}")
        result = summarize_article(article['url'], article['title'])

        if result:
            print("Summary generated successfully:")
            print(f"Summary: {result['summary'][:200]}...")
            print(f"Keywords: {result['keywords']}")
            print(f"Bible verses: {result['bible_verses']}")
        else:
            print("Failed to generate summary")
    else:
        print("No articles found to test with")

if __name__ == "__main__":
    test_summarizer()
