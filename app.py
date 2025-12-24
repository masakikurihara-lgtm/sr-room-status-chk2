import streamlit as st
import requests
import pandas as pd
import io
import datetime

JST = datetime.timezone(datetime.timedelta(hours=9))

# Streamlit の初期設定
st.set_page_config(
    page_title="SHOWROOM ルームステータス確認ツール",
    layout="wide"
)

# --- 定数設定 ---
ROOM_LIST_URL = "https://mksoul-pro.com/showroom/file/room_list.csv"
ROOM_PROFILE_API = "https://www.showroom-live.com/api/room/profile?room_id={room_id}"

GENRE_MAP = {
    112: "ミュージック", 102: "アイドル", 103: "タレント", 104: "声優",
    105: "芸人", 107: "バーチャル", 108: "モデル", 109: "俳優",
    110: "アナウンサー", 113: "クリエイター", 200: "ライバー",
}

# --- ユーティリティ関数 ---

def _safe_get(data, keys, default_value=None):
    """ネストされた辞書から安全に値を取得するヘルパー関数"""
    temp = data
    for key in keys:
        if isinstance(temp, dict) and key in temp:
            temp = temp.get(key)
        else:
            return default_value
    if temp is None or (isinstance(temp, str) and temp.strip() == "") or (isinstance(temp, float) and pd.isna(temp)):
        return default_value
    return temp

def get_room_profile(room_id):
    """ライバー（ルーム）プロフィール情報APIからデータを取得する"""
    url = ROOM_PROFILE_API.format(room_id=room_id)
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException:
        return None

def display_room_status(profile_data, input_room_id):
    """取得したルームプロフィールデータを表示する（ルーム基本情報のみ）"""

    # 取得時刻表示
    st.caption(
        f"（取得時刻: {datetime.datetime.now(JST).strftime('%Y/%m/%d %H:%M:%S')} 現在）"
    )
    
    # データを安全に取得
    room_name = _safe_get(profile_data, ["room_name"], "取得失敗")
    room_level = _safe_get(profile_data, ["room_level"], "-")
    show_rank = _safe_get(profile_data, ["show_rank_subdivided"], "-")
    next_score = _safe_get(profile_data, ["next_score"], "-")
    prev_score = _safe_get(profile_data, ["prev_score"], "-")
    follower_num = _safe_get(profile_data, ["follower_num"], "-")
    live_continuous_days = _safe_get(profile_data, ["live_continuous_days"], "-")
    is_official = _safe_get(profile_data, ["is_official"], None)
    genre_id = _safe_get(profile_data, ["genre_id"], None)

    official_status = "公式" if is_official is True else "フリー" if is_official is False else "-"
    genre_name = GENRE_MAP.get(genre_id, f"その他 ({genre_id})" if genre_id else "-")
    room_url = f"https://www.showroom-live.com/room/profile?room_id={input_room_id}"
    
    # --- カスタムCSS（基本情報テーブル用を維持） ---
    custom_styles = """
    <style>
    .room-title-container {
        padding: 15px 20px;
        margin-bottom: 20px;
        border-radius: 8px;
        background-color: #f0f2f6; 
        border: 1px solid #e6e6e6;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
        display: flex;
        align-items: center;
    }
    .room-title-container a {
        text-decoration: none; 
        color: #1c1c1c; 
    }
    .basic-info-table-wrapper {
        width: 100%;
        margin: 0 auto;
        overflow-x: auto;
    }
    .basic-info-table {
        border-collapse: collapse;
        width: 100%; 
        margin-top: 10px;
    }
    .basic-info-table th {
        text-align: center !important; 
        background-color: #e8eaf6; 
        color: #1a237e; 
        font-weight: bold;
        padding: 8px 10px; 
        border-top: 1px solid #c5cae9; 
        border-bottom: 1px solid #c5cae9; 
        white-space: nowrap;
        width: 12.5%;
    }
    .basic-info-table td {
        text-align: center !important; 
        padding: 6px 10px; 
        line-height: 1.4;
        border-bottom: 1px solid #f0f0f0;
        white-space: nowrap;
        width: 12.5%;
        font-weight: 600;
    }
    .basic-info-table tbody tr:hover {
        background-color: #f7f9fd; 
    }
    .basic-info-highlight-upper {
        background-color: #e3f2fd !important;
        color: #0d47a1;
    }
    .basic-info-highlight-lower {
        background-color: #fff9c4 !important;
        color: #795548;
    }
    </style>
    """
    st.markdown(custom_styles, unsafe_allow_html=True)

    # タイトル表示
    st.markdown(
        f'<div class="room-title-container">'
        f'<h1 style="font-size:25px; text-align:left; color:#1f2937;"><a href="{room_url}" target="_blank"><u>{room_name} ({input_room_id})</u></a> のルームステータス</h1>'
        f'</div>', 
        unsafe_allow_html=True
    ) 
    
    st.markdown("<div style='margin-top: 16px;'></div>", unsafe_allow_html=True)
    st.markdown("<h1 style='font-size:22px; text-align:left; color:#1f2937; padding: 5px 0px 0px 0px;'>📊 ルーム基本情報</h1>", unsafe_allow_html=True)

    # 数値フォーマットと判定ロジック
    def is_within_30000(value):
        try:
            return int(value) <= 30000
        except (TypeError, ValueError):
            return False

    def format_value(value):
        if value == "-" or value is None:
            return "-"
        try:
            return f"{int(value):,}"
        except (ValueError, TypeError):
            return str(value)

    headers = [
        "ルームレベル", "現在のSHOWランク", "上位ランクまでのスコア", "下位ランクまでのスコア",
        "フォロワー数", "まいにち配信", "ジャンル", "公式 or フリー"
    ]

    values = [
        format_value(room_level), show_rank, format_value(next_score), format_value(prev_score),
        format_value(follower_num), format_value(live_continuous_days), genre_name, official_status
    ]
    
    # HTMLテーブル構築
    td_html = []
    for header, value in zip(headers, values):
        css_class = ""
        if header == "上位ランクまでのスコア" and is_within_30000(next_score):
            css_class = "basic-info-highlight-upper"
        if header == "下位ランクまでのスコア" and is_within_30000(prev_score):
            css_class = "basic-info-highlight-lower"
        td_html.append(f'<td class="{css_class}">{value}</td>')

    html_content = f"""
    <div class="basic-info-table-wrapper">
        <table class="basic-info-table">
            <thead>
                <tr>{"".join(f'<th>{h}</th>' for h in headers)}</tr>
            </thead>
            <tbody>
                <tr>{"".join(td_html)}</tr>
            </tbody>
        </table>
    </div>
    """
    st.markdown(html_content, unsafe_allow_html=True)
    st.caption("※取得できないデータなどはハイフン表示となる場合があります。")

