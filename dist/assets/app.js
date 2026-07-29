const { createApp, ref, computed, nextTick } = Vue;
const API = window.__TIANSHU_API_BASE__ || window.location.origin;

function renderMarkdown(text) {
  if (!text) return '';
  let html = text
    .replace(/^### (.+)$/gm, '<h3>$1</h3>')
    .replace(/^## (.+)$/gm, '<h2>$1</h2>')
    .replace(/^# (.+)$/gm, '<h1>$1</h1>')
    .replace(/\*\*\*(.+?)\*\*\*/g, '<strong><em>$1</em></strong>')
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.+?)\*/g, '<em>$1</em>')
    .replace(/`([^`]+)`/g, '<code>$1</code>')
    .replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank">$1</a>')
    .replace(/^---$/gm, '<hr>')
    .replace(/^> (.+)$/gm, '<blockquote>$1</blockquote>')
    .replace(/^[\*\-] (.+)$/gm, '<li>$1</li>')
    .replace(/^\d+\. (.+)$/gm, '<li>$1</li>')
    .replace(/```(\w*)\n([\s\S]*?)```/g, '<pre><code>$2</code></pre>')
    .replace(/\n\n/g, '</p><p>')
    .replace(/\n/g, '<br>');
  html = html.replace(/((?:<li>.*?<\/li><br>?)+)/g, '<ul>$1</ul>');
  if (!html.startsWith('<h') && !html.startsWith('<pre') && !html.startsWith('<ul') && !html.startsWith('<blockquote') && !html.startsWith('<hr') && !html.startsWith('<table') && !html.startsWith('<p>')) {
    html = '<p>' + html + '</p>';
  }
  html = html.replace(/<\/(h[123]|pre|ul|blockquote|li)><br>/g, '</$1>');
  return html;
}

const App = {
  setup() {
    const textInput = ref('');
    const styleMode = ref('C');
    const textType = ref('full');
    const polishing = ref(false);
    const resultText = ref('');
    const resultTab = ref('polished');

    const textTypes = [
      { value: 'abstract', label: '摘要' },
      { value: 'introduction', label: '引言' },
      { value: 'literature', label: '文献综述' },
      { value: 'theory', label: '理论分析' },
      { value: 'hypothesis', label: '假设推导' },
      { value: 'design', label: '研究设计' },
      { value: 'results', label: '结果分析' },
      { value: 'mechanism', label: '机制检验' },
      { value: 'further', label: '进一步研究' },
      { value: 'discussion', label: '讨论' },
      { value: 'conclusion', label: '结论' },
      { value: 'policy', label: '政策启示' },
      { value: 'full', label: '完整论文' }
    ];

    const styleModes = [
      { value: 'A', label: '管理世界偏向', desc: '国家战略·制度互动·跨层次治理' },
      { value: 'B', label: '经济研究偏向', desc: '机制严谨·资源配置·表达克制' },
      { value: 'C', label: '融合型', desc: '问题高度+机制严谨（推荐）' }
    ];

    const charCount = computed(() => textInput.value.length);

    function getTypeLabel() {
      const t = textTypes.find(x => x.value === textType.value);
      return t ? t.label : '完整论文';
    }

    async function startPolish() {
      if (!textInput.value.trim() || polishing.value) return;
      polishing.value = true;
      resultText.value = '';
      try {
        const res = await fetch(`${API}/api/polish`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            text: textInput.value.trim(),
            style_mode: styleMode.value,
            text_type: textType.value
          })
        });
        if (!res.ok) throw new Error('请求失败');
        const reader = res.body.getReader();
        const decoder = new TextDecoder();
        let full = '';
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          const text = decoder.decode(value);
          const lines = text.split('\n');
          for (const line of lines) {
            if (line.startsWith('data: ')) {
              try {
                const data = JSON.parse(line.slice(6));
                if (data.type === 'content') {
                  full += data.data;
                  resultText.value = full;
                } else if (data.type === 'error') {
                  resultText.value = '润色出错：' + data.data;
                }
              } catch(e) {}
            }
          }
        }
        if (!full) resultText.value = '未收到润色结果，请重试。';
      } catch(e) {
        resultText.value = '网络连接失败，请检查服务器或API Key配置。';
      }
      polishing.value = false;
      scrollToResult();
    }

    function scrollToResult() {
      nextTick(() => {
        const el = document.querySelector('.result-section');
        if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' });
      });
    }

    function downloadResult() {
      const blob = new Blob([resultText.value], { type: 'text/plain;charset=utf-8' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = '天书润色_' + new Date().toISOString().slice(0, 10) + '.txt';
      a.click();
      URL.revokeObjectURL(url);
    }

    async function copyResult() {
      try {
        await navigator.clipboard.writeText(resultText.value);
        alert('已复制到剪贴板');
      } catch {
        alert('复制失败，请手动选择复制');
      }
    }

    function clearAll() {
      textInput.value = '';
      resultText.value = '';
    }

    return {
      textInput, styleMode, textType, polishing, resultText, resultTab,
      textTypes, styleModes, charCount,
      startPolish, scrollToResult, downloadResult, copyResult, clearAll,
      renderMarkdown, getTypeLabel
    };
  }
};

createApp(App).mount('#app');
