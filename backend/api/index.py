from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import os
from datetime import datetime
from typing import List, Dict

from scraper import get_latest_links
from db import init_db, save_new_links, get_all_links, get_latest_links as get_stored_links, get_article_summaries, get_article_summary
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
async def get_latest_articles(limit: int = 10):
    """최근 저장된 기사 목록을 JSON으로 반환"""
    try:
        links = get_stored_links()
        return JSONResponse({
            "articles": links[:limit],
            "count": len(links[:limit]),
            "total_stored": len(get_all_links())
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
        # URL 디코딩
        from urllib.parse import unquote
        decoded_url = unquote(article_url)

        # 기사 정보 조회
        from db import get_all_links
        articles = get_all_links()
        article = next((a for a in articles if a['url'] == decoded_url), None)

        if not article:
            raise HTTPException(status_code=404, detail="기사를 찾을 수 없습니다.")

        # 이미 요약이 있는지 확인
        existing_summary = get_article_summary(decoded_url)
        if existing_summary:
            return JSONResponse({
                "success": False,
                "message": "이미 요약이 존재합니다.",
                "summary": existing_summary
            })

        # 새 요약 생성
        from summarizer import summarize_article
        summary_data = summarize_article(decoded_url, article['title'])

        if summary_data:
            # DB에 저장
            save_article_summary(
                decoded_url,
                summary_data['summary'],
                summary_data['keywords'],
                summary_data['bible_verses']
            )

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
            raise HTTPException(status_code=500, detail="요약 생성에 실패했습니다.")

    except HTTPException:
        raise
    except Exception as e:
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
