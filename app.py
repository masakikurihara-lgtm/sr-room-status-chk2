import streamlit as st
import requests
import pandas as pd
import datetime
import re
import json

JST = datetime.timezone(datetime.timedelta(hours=9))

# ----------------------------------------------------------------------
# Streamlit 初期設定（変更なし）
# ----------------------------------------------------------------------
st.set_page_config(
    page_title="SHOWROOM ルームステータス確認ツール",
    layout="wide"
)

# ----------------------------------------------------------------------
# 定数
# ----------------------------------------------------------------------
ROOM_PROFILE_API = "https://www.showroom-live.com/api/room/profile?room_id={room_id}"

GENRE_MAP = {
    112: "ミュージック", 102: "アイドル", 103: "タレント", 104: "声優",
    105: "芸人", 107: "バーチャル", 108: "モデル", 109: "俳優",
    110: "アナウンサー", 113: "クリエイター", 200: "ライバー",
}

# ----------------------------------------------------------------------
# ユーティリティ
# ----------------------------------------------------------------------
def _safe_get(data, keys, default=None):
    tmp = data
    for k in keys:
        if isinstance(tmp, dict) and k in tmp:
            tmp = tmp[k]
        else:
            return default
    if tmp is None or (isinstance(tmp, str) and tmp.strip() == ""):
        return default
    return tmp


def get_room_profile(room_id):
    try:
        r = requests.get(
            ROOM_PROFILE_API.format(room_id=room_id),
            timeout=10
        )
        r.raise_for_status()
        return r.json()
    except Exception:
        return None


# ----------------------------------------------------------------------
# 表示処理（📊 ルーム基本情報のみ）
# ----------------------------------------------------------------------
def display_room_status(profile_data, input_room_id):

    st.caption(
        f"（取得時刻: {datetime.datetime.now(JST).strftime('%Y/%m/%d %H:%M:%S')} 現在）"
    )

    room_name = _safe_get(profile_data, ["room_name"], "取得失敗")
    room_level = _safe_get(profile_data, ["room_level"], "-")
    show_rank = _safe_get(profile_data, ["show_rank_subdivided"], "-")
    next_score = _safe_get(profile_data, ["next_score"], "-")
    prev_score = _safe_get(profile_data, ["prev_score"], "-")
    follower_num = _safe_get(profile_data, ["follower_num"], "-")
    live_days = _safe_get(profile_data, ["live_continuous_days"], "-")
    is_official = _safe_get(profile_data, ["is_official"], None)
    genre_id = _safe_get(profile_data, ["genre_id"], None)

    official_status = "公式" if is_official is True else "フリー" if is_official is False else "-"
    genre_name = GENRE_MAP.get(genre_id, f"その他 ({genre_id})" if genre_id else "-")

    room_url = f"https://www.showroom-live.com/room/profile?room_id={input_room_id}"

    # ------------------------------------------------------------------
    # CSS（完全維持）
    # ------------------------------------------------------------------
    custom_styles = """
    <style>
    h3 { margin-top:20px; padding-top:10px; border-bottom:none; }

    .room-title-container {
        padding: 15px 20px;
        margin-bottom: 20px;
        border-radius: 8px;
        background-color: #f0f2f6;
        border: 1px solid #e6e6e6;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        display: flex;
        align-items: center;
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
        border-bottom: 1px solid #f0f0f0;
        font-weight: 600;
        white-space: nowrap;
        width: 12.5%;
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

    # ------------------------------------------------------------------
    # タイトル
    # ------------------------------------------------------------------
    st.markdown(
        f"""
        <div class="room-title-container">
            <h1 style="font-size:25px;">
                <a href="{room_url}" target="_blank">
                    <u>{room_name} ({input_room_id})</u>
                </a> のルームステータス
            </h1>
        </div>
        """,
        unsafe_allow_html=True
    )

    # ------------------------------------------------------------------
    # 📊 ルーム基本情報
    # ------------------------------------------------------------------
    def fmt(v):
        if v in ("-", None):
            return "-"
        try:
            return f"{int(v):,}"
        except Exception:
            return str(v)

    def within_30000(v):
        try:
            return int(v) <= 30000
        except Exception:
            return False

    headers = [
        "ルームレベル", "現在のSHOWランク", "上位ランクまでのスコア", "下位ランクまでのスコア",
        "フォロワー数", "まいにち配信", "ジャンル", "公式 or フリー"
    ]

    values = [
        fmt(room_level),
        show_rank,
        fmt(next_score),
        fmt(prev_score),
        fmt(follower_num),
        fmt(live_days),
        genre_name,
        official_status
    ]

    td_html = []
    for h, v in zip(headers, values):
        cls = ""
        if h == "上位ランクまでのスコア" and within_30000(next_score):
            cls = "basic-info-highlight-upper"
        if h == "下位ランクまでのスコア" and within_30000(prev_score):
            cls = "basic-info-highlight-lower"
        td_html.append(f'<td class="{cls}">{v}</td>')

    st.markdown(
        f"""
        <h1 style="font-size:22px;">📊 ルーム基本情報</h1>
        <div class="basic-info-table-wrapper">
            <table class="basic-info-table">
                <thead>
                    <tr>{"".join(f"<th>{h}</th>" for h in headers)}</tr>
                </thead>
                <tbody>
                    <tr>{"".join(td_html)}</tr>
                </tbody>
            </table>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.caption("※取得できないデータはハイフン表示となります。")


# ----------------------------------------------------------------------
# メイン
# ----------------------------------------------------------------------
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

if 'show_status' not in st.session_state:
    st.session_state.show_status = False

room_id = st.text_input("ルームIDを入力してください")

if room_id and st.button("ステータス表示"):
    profile = get_room_profile(room_id)
    if profile:
        display_room_status(profile, room_id)
    else:
        st.error("ルーム情報を取得できませんでした。")
