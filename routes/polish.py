"""
天书系统 - 语言润色 API
"""
from flask import Blueprint, request, jsonify, current_app, Response, stream_with_context
import json
import requests
from services.prompts import POLISH_SYSTEM_PROMPT, POLISH_USER_TEMPLATE

polish_bp = Blueprint('polish', __name__)

STYLE_MODES = {
    'A': '《管理世界》偏向——加强国家战略和重大现实问题、多目标协调、制度与主体互动、跨层次治理、中国实践理论化、政策与管理启示，但不得口号化',
    'B': '《经济研究》偏向——加强理论与事实冲突、主体选择、机制推导、资源配置、结构/均衡/福利、概念与结论的精确性，减少修辞和宏大表达',
    'C': '融合型——兼顾《管理世界》的问题高度与《经济研究》的机制严谨，克制、稳健、准确的学术表达，清晰、自然、层层递进的论证节奏'
}

TEXT_TYPES = {
    'abstract': '摘要',
    'introduction': '引言',
    'literature': '文献综述',
    'theory': '理论分析',
    'hypothesis': '假设推导',
    'design': '研究设计',
    'results': '结果分析',
    'mechanism': '机制检验',
    'further': '进一步研究',
    'case': '案例分析',
    'discussion': '讨论',
    'conclusion': '结论',
    'policy': '政策启示',
    'full': '完整论文'
}


def call_deepseek_stream(api_key, api_url, messages):
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {api_key}'
    }
    payload = {
        'model': 'deepseek-chat',
        'messages': messages,
        'stream': True,
        'temperature': 0.3,
        'max_tokens': 8000
    }

    try:
        resp = requests.post(
            f"{api_url}/v1/chat/completions",
            headers=headers,
            json=payload,
            stream=True,
            timeout=300
        )

        if resp.status_code != 200:
            yield 'error', f'API请求失败 (HTTP {resp.status_code})'
            return

        for line in resp.iter_lines():
            if not line:
                continue
            line = line.decode('utf-8')
            if line.startswith('data: '):
                data_str = line[6:]
                if data_str == '[DONE]':
                    break
                try:
                    data = json.loads(data_str)
                    delta = data.get('choices', [{}])[0].get('delta', {})
                    if 'content' in delta and delta['content']:
                        yield 'content', delta['content']
                except (json.JSONDecodeError, KeyError, IndexError):
                    continue
    except requests.exceptions.Timeout:
        yield 'error', 'AI响应超时，请稍后重试'
    except requests.exceptions.RequestException as e:
        yield 'error', f'网络连接失败: {str(e)}'


@polish_bp.route('/polish', methods=['POST'])
def polish_text():
    """语言润色（流式输出）"""
    try:
        data = request.get_json()
        text = data.get('text', '').strip()
        style_mode = data.get('style_mode', 'C').upper()
        text_type = data.get('text_type', 'full')

        if not text:
            return jsonify({'error': '文本内容不能为空'}), 400

        if len(text) > 15000:
            return jsonify({'error': '文本长度不能超过15000字符'}), 400

        if style_mode not in STYLE_MODES:
            style_mode = 'C'

        api_key = current_app.config.get('DEEPSEEK_API_KEY', '')
        api_url = current_app.config.get('DEEPSEEK_API_URL', 'https://api.deepseek.com')

        if not api_key:
            def no_key_gen():
                yield f"data: {json.dumps({'type': 'error', 'data': '请先配置 DeepSeek API Key'}, ensure_ascii=False)}\n\n"
            return Response(stream_with_context(no_key_gen()), mimetype='text/event-stream')

        style_desc = STYLE_MODES.get(style_mode, STYLE_MODES['C'])
        type_desc = TEXT_TYPES.get(text_type, '完整论文')

        user_message = POLISH_USER_TEMPLATE.format(
            style_mode=style_desc,
            text_type=type_desc,
            text=text
        )

        messages = [
            {'role': 'system', 'content': POLISH_SYSTEM_PROMPT},
            {'role': 'user', 'content': user_message}
        ]

        def generate():
            for chunk_type, chunk_content in call_deepseek_stream(api_key, api_url, messages):
                if chunk_type == 'content':
                    yield f"data: {json.dumps({'type': 'content', 'data': chunk_content}, ensure_ascii=False)}\n\n"
                elif chunk_type == 'error':
                    yield f"data: {json.dumps({'type': 'error', 'data': chunk_content}, ensure_ascii=False)}\n\n"
                    return

        return Response(
            stream_with_context(generate()),
            mimetype='text/event-stream',
            headers={'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no'}
        )

    except Exception as e:
        print(f"语言润色出错: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'服务器错误: {str(e)}'}), 500
