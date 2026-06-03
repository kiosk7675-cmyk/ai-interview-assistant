// 面试备考页面交互逻辑

const API = '/api/interview';

// 状态
let resumeId = null;
let filePath = null;
let interviewId = null;
let currentQuestionId = null;
let selectedJobTitle = null;
let reportMarkdown = '';

// Loading 覆盖层
function showLoading(msg) {
    let overlay = document.getElementById('loadingOverlay');
    if (!overlay) {
        overlay = document.createElement('div');
        overlay.id = 'loadingOverlay';
        overlay.innerHTML = '<div class="spinner"></div><p class="loading-msg"></p>';
        document.body.appendChild(overlay);
    }
    overlay.querySelector('.loading-msg').textContent = msg || '处理中...';
    overlay.style.display = 'flex';
}
function hideLoading() {
    const overlay = document.getElementById('loadingOverlay');
    if (overlay) overlay.style.display = 'none';
}

// DOM
const steps = {
    upload: document.getElementById('stepUpload'),
    parsing: document.getElementById('stepParsing'),
    match: document.getElementById('stepMatch'),
    interview: document.getElementById('stepInterview'),
    report: document.getElementById('stepReport'),
};

// ---- 工具函数 ----
function showStep(name) {
    Object.values(steps).forEach(el => el.classList.remove('active'));
    steps[name].classList.add('active');
}

