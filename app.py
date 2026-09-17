import streamlit as st
import requests
import json
import re

# 页面基础配置
st.set_page_config(
    page_title="知网、维普强降AI率系统",
    page_icon="🎓",
    layout="wide"
)

# ----------------- 抹除顶部菜单与多余外链 -----------------
hide_top_menu = """
<style>
header[data-testid="stHeader"] {
    visibility: hidden !important;
    display: none !important;
    height: 0px !important;
}
header {
    visibility: hidden !important;
    display: none !important;
}
#MainMenu {
    visibility: hidden !important;
}
footer {
    visibility: hidden !important;
    display: none !important;
}
</style>
"""
st.markdown(hide_top_menu, unsafe_allow_html=True)

# ----------------- 卡密库管理 -----------------
DEFAULT_KEYS = {
    "SP-TEST888": 5000,
    "SP-VIP10000": 10000,
    "SP-VIP20000": 20000,
}

if "key_db" not in st.session_state:
    st.session_state.key_db = DEFAULT_KEYS

# ----------------- 界面与侧边栏 -----------------
st.title("🎓 知网、维普强降AI率系统")

with st.sidebar:
    st.header("🔑 授权与凭证")
    license_key = st.text_input("请输入您的卡密授权码", type="password", placeholder="例如: SP-XXXXXX")
    
    if st.button("查询卡密额度"):
        if not license_key:
            st.warning("请先输入授权码！")
        elif license_key in st.session_state.key_db:
            remain = st.session_state.key_db[license_key]
            st.success(f"授权有效！剩余可用额度：{remain} 字符")
        else:
            st.error("授权码无效或已过期，请核对后重试")
            
    st.markdown("---")
    st.markdown("**📌 核心使用规范：**")
    st.markdown("1. **严禁整篇提交**：为确保突破查重系统底层算法，单次严格限制在 **1000 字符** 以内。")
    st.markdown("2. **按段精修**：建议按 1~2 个自然段分段提交，降重与去 AI 效果最佳。")
    st.markdown("3. **专家引擎**：后端已启用专家级深度重塑引擎，单次处理耗时约 15~30 秒，请耐心等待。")
    st.markdown("4. 如需购买或补充额度，请联系店铺客服。")

# ----------------- 主操作区 -----------------
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

# ----------------- 核心处理逻辑 -----------------
with col2:
    st.subheader("优化重塑正文")
    output_box = st.empty()

    if start_btn:
        if not license_key:
            st.error("请先在左侧输入卡密授权码！")
        elif license_key not in st.session_state.key_db:
            st.error("授权码无效，请检查是否输入正确！")
        elif char_count == 0:
            st.warning("请输入需要优化的学术内容！")
        elif char_count > MAX_SINGLE_LEN:
            st.error(f"单次提交严禁超过 {MAX_SINGLE_LEN} 字符，请分段处理后重试！")
        elif st.session_state.key_db[license_key] < char_count:
            remain = st.session_state.key_db[license_key]
            st.error(f"卡密额度不足！本次需要 {char_count} 字符，当前卡密仅剩 {remain} 字符。")
        else:
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
                            
                            st.session_state.key_db[license_key] -= char_count
                            remain = st.session_state.key_db[license_key]
                            
                            output_box.text_area("优化完成正文：", value=clean_text, height=360)
                            st.success(f"重塑成功！本次已核销：{char_count} 字符，卡密剩余：{remain} 字符。")
                        else:
                            st.error(f"处理失败，模型响应异常（错误码：{response.status_code}）")
                except Exception as e:
                    st.error(f"请求超时或网络异常：{str(e)}")
