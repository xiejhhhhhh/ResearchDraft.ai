const API_BASE = 'http://127.0.0.1:9000';

const translations = {
  zh: {
    nav: { value: '服务价值', process: '流程', start: '开始使用' },
    hero: {
      eyebrow: 'Zotero 驱动的科研写作自动化',
      title: '从指定 Zotero 文献文件夹生成英文研究初稿和 LaTeX 文件',
      description: '先在 Zotero 中按研究项目整理文献，系统只读取被选择的 collection。若该文件夹不足 20 篇参考文献，后端会自动补充外部学术索引结果，并生成英文研究文案、Markdown、LaTeX、BibTeX 和 PDF 审阅文件。',
      startBtn: '立即开始',
      processBtn: '了解流程',
      useCases: '适用场景',
      useCase1: '按 Zotero collection 管理不同论文的参考文献',
      useCase2: '在文献不足时自动补足到 20 篇候选引用',
      useCase3: '生成英文论文大纲、LaTeX、BibTeX 和 PDF 审阅稿',
    },
    features: {
      eyebrow: '服务价值',
      title: '让引用来源可控，让初稿生成更贴近真实科研流程',
      description: '当前版本采用 Zotero-first 工作流：用户选择一个 collection，系统只读取该文件夹内文献；若数量不足 20 篇，再自动补充外部学术索引结果，避免直接切换来源造成引用混乱。',
      collection: 'Collection 精准引用',
      collectionDesc: '每篇文章选择一个 Zotero 文件夹，系统不会回退到全库，减少误引其他项目文献的风险。',
      supplement: '自动补充文献',
      supplementDesc: '当已选 collection 少于 20 篇文献时，后端会自动检索相关英文文献并补足候选引用。',
      bibtex: 'BibTeX 与 PDF 输出',
      bibtexDesc: '基于文献元数据导出 BibTeX，并与 LaTeX 初稿、PDF 审阅稿一起保存，方便后续导入 Overleaf。',
    },
    process: {
      eyebrow: '工作流程',
      title: '4 步完成 Zotero-backed research draft',
      step1: '整理 Zotero 文件夹',
      step1Desc: '把本篇文章需要使用的文献放入一个明确命名的 Zotero collection。',
      step2: '选择 collection',
      step2Desc: '页面从后端读取 Zotero collection 列表，用户选择本次写作对应的文献文件夹。',
      step3: '生成英文初稿',
      step3Desc: 'AI 基于指定 collection 和自动补充文献构建背景、综述、数据、方法和预期结果。',
      step4: '下载文件',
      step4Desc: '下载 Markdown、LaTeX、BibTeX 和 PDF 文件，并在本地或 Overleaf 中继续修改。',
    },
    form: {
      eyebrow: '开始使用',
      title: '提交研究方向并选择 Zotero 文献文件夹',
      ideaLabel: '研究主题 / Idea',
      ideaPlaceholder: '例如：基于多模态数据和 transformer 模型的长时标 AGN 爆发预测',
      fieldLabel: '研究领域',
      fieldPlaceholder: '例如：machine learning, astronomy computing',
      dataLabel: '数据介绍',
      dataPlaceholder: '例如：AGN 爆发相关项目数据，包括 LSST、LAMOST、Einstein Probe 等天文项目的 FITS 星表文件、光变曲线、光谱和图像文件。',
      dataHint: '说明数据类型、来源、用途、质量、时间范围、空间范围和主要限制。',
      literatureModeLabel: '引用文献来源',
      modeZotero: '从 Zotero collection 导入',
      modeExternal: '外部学术检索',
      literatureModeHint: 'Zotero 模式会优先读取指定文件夹；外部检索模式会直接检索 20 篇候选文献。',
      collectionLabel: 'Zotero 文献文件夹',
      collectionLoading: '正在读取 Zotero collection...',
      collectionEmpty: '没有读取到 Zotero collection',
      collectionHint: '系统优先使用该文件夹中的文献；不足 20 篇时自动补充外部学术索引结果。',
      journalLabel: '目标期刊 / 期刊类型',
      journalPlaceholder: '例如：Astronomy and Computing',
      formatLabel: '输出格式',
      emailLabel: '联系邮箱',
      emailPlaceholder: 'example@domain.com',
      zoteroLabel: '将补充检索到的文献同步回 Zotero',
      zoteroHint: 'Zotero 模式下若文献不足 20 篇，系统会自动补充外部检索结果；该同步能力后续会继续完善。',
      submitBtn: '提交研究 Idea',
      note: '请先启动本地后端，再提交表单。',
      validationError: '请完整填写研究主题、研究领域、Zotero collection 和联系邮箱。',
      loading: '正在生成英文研究初稿，请稍等...',
      collectionLoadFailed: '无法读取 Zotero collection，请确认本地后端已启动且 .env 配置正确。',
    },
    result: {
      draftTitle: '生成的研究初稿',
      title: '标题',
      abstract: '摘要',
      introduction: '引言',
      literature: '文献综述',
      methodology: '研究方法',
      results: '预期结果',
      conclusion: '讨论与结论',
      references: '参考文献',
      downloads: '下载文件',
      stats: '统计信息',
      storage: '完整内容已保存为独立文件；submissions.json 只保存元数据。',
      words: '词',
      generatedAt: '生成时间',
      download: '下载',
      supplements: '补充文献数量',
      sourceCount: '参考文献数量',
      mode: '文献模式',
    },
    footer: 'ResearchDraft.ai 当前是本地 MVP：前端负责提交，后端负责读取 Zotero、自动补充文献、生成草稿和保存文件。',
  },
  en: {
    nav: { value: 'Value', process: 'Workflow', start: 'Get Started' },
    hero: {
      eyebrow: 'Zotero-driven research writing automation',
      title: 'Generate English research drafts and LaTeX files from a selected Zotero collection',
      description: 'Organize references by project in Zotero. The system reads only the selected collection. If it contains fewer than 20 references, the backend automatically supplements external scholarly-index records and generates English research text, Markdown, LaTeX, BibTeX, and PDF review files.',
      startBtn: 'Get Started',
      processBtn: 'Workflow',
      useCases: 'Use Cases',
      useCase1: 'Manage references for different papers through Zotero collections',
      useCase2: 'Automatically supplement up to 20 candidate references when needed',
      useCase3: 'Generate English outlines, LaTeX, BibTeX, and PDF review drafts',
    },
    features: {
      eyebrow: 'Value',
      title: 'Controlled references for a realistic research workflow',
      description: 'The current version uses a Zotero-first workflow: users select one collection, the backend reads only that folder, and external scholarly-index supplementation is triggered only when fewer than 20 references are available.',
      collection: 'Collection-scoped references',
      collectionDesc: 'Select one Zotero collection for each paper. The backend does not fall back to the full library.',
      supplement: 'Automatic supplements',
      supplementDesc: 'When the selected collection has fewer than 20 papers, the backend searches relevant English scholarly records to complete the candidate reference set.',
      bibtex: 'BibTeX and PDF output',
      bibtexDesc: 'Export BibTeX from literature metadata alongside LaTeX and PDF review files for Overleaf editing.',
    },
    process: {
      eyebrow: 'Workflow',
      title: '4 steps to a Zotero-backed research draft',
      step1: 'Organize Zotero',
      step1Desc: 'Put the papers for this manuscript into a clearly named Zotero collection.',
      step2: 'Select collection',
      step2Desc: 'The page loads Zotero collections from the backend and lets you select the literature folder.',
      step3: 'Generate draft',
      step3Desc: 'AI builds the background, review, data, methods, and expected results from the selected collection plus automatic supplements.',
      step4: 'Download files',
      step4Desc: 'Download Markdown, LaTeX, BibTeX, and PDF files for local or Overleaf editing.',
    },
    form: {
      eyebrow: 'Get Started',
      title: 'Submit a research direction and select a Zotero collection',
      ideaLabel: 'Research Topic / Idea',
      ideaPlaceholder: 'e.g., Long-timescale AGN outburst prediction using multimodal data and transformer models',
      fieldLabel: 'Research Field',
      fieldPlaceholder: 'e.g., machine learning, astronomy computing',
      dataLabel: 'Data Description',
      dataPlaceholder: 'e.g., AGN outburst datasets from LSST, LAMOST, Einstein Probe, FITS catalogs, light curves, spectra, and image files.',
      dataHint: 'Describe data type, source, purpose, quality, time span, spatial coverage, and main limitations.',
      literatureModeLabel: 'Reference Source',
      modeZotero: 'Import from Zotero collection',
      modeExternal: 'External scholarly search',
      literatureModeHint: 'Zotero mode reads the selected collection first; external mode directly searches 20 candidate references.',
      collectionLabel: 'Zotero Collection',
      collectionLoading: 'Loading Zotero collections...',
      collectionEmpty: 'No Zotero collections found',
      collectionHint: 'The backend uses this collection first and automatically supplements external records when fewer than 20 papers are available.',
      journalLabel: 'Target Journal / Journal Type',
      journalPlaceholder: 'e.g., Astronomy and Computing',
      formatLabel: 'Output Format',
      emailLabel: 'Contact Email',
      emailPlaceholder: 'example@domain.com',
      zoteroLabel: 'Sync supplemental references back to Zotero',
      zoteroHint: 'In Zotero mode, the backend supplements external references when fewer than 20 papers are available; Zotero sync will be improved later.',
      submitBtn: 'Submit Research Idea',
      note: 'Start the local backend before submitting the form.',
      validationError: 'Please complete the topic, field, Zotero collection, and email.',
      loading: 'Generating the English research draft...',
      collectionLoadFailed: 'Could not load Zotero collections. Check that the local backend is running and .env is configured.',
    },
    result: {
      draftTitle: 'Generated Research Draft',
      title: 'Title',
      abstract: 'Abstract',
      introduction: 'Introduction',
      literature: 'Literature Review',
      methodology: 'Methodology',
      results: 'Results',
      conclusion: 'Discussion and Conclusion',
      references: 'References',
      downloads: 'Downloads',
      stats: 'Stats',
      storage: 'Full content is saved as separate files; submissions.json stores metadata only.',
      words: 'words',
      generatedAt: 'Generated at',
      download: 'Download',
      supplements: 'Supplemental references',
      sourceCount: 'Reference count',
      mode: 'Literature mode',
    },
    footer: 'ResearchDraft.ai is currently a local MVP: the frontend submits requests, and the backend reads Zotero, supplements references, generates drafts, and saves files.',
  },
};

