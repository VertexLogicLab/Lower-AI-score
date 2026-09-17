import os
import re
import json
import requests
from flask import Flask, request, jsonify, render_template_string

app = Flask(__name__)

# ----------------- 核心安全与管理配置 -----------------
# 1. 你的专属管理员后台密码（你可以随时在此修改，防止外人进入后台）
ADMIN_PASSWORD = "admin_secure_888"

# 2. 初始卡密库：卡号: 剩余额度字符数
KEYS_DB = {
    "SP-TEST888": 5000,
    "SP-VIP10000": 10000,
    "SP-VIP20000": 20000,
}

# ----------------- 1. 买家纯净商业前端 (HTML+CSS) -----------------
USER_HTML = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>知网、维普强降AI率系统</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body { background-color: #f8fafc; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif; color: #1e293b; }
        .main-card { background: #ffffff; border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.05); border: 1px solid #e2e8f0; }
        .header-title { font-weight: 700; color: #0f172a; }
        .btn-primary { background-color: #2563eb; border-color: #2563eb; font-weight: 600; padding: 10px 20px; }
        .btn-primary:hover { background-color: #1d4ed8; }
        .sidebar-box { background: #f1f5f9; border-radius: 8px; padding: 16px; margin-bottom: 20px; }
        .char-count { font-size: 13px; color: #64748b; margin-top: 5px; }
        .char-alert { color: #dc2626; font-weight: 600; }
    </style>
</head>
<body class="py-4">
<div class="container" style="max-width: 1100px;">
    <div class="text-center mb-4">
        <h2 class="header-title">🎓 知网、维普强降AI率系统</h2>
        <p class="text-muted" style="font-size: 14px;">对标主流学术查重检测机制 · 深度解构AIGC句式特征 · 专家级语义重构</p>
    </div>

    <div class="row">
        <div class="col-md-3 mb-3">
            <div class="sidebar-box">
                <h6 class="fw-bold mb-3">🔑 授权与凭证</h6>
                <div class="mb-3">
                    <input type="password" id="licenseKey" class="form-control" placeholder="输入卡密授权码">
                </div>
                <button class="btn btn-outline-secondary btn-sm w-100 mb-2" onclick="checkKey()">查询卡密额度</button>
                <div id="keyStatus" class="small mt-2"></div>
            </div>

            <div class="sidebar-box">
                <h6 class="fw-bold mb-2">📌 使用规范</h6>
                <ul class="text-muted small ps-3 mb-0" style="line-height: 1.8;">
                    <li><strong>单次限额</strong>：单次严格限制 <strong>1000 字符</strong> 以内。</li>
                    <li><strong>分段提交</strong>：建议按 1~2 个自然段精修，降 AI 效果最佳。</li>
                    <li><strong>专家引擎</strong>：单次深度推理耗时约 15~25 秒，请耐心等待。</li>
                    <li>如需购买或补充额度，请联系店铺客服。</li>
                </ul>
            </div>
        </div>

        <div class="col-md-9">
            <div class="main-card p-4">
                <div class="row mb-3">
                    <div class="col-md-6 mb-3">
                        <label class="form-label fw-bold">待优化学术段落：</label>
                        <textarea id="sourceText" class="form-control" rows="12" placeholder="在此粘贴需要彻底消除AI痕迹的学术段落（建议每次提交500~800字，效果最强）..." oninput="updateCharCount()"></textarea>
                        <div id="charCountTip" class="char-count">当前文本长度：0 / 1000 字符</div>
                    </div>
                    <div class="col-md-6 mb-3">
                        <label class="form-label fw-bold">优化重塑正文：</label>
                        <textarea id="resultText" class="form-control" rows="12" readonly placeholder="降AI重塑后的学术正文将在此显示..."></textarea>
                    </div>
                </div>

                <div class="row align-items-center">
                    <div class="col-md-7 mb-2">
                        <select id="targetEngine" class="form-select">
                            <option value="知网">🎯 强效降知网AI率</option>
                            <option value="维普">🎯 强效降维普AI率</option>
                        </select>
                    </div>
                    <div class="col-md-5 mb-2">
                        <button id="submitBtn" class="btn btn-primary w-100" onclick="startPolish()">🚀 启动专家级去AI重塑</button>
                    </div>
                </div>
                <div id="msgBox" class="mt-3"></div>
            </div>
        </div>
    </div>
</div>

<script>
function updateCharCount() {
    let text = document.getElementById('sourceText').value.trim();
    let len = text.length;
    let tip = document.getElementById('charCountTip');
    if (len > 1000) {
        tip.innerHTML = `<span class="char-alert">⚠️ 当前已达 ${len} 字符（超出单次 1000 字上限）！请分段提交。</span>`;
    } else {
        tip.innerHTML = `当前文本长度：${len} / 1000 字符`;
    }
}

async function checkKey() {
    let key = document.getElementById('licenseKey').value.trim();
    let statusDiv = document.getElementById('keyStatus');
    if(!key) { statusDiv.innerHTML = '<span class="text-danger">请输入卡密！</span>'; return; }
    
    statusDiv.innerHTML = '<span class="text-muted">查询中...</span>';
    let res = await fetch('/api/check_key', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({key: key})
    });
    let data = await res.json();
    if(data.valid) {
        statusDiv.innerHTML = `<span class="text-success">✅ 授权有效！剩余：${data.remain} 字符</span>`;
    } else {
        statusDiv.innerHTML = `<span class="text-danger">❌ 授权码无效或已用尽</span>`;
    }
}

async function startPolish() {
    let key = document.getElementById('licenseKey').value.trim();
    let text = document.getElementById('sourceText').value.trim();
    let engine = document.getElementById('targetEngine').value;
    let btn = document.getElementById('submitBtn');
    let msgBox = document.getElementById('msgBox');
    let resultText = document.getElementById('resultText');

    if(!key) { alert("请先在左侧输入卡密授权码！"); return; }
    if(!text) { alert("请输入需要优化的学术内容！"); return; }
    if(text.length > 1000) { alert("单次提交不能超过 1000 字符，请分段提交！"); return; }

    btn.disabled = true;
    btn.innerText = "⏳ 专家引擎深度思考重塑中(约15-25秒)...";
    msgBox.innerHTML = '<div class="alert alert-info py-2">系统正在解构句式、粉碎AIGC检测特征，请稍候...</div>';

    try {
        let res = await fetch('/api/polish', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({key: key, text: text, engine: engine})
        });
        let data = await res.json();
        if(data.success) {
            resultText.value = data.result;
            msgBox.innerHTML = `<div class="alert alert-success py-2">重塑成功！本次核销：${data.cost} 字符，剩余：${data.remain} 字符。</div>`;
            checkKey();
        } else {
            msgBox.innerHTML = `<div class="alert alert-danger py-2">处理失败：${data.error}</div>`;
        }
    } catch(e) {
        msgBox.innerHTML = `<div class="alert alert-danger py-2">网络请求超时或服务异常，请重试</div>`;
    } finally {
        btn.disabled = false;
        btn.innerText = "🚀 启动专家级去AI重塑";
    }
}
</script>
</body>
</html>
"""

# ----------------- 2. 专属管理员后台 (HTML+CSS) -----------------
ADMIN_HTML = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>系统后台卡密管理中心</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body class="bg-light py-4">
<div class="container" style="max-width: 800px;">
    <div class="card p-4 shadow-sm border-0 mb-4">
        <h4 class="fw-bold mb-3">🛠️ 系统后台卡密管理中心</h4>
        <div class="row g-2 mb-3">
            <div class="col-md-6">
                <input type="password" id="adminPwd" class="form-control" placeholder="输入管理员访问密码">
            </div>
            <div class="col-md-6">
                <button class="btn btn-dark w-100" onclick="loadKeys()">登录并刷新卡密列表</button>
            </div>
        </div>
    </div>

    <div class="card p-4 shadow-sm border-0 mb-4">
        <h5 class="fw-bold mb-3">➕ 快速添加/修改卡密</h5>
        <div class="row g-2">
            <div class="col-md-5">
                <input type="text" id="newKey" class="form-control" placeholder="卡密字符串(如 VIP-9988)">
            </div>
            <div class="col-md-4">
                <input type="number" id="newAmount" class="form-control" placeholder="额度字数(如 10000)">
            </div>
            <div class="col-md-3">
                <button class="btn btn-success w-100" onclick="addKey()">立即生效</button>
            </div>
        </div>
        <div id="adminMsg" class="mt-2 small"></div>
    </div>

    <div class="card p-4 shadow-sm border-0">
        <h5 class="fw-bold mb-3">📋 当前系统卡密与额度概况</h5>
        <div class="table-responsive">
            <table class="table table-bordered table-striped" id="keyTable">
                <thead class="table-dark">
                    <tr>
                        <th>卡密授权码</th>
                        <th>剩余可用字符额度</th>
                        <th>状态</th>
                    </tr>
                </thead>
                <tbody id="tableBody">
                    <tr><td colspan="3" class="text-center text-muted">请输入管理员密码后点击上方“登录并刷新”</td></tr>
                </tbody>
            </table>
        </div>
    </div>
</div>

<script>
async function loadKeys() {
    let pwd = document.getElementById('adminPwd').value.trim();
    let res = await fetch('/api/admin/list_keys', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({admin_pwd: pwd})
    });
    let data = await res.json();
    if(data.success) {
        let rows = '';
        for (let [k, v] of Object.entries(data.keys)) {
            let status = v > 0 ? '<span class="badge bg-success">正常可用</span>' : '<span class="badge bg-danger">已耗尽</span>';
            rows += `<tr><td><strong>${k}</strong></td><td>${v} 字符</td><td>${status}</td></tr>`;
        }
        document.getElementById('tableBody').innerHTML = rows;
    } else {
        alert(data.error);
    }
}

async function addKey() {
    let pwd = document.getElementById('adminPwd').value.trim();
    let key = document.getElementById('newKey').value.trim();
    let amount = parseInt(document.getElementById('newAmount').value);
    if(!key || isNaN(amount)) { alert("请填写完整的卡密和有效字数！"); return; }

    let res = await fetch('/api/admin/add_key', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({admin_pwd: pwd, key: key, amount: amount})
    });
    let data = await res.json();
    if(data.success) {
        document.getElementById('adminMsg').innerHTML = `<span class="text-success">✅ 卡密 [${key}] 已成功注入，额度 ${amount} 字符！</span>`;
        loadKeys();
    } else {
        alert(data.error);
    }
}
</script>
</body>
</html>
"""

# ----------------- 3. 路由与业务逻辑 -----------------
@app.route('/')
def user_page():
    return render_template_string(USER_HTML)

@app.route('/admin')
def admin_page():
    return render_template_string(ADMIN_HTML)

@app.route('/api/check_key', methods=['POST'])
def check_key():
    data = request.json or {}
    key = data.get('key', '').strip()
    if key in KEYS_DB and KEYS_DB[key] > 0:
        return jsonify({"valid": True, "remain": KEYS_DB[key]})
    return jsonify({"valid": False, "remain": 0})

@app.route('/api/admin/list_keys', methods=['POST'])
def admin_list_keys():
    data = request.json or {}
    if data.get('admin_pwd') != ADMIN_PASSWORD:
        return jsonify({"success": False, "error": "管理员密码错误！"})
    return jsonify({"success": True, "keys": KEYS_DB})

@app.route('/api/admin/add_key', methods=['POST'])
def admin_add_key():
    data = request.json or {}
    if data.get('admin_pwd') != ADMIN_PASSWORD:
        return jsonify({"success": False, "error": "管理员密码错误！"})
    key = data.get('key', '').strip()
    amount = data.get('amount', 0)
    KEYS_DB[key] = amount
    return jsonify({"success": True})

@app.route('/api/polish', methods=['POST'])
def polish():
    data = request.json or {}
    key = data.get('key', '').strip()
    text = data.get('text', '').strip()
    engine = data.get('engine', '知网')
    
    char_count = len(text)
    if key not in KEYS_DB:
        return jsonify({"success": False, "error": "授权码无效！"})
    if KEYS_DB[key] < char_count:
        return jsonify({"success": False, "error": f"卡密额度不足，当前仅剩 {KEYS_DB[key]} 字。"})
    if char_count > 1000:
        return jsonify({"success": False, "error": "单次提交严禁超过 1000 字符。"})

    api_key = os.environ.get("API_KEY", "")
    if not api_key:
        return jsonify({"success": False, "error": "服务端未配置 API_KEY，请联系管理员。"})

    if "知网" in engine:
        prompt = (
            "严格对标知网（CNKI）查AI率的底层检测机制（包括语言困惑度Perplexity、突发度Burstiness分析、高频语法共现矩阵与逻辑连接词密度）。"
            "请把下面的文字内容用尽所有办法，彻底去除内容中能被知网检测出的AI痕迹：\n"
            "1. 彻底粉碎原有句式结构，大幅提高长短句交替突发度，打破AI固有的平均句长和整齐韵律；\n"
            "2. 颠覆原有的因果与递进连接逻辑，改用符合人类严谨学术作者习惯的论述语序；\n"
            "3. 保持原文所有专业术语、学术核心观点与数据论据绝对不变；\n"
            "4. 直接输出重塑后的最终学术正文，严禁输出任何多余寒暄、说明或解释。\n\n"
            f"待重塑内容如下：\n{text}"
        )
    else:
        prompt = (
            "严格对标维普（VP）查AI率的底层检测机制（包括高频AI套话特征库比对、模板化段落总分总结构识别、特征连接词聚类）。"
            "请把下面的文字内容用尽所有办法，彻底去除内容中维普检测能探测出的AI痕迹：\n"
            "1. 彻底清除并替换所有维普特征词与机械套话（如杜绝'综上所述'、'不可否认'、'总而言之'、'深入探讨'、'双刃剑'、'具有重要意义'等）；\n"
            "2. 重构段落叙事逻辑，打乱固定总分段落形态，变换主被动语态与陈述视角；\n"
            "3. 保持原文全部核心学术论点、数据和专业名词绝对一致；\n"
            "4. 直接输出重塑后的最终学术正文，严禁输出任何多余寒暄、说明或解释。\n\n"
            f"待重塑内容如下：\n{text}"
        )

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "deepseek-ai/DeepSeek-R1",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.6
    }

    try:
        resp = requests.post("https://api.siliconflow.cn/v1/chat/completions", headers=headers, json=payload, timeout=120)
        if resp.status_code == 200:
            result_data = resp.json()
            raw_content = result_data["choices"][0]["message"]["content"]
            clean_text = re.sub(r'<think>.*?</think>', '', raw_content, flags=re.DOTALL).strip()
            
            KEYS_DB[key] -= char_count
            return jsonify({"success": True, "result": clean_text, "cost": char_count, "remain": KEYS_DB[key]})
        else:
            return jsonify({"success": False, "error": f"模型响应异常(状态码:{resp.status_code})"})
    except Exception as e:
        return jsonify({"success": False, "error": f"服务请求异常:{str(e)}"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
