// Backend API URL - 배포시 실제 API URL로 변경
// const API_BASE_URL = 'http://localhost:8000'; // 로컬 개발용
const API_BASE_URL = 'https://daniel-crawl-web.onrender.com'; // Render backend

// DOM 요소들
const articleList = document.getElementById('article-list');
const loading = document.getElementById('loading');
const statusMessage = document.getElementById('status-message');
const noArticles = document.getElementById('no-articles');
const totalCount = document.getElementById('total-count');
const lastUpdated = document.getElementById('last-updated');

// 페이지네이션 관련 변수들
let currentPage = 1;
let totalPages = 1;
let perPage = 10;

// 페이지 데이터 동시 로딩
async function loadPageData(page = 1) {
    showLoading(true);
    currentPage = page;

    let articles = [];

    try {
        const articlesData = await apiCall(`/latest?page=${page}&per_page=${perPage}`);

        if (articlesData.articles && articlesData.articles.length > 0) {
            articles = articlesData.articles;
            // 페이지네이션 정보 업데이트
            totalPages = articlesData.pagination?.total_pages || 1;

            displayArticlesWithSummaries(articles, new Map());
            updatePaginationControls();
            hideNoArticles();
        } else {
            showNoArticles();
            showLoading(false);
            return;
        }
    } catch (error) {
        console.error('Failed to load articles:', error);
        showError('기사를 불러오는데 실패했습니다.');
        showLoading(false);
        return;
    }

    try {
        const summariesData = await apiCall('/summaries?limit=50');
        const summaryMap = new Map();

        if (summariesData.summaries && summariesData.summaries.length > 0) {
            summariesData.summaries.forEach(summary => {
                summaryMap.set(summary.article_url, summary);
            });
        }

        updateSummaryButtons(summaryMap);
    } catch (error) {
        console.error('Failed to load summaries:', error);
        showError('요약 정보를 불러오는데 실패했습니다.');
        updateSummaryButtons(new Map());
    } finally {
        showLoading(false);
    }
}

// 페이지 로드 시 초기화
document.addEventListener('DOMContentLoaded', function() {
    loadPageData();
    updateStats();
});

