// ===== 워크북 (Workbook) Tab =====
(function () {
    const dropZone = document.getElementById('wb-drop-zone');
    const fileInput = document.getElementById('wb-file-input');
    const fileList = document.getElementById('wb-file-list');
    const extractBtn = document.getElementById('wb-extract-btn');
    const uploadSection = document.getElementById('wb-upload-section');
    const loadingSection = document.getElementById('wb-loading-section');
    const resultSectionType1 = document.getElementById('wb-result-section-type1');
    const resultSectionType2 = document.getElementById('wb-result-section-type2');
    const downloadSection = document.getElementById('wb-download-section');
    const downloadLink = document.getElementById('wb-download-link');
    const resetBtn = document.getElementById('wb-reset-btn');

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

    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text || '';
        return div.innerHTML;
    }

    // --- Extract (auto-detect type) ---
    extractBtn.addEventListener('click', async () => {
        if (selectedFiles.length === 0) return;

        uploadSection.style.display = 'none';
        loadingSection.style.display = 'block';

        const formData = new FormData();
        selectedFiles.forEach(f => formData.append('files', f));

        try {
            const res = await fetch('/api/workbook/upload', { method: 'POST', body: formData });
            if (!res.ok) {
                const text = await res.text();
                let msg = '추출에 실패했습니다.';
                try { const err = JSON.parse(text); msg = err.detail || msg; } catch { msg = text || msg; }
                throw new Error(msg);
            }
            const data = await res.json();
            currentJobId = data.job_id;

            loadingSection.style.display = 'none';

            // Show results based on what was detected
            const hasType1 = data.type1_entries && data.type1_entries.length > 0;
            const hasType2 = data.type2_entries && data.type2_entries.length > 0;

            if (hasType1) {
                renderType1Result(data.type1_entries);
                resultSectionType1.style.display = 'block';
            }
            if (hasType2) {
                renderType2Result(data.type2_entries);
                resultSectionType2.style.display = 'block';
            }
            if (!hasType1 && !hasType2) {
                alert('이미지에서 워크북 데이터를 추출하지 못했습니다.');
                uploadSection.style.display = 'block';
            }
        } catch (err) {
            alert('오류: ' + err.message);
            loadingSection.style.display = 'none';
            uploadSection.style.display = 'block';
        }
    });

    // ===== Type 1: 세로 테이블 =====
    const resultBodyType1 = document.getElementById('wb-result-body-type1');
    const entryCountType1 = document.getElementById('wb-entry-count-type1');
    const addRowBtnType1 = document.getElementById('wb-add-row-btn-type1');
    const generateBtnType1 = document.getElementById('wb-generate-btn-type1');

    function renderType1Result(entries) {
        resultBodyType1.innerHTML = '';
        entries.forEach((e, i) => addType1Row(e, i + 1));
        updateType1Count();
    }

    function addType1Row(entry, num) {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>${num}</td>
            <td><input type="text" class="chinese" value="${escapeHtml(entry.chinese)}"></td>
            <td><input type="text" class="pinyin" value="${escapeHtml(entry.pinyin)}"></td>
            <td><input type="text" class="meaning" value="${escapeHtml(entry.meaning)}"></td>
            <td><input type="text" class="example" value="${escapeHtml(entry.example)}"></td>
            <td><button class="delete-btn" title="삭제">&times;</button></td>
        `;
        tr.querySelector('.delete-btn').addEventListener('click', () => {
            tr.remove();
            renumberRows(resultBodyType1);
            updateType1Count();
        });
        resultBodyType1.appendChild(tr);
    }

    function updateType1Count() {
        entryCountType1.textContent = `(${resultBodyType1.querySelectorAll('tr').length}개)`;
    }

    addRowBtnType1.addEventListener('click', () => {
        const num = resultBodyType1.querySelectorAll('tr').length + 1;
        addType1Row({ chinese: '', pinyin: '', meaning: '', example: '' }, num);
        updateType1Count();
        const lastRow = resultBodyType1.lastElementChild;
        if (lastRow) lastRow.querySelector('input').focus();
    });

    generateBtnType1.addEventListener('click', () => {
        const rows = resultBodyType1.querySelectorAll('tr');
        const entries = [];
        rows.forEach(tr => {
            const chinese = tr.querySelector('.chinese').value.trim();
            const pinyin = tr.querySelector('.pinyin').value.trim();
            const meaning = tr.querySelector('.meaning').value.trim();
            const example = tr.querySelector('.example').value.trim();
            if (chinese || pinyin || meaning) {
                entries.push({ chinese, pinyin, meaning, example });
            }
        });
        generateWorkbook('type1', entries);
    });

    // ===== Type 2: 유형학습 =====
    const resultBodyType2 = document.getElementById('wb-result-body-type2');
    const entryCountType2 = document.getElementById('wb-entry-count-type2');
    const addRowBtnType2 = document.getElementById('wb-add-row-btn-type2');
    const generateBtnType2 = document.getElementById('wb-generate-btn-type2');

    function renderType2Result(entries) {
        resultBodyType2.innerHTML = '';
        entries.forEach((e, i) => addType2Row(e, i + 1));
        updateType2Count();
    }

    function addType2Row(entry, num) {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>${num}</td>
            <td><input type="text" class="speaker" value="${escapeHtml(entry.speaker)}" style="width:40px;"></td>
            <td><input type="text" class="korean" value="${escapeHtml(entry.korean)}"></td>
            <td><input type="text" class="chinese_text" value="${escapeHtml(entry.chinese_text)}"></td>
            <td><button class="delete-btn" title="삭제">&times;</button></td>
        `;
        tr.querySelector('.delete-btn').addEventListener('click', () => {
            tr.remove();
            renumberRows(resultBodyType2);
            updateType2Count();
        });
        resultBodyType2.appendChild(tr);
    }

    function updateType2Count() {
        entryCountType2.textContent = `(${resultBodyType2.querySelectorAll('tr').length}개)`;
    }

    addRowBtnType2.addEventListener('click', () => {
        const num = resultBodyType2.querySelectorAll('tr').length + 1;
        addType2Row({ speaker: '', korean: '', chinese_text: '' }, num);
        updateType2Count();
        const lastRow = resultBodyType2.lastElementChild;
        if (lastRow) lastRow.querySelector('input').focus();
    });

    generateBtnType2.addEventListener('click', () => {
        const rows = resultBodyType2.querySelectorAll('tr');
        const entries = [];
        rows.forEach(tr => {
            const speaker = tr.querySelector('.speaker').value.trim();
            const korean = tr.querySelector('.korean').value.trim();
            const chinese_text = tr.querySelector('.chinese_text').value.trim();
            if (korean || chinese_text) {
                entries.push({ speaker, korean, chinese_text });
            }
        });
        generateWorkbook('type2', entries);
    });

    // ===== Common =====
    function renumberRows(tbody) {
        tbody.querySelectorAll('tr').forEach((tr, i) => {
            tr.querySelector('td').textContent = i + 1;
        });
    }

    async function generateWorkbook(wbType, entries) {
        if (entries.length === 0) {
            alert('데이터가 없습니다.');
            return;
        }

        resultSectionType1.style.display = 'none';
        resultSectionType2.style.display = 'none';
        loadingSection.style.display = 'block';
        loadingSection.querySelector('p').textContent = '워크북을 생성 중입니다...';

        try {
            const res = await fetch('/api/workbook/generate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    job_id: currentJobId,
                    workbook_type: wbType,
                    entries: entries,
                }),
            });
            if (!res.ok) {
                const err = await res.json();
                throw new Error(err.detail || '파일 생성에 실패했습니다.');
            }
            const data = await res.json();
            downloadLink.href = `/api/workbook/download/${data.download_id}`;
            loadingSection.style.display = 'none';
            downloadSection.style.display = 'block';
        } catch (err) {
            alert('오류: ' + err.message);
            loadingSection.style.display = 'none';
            loadingSection.querySelector('p').textContent = 'AI가 교재를 분석 중입니다...';
            // Show back whichever result sections had data
            if (resultBodyType1.querySelectorAll('tr').length > 0) resultSectionType1.style.display = 'block';
            if (resultBodyType2.querySelectorAll('tr').length > 0) resultSectionType2.style.display = 'block';
        }
    }

    // --- Reset ---
    resetBtn.addEventListener('click', () => {
        selectedFiles = [];
        currentJobId = null;
        fileList.innerHTML = '';
        resultBodyType1.innerHTML = '';
        resultBodyType2.innerHTML = '';
        extractBtn.disabled = true;
        downloadSection.style.display = 'none';
        resultSectionType1.style.display = 'none';
        resultSectionType2.style.display = 'none';
        loadingSection.style.display = 'none';
        loadingSection.querySelector('p').textContent = 'AI가 교재를 분석 중입니다...';
        uploadSection.style.display = 'block';
    });
})();
