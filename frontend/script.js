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

// 페이지 로드 시 초기화
document.addEventListener('DOMContentLoaded', function() {
    loadArticles();
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
        const data = await apiCall('/summaries?limit=10');

        if (data.summaries && data.summaries.length > 0) {
            displaySummaries(data.summaries);
        }
    } catch (error) {
        console.error('Failed to load summaries:', error);
    }
}

// 요약 표시
function displaySummaries(summaries) {
    // 기존 기사 목록에 요약 정보 추가
    summaries.forEach(summary => {
        const articleElement = document.querySelector(`[data-url="${summary.article_url}"]`);
        if (articleElement) {
            // 요약 버튼 추가 또는 업데이트
            let summaryBtn = articleElement.querySelector('.summary-btn');
            if (!summaryBtn) {
                summaryBtn = document.createElement('button');
                summaryBtn.className = 'btn btn-secondary summary-btn';
                summaryBtn.textContent = '📖 요약 보기';
                summaryBtn.onclick = () => showSummaryModal(summary);
                articleElement.appendChild(summaryBtn);
            }
        }
    });
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

// 페이지 로드 시 요약도 불러오기
document.addEventListener('DOMContentLoaded', function() {
    loadArticles();
    updateStats();
    loadSummaries(); // 요약도 불러오기
});

// 주기적으로 통계 업데이트 (30초마다)
setInterval(updateStats, 30000);