// API 호출 헬퍼 함수
async function apiCall(endpoint, options = {}) {
    try {
        const response = await fetch(`${API_BASE_URL}${endpoint}`, {
            ...options,
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            }
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        return await response.json();
    } catch (error) {
        console.error('API call failed:', error);
        throw error;
    }
}

// 기사 목록 불러오기
async function loadArticles() {
    try {
        showLoading(true);
        const data = await apiCall('/latest?limit=50');

        if (data.articles && data.articles.length > 0) {
            displayArticles(data.articles);
            hideNoArticles();
        } else {
            showNoArticles();
        }
    } catch (error) {
        console.error('Failed to load articles:', error);
        showError('기사를 불러오는데 실패했습니다.');
    } finally {
        showLoading(false);
    }
}

// 기사 표시 (요약 데이터와 함께)
function displayArticlesWithSummaries(articles, summaryMap) {
    articleList.innerHTML = '';

    articles.forEach(article => {
        const li = document.createElement('li');
        li.className = 'article-item';
        li.setAttribute('data-url', article.url);

        li.innerHTML = `
            <div class="article-title">${escapeHtml(article.title)}</div>
            <a href="${escapeHtml(article.url)}" target="_blank" class="article-link">
                기사 읽기 →
            </a>
            <div class="article-meta">
                작성일: ${formatDate(article.created_at)}
            </div>
        `;

        // 요약 버튼 즉시 추가
        const existingSummary = summaryMap.get(article.url);
        configureSummaryButtons(li, { url: article.url, title: article.title }, existingSummary);
        articleList.appendChild(li);
    });
}

// 기사 표시
function displayArticles(articles) {
    articleList.innerHTML = '';

    articles.forEach(article => {
        const li = document.createElement('li');
        li.className = 'article-item';
        li.setAttribute('data-url', article.url);

        li.innerHTML = `
            <div class="article-title">${escapeHtml(article.title)}</div>
            <a href="${escapeHtml(article.url)}" target="_blank" class="article-link">
                기사 읽기 →
            </a>
            <div class="article-meta">
                작성일: ${formatDate(article.created_at)}
            </div>
        `;

        articleList.appendChild(li);
    });

    // 요약 버튼들은 loadSummaries()에서 추가됨
}

// 통계 정보 업데이트
async function updateStats() {
    try {
        const data = await apiCall('/stats');
        totalCount.textContent = data.total_articles || 0;

        if (data.last_updated) {
            lastUpdated.textContent = formatDate(data.last_updated);
        } else {
            lastUpdated.textContent = '없음';
        }
    } catch (error) {
        console.error('Failed to update stats:', error);
        totalCount.textContent = '-';
        lastUpdated.textContent = '-';
    }
}

// 새 기사 확인
async function checkNewArticles() {
    const checkButton = document.querySelector('.btn-primary');

    // 로딩 상태로 변경
    showLoading(true);
    checkButton.disabled = true;
    checkButton.textContent = '확인 중...';
    hideStatusMessage();

    try {
        const data = await apiCall('/check');

        if (data.success) {
            showSuccess(data.message);

            // 새 기사가 있으면 목록 새로고침
            if (data.new_articles && data.new_articles.length > 0) {
                setTimeout(() => {
                    loadPageData();
                    updateStats();
                }, 2000);
            } else {
                updateStats();
            }
        } else {
            showError(data.message);
        }
    } catch (error) {
        console.error('Failed to check new articles:', error);
        showError('새 기사 확인 중 오류가 발생했습니다.');
    } finally {
        showLoading(false);
        checkButton.disabled = false;
        checkButton.textContent = '🔄 새 기사 확인';
    }
}

// UI 헬퍼 함수들
function showLoading(show) {
    loading.style.display = show ? 'block' : 'none';
}

function showSuccess(message) {
    statusMessage.textContent = message;
    statusMessage.className = 'status-message status-success';
    statusMessage.style.display = 'block';
}

function showError(message) {
    statusMessage.textContent = message;
    statusMessage.className = 'status-message status-error';
    statusMessage.style.display = 'block';
}

function hideStatusMessage() {
    statusMessage.style.display = 'none';
}

function showNoArticles() {
    noArticles.style.display = 'block';
    articleList.style.display = 'none';
}

function hideNoArticles() {
    noArticles.style.display = 'none';
    articleList.style.display = 'block';
}

// 유틸리티 함수들
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function formatDate(dateString) {
    try {
        const date = new Date(dateString);
        return date.toLocaleString('ko-KR', {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit'
        });
    } catch (error) {
        return dateString;
    }
}


// 요약 버튼들 업데이트 (모든 기사에 대해)
function updateSummaryButtons(summaryMap = new Map()) {
    // 모든 기사 요소 가져오기
    const articleElements = document.querySelectorAll('.article-item');

    articleElements.forEach((articleElement) => {
        const articleUrl = articleElement.getAttribute('data-url');
        if (!articleUrl) return;

        const summaryData = summaryMap.get(articleUrl);
        const articleInfo = {
            url: articleUrl,
            title: articleElement.querySelector('.article-title')?.textContent || ''
        };

        configureSummaryButtons(articleElement, articleInfo, summaryData);
    });
}

// 개별 기사 요약
async function summarizeSingleArticle(articleUrl, articleElement) {
    if (!articleElement) return;

    const generateBtn = articleElement.querySelector('.summary-generate-btn');
    const viewBtn = articleElement.querySelector('.summary-view-btn');
    const originalSummary = articleElement._summaryData || null;

    if (generateBtn) {
        generateBtn.disabled = true;
        generateBtn.textContent = '생성 중...';
        generateBtn.classList.remove('btn-secondary');
        if (!generateBtn.classList.contains('btn-outline')) {
            generateBtn.classList.add('btn-outline');
        }
    }

    if (viewBtn) {
        viewBtn.disabled = true;
        viewBtn.textContent = '생성 중...';
        viewBtn.classList.remove('btn-secondary');
        if (!viewBtn.classList.contains('btn-outline')) {
            viewBtn.classList.add('btn-outline');
        }
    }

    try {
        const response = await apiCall(`/summarize/${encodeURIComponent(articleUrl)}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
        });

        const articleTitle = articleElement.querySelector('.article-title')?.textContent || '';

        if (response.success) {
            showSuccess('기사 요약을 생성했습니다.');

            const summaryPayload = response.summary ? {
                article_url: articleUrl,
                title: response.summary?.title || articleTitle,
                ...response.summary,
            } : null;

            configureSummaryButtons(articleElement, { url: articleUrl, title: articleTitle }, summaryPayload);
        } else {
            showError(response.message || '요약 생성에 실패했습니다.');
            configureSummaryButtons(articleElement, { url: articleUrl, title: articleTitle }, originalSummary);
        }
    } catch (error) {
        console.error('Failed to summarize article:', error);
        showError('요약 생성 중 오류가 발생했습니다.');

        const articleTitle = articleElement.querySelector('.article-title')?.textContent || '';
        configureSummaryButtons(articleElement, { url: articleUrl, title: articleTitle }, originalSummary);
    }
}

function configureSummaryButtons(articleElement, articleInfo = {}, summary) {
    if (!articleElement) return;

    let buttonsContainer = articleElement.querySelector('.summary-buttons');
    if (!buttonsContainer) {
        buttonsContainer = document.createElement('div');
        buttonsContainer.className = 'summary-buttons';
        articleElement.appendChild(buttonsContainer);
    }

    let generateBtn = buttonsContainer.querySelector('.summary-generate-btn');
    if (!generateBtn) {
        generateBtn = document.createElement('button');
        generateBtn.className = 'btn btn-outline summary-btn summary-generate-btn';
        buttonsContainer.appendChild(generateBtn);
    }

    let viewBtn = buttonsContainer.querySelector('.summary-view-btn');
    if (!viewBtn) {
        viewBtn = document.createElement('button');
        viewBtn.className = 'btn btn-outline summary-btn summary-view-btn';
        buttonsContainer.appendChild(viewBtn);
    }

    const articleUrl = articleInfo.url || articleElement.getAttribute('data-url');
    const articleTitle = articleInfo.title || articleElement.querySelector('.article-title')?.textContent || '';

    generateBtn.disabled = false;
    generateBtn.textContent = '🤖 요약하기';
    generateBtn.className = 'btn btn-outline summary-btn summary-generate-btn';
    generateBtn.onclick = () => summarizeSingleArticle(articleUrl, articleElement);

    viewBtn.disabled = false;
    viewBtn.textContent = '📖 요약 보기';

    if (summary) {
        const modalPayload = {
            article_url: articleUrl,
            title: summary.title || articleTitle,
            ...summary,
        };

        articleElement._summaryData = modalPayload;

        viewBtn.className = 'btn btn-secondary summary-btn summary-view-btn';
        viewBtn.onclick = () => showSummaryModal(articleElement._summaryData);
    } else {
        articleElement._summaryData = null;

        viewBtn.className = 'btn btn-outline summary-btn summary-view-btn';
        viewBtn.onclick = () => summarizeSingleArticle(articleUrl, articleElement);
    }
}

// 요약 표시
function displaySummaries(summaries) {
    // 기존 요약 버튼들 업데이트
    updateSummaryButtons();
}

// 요약 모달 표시
function showSummaryModal(summary) {
    // 간단한 모달 생성
    const modal = document.createElement('div');
    modal.className = 'summary-modal';
    modal.innerHTML = `
        <div class="summary-modal-content">
            <div class="summary-modal-header">
                <h3>${escapeHtml(summary.title)}</h3>
                <button onclick="this.closest('.summary-modal').remove()">✕</button>
            </div>
            <div class="summary-modal-body">
                <div class="summary-section">
                    <h4>📝 요약</h4>
                    <p>${escapeHtml(summary.summary)}</p>
                </div>
                <div class="summary-section">
                    <h4>🏷️ 키워드</h4>
                    <div class="keywords">
                        ${summary.keywords.map(k => `<span class="keyword">${escapeHtml(k)}</span>`).join('')}
                    </div>
                </div>
                <div class="summary-section">
                    <h4>📖 관련 성경 구절</h4>
                    <ul class="bible-verses">
                        ${summary.bible_verses.map(v => `<li>${escapeHtml(v)}</li>`).join('')}
                    </ul>
                </div>
            </div>
        </div>
    `;

    // 모달을 body에 추가
    document.body.appendChild(modal);

    // 배경 클릭으로 닫기
    modal.addEventListener('click', function(e) {
        if (e.target === modal) {
            modal.remove();
        }
    });
}

// 페이지네이션 관련 함수들
function changePage(page) {
    if (page < 1 || page > totalPages) return;

    loadPageData(page);
    // 페이지 맨 위로 스크롤
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

function updatePaginationControls() {
    let paginationContainer = document.getElementById('pagination-controls');

    if (!paginationContainer) {
        paginationContainer = document.createElement('div');
        paginationContainer.id = 'pagination-controls';
        paginationContainer.className = 'pagination-controls';

        // 기사 목록 다음에 삽입
        const articlesSection = document.querySelector('.articles-section');
        articlesSection.appendChild(paginationContainer);
    }

    // 페이지네이션이 필요 없는 경우 (1페이지만 있는 경우)
    if (totalPages <= 1) {
        paginationContainer.style.display = 'none';
        return;
    }

    paginationContainer.style.display = 'flex';

    let paginationHtml = '';

    // 이전 버튼
    paginationHtml += `<button class="pagination-btn pagination-prev" ${currentPage === 1 ? 'disabled' : ''} onclick="changePage(${currentPage - 1})">‹ 이전</button>`;

    // 페이지 번호들
    const startPage = Math.max(1, currentPage - 2);
    const endPage = Math.min(totalPages, currentPage + 2);

    // 첫 페이지로 이동
    if (startPage > 1) {
        paginationHtml += `<button class="pagination-btn" onclick="changePage(1)">1</button>`;
        if (startPage > 2) {
            paginationHtml += `<span class="pagination-dots">...</span>`;
        }
    }

    // 페이지 번호 버튼들
    for (let i = startPage; i <= endPage; i++) {
        const activeClass = i === currentPage ? 'active' : '';
        paginationHtml += `<button class="pagination-btn ${activeClass}" onclick="changePage(${i})">${i}</button>`;
    }

    // 마지막 페이지로 이동
    if (endPage < totalPages) {
        if (endPage < totalPages - 1) {
            paginationHtml += `<span class="pagination-dots">...</span>`;
        }
        paginationHtml += `<button class="pagination-btn" onclick="changePage(${totalPages})">${totalPages}</button>`;
    }

    // 다음 버튼
    paginationHtml += `<button class="pagination-btn pagination-next" ${currentPage === totalPages ? 'disabled' : ''} onclick="changePage(${currentPage + 1})">다음 ›</button>`;

    paginationContainer.innerHTML = paginationHtml;
}

// 기존 초기화 코드는 loadPageData()로 대체됨

// 주기적으로 통계 업데이트 (30초마다)
setInterval(updateStats, 30000);
