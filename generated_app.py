import streamlit as st
import os
import json
import time
from openai import OpenAI

# ページ設定
st.set_page_config(page_title="先延ばし分解アプリ", page_icon="🧩", layout="centered")

# セッション状態初期化
if "tasks" not in st.session_state:
    st.session_state.tasks = []
if "current_index" not in st.session_state:
    st.session_state.current_index = 0
if "show_result" not in st.session_state:
    st.session_state.show_result = False
if "original_task" not in st.session_state:
    st.session_state.original_task = ""

def decompose_with_ai(task_text):
    """DeepSeek APIでタスクを分解"""
    api_key = os.environ.get("DEEPSEEK_API_KEY")
    if not api_key:
        st.error("環境変数 DEEPSEEK_API_KEY が設定されていません")
        return ["タスクを小さくする", "最初の一歩を踏み出す", "続ける"]
    
    client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")
    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "あなたはタスク分解の専門家です。ユーザーが入力したタスクを、今すぐできる小さなステップに分解してください。必ず4〜6個のステップに分け、各ステップは簡潔に（10文字以内）日本語で出力。出力はJSON配列形式のみ。例: [\"PCを開く\", \"ファイルを作る\"]"},
                {"role": "user", "content": f"次のタスクを分解してください: {task_text}"}
            ],
            temperature=0.7,
            max_tokens=200
        )
        content = response.choices[0].message.content.strip()
        # JSONパース試行
        try:
            tasks = json.loads(content)
            if isinstance(tasks, list) and len(tasks) >= 2:
                return tasks[:6]
        except:
            pass
        # 改行区切りでパース
        lines = [l.strip().lstrip("0123456789.- ") for l in content.split("\n") if l.strip()]
        if len(lines) >= 2:
            return lines[:6]
        return ["最初の一歩を決める", "行動を開始する", "続ける"]
    except Exception as e:
        st.error(f"AI分解中にエラー: {e}")
        return ["タスクを小さくする", "最初の一歩を踏み出す", "続ける"]

def play_complete_sound():
    """完了音を再生（Web Audio API）"""
    st.markdown("""
    <script>
    (function() {
        try {
            const ctx = new (window.AudioContext || window.webkitAudioContext)();
            const osc = ctx.createOscillator();
            const gain = ctx.createGain();
            osc.connect(gain);
            gain.connect(ctx.destination);
            osc.frequency.value = 880;
            osc.type = 'sine';
            gain.gain.setValueAtTime(0.3, ctx.currentTime);
            gain.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + 0.3);
            osc.start(ctx.currentTime);
            osc.stop(ctx.currentTime + 0.3);
        } catch(e) {}
    })();
    </script>
    """, unsafe_allow_html=True)

# タイトル
col_logo, col_title = st.columns([1, 8], vertical_alignment="center")
with col_logo:
    try:
        st.image('kotone.png', width=70)
    except Exception:
        st.write("LOGO") # sayaka.pngが無い場合のフォールバック
with col_title:
    st.title("先延ばし分解アプリ")
    st.markdown("「やりたくない」を **今すぐできるサイズ** に分解しよう")

# メイン画面
if not st.session_state.show_result:
    # 入力画面
    with st.container():
        st.subheader("📝 やることを入力")
        task_input = st.text_input("例: 資料作成、部屋片付け、勉強...", placeholder="例: 資料作成", label_visibility="collapsed")
        
        if st.button("🔨 分解する", type="primary", use_container_width=True):
            if task_input.strip():
                st.session_state.original_task = task_input.strip()
                with st.spinner("AIがタスクを分解中..."):
                    st.session_state.tasks = decompose_with_ai(task_input)
                st.session_state.current_index = 0
                st.session_state.show_result = True
                st.rerun()
            else:
                st.warning("タスクを入力してください")
else:
    # 分解結果画面
    tasks = st.session_state.tasks
    idx = st.session_state.current_index
    
    if idx < len(tasks):
        # 現在のタスク（大きく表示）
        st.markdown(f"### 今やること")
        st.markdown(f'<div class="big-task">{tasks[idx]}</div>', unsafe_allow_html=True)
        
        # 完了ボタン
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("✅ 完了！", key="complete", use_container_width=True):
                play_complete_sound()
                st.session_state.current_index += 1
                time.sleep(0.3)
                st.rerun()
        
        # 次のタスク（小さく表示）
        if idx + 1 < len(tasks):
            st.markdown("#### 次のステップ")
            st.markdown(f'<div class="next-task">{tasks[idx+1]}</div>', unsafe_allow_html=True)
        
        # 残りタスク一覧（さらに小さく）
        if idx + 2 < len(tasks):
            with st.expander("残りのステップを見る"):
                for i in range(idx+2, len(tasks)):
                    st.markdown(f"- {tasks[i]}")
    else:
        # すべて完了
        st.balloons()
        st.success("🎉 すべてのステップを完了しました！")
        st.markdown(f"元のタスク「**{st.session_state.original_task}**」を小さく分解して実行しました。")
        if st.button("🔄 新しいタスクを分解する", use_container_width=True):
            st.session_state.show_result = False
            st.session_state.tasks = []
            st.session_state.current_index = 0
            st.session_state.original_task = ""
            st.rerun()
    
    # 戻るボタン
    if st.button("← 入力に戻る", use_container_width=True):
        st.session_state.show_result = False
        st.session_state.tasks = []
        st.session_state.current_index = 0
        st.session_state.original_task = ""
        st.rerun()