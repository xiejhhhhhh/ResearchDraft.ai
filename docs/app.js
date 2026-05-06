const form = document.getElementById('idea-form');
const resultBox = document.getElementById('form-result');
const apiEndpoint = 'http://localhost:9000/api/submit-idea';

form.addEventListener('submit', async (event) => {
  event.preventDefault();
  const idea = document.getElementById('idea').value.trim();
  const field = document.getElementById('field').value.trim();
  const journal = document.getElementById('journal').value.trim();
  const email = document.getElementById('email').value.trim();
  const outputFormat = document.getElementById('output-format').value;

  if (!idea || !field || !email) {
    showResult('请完整填写研究主题、研究领域和联系邮箱。', true);
    return;
  }

  const payload = {
    idea,
    field,
    journal: journal || null,
    output_format: outputFormat,
    email,
  };

  try {
    const response = await fetch(apiEndpoint, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
    });

    if (response.ok) {
      const data = await response.json();
      showResult(data.message || '研究文案请求已提交，后续将通过邮箱联系您。', false);
      form.reset();
      return;
    }

    throw new Error('API 返回错误');
  } catch (error) {
    const summary = `已收到您的研究Idea。我们将根据“${field}”领域和目标期刊“${journal || '未指定'}”准备规范研究文案，并通过邮箱 ${email} 与您联系。`;
    showResult(`${summary} 当前本地后端未连接，页面已切换到离线反馈模式。`, false);
    form.reset();
  }
});

function showResult(message, isError) {
  resultBox.textContent = message;
  resultBox.classList.remove('hidden');
  resultBox.style.borderColor = isError ? 'rgba(221, 60, 60, 0.2)' : 'rgba(26, 108, 255, 0.18)';
  resultBox.style.backgroundColor = isError ? 'rgba(255, 235, 238, 0.9)' : 'rgba(26, 108, 255, 0.08)';
  resultBox.style.color = isError ? '#7f1d1d' : '#0d1f45';
}
