const form = document.getElementById('idea-form');
const resultBox = document.getElementById('form-result');

form.addEventListener('submit', (event) => {
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

  const summary = `已收到您的研究Idea。我们将根据“${field}”领域和目标期刊“${journal || '未指定'}”准备规范研究文案，并通过邮箱 ${email} 与您联系。`;
  showResult(summary, false);
  form.reset();
});

function showResult(message, isError) {
  resultBox.textContent = message;
  resultBox.classList.remove('hidden');
  resultBox.style.borderColor = isError ? 'rgba(221, 60, 60, 0.2)' : 'rgba(26, 108, 255, 0.18)';
  resultBox.style.backgroundColor = isError ? 'rgba(255, 235, 238, 0.9)' : 'rgba(26, 108, 255, 0.08)';
  resultBox.style.color = isError ? '#7f1d1d' : '#0d1f45';
}
