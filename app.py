import streamlit as st
import requests
import json
import os
import re
import hashlib

# 页面基础配置
st.set_page_config(
    page_title="知网、维普强降AI率系统",
    page_icon="🎓",
    layout="wide"
)

# ----------------- 1. 隐藏官方顶部菜单与页脚 -----------------
hide_top_menu = """
<style>
header[data-testid="stHeader"] { visibility: hidden !important; display: none !important; height: 0px !important; }
header { visibility: hidden !important; display: none !important; }
#MainMenu { visibility: hidden !important; }
footer { visibility: hidden !important; display: none !important; }
</style>
"""
st.markdown(hide_top_menu, unsafe_allow_html=True)

# ----------------- 2. 设备指纹生成与自动获取 -----------------
# 注入前端脚本：在买家浏览器本地生成永久唯一的设备特征码，并注入 URL 参数
device_js = """
<script>
(function() {
    let devId = localStorage.getItem('_scholar_device_id');
    if (!devId) {
        // 生成由硬件随机数与时间戳组成的唯一设备码
        devId = 'DEV-' + Math.random().toString(36).substring(2, 10).toUpperCase() + '-' + Date.now().toString(36).toUpperCase();
        localStorage.setItem('_scholar_device_id', devId);
    }
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.get('dev_id') !== devId) {
        urlParams.set('dev_id', devId);
        window.location.search = urlParams.toString();
    }
})();
</script>
"""
st.components.v1.html(device_js, height=0)

# 从当前请求中读取买家的设备指纹
current_device = st.query_params.get("dev_id", "")

# ----------------- 3. 卡密与设备锁数据库持久化 -----------------
DB_FILE = "keys_database.json"

# 默认初始卡密：卡号: {剩余额度, 绑定设备ID}
INITIAL_KEYS = {
    "SP-TEST888": {"remain": 5000, "device": None},
    "SP-VIP10000": {"remain": 10000, "device": None},
    "SP-VIP20000": {"remain": 20000, "device": None},
}