# --- メインロジック ---
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'show_status' not in st.session_state:
    st.session_state.show_status = False
if 'input_room_id' not in st.session_state:
    st.session_state.input_room_id = ""

if not st.session_state.authenticated:
    st.markdown("<h1 style='font-size:28px; text-align:left; color:#1f2937;'>💖 SHOWROOM ルームステータス確認ツール</h1>", unsafe_allow_html=True)
    st.markdown("##### 🔑 認証コードを入力してください")
    input_auth_code = st.text_input("認証コードを入力してください:", placeholder="認証コード", type="password", key="room_id_input_auth")
    
    if st.button("認証する"):
        if input_auth_code:
            with st.spinner("認証中..."):
                try:
                    response = requests.get(ROOM_LIST_URL, timeout=5)
                    response.raise_for_status()
                    room_df = pd.read_csv(io.StringIO(response.text), header=None, dtype=str)
                    valid_codes = set(str(x).strip() for x in room_df.iloc[:, 0].dropna())
                    if input_auth_code.strip() in valid_codes:
                        st.session_state.authenticated = True
                        st.rerun()
                    else:
                        st.error("❌ 認証コードが無効です。")
                except Exception as e:
                    st.error(f"認証リストを取得できませんでした: {e}")
    st.stop()

if st.session_state.authenticated:
    st.markdown("<h1 style='font-size:28px; text-align:left; color:#1f2937;'>💖 SHOWROOM ルームステータス確認ツール</h1>", unsafe_allow_html=True)
    st.markdown("##### 🔎 ルームIDの入力")

    input_room_id_current = st.text_input(
        "表示したいルームIDを入力してください:",
        placeholder="例: 123456",
        key="room_id_input_main",
        value=st.session_state.input_room_id
    ).strip()
    
    if input_room_id_current != st.session_state.input_room_id:
        st.session_state.input_room_id = input_room_id_current
        st.session_state.show_status = False
        
    if st.button("ルームステータスを表示"):
        if st.session_state.input_room_id and st.session_state.input_room_id.isdigit():
            st.session_state.show_status = True
        elif st.session_state.input_room_id:
            st.error("ルームIDは数字で入力してください。")
        else:
            st.warning("ルームIDを入力してください。")
            
    if st.session_state.show_status and st.session_state.input_room_id:
        with st.spinner(f"ルームID {st.session_state.input_room_id} の情報を取得中..."):
            room_profile = get_room_profile(st.session_state.input_room_id)
        if room_profile:
            display_room_status(room_profile, st.session_state.input_room_id)
        else:
            st.error(f"ルームID {st.session_state.input_room_id} の情報を取得できませんでした。")