let currentLang = localStorage.getItem('language') || 'zh';
const form = document.getElementById('idea-form');
const resultBox = document.getElementById('form-result');
const collectionSelect = document.getElementById('collection');
const literatureModeSelect = document.getElementById('literature-mode');
const zoteroSyncLabel = document.querySelector('label[for="add-to-zotero"]');

function t(path) {
  return path.split('.').reduce((value, key) => value?.[key], translations[currentLang]) || path;
}

function escapeHtml(value) {
  return String(value || '')
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#039;');
}

function applyTranslations() {
  document.documentElement.lang = currentLang === 'zh' ? 'zh-CN' : 'en';
  document.querySelectorAll('[data-i18n]').forEach((element) => {
    element.textContent = t(element.dataset.i18n);
  });
  document.getElementById('idea').placeholder = t('form.ideaPlaceholder');
  document.getElementById('field').placeholder = t('form.fieldPlaceholder');
  document.getElementById('data-description').placeholder = t('form.dataPlaceholder');
  document.getElementById('journal').placeholder = t('form.journalPlaceholder');
  document.getElementById('email').placeholder = t('form.emailPlaceholder');
  document.getElementById('lang-zh').classList.toggle('active', currentLang === 'zh');
  document.getElementById('lang-en').classList.toggle('active', currentLang === 'en');
}

