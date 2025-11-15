from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import os
from datetime import datetime
from typing import List, Dict

from scraper import get_latest_links
from db import init_db, save_new_links, get_all_links, get_latest_links as get_stored_links, get_article_summaries, get_article_summary, save_article_summary, get_paginated_links, get_total_article_count, migrate_published_dates
from summarizer import summarize_top_articles

app = FastAPI(
    title="다니엘기도회 뉴스 API",
    description="Christian Today 다니엘기도회 뉴스 자동 감지 및 저장 API",
    version="1.0.0"
)

# CORS 설정 - 프론트엔드에서 API 호출 가능하도록
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 실제 배포시 특정 도메인으로 제한
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database on startup
init_db()

# 환경변수로 제어되는 1회성 bulk import
if os.getenv("RUN_BULK_IMPORT") == "true":
    print("🏗️ 환경변수 RUN_BULK_IMPORT=true 감지!")
    print("1회성 bulk import 시작...")
    try:
        from bulk_import import import_page2_articles
        count = import_page2_articles()
        print(f"✅ {count}개 과거 기사 추가 완료!")
    except Exception as e:
        print(f"❌ Bulk import 실패: {e}")
else:
    print("ℹ️ RUN_BULK_IMPORT 환경변수가 설정되지 않아 bulk import 생략")

@app.get("/check")
async def check_new_articles():
    """새로운 기사를 수동으로 확인하고 저장"""
    try:
        # 웹사이트에서 최신 기사 가져오기
        latest_articles = get_latest_links()

        if not latest_articles:
            return JSONResponse({
                "success": False,
                "message": "웹사이트에서 기사를 가져올 수 없습니다.",
                "new_articles": []
            })

        # 새로운 기사만 저장
        new_articles = save_new_links(latest_articles)

        return JSONResponse({
            "success": True,
            "message": f"{len(new_articles)}개의 새로운 기사를 발견했습니다.",
            "new_articles": new_articles,
            "total_found": len(latest_articles),
            "checked_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"기사 확인 중 오류 발생: {str(e)}")

@app.get("/latest")
async def get_latest_articles(page: int = 1, per_page: int = 20):
    """최근 저장된 기사 목록을 페이지별로 JSON으로 반환"""
    try:
        # 입력값 검증
        if page < 1:
            page = 1
        if per_page < 1 or per_page > 100:
            per_page = 20

        # 페이징된 기사 가져오기
        articles = get_paginated_links(page=page, per_page=per_page)

        # 전체 기사 수 가져오기
        total_articles = get_total_article_count()
        total_pages = (total_articles + per_page - 1) // per_page  # 올림 나눗셈

        return JSONResponse({
            "articles": articles,
            "pagination": {
                "current_page": page,
                "per_page": per_page,
                "total_articles": total_articles,
                "total_pages": total_pages
            }
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"데이터 조회 오류: {str(e)}")

@app.get("/stats")
async def get_stats():
    """저장된 기사 통계 정보"""
    try:
        all_links = get_all_links(limit=1000)  # 충분히 큰 숫자로 전체 조회
        return JSONResponse({
            "total_articles": len(all_links),
            "last_updated": all_links[0]["created_at"] if all_links else None,
            "source_url": "https://www.christiantoday.co.kr/sections/pd_19"
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"통계 조회 오류: {str(e)}")

@app.get("/summaries")
async def get_summaries(limit: int = 10):
    """요약된 기사 목록을 반환"""
    try:
        summaries = get_article_summaries(limit=limit)
        return JSONResponse({
            "summaries": summaries,
            "count": len(summaries)
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"요약 데이터 조회 오류: {str(e)}")

@app.post("/summarize")
async def generate_summaries(limit: int = 3):
    """상위 N개 기사를 요약하여 저장"""
    try:
        summaries = summarize_top_articles(limit=limit)
        return JSONResponse({
            "success": True,
            "message": f"{len(summaries)}개의 기사 요약을 생성했습니다.",
            "summaries": summaries,
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"요약 생성 중 오류 발생: {str(e)}")

@app.post("/summarize/{article_url:path}")
async def summarize_single_article(article_url: str):
    """특정 기사를 요약하여 저장"""
    try:
        print(f"DEBUG: Received URL: {article_url}")

        # URL 디코딩
        from urllib.parse import unquote
        decoded_url = unquote(article_url)
        print(f"DEBUG: Decoded URL: {decoded_url}")

        # 기사 정보 조회
        from db import get_all_links
        articles = get_all_links()
        print(f"DEBUG: Total articles in DB: {len(articles)}")

        article = next((a for a in articles if a['url'] == decoded_url), None)
        print(f"DEBUG: Found article: {article}")

        if not article:
            print(f"ERROR: Article not found for URL: {decoded_url}")
            raise HTTPException(status_code=404, detail="기사를 찾을 수 없습니다.")

        # 이미 요약이 있는지 확인
        existing_summary = get_article_summary(decoded_url)
        print(f"DEBUG: Existing summary: {existing_summary is not None}")

        if existing_summary:
            return JSONResponse({
                "success": False,
                "message": "이미 요약이 존재합니다.",
                "summary": existing_summary
            })

        print(f"DEBUG: Starting summarization for: {article['title']}")

        # 새 요약 생성
        from summarizer import summarize_article
        summary_data = summarize_article(decoded_url, article['title'])
        print(f"DEBUG: Summary data generated: {summary_data is not None}")

        if summary_data:
            print(f"DEBUG: Saving summary to DB")

            # DB에 저장
            save_article_summary(
                decoded_url,
                summary_data['summary'],
                summary_data['keywords'],
                summary_data['bible_verses']
            )

            print(f"DEBUG: Summary saved successfully")

            return JSONResponse({
                "success": True,
                "message": "기사 요약을 생성했습니다.",
                "summary": {
                    "article_url": decoded_url,
                    "title": article['title'],
                    **summary_data
                },
                "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
        else:
            print(f"ERROR: Summary generation failed")
            raise HTTPException(status_code=500, detail="요약 생성에 실패했습니다.")

    except HTTPException:
        raise
    except Exception as e:
        print(f"ERROR: Exception in summarize_single_article: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"요약 생성 중 오류 발생: {str(e)}")

@app.get("/summary/{article_url:path}")
async def get_single_summary(article_url: str):
    """특정 기사의 요약을 반환"""
    try:
        # URL 디코딩
        from urllib.parse import unquote
        decoded_url = unquote(article_url)

        summary = get_article_summary(decoded_url)
        if summary:
            return JSONResponse(summary)
        else:
            raise HTTPException(status_code=404, detail="요약을 찾을 수 없습니다.")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"요약 조회 오류: {str(e)}")

@app.post("/migrate")
async def migrate_existing_articles():
    """기존 기사들의 작성일 정보를 마이그레이션"""
    try:
        updated_count = migrate_published_dates()
        return JSONResponse({
            "success": True,
            "message": f"{updated_count}개 기사의 작성일을 마이그레이션했습니다.",
            "updated_count": updated_count
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"마이그레이션 중 오류 발생: {str(e)}")

@app.get("/health")
async def health_check():
    """서버 상태 확인"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

# Vercel serverless function entry point
def handler(event, context):
    """Vercel serverless function handler"""
    return app(event, context)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
