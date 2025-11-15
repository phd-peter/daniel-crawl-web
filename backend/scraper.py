import requests
from bs4 import BeautifulSoup
import time
from typing import List, Tuple

URL = "https://www.christiantoday.co.kr/sections/pd_19"
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

def scrape_article_date(article_url: str) -> str:
    """
    개별 기사 페이지에서 작성일 추출
    """
    try:
        response = requests.get(article_url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        response.encoding = 'utf-8'

        soup = BeautifulSoup(response.text, 'html.parser')

        # Christian Today의 작성일 표기 방식들:
        # 1. <time datetime="2024-11-15T10:30:00+09:00">형식
        # 2. 기사 메타 정보에서 날짜 찾기
        # 3. <span class="date"> 또는 유사한 클래스

        # 방법 1: <time> 태그에서 datetime 속성 찾기
        time_element = soup.find('time', {'datetime': True})
        if time_element and time_element.get('datetime'):
            datetime_str = time_element.get('datetime')
            # ISO 8601 형식에서 날짜 부분만 추출 (2024-11-15T10:30:00+09:00 -> 2024-11-15)
            if 'T' in datetime_str:
                return datetime_str.split('T')[0]
            return datetime_str

        # 방법 2: 날짜 관련 텍스트 찾기 (예: "2024-11-15", "2024.11.15" 등)
        import re
        date_patterns = [
            r'\d{4}-\d{2}-\d{2}',  # 2024-11-15
            r'\d{4}\.\d{2}\.\d{2}',  # 2024.11.15
        ]

        text_content = soup.get_text()
        for pattern in date_patterns:
            matches = re.findall(pattern, text_content)
            if matches:
                # 첫 번째 매치를 표준 형식으로 변환
                date_str = matches[0]
                if '.' in date_str:
                    date_str = date_str.replace('.', '-')
                return date_str

        return None

    except Exception as e:
        print(f"날짜 추출 실패 {article_url}: {e}")
        return None

def get_latest_links() -> List[Tuple[str, str, str]]:
    """
    Scrape the Christian Today Daniel Prayer section for article links and titles.
    Handles two different HTML structures:
    1. Latest news: article h2 a (most recent article)
    2. Regular news: ul.l-list li a (other articles)
    Returns list of tuples: (url, title)
    """
    try:
        response = requests.get(URL, headers=HEADERS, timeout=10)
        response.raise_for_status()
        response.encoding = 'utf-8'

        soup = BeautifulSoup(response.text, 'html.parser')

        articles = []

        # Phase 1: Extract latest news (article h2 a)
        # This is the most recent article featured prominently
        latest_news_links = soup.select('article h2 a[href*="/news/"]')
        for link in latest_news_links:
            href = link.get('href')
            if href:
                # Make sure it's a full URL
                if href.startswith('http'):
                    full_url = href
                else:
                    full_url = f"https://www.christiantoday.co.kr{href}"

                # Extract title from the link text
                title = link.get_text(strip=True)

                # Clean up title
                if title:
                    title = title.replace('\n', ' ').replace('\r', ' ').strip()
                    # Remove extra whitespace
                    while '  ' in title:
                        title = title.replace('  ', ' ')
                else:
                    title = "제목 없음"

                # Only add if it's a valid Christian Today news URL
                if 'christiantoday.co.kr/news/' in full_url:
                    articles.append((full_url, title))

        # Phase 2: Extract regular news from the specific list container
        # Only from ul.l-list.w-divider.gap-md.no-bullet li elements
        list_items = soup.select('ul.l-list.w-divider.gap-md.no-bullet li')

        for li in list_items:
            # Find the news link within this li element
            link = li.find('a', href=lambda x: x and '/news/' in x)
            if link:
                href = link.get('href')
                if href:
                    # Make sure it's a full URL
                    if href.startswith('http'):
                        full_url = href
                    else:
                        full_url = f"https://www.christiantoday.co.kr{href}"

                    # Try to extract title from the link first
                    title = link.get_text(strip=True)

                    # If no title in link, look for title in the li element
                    if not title or title == "...":
                        # Look for title in various places within the li
                        title_elem = li.find(['h3', 'h4', 'strong', 'b', '.title', '.headline'])
                        if title_elem:
                            title = title_elem.get_text(strip=True)
                        else:
                            # Look for any text content in the li that's not in other links
                            li_text = li.get_text(separator=' ', strip=True)
                            # Remove other URLs from the text
                            for other_link in li.find_all('a'):
                                if other_link != link:
                                    other_link.extract()
                            li_text = li.get_text(separator=' ', strip=True)
                            if li_text and len(li_text) > 10:  # Reasonable title length
                                title = li_text

                    # Clean up title
                    if title and title not in ["...", ""]:
                        title = title.replace('\n', ' ').replace('\r', ' ').strip()
                        # Remove extra whitespace
                        while '  ' in title:
                            title = title.replace('  ', ' ')
                    else:
                        title = "제목 없음"

                    # Only add if it's a valid Christian Today news URL
                    if 'christiantoday.co.kr/news/' in full_url:
                        articles.append((full_url, title))

        # 기사별 작성일 추출 및 튜플 생성 (url, title, published_at)
        articles_with_dates = []
        seen = set()

        for url, title in articles:
            if url not in seen:
                seen.add(url)
                # 작성일 추출
                published_at = scrape_article_date(url)
                articles_with_dates.append((url, title, published_at))

        return articles_with_dates

    except requests.RequestException as e:
        print(f"Error scraping website: {e}")
        return []
    except Exception as e:
        print(f"Unexpected error during scraping: {e}")
        return []

def test_scraper():
    """Test function to verify scraper is working."""
    print("Testing scraper...")
    articles = get_latest_links()
    print(f"Found {len(articles)} articles:")
    for i, (url, title, published_at) in enumerate(articles[:5]):  # Show first 5
        print(f"{i+1}. {title}")
        print(f"   URL: {url}")
        print(f"   날짜: {published_at}")
        print()
    return articles



def scrape_article_content(article_url):
    """
    Scrape the full content of an article from its URL.
    Returns the article content text.
    """
    try:
        response = requests.get(article_url, headers=HEADERS, timeout=15)
        response.raise_for_status()
        response.encoding = 'utf-8'

        soup = BeautifulSoup(response.text, 'html.parser')

        # Find the article content div
        content_div = soup.select_one('.article-content')
        if not content_div:
            return None

        # Extract text from the content div
        # Remove script tags and other unwanted elements
        for script in content_div.find_all('script'):
            script.decompose()
        for style in content_div.find_all('style'):
            style.decompose()

        # Get text content
        content_text = content_div.get_text(separator='\n', strip=True)

        # Clean up the text
        lines = [line.strip() for line in content_text.split('\n') if line.strip()]
        content_text = '\n'.join(lines)

        return content_text if len(content_text) > 100 else None  # Minimum content length

    except requests.RequestException as e:
        print(f"Error scraping article {article_url}: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error scraping article {article_url}: {e}")
        return None

def get_articles_from_page(page_num=2) -> List[Tuple[str, str, str]]:
    """
    특정 페이지의 기사들을 크롤링
    기존 get_latest_links() 로직 재사용
    """
    page_url = f"https://www.christiantoday.co.kr/sections/pd_19/page{page_num}.htm"

    try:
        response = requests.get(page_url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        response.encoding = 'utf-8'

        soup = BeautifulSoup(response.text, 'html.parser')

        articles = []

        # Phase 1: Extract latest news (article h2 a)
        latest_news_links = soup.select('article h2 a[href*="/news/"]')
        for link in latest_news_links:
            href = link.get('href')
            if href:
                if href.startswith('http'):
                    full_url = href
                else:
                    full_url = f"https://www.christiantoday.co.kr{href}"

                title = link.get_text(strip=True)
                if title:
                    title = title.replace('\n', ' ').replace('\r', ' ').strip()
                    while '  ' in title:
                        title = title.replace('  ', ' ')
                else:
                    title = "제목 없음"

                if 'christiantoday.co.kr/news/' in full_url:
                    articles.append((full_url, title))

        # Phase 2: Extract regular news from the specific list container
        # Only from ul.l-list.w-divider.gap-md.no-bullet li elements
        list_items = soup.select('ul.l-list.w-divider.gap-md.no-bullet li')

        for li in list_items:
            link = li.find('a', href=lambda x: x and '/news/' in x)
            if link:
                href = link.get('href')
                if href:
                    if href.startswith('http'):
                        full_url = href
                    else:
                        full_url = f"https://www.christiantoday.co.kr{href}"

                    title = link.get_text(strip=True)

                    if not title or title == "...":
                        title_elem = li.find(['h3', 'h4', 'strong', 'b', '.title', '.headline'])
                        if title_elem:
                            title = title_elem.get_text(strip=True)
                        else:
                            li_text = li.get_text(separator=' ', strip=True)
                            for other_link in li.find_all('a'):
                                if other_link != link:
                                    other_link.extract()
                            li_text = li.get_text(separator=' ', strip=True)
                            if li_text and len(li_text) > 10:
                                title = li_text

                    if title and title not in ["...", ""]:
                        title = title.replace('\n', ' ').replace('\r', ' ').strip()
                        while '  ' in title:
                            title = title.replace('  ', ' ')
                    else:
                        title = "제목 없음"

                    if 'christiantoday.co.kr/news/' in full_url:
                        articles.append((full_url, title))

        # 기사별 작성일 추출 및 튜플 생성 (url, title, published_at)
        articles_with_dates = []
        seen = set()

        for url, title in articles:
            if url not in seen:
                seen.add(url)
                # 작성일 추출
                published_at = scrape_article_date(url)
                articles_with_dates.append((url, title, published_at))

        return articles_with_dates

    except requests.RequestException as e:
        print(f"Error scraping page {page_num}: {e}")
        return []
    except Exception as e:
        print(f"Unexpected error during scraping page {page_num}: {e}")
        return []

if __name__ == "__main__":
    test_scraper()