async function loadCollections() {
  collectionSelect.innerHTML = `<option value="">${t('form.collectionLoading')}</option>`;
  try {
    const response = await fetch(`${API_BASE}/api/zotero/collections`);
    if (!response.ok) {
      throw new Error('Collection API failed');
    }
    const data = await response.json();
    const collections = data.collections || [];
    if (!collections.length) {
      collectionSelect.innerHTML = `<option value="">${t('form.collectionEmpty')}</option>`;
      return;
    }
    collectionSelect.innerHTML = `<option value="">${t('form.collectionLabel')}</option>`;
    collections.forEach((collection) => {
      const option = document.createElement('option');
      option.value = collection.name;
      option.textContent = collection.name;
      option.dataset.key = collection.key;
      collectionSelect.appendChild(option);
    });
  } catch (error) {
    collectionSelect.innerHTML = `<option value="">${t('form.collectionLoadFailed')}</option>`;
  }
}

function updateLiteratureModeUI() {
  const useZotero = literatureModeSelect.value === 'zotero';
  const collectionLabel = document.querySelector('label[for="collection"]');
  collectionLabel.style.display = useZotero ? 'grid' : 'none';
  collectionSelect.required = useZotero;
  zoteroSyncLabel.style.display = useZotero ? 'flex' : 'none';
  if (!useZotero) {
    document.getElementById('add-to-zotero').checked = false;
  }
}