async function apiPost(path, body) {
    const r = await fetch(`${API}${path}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
    });
    const data = await r.json();
    if (!r.ok || data.code !== 200) {
        const msg = data.detail || data.message || '请求失败';
        throw new Error(typeof msg === 'object' ? JSON.stringify(msg) : String(msg));
    }
    return data.data;
}

// ---- 步骤1: 上传简历 ----
const uploadZone = document.getElementById('uploadZone');
const fileInput = document.getElementById('fileInput');
const browseLink = document.getElementById('browseLink');

browseLink.addEventListener('click', () => fileInput.click());
uploadZone.addEventListener('click', (e) => { if (e.target !== browseLink) fileInput.click(); });

uploadZone.addEventListener('dragover', (e) => { e.preventDefault(); uploadZone.classList.add('dragover'); });
uploadZone.addEventListener('dragleave', () => uploadZone.classList.remove('dragover'));
uploadZone.addEventListener('drop', (e) => {
    e.preventDefault();
    uploadZone.classList.remove('dragover');
    const file = e.dataTransfer.files[0];
    if (file) handleFile(file);
});

fileInput.addEventListener('change', () => {
    if (fileInput.files[0]) handleFile(fileInput.files[0]);
});

async function handleFile(file) {
    if (!file.name.toLowerCase().endsWith('.pdf')) {
        alert('仅支持 PDF 格式'); return;
    }
    if (file.size > 10 * 1024 * 1024) {
        alert('文件大小不能超过 10MB'); return;
    }

    // 上传
    const progressEl = document.getElementById('uploadProgress');
    const progressFill = document.getElementById('progressFill');
    const progressText = document.getElementById('progressText');
    progressEl.style.display = 'block';
    progressFill.style.width = '30%';
    progressText.textContent = '上传中...';

    const formData = new FormData();
    formData.append('file', file);
    try {
        const r = await fetch(`${API}/resume/upload`, { method: 'POST', body: formData });
        const data = await r.json();
        if (data.code !== 200) {
            const errMsg = data.detail || data.message || '上传失败';
            throw new Error(typeof errMsg === 'object' ? JSON.stringify(errMsg) : String(errMsg));
        }
        filePath = data.data.file_path;
        progressFill.style.width = '60%';
        progressText.textContent = '上传成功，开始解析...';

        // 自动解析
        const parsed = await apiPost('/resume/parse', { file_path: filePath });
        resumeId = parsed.resume_id;
        progressFill.style.width = '100%';

        // 渲染简历摘要
        renderResume(parsed);

        // 岗位匹配
        progressText.textContent = '岗位匹配中...';
        showStep('parsing');
        const matchResult = await apiPost('/job/match', { resume_id: resumeId });
        renderJobs(matchResult);
        showStep('match');
    } catch (e) {
        progressFill.style.width = '0%';
        progressEl.style.display = 'none';
        alert('处理失败: ' + e.message);
    }
}

function renderResume(resume) {
    const el = document.getElementById('resumeInfo');
    let html = '';
    if (resume.name) html += `<p><span class="label">姓名:</span>${resume.name}</p>`;
    if (resume.email) html += `<p><span class="label">邮箱:</span>${resume.email}</p>`;
    if (resume.phone) html += `<p><span class="label">电话:</span>${resume.phone}</p>`;
    if (resume.years_of_experience) html += `<p><span class="label">工作年限:</span>${resume.years_of_experience}年</p>`;
    if (resume.skills && resume.skills.length) {
        html += `<p><span class="label">技能:</span></p><div class="skill-tags">`;
        resume.skills.forEach(s => html += `<span class="skill-tag">${s}</span>`);
        html += '</div>';
    }
    if (resume.education && resume.education.length) {
        html += '<p><span class="label">教育:</span></p>';
        resume.education.forEach(e => {
            html += `<p style="margin-left:8px">${e.school} - ${e.degree} - ${e.major}</p>`;
        });
    }
    el.innerHTML = html || '<p>未能提取到简历信息</p>';
}

function renderJobs(matchResult) {
    const list = document.getElementById('jobList');
    const startBtn = document.getElementById('startBtn');
    list.innerHTML = '';

    matchResult.recommendations.forEach((job, i) => {
        const card = document.createElement('div');
        card.className = 'job-card';
        card.dataset.jobTitle = job.job_title;
        card.innerHTML = `
            <div>
                <span class="job-title">${job.job_title}</span>
                <span class="job-score">匹配度 ${job.match_percentage}%</span>
            </div>
            <p class="job-reason">${job.reason}</p>
            <div class="job-skills">
                ${job.matching_skills.map(s => `<span class="skill-tag match">${s}</span>`).join('')}
                ${job.missing_skills.map(s => `<span class="skill-tag missing">${s}</span>`).join('')}
            </div>
        `;
        card.addEventListener('click', () => {
            document.querySelectorAll('.job-card').forEach(c => c.classList.remove('selected'));
            card.classList.add('selected');
            selectedJobTitle = job.job_title;
            startBtn.disabled = false;
        });
        list.appendChild(card);
    });
}

// ---- 步骤3: 开始面试 ----
document.getElementById('startBtn').addEventListener('click', async () => {
    if (!selectedJobTitle) return;
    const btn = document.getElementById('startBtn');
    btn.disabled = true;
    btn.textContent = 'AI 出题中...';
    // 显示 loading 覆盖层
    showLoading('正在基于简历和面经生成面试题，请稍候...');
    try {
        const data = await apiPost('/start', {
            resume_id: resumeId,
            job_title: selectedJobTitle,
            total_questions: 10,
        });
        hideLoading();
        interviewId = data.interview_id;
        document.getElementById('jobBadge').textContent = `· ${selectedJobTitle}`;
        updateProgress(1, data.total_questions);
        showQuestion(data.question);
        showStep('interview');
    } catch (e) {
        hideLoading();
        alert('开始面试失败: ' + e.message);
    } finally {
        btn.disabled = false;
        btn.textContent = '开始面试';
    }
});

function updateProgress(current, total) {
    const pct = Math.round(current / total * 100);
    document.getElementById('interviewProgressFill').style.width = pct + '%';
    document.getElementById('interviewProgressText').textContent = `${current}/${total}`;
}

function showQuestion(q) {
    currentQuestionId = q.id;

    // 题型标签映射
    const categoryMap = {
        'bagu': '八股文',
        'scenario': '场景题',
        'project': '项目深挖',
        'algorithm': '算法题',
        'technical': '技术题',
        'behavioral': '行为题',
        'comprehensive': '综合题',
    };
    const category = q.category || categoryMap[q.type] || '技术题';
    document.getElementById('qTypeBadge').textContent = category;
    document.getElementById('qTypeBadge').className = 'q-type-badge q-type-' + (q.type || 'technical');
    document.getElementById('qText').textContent = q.question;

    // 力扣链接（算法题）
    const lcLinkEl = document.getElementById('leetcodeLink');
    if (q.leetcode_link) {
        lcLinkEl.href = q.leetcode_link;
        lcLinkEl.style.display = 'inline-flex';
    } else {
        lcLinkEl.style.display = 'none';
    }

    document.getElementById('answerInput').value = '';
    document.getElementById('charCount').textContent = '0';
    document.getElementById('answerArea').style.display = 'block';
    document.getElementById('feedbackCard').style.display = 'none';
    document.getElementById('answerInput').focus();
}

// ---- 字符计数 ----
document.getElementById('answerInput').addEventListener('input', (e) => {
    document.getElementById('charCount').textContent = e.target.value.length;
});

// ---- 提交回答 ----
document.getElementById('submitBtn').addEventListener('click', () => submitAnswer(false));
document.getElementById('skipBtn').addEventListener('click', () => submitAnswer(true));

async function submitAnswer(skip = false) {
    const answer = skip ? '[SKIP]' : document.getElementById('answerInput').value.trim();
    if (!skip && !answer) {
        alert('请先输入答案后再提交');
        return;
    }

    const btn = document.getElementById('submitBtn');
    btn.disabled = true;
    btn.textContent = 'AI 评分中...';
    showLoading('正在评分并生成下一题，请稍候...');

    try {
        const data = await apiPost('/answer', {
            interview_id: interviewId,
            question_id: currentQuestionId,
            answer: answer,
            time_spent: 0,
        });

        // 显示评分反馈
        const ev = data.evaluation;
        document.getElementById('scoreNum').textContent = ev.score;
        document.getElementById('feedbackText').textContent = ev.feedback;

        const strList = document.getElementById('strengthsList');
        strList.innerHTML = ev.strengths.length
            ? `<h4>优点</h4><ul>${ev.strengths.map(s => `<li>${s}</li>`).join('')}</ul>`
            : '';

        const weakList = document.getElementById('weaknessesList');
        weakList.innerHTML = ev.weaknesses.length
            ? `<h4>不足</h4><ul>${ev.weaknesses.map(s => `<li>${s}</li>`).join('')}</ul>`
            : '';

        document.getElementById('answerArea').style.display = 'none';
        document.getElementById('feedbackCard').style.display = 'block';

        if (data.interview_completed) {
            document.getElementById('nextBtn').textContent = '查看报告';
            document.getElementById('nextBtn').onclick = () => generateReport();
        } else {
            document.getElementById('nextBtn').textContent = '下一题';
            document.getElementById('nextBtn').onclick = () => {
                showQuestion(data.next_question);
                if (data.progress) updateProgress(data.progress.current, data.progress.total);
            };
        }
    } catch (e) {
        hideLoading();
        alert('提交失败: ' + e.message);
    } finally {
        hideLoading();
        btn.disabled = false;
        btn.textContent = '提交回答';
    }
}

// ---- 步骤5: 生成报告 ----
async function generateReport() {
    showStep('report');
    document.getElementById('reportLoading').style.display = 'block';
    document.getElementById('reportContainer').style.display = 'none';
    document.getElementById('reportActions').style.display = 'none';

    try {
        const data = await apiPost('/end', { interview_id: interviewId });
        reportMarkdown = data.report_markdown;
        const container = document.getElementById('reportContainer');
        if (typeof marked !== 'undefined') {
            container.innerHTML = marked.parse(reportMarkdown);
        } else {
            container.innerHTML = `<pre>${reportMarkdown}</pre>`;
        }
        document.getElementById('reportLoading').style.display = 'none';
        container.style.display = 'block';
        document.getElementById('reportActions').style.display = 'flex';
    } catch (e) {
        document.getElementById('reportLoading').innerHTML = `<p style="color:var(--danger)">报告生成失败: ${e.message}</p>`;
    }
}

// ---- 下载报告 ----
document.getElementById('downloadBtn').addEventListener('click', () => {
    const blob = new Blob([reportMarkdown], { type: 'text/markdown;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `面试报告-${selectedJobTitle}.md`;
    a.click();
    URL.revokeObjectURL(url);
});

// ---- 重新开始 ----
document.getElementById('restartBtn').addEventListener('click', () => {
    resumeId = null;
    filePath = null;
    interviewId = null;
    currentQuestionId = null;
    selectedJobTitle = null;
    reportMarkdown = '';
    fileInput.value = '';
    document.querySelectorAll('.job-card').forEach(c => c.classList.remove('selected'));
    document.getElementById('startBtn').disabled = true;
    document.getElementById('uploadProgress').style.display = 'none';
    showStep('upload');
});
