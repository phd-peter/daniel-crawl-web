"""
1회성 bulk import 스크립트
page2의 과거 기사들을 DB에 추가하기 위해 사용

주의: 이 스크립트는 수동으로 1회만 실행해야 함.
Deploy할 때마다 실행되지 않도록 주의.
"""

from scraper import get_articles_from_page
from db import save_new_links
import sys

def import_page2_articles():
    """
    Page 2의 기사들을 DB에 bulk import
    """
    print("Page 2 기사 크롤링 시작...")
    articles = get_articles_from_page(2)

    if not articles:
        print("Page 2에서 기사를 찾을 수 없습니다.")
        return 0

    print(f"Page 2에서 {len(articles)}개 기사 발견")
    print("샘플 기사들:")
    for i, (url, title, published_at) in enumerate(articles[:3]):
        if published_at:
            print(f"  {i+1}. [{published_at}] {title[:40]}...")
        else:
            print(f"  {i+1}. {title[:50]}...")

    print("\nDB에 저장 시작...")
    new_articles = save_new_links(articles)

    print(f"\n✅ 완료! {len(new_articles)}개 새로운 기사 추가됨")
    if len(new_articles) < len(articles):
        print(f"   (중복된 {len(articles) - len(new_articles)}개는 건너뜀)")

    return len(new_articles)

if __name__ == "__main__":
    print("=" * 50)
    print("다니엘기도회 뉴스 과거 기사 Bulk Import")
    print("=" * 50)

    try:
        new_count = import_page2_articles()
        if new_count > 0:
            print(f"\n🎉 성공적으로 {new_count}개 과거 기사 추가됨!")
        else:
            print("\n⚠️  새로운 기사가 없거나 모두 중복됨")

    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        sys.exit(1)