function showResult(message, isError = false) {
  resultBox.textContent = message;
  resultBox.classList.remove('hidden');
  resultBox.style.borderColor = isError ? 'rgba(221, 60, 60, 0.2)' : 'rgba(26, 108, 255, 0.18)';
  resultBox.style.backgroundColor = isError ? 'rgba(255, 235, 238, 0.9)' : 'rgba(26, 108, 255, 0.08)';
  resultBox.style.color = isError ? '#7f1d1d' : '#0d1f45';
}

function sectionHtml(title, content) {
  if (!content) return '';
  return `
    <div style="margin-bottom: 20px;">
      <h4 style="margin: 0 0 10px 0; color: #0d1f45; font-size: 16px;">${escapeHtml(title)}</h4>
      <p style="margin: 0; line-height: 1.6; color: #24303e;">${escapeHtml(content)}</p>
    </div>`;
}

function fullOutlineHtml(rawContent) {
  if (!rawContent || rawContent.trim().length < 200) return '';
  return `
    <div style="margin-bottom: 20px;">
      <h4 style="margin: 0 0 10px 0; color: #0d1f45; font-size: 16px;">Full Publishable Outline</h4>
      <pre style="white-space: pre-wrap; margin: 0; line-height: 1.55; color: #24303e; font-family: inherit; background: #fbfdff; border: 1px solid rgba(26, 108, 255, 0.16); border-radius: 8px; padding: 14px; max-height: 520px; overflow: auto;">${escapeHtml(rawContent)}</pre>
    </div>`;
}

function showDraftDetails(draft) {
  document.querySelectorAll('.draft-details').forEach((node) => node.remove());
  const detailsDiv = document.createElement('div');
  detailsDiv.className = 'draft-details';
  detailsDiv.style.cssText = `
    margin-top: 20px;
    padding: 20px;
    background: rgba(26, 108, 255, 0.05);
    border: 1px solid rgba(26, 108, 255, 0.2);
    border-radius: 12px;
    max-height: 700px;
    overflow-y: auto;
  `;

  const references = (draft.references || [])
    .map((ref) => `<li style="margin-bottom: 5px;">${escapeHtml(ref)}</li>`)
    .join('');
  const pdfStatus = draft.files && draft.files.pdf_status
    ? `<p style="margin: 10px 0 0 0; color: #666; font-size: 13px;">PDF: ${escapeHtml(draft.files.pdf_status)}</p>`
    : '';
  const quality = draft.quality || {};
  const qualityHtml = quality.status
    ? `<p style="margin: 10px 0 0 0; color: ${quality.status === 'passed' ? '#1f7a45' : '#b42318'}; font-size: 13px;">
        Quality gate: ${escapeHtml(quality.status)} (${quality.error_count || 0} errors, ${quality.warning_count || 0} warnings)
      </p>`
    : '';
  const downloads = draft.files
    ? Object.entries(draft.files)
      .filter(([format]) => format !== 'pdf_status')
      .map(([format, filename]) => {
        const label = format === 'markdown' ? 'Markdown (.md)' :
          format === 'latex' ? 'LaTeX (.tex)' :
          format === 'bibtex' ? 'BibTeX (.bib)' :
          format === 'pdf' ? 'PDF (.pdf)' :
          format === 'text' ? 'Text (.txt)' :
          format === 'demo_data' ? 'demo_data.py' :
          format === 'demo_method' ? 'demo_method.py' :
          format === 'quality_report' ? 'Quality report (.json)' : format;
        return `<button type="button" class="btn btn-primary" style="padding: 8px 12px;" onclick="downloadFile('${escapeHtml(filename)}')">${t('result.download')} ${label}</button>`;
      }).join('')
    : '';
  const literatureSummaries = (draft.literature_summary_files || [])
    .map((filename, index) => `<button type="button" class="btn btn-secondary" style="padding: 8px 12px;" onclick="downloadLiteratureSummary('${escapeHtml(filename)}')">Paper ${index + 1} HTML</button>`)
    .join('');

  detailsDiv.innerHTML = `
    <h3 style="margin: 0 0 15px 0; color: #0d1f45; font-size: 18px;">${t('result.draftTitle')}</h3>
    ${fullOutlineHtml(draft.raw_content)}
    ${sectionHtml(t('result.title'), draft.title)}
    ${sectionHtml(t('result.abstract'), draft.abstract)}
    ${sectionHtml(t('result.introduction'), draft.introduction)}
    ${sectionHtml(t('result.literature'), draft.literature_review)}
    ${sectionHtml(t('result.methodology'), draft.methodology)}
    ${sectionHtml(t('result.results'), draft.expected_results)}
    ${sectionHtml(t('result.conclusion'), draft.conclusion)}
    <div style="margin-bottom: 20px;">
      <h4 style="margin: 0 0 10px 0; color: #0d1f45; font-size: 16px;">${t('result.references')}</h4>
      <ol style="margin: 0; padding-left: 20px; color: #24303e;">${references}</ol>
    </div>
    <div style="margin-bottom: 20px;">
      <h4 style="margin: 0 0 10px 0; color: #0d1f45; font-size: 16px;">${t('result.downloads')}</h4>
      <div style="display: flex; gap: 10px; flex-wrap: wrap;">${downloads}</div>
      ${pdfStatus}
      ${qualityHtml}
    </div>
    ${literatureSummaries ? `
    <div style="margin-bottom: 20px;">
      <h4 style="margin: 0 0 10px 0; color: #0d1f45; font-size: 16px;">Literature HTML Summaries</h4>
      <div style="display: flex; gap: 10px; flex-wrap: wrap;">${literatureSummaries}</div>
    </div>` : ''}
    <p style="margin: 0 0 8px 0; color: #666; font-size: 14px;">
      <strong>${t('result.stats')}:</strong> ${draft.word_count} ${t('result.words')} |
      ${t('result.mode')}: ${escapeHtml(draft.literature_mode || '')} |
      ${t('result.sourceCount')}: ${draft.source_count || 0} |
      ${t('result.supplements')}: ${draft.supplemental_source_count || 0} |
      ${t('result.generatedAt')}: ${new Date(draft.generated_at).toLocaleString()}
    </p>
    <p style="margin: 0; color: #666; font-size: 14px;">${t('result.storage')}</p>
  `;
  resultBox.insertAdjacentElement('afterend', detailsDiv);
}