def load_keys():
    if not os.path.exists(DB_FILE):
        with open(DB_FILE, "w", encoding="utf-8") as f:
            json.dump(INITIAL_KEYS, f, ensure_ascii=False, indent=2)
        return INITIAL_KEYS
    try:
        with open(DB_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return INITIAL_KEYS

def save_keys(keys_data):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(keys_data, f, ensure_ascii=False, indent=2)

keys_db = load_keys()

# ----------------- 4. 界面与侧边栏 -----------------
st.title("🎓 知网、维普强降AI率系统")

with st.sidebar:
    st.header("🔑 授权与凭证")
    license_key = st.text_input("请输入您的卡密授权码", type="password", placeholder="例如: SP-XXXXXX")
    
    if st.button("查询卡密状态"):
        if not license_key:
            st.warning("请先输入授权码！")
        elif license_key in keys_db:
            card_info = keys_db[license_key]
            bound_dev = card_info.get("device")
            remain_chars = card_info.get("remain", 0)
            
            if bound_dev is None:
                st.info(f"🟢 授权有效（未绑定设备）\n剩余额度：{remain_chars} 字符\n首次使用将自动绑定当前设备。")
            elif bound_dev == current_device:
                st.success(f"✅ 当前设备已认证！\n剩余额度：{remain_chars} 字符")
            else:
                st.error("❌ 设备受限：该卡密已在其他电脑上激活绑定，无法跨设备使用！")
        else:
            st.error("授权码不存在或已失效！")
            
    st.markdown("---")
    st.markdown("**📌 核心使用规范：**")
    st.markdown("1. **一机一码锁定**：卡密首次使用将自动绑定当前电脑，**严禁换设备或外借他人**。")
    st.markdown("2. **单次限额 1000 字**：按 1~2 个自然段精修，降重与去 AI 效果最佳。")
    st.markdown("3. **专家推理引擎**：单次处理耗时约 15~30 秒，请耐心等待。")
    st.markdown("4. 如需购买或扩充额度，请联系店铺客服。")

# ----------------- 5. 主操作区 -----------------
col1, col2 = st.columns([1, 1])
MAX_SINGLE_LEN = 1000

with col1:
    st.subheader("待优化学术段落")
    source_text = st.text_area(
        "粘贴待降重/去AI痕迹的段落：", 
        height=360,
        placeholder="在此粘贴需要彻底消除AI痕迹的学术段落（建议每次提交500~800字，效果最强）..."
    )
    
    char_count = len(source_text.strip())
    
    if char_count > MAX_SINGLE_LEN:
        st.error(f"⚠️ 当前文本已达 {char_count} 字符（超出单次上限 {MAX_SINGLE_LEN} 字）！为保证深层去AI效果，请分段提交。")
    else:
        st.info(f"当前文本长度：{char_count} / {MAX_SINGLE_LEN} 字符")
    
    target_engine = st.selectbox(
        "🎯 选择优化模式：",
        [
            "强效降知网AI率",
            "强效降维普AI率"
        ]
    )
    
    start_btn = st.button("🚀 启动专家级去AI重塑", type="primary", use_container_width=True)

# ----------------- 6. 核心处理与一机一码核销 -----------------
with col2:
    st.subheader("优化重塑正文")
    output_box = st.empty()

    if start_btn:
        card = keys_db.get(license_key)
        
        # 严格的多重拦截防白嫖
        if not license_key:
            st.error("请先在左侧输入卡密授权码！")
        elif not card:
            st.error("卡密授权码无效，请检查是否输入正确！")
        elif card.get("device") is not None and card.get("device") != current_device:
            # 触发一机一码拦截！
            st.error("🚫 拦截：该卡密已被首台设备绑定！为保障版权，系统严禁借给他人或跨设备共享！")
        elif char_count == 0:
            st.warning("请输入需要优化的学术内容！")
        elif char_count > MAX_SINGLE_LEN:
            st.error(f"单次提交严禁超过 {MAX_SINGLE_LEN} 字符，请分段处理后重试！")
        elif card.get("remain", 0) < char_count:
            remain = card.get("remain", 0)
            st.error(f"卡密额度不足！本次需要 {char_count} 字符，当前卡密仅剩 {remain} 字符。")
        else:
            # 首次使用，自动完成设备指纹绑定！
            if card.get("device") is None and current_device:
                card["device"] = current_device
                save_keys(keys_db)
                st.toast("🖥️ 当前设备绑定成功！本卡密已受专属保护。")

            # 组装专属对标提示词
            if "知网" in target_engine:
                prompt_text = (
                    "严格对标知网（CNKI）查AI率的底层检测机制（包括语言困惑度Perplexity、突发度Burstiness分析、高频语法共现矩阵与逻辑连接词密度）。"
                    "请把下面的文字内容用尽所有办法，彻底去除内容中能被知网检测出的AI痕迹：\n"
                    "1. 彻底粉碎原有句式结构，大幅提高长短句交替突发度，打破AI固有的平均句长和整齐韵律；\n"
                    "2. 颠覆原有的因果与递进连接逻辑，改用符合人类严谨学术作者习惯的论述语序；\n"
                    "3. 保持原文所有专业术语、学术核心观点与数据论据绝对不变；\n"
                    "4. 直接输出重塑后的最终学术正文，严禁输出任何多余寒暄、说明或解释。\n\n"
                    f"待重塑内容如下：\n{source_text}"
                )
            else:
                prompt_text = (
                    "严格对标维普（VP）查AI率的底层检测机制（包括高频AI套话特征库比对、模板化段落总分总结构识别、特征连接词聚类）。"
                    "请把下面的文字内容用尽所有办法，彻底去除内容中维普检测能探测出的AI痕迹：\n"
                    "1. 彻底清除并替换所有维普特征词与机械套话（如杜绝'综上所述'、'不可否认'、'总而言之'、'深入探讨'、'双刃剑'、'具有重要意义'等）；\n"
                    "2. 重构段落叙事逻辑，打乱固定总分段落形态，变换主被动语态与陈述视角；\n"
                    "3. 保持原文全部核心学术论点、数据和专业名词绝对一致；\n"
                    "4. 直接输出重塑后的最终学术正文，严禁输出任何多余寒暄、说明或解释。\n\n"
                    f"待重塑内容如下：\n{source_text}"
                )

            with st.spinner("专家引擎正在深度思考重塑句式、彻底粉碎检测特征，请稍候（约15-30秒）..."):
                try:
                    api_key = st.secrets.get("API_KEY", "")
                    
                    if not api_key:
                        st.error("系统引擎未配置密钥，请联系客服检查后台。")
                    else:
                        headers = {
                            "Authorization": f"Bearer {api_key}",
                            "Content-Type": "application/json"
                        }
                        
                        payload = {
                            "model": "deepseek-ai/DeepSeek-R1",
                            "messages": [
                                {"role": "user", "content": prompt_text}
                            ],
                            "temperature": 0.6
                        }
                        
                        response = requests.post(
                            "https://api.siliconflow.cn/v1/chat/completions",
                            headers=headers,
                            data=json.dumps(payload),
                            timeout=120
                        )
                        
                        if response.status_code == 200:
                            result_data = response.json()
                            raw_content = result_data["choices"][0]["message"]["content"]
                            clean_text = re.sub(r'<think>.*?</think>', '', raw_content, flags=re.DOTALL).strip()
                            
                            # 精确扣减字符额度并实时写入数据库
                            card["remain"] -= char_count
                            save_keys(keys_db)
                            remain = card["remain"]
                            
                            output_box.text_area("优化完成正文：", value=clean_text, height=360)
                            st.success(f"重塑成功！本次已核销：{char_count} 字符，卡密剩余：{remain} 字符。")
                        else:
                            st.error(f"处理失败，模型响应异常（错误码：{response.status_code}）")
                except Exception as e:
                    st.error(f"请求超时或网络异常：{str(e)}")
