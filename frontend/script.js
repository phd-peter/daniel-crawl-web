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

// 페이지 데이터 동시 로딩
async function loadPageData() {
    try {
        showLoading(true);

        // 기사와 요약 데이터를 동시에 가져옴
        const [articlesData, summariesData] = await Promise.all([
            apiCall('/latest?limit=50'),
            apiCall('/summaries?limit=50')
        ]);

        if (articlesData.articles && articlesData.articles.length > 0) {
            // 요약 데이터를 Map으로 변환
            const summaryMap = new Map();
            if (summariesData.summaries && summariesData.summaries.length > 0) {
                summariesData.summaries.forEach(summary => {
                    summaryMap.set(summary.article_url, summary);
                });
            }

            // 기사 표시 + 요약 버튼 즉시 추가
            displayArticlesWithSummaries(articlesData.articles, summaryMap);
            hideNoArticles();
        } else {
            showNoArticles();
        }
    } catch (error) {
        console.error('Failed to load page data:', error);
        showError('데이터를 불러오는데 실패했습니다.');
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
                저장일: ${formatDate(article.created_at)}
            </div>
        `;

        // 요약 버튼 즉시 추가
        const existingSummary = summaryMap.get(article.url);
        const summaryBtn = document.createElement('button');
        summaryBtn.className = existingSummary ? 'btn btn-secondary summary-btn' : 'btn btn-outline summary-btn';
        summaryBtn.textContent = existingSummary ? '📖 요약 보기' : '🤖 요약하기';

        if (existingSummary) {
            summaryBtn.onclick = () => showSummaryModal({
                article_url: article.url,
                title: article.title,
                ...existingSummary
            });
        } else {
            summaryBtn.onclick = () => summarizeSingleArticle(article.url, summaryBtn);
        }

        li.appendChild(summaryBtn);
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
                저장일: ${formatDate(article.created_at)}
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
                    loadArticles();
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

// 요약 생성
async function generateSummaries() {
    const generateButton = document.querySelectorAll('.btn-primary')[1]; // 두 번째 버튼

    // 로딩 상태로 변경
    showLoading(true);
    generateButton.disabled = true;
    generateButton.textContent = '생성 중...';
    hideStatusMessage();

    try {
        const response = await apiCall('/summarize', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
        });

        if (response.success) {
            showSuccess(response.message);

            // 요약 목록 새로고침
            setTimeout(() => {
                loadSummaries();
            }, 2000);
        } else {
            showError('요약 생성에 실패했습니다.');
        }
    } catch (error) {
        console.error('Failed to generate summaries:', error);
        showError('요약 생성 중 오류가 발생했습니다.');
    } finally {
        showLoading(false);
        generateButton.disabled = false;
        generateButton.textContent = '🤖 요약 생성';
    }
}

// 요약 목록 불러오기
async function loadSummaries() {
    try {
        const data = await apiCall('/summaries?limit=50'); // 충분한 수의 요약 가져옴

        // 요약 데이터를 Map으로 변환
        const summaryMap = new Map();
        if (data.summaries && data.summaries.length > 0) {
            data.summaries.forEach(summary => {
                summaryMap.set(summary.article_url, summary);
            });
        }

        // 요약 데이터를 전달해서 버튼 업데이트
        updateSummaryButtons(summaryMap);
    } catch (error) {
        console.error('Failed to load summaries:', error);
        updateSummaryButtons(new Map()); // 오류 시 빈 Map
    }
}

// 요약 버튼들 업데이트 (모든 기사에 대해)
function updateSummaryButtons(summaryMap = new Map()) {
    // 모든 기사 요소 가져오기
    const articleElements = document.querySelectorAll('.article-item');

    articleElements.forEach((articleElement) => {
        const articleUrl = articleElement.getAttribute('data-url');
        if (!articleUrl) return;

        // 기존 요약 버튼이 있는지 확인
        let summaryBtn = articleElement.querySelector('.summary-btn');

        // 요약 데이터 확인
        const existingSummary = summaryMap.get(articleUrl);

        if (existingSummary) {
            // 요약이 있음: "요약 보기" 버튼
            if (!summaryBtn) {
                summaryBtn = document.createElement('button');
                summaryBtn.className = 'btn btn-secondary summary-btn';
                articleElement.appendChild(summaryBtn);
            }
            summaryBtn.textContent = '📖 요약 보기';
            summaryBtn.onclick = () => showSummaryModal({
                article_url: articleUrl,
                title: articleElement.querySelector('.article-title').textContent,
                ...existingSummary
            });
        } else {
            // 요약이 없음: "요약하기" 버튼
            if (!summaryBtn) {
                summaryBtn = document.createElement('button');
                summaryBtn.className = 'btn btn-outline summary-btn';
                articleElement.appendChild(summaryBtn);
            }
            summaryBtn.textContent = '🤖 요약하기';
            summaryBtn.onclick = () => summarizeSingleArticle(articleUrl, summaryBtn);
        }
    });
}

// 개별 기사 요약
async function summarizeSingleArticle(articleUrl, buttonElement) {
    // 로딩 상태로 변경
    const originalText = buttonElement.textContent;
    buttonElement.disabled = true;
    buttonElement.textContent = '생성 중...';

    try {
        const response = await apiCall(`/summarize/${encodeURIComponent(articleUrl)}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
        });

        if (response.success) {
            showSuccess('기사 요약을 생성했습니다.');

            // 버튼 상태 업데이트
            buttonElement.disabled = false;
            buttonElement.textContent = '📖 요약 보기';
            buttonElement.className = 'btn btn-secondary summary-btn';

            // 요약 모달 표시
            buttonElement.onclick = () => showSummaryModal(response.summary);
        } else {
            showError(response.message || '요약 생성에 실패했습니다.');
            buttonElement.disabled = false;
            buttonElement.textContent = originalText;
        }
    } catch (error) {
        console.error('Failed to summarize article:', error);
        showError('요약 생성 중 오류가 발생했습니다.');
        buttonElement.disabled = false;
        buttonElement.textContent = originalText;
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

// 기존 초기화 코드는 loadPageData()로 대체됨

// 주기적으로 통계 업데이트 (30초마다)
setInterval(updateStats, 30000);