async function submitForm(event) {
  event.preventDefault();
  const payload = {
    idea: document.getElementById('idea').value.trim(),
    field: document.getElementById('field').value.trim(),
    data_description: document.getElementById('data-description').value.trim(),
    journal: document.getElementById('journal').value.trim() || null,
    literature_mode: literatureModeSelect.value,
    collection: literatureModeSelect.value === 'zotero' ? collectionSelect.value : null,
    output_format: document.getElementById('output-format').value,
    add_to_zotero: literatureModeSelect.value === 'zotero' && document.getElementById('add-to-zotero').checked,
    email: document.getElementById('email').value.trim(),
  };

  if (!payload.idea || !payload.field || !payload.email || (payload.literature_mode === 'zotero' && !payload.collection)) {
    showResult(t('form.validationError'), true);
    return;
  }

  showResult(t('form.loading'), false);
  try {
    const response = await fetch(`${API_BASE}/api/submit-idea`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    const data = await response.json();
    if (!response.ok || data.status === 'error') {
      throw new Error(data.message || 'Draft generation failed');
    }
    showResult(data.message, false);
    if (data.draft) {
      showDraftDetails(data.draft);
    }
  } catch (error) {
    const message = error instanceof TypeError && String(error.message).includes('fetch')
      ? 'Failed to connect to the backend. Please restart the Flask backend at http://127.0.0.1:9000 and submit again.'
      : error.message;
    showResult(message, true);
  }
}

function downloadFile(filename) {
  const link = document.createElement('a');
  link.href = `${API_BASE}/api/download/${encodeURIComponent(filename)}`;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
}

window.downloadFile = downloadFile;

function downloadLiteratureSummary(filename) {
  const link = document.createElement('a');
  link.href = `${API_BASE}/api/download-literature/${encodeURIComponent(filename)}`;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
}

window.downloadLiteratureSummary = downloadLiteratureSummary;

document.getElementById('lang-zh').addEventListener('click', () => {
  currentLang = 'zh';
  localStorage.setItem('language', currentLang);
  applyTranslations();
  loadCollections();
});

document.getElementById('lang-en').addEventListener('click', () => {
  currentLang = 'en';
  localStorage.setItem('language', currentLang);
  applyTranslations();
  loadCollections();
});

form.addEventListener('submit', submitForm);
literatureModeSelect.addEventListener('change', updateLiteratureModeUI);

document.addEventListener('DOMContentLoaded', () => {
  applyTranslations();
  updateLiteratureModeUI();
  loadCollections();
});
