"""
기존 DB의 모든 기사에 실제 OpenAI 요약을 추가하는 스크립트

기존 요약이 있더라도 OpenAI로 새로 생성하여 덮어쓰기
OpenAI API를 사용하여 모든 기사에 고품질 요약과 키워드, 성경 구절 추천을 추가
"""

import time
import sys
from db import get_all_links, save_article_summary, get_article_summary
from summarizer import summarize_article

def populate_all_summaries():
    """
    DB에 있는 모든 기사에 실제 OpenAI 요약을 추가하는 함수
    기존 요약이 있더라도 새로 생성하여 덮어쓰기
    """
    print("🤖 DB 실제 OpenAI 요약 데이터 추가 시작 (30개 기사)")
    print("=" * 50)

    # 1. 모든 기사 가져오기 (30개)
    articles = get_all_links(limit=30)
    total_articles = len(articles)

    print(f"📄 총 {total_articles}개 기사 발견")
    print()

    processed_count = 0
    failed_count = 0

    # 2. 각 기사별 실제 요약 생성 (기존 무시하고 항상 생성)
    for i, article in enumerate(articles, 1):
        print(f"[{i:2d}/{total_articles}] 처리 중: {article['title'][:50]}...")

        try:
            print(f"    🤖 실제 OpenAI 요약 생성 중...")

            # 실제 OpenAI 요약 생성
            summary_data = summarize_article(article['url'], article['title'])

            if summary_data:
                # 요약 데이터 저장 (덮어쓰기)
                save_article_summary(
                    article_url=article['url'],
                    summary=summary_data['summary'],
                    keywords=summary_data['keywords'],
                    bible_verses=summary_data['bible_verses']
                )
                print(f"    ✅ 실제 요약 저장 완료")
                processed_count += 1
            else:
                print(f"    ❌ 요약 생성 실패")
                failed_count += 1

        except Exception as e:
            print(f"    ❌ 요약 생성 중 오류: {str(e)}")
            failed_count += 1

        # API rate limit 방지 (5초 대기)
        print("    ⏱️  API rate limit 대기 중... (5초)")
        time.sleep(5)

    # 3. 결과 요약
    print()
    print("=" * 50)
    print("📊 최종 결과:")
    print(f"  ✅ 성공적으로 요약된 기사: {processed_count}개")
    print(f"  ❌ 실패한 기사: {failed_count}개")
    print(f"  📄 총 기사 수: {total_articles}개")
    print("=" * 50)

    if processed_count == total_articles:
        print("🎉 모든 기사에 실제 OpenAI 요약 추가 완료!")
        print("   이제 프론트엔드에서 고품질 요약을 볼 수 있습니다.")
    else:
        print("⚠️  일부 기사에서 오류가 발생했습니다. 로그를 확인하세요.")

    return processed_count, failed_count

if __name__ == "__main__":
    print("다니엘기도회 뉴스 - DB 실제 OpenAI 요약 데이터 추가 스크립트")
    print("OpenAI GPT-4o-mini를 사용하여 30개 기사에 고품질 요약을 추가합니다.")
    print("주의: API 비용이 발생할 수 있습니다. (약 30 요청)")
    print()

    try:
        processed, failed = populate_all_summaries()

        # 작업 결과에 따라 exit code 설정
        if failed > 0:
            print(f"\n⚠️  일부 실패: {failed}개")
            sys.exit(1)
        else:
            print(f"\n✅ 모든 작업 완료! (성공: {processed})")
            sys.exit(0)

    except KeyboardInterrupt:
        print("\n\n⚠️  사용자가 작업을 중단했습니다.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 예상치 못한 오류 발생: {e}")
        sys.exit(1)
