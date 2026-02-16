const dropZone = document.getElementById('drop-zone');
const fileInput = document.getElementById('file-input');
const fileList = document.getElementById('file-list');
const extractBtn = document.getElementById('extract-btn');
const uploadSection = document.getElementById('upload-section');
const loadingSection = document.getElementById('loading-section');
const resultSection = document.getElementById('result-section');
const downloadSection = document.getElementById('download-section');
const resultBody = document.getElementById('result-body');
const wordCount = document.getElementById('word-count');
const generateBtn = document.getElementById('generate-btn');
const addRowBtn = document.getElementById('add-row-btn');
const downloadLink = document.getElementById('download-link');
const resetBtn = document.getElementById('reset-btn');

let selectedFiles = [];
let currentJobId = null;

// --- Upload ---
dropZone.addEventListener('click', () => fileInput.click());
dropZone.addEventListener('dragover', (e) => { e.preventDefault(); dropZone.classList.add('dragover'); });
dropZone.addEventListener('dragleave', () => dropZone.classList.remove('dragover'));
dropZone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropZone.classList.remove('dragover');
    addFiles(e.dataTransfer.files);
});
fileInput.addEventListener('change', () => addFiles(fileInput.files));

function addFiles(files) {
    for (const f of files) {
        if (f.type.startsWith('image/')) {
            selectedFiles.push(f);
        }
    }
    renderFileList();
    extractBtn.disabled = selectedFiles.length === 0;
}

function renderFileList() {
    fileList.innerHTML = '';
    selectedFiles.forEach((f, i) => {
        const tag = document.createElement('span');
        tag.className = 'file-tag';
        tag.innerHTML = `${f.name} <span class="remove" data-idx="${i}">&times;</span>`;
        fileList.appendChild(tag);
    });
    fileList.querySelectorAll('.remove').forEach(el => {
        el.addEventListener('click', (e) => {
            selectedFiles.splice(parseInt(e.target.dataset.idx), 1);
            renderFileList();
            extractBtn.disabled = selectedFiles.length === 0;
        });
    });
}

// --- Extract ---
extractBtn.addEventListener('click', async () => {
    if (selectedFiles.length === 0) return;

    uploadSection.style.display = 'none';
    loadingSection.style.display = 'block';

    const formData = new FormData();
    selectedFiles.forEach(f => formData.append('files', f));

    try {
        const res = await fetch('/api/upload', { method: 'POST', body: formData });
        if (!res.ok) {
            const text = await res.text();
            let msg = '추출에 실패했습니다.';
            try { const err = JSON.parse(text); msg = err.detail || msg; } catch { msg = text || msg; }
            throw new Error(msg);
        }
        const data = await res.json();
        currentJobId = data.job_id;
        renderResult(data.words);
        loadingSection.style.display = 'none';
        resultSection.style.display = 'block';
    } catch (err) {
        alert('오류: ' + err.message);
        loadingSection.style.display = 'none';
        uploadSection.style.display = 'block';
    }
});

// --- Result Table ---
function renderResult(words) {
    resultBody.innerHTML = '';
    words.forEach((w, i) => addTableRow(w, i + 1));
    updateWordCount();
}

function addTableRow(word, num) {
    const tr = document.createElement('tr');
    tr.innerHTML = `
        <td>${num}</td>
        <td><input type="text" class="chinese" value="${escapeHtml(word.chinese)}"></td>
        <td><input type="text" class="pinyin" value="${escapeHtml(word.pinyin)}"></td>
        <td><input type="text" class="korean" value="${escapeHtml(word.korean)}"></td>
        <td><button class="delete-btn" title="삭제">&times;</button></td>
    `;
    tr.querySelector('.delete-btn').addEventListener('click', () => {
        tr.remove();
        renumberRows();
        updateWordCount();
    });
    resultBody.appendChild(tr);
}

function renumberRows() {
    resultBody.querySelectorAll('tr').forEach((tr, i) => {
        tr.querySelector('td').textContent = i + 1;
    });
}

function updateWordCount() {
    const count = resultBody.querySelectorAll('tr').length;
    wordCount.textContent = `(${count}개)`;
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

addRowBtn.addEventListener('click', () => {
    const num = resultBody.querySelectorAll('tr').length + 1;
    addTableRow({ chinese: '', pinyin: '', korean: '' }, num);
    updateWordCount();
    // Focus the new row's first input
    const lastRow = resultBody.lastElementChild;
    if (lastRow) lastRow.querySelector('input').focus();
});

// --- Generate ---
generateBtn.addEventListener('click', async () => {
    const rows = resultBody.querySelectorAll('tr');
    const words = [];
    rows.forEach(tr => {
        const chinese = tr.querySelector('.chinese').value.trim();
        const pinyin = tr.querySelector('.pinyin').value.trim();
        const korean = tr.querySelector('.korean').value.trim();
        if (chinese || pinyin || korean) {
            words.push({ chinese, pinyin, korean });
        }
    });

    if (words.length === 0) {
        alert('단어가 없습니다.');
        return;
    }

    resultSection.style.display = 'none';
    loadingSection.style.display = 'block';
    loadingSection.querySelector('p').textContent = 'Word 파일을 생성 중입니다...';

    try {
        const res = await fetch('/api/generate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ job_id: currentJobId, words }),
        });
        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail || '파일 생성에 실패했습니다.');
        }
        const data = await res.json();
        downloadLink.href = `/api/download/${data.download_id}`;
        loadingSection.style.display = 'none';
        downloadSection.style.display = 'block';
    } catch (err) {
        alert('오류: ' + err.message);
        loadingSection.style.display = 'none';
        loadingSection.querySelector('p').textContent = 'AI가 이미지를 분석 중입니다...';
        resultSection.style.display = 'block';
    }
});

// --- Reset ---
resetBtn.addEventListener('click', () => {
    selectedFiles = [];
    currentJobId = null;
    fileList.innerHTML = '';
    resultBody.innerHTML = '';
    extractBtn.disabled = true;
    downloadSection.style.display = 'none';
    loadingSection.querySelector('p').textContent = 'AI가 이미지를 분석 중입니다...';
    uploadSection.style.display = 'block';
});
