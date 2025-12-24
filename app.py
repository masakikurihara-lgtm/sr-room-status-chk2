import streamlit as st
import requests
import datetime
import pandas as pd

# =========================================================
# 基本設定
# =========================================================
JST = datetime.timezone(datetime.timedelta(hours=9))

st.set_page_config(
    page_title="SHOWROOM ルームステータス確認ツール",
    layout="wide"
)

ROOM_PROFILE_API = "https://www.showroom-live.com/api/room/profile?room_id={room_id}"

GENRE_MAP = {
    112: "ミュージック", 102: "アイドル", 103: "タレント", 104: "声優",
    105: "芸人", 107: "バーチャル", 108: "モデル", 109: "俳優",
    110: "アナウンサー", 113: "クリエイター", 200: "ライバー",
}

# =========================================================
# ユーティリティ
# =========================================================
def _safe_get(data, keys, default="-"):
    tmp = data
    for k in keys:
        if isinstance(tmp, dict) and k in tmp:
            tmp = tmp[k]
        else:
            return default
    if tmp is None or tmp == "":
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


# =========================================================
# 表示処理（ルーム基本情報のみ）
# =========================================================
def display_room_basic_info(profile, room_id):

    # 取得時刻
    st.caption(
        f"（取得時刻: {datetime.datetime.now(JST).strftime('%Y/%m/%d %H:%M:%S')} 現在）"
    )

    room_name = _safe_get(profile, ["room_name"], "取得失敗")
    room_level = _safe_get(profile, ["room_level"])
    show_rank = _safe_get(profile, ["show_rank_subdivided"])
    next_score = _safe_get(profile, ["next_score"])
    prev_score = _safe_get(profile, ["prev_score"])
    follower_num = _safe_get(profile, ["follower_num"])
    live_days = _safe_get(profile, ["live_continuous_days"])
    is_official = _safe_get(profile, ["is_official"], None)
    genre_id = _safe_get(profile, ["genre_id"], None)

    official_status = (
        "公式" if is_official is True else
        "フリー" if is_official is False else "-"
    )
    genre_name = GENRE_MAP.get(genre_id, "-")

    room_url = f"https://www.showroom-live.com/room/profile?room_id={room_id}"

    # -----------------------------------------------------
    # CSS（基本情報テーブル専用）
    # -----------------------------------------------------
    st.markdown("""
    <style>
    .title-box {
        padding: 15px 20px;
        margin-bottom: 20px;
        border-radius: 8px;
        background-color: #f0f2f6;
        border: 1px solid #e6e6e6;
    }
    .basic-info-table {
        border-collapse: collapse;
        width: 100%;
        margin-top: 10px;
    }
    .basic-info-table th {
        background-color: #e8eaf6;
        color: #1a237e;
        padding: 8px;
        text-align: center;
    }
    .basic-info-table td {
        padding: 8px;
        text-align: center;
        font-weight: 600;
        border-bottom: 1px solid #eee;
    }
    .highlight-upper {
        background-color: #e3f2fd;
    }
    .highlight-lower {
        background-color: #fff9c4;
    }
    </style>
    """, unsafe_allow_html=True)

    # -----------------------------------------------------
    # タイトル
    # -----------------------------------------------------
    st.markdown(
        f"""
        <div class="title-box">
            <h1 style="font-size:24px;">
                <a href="{room_url}" target="_blank">
                    {room_name} ({room_id})
                </a> のルームステータス
            </h1>
        </div>
        """,
        unsafe_allow_html=True
    )

    # -----------------------------------------------------
    # ルーム基本情報
    # -----------------------------------------------------
    st.markdown(
        "<h2 style='font-size:22px;'>📊 ルーム基本情報</h2>",
        unsafe_allow_html=True
    )

    def fmt(v):
        try:
            return f"{int(v):,}"
        except Exception:
            return v

    def is_within_30000(v):
        try:
            return int(v) <= 30000
        except Exception:
            return False

    headers = [
        "ルームレベル", "SHOWランク",
        "上位ランクまで", "下位ランクまで",
        "フォロワー数", "まいにち配信",
        "ジャンル", "公式 / フリー"
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

    tds = []
    for h, v in zip(headers, values):
        cls = ""
        if h == "上位ランクまで" and is_within_30000(next_score):
            cls = "highlight-upper"
        if h == "下位ランクまで" and is_within_30000(prev_score):
            cls = "highlight-lower"
        tds.append(f'<td class="{cls}">{v}</td>')

    table_html = f"""
    <table class="basic-info-table">
        <thead>
            <tr>{"".join(f"<th>{h}</th>" for h in headers)}</tr>
        </thead>
        <tbody>
            <tr>{"".join(tds)}</tr>
        </tbody>
    </table>
    """

    st.markdown(table_html, unsafe_allow_html=True)


# =========================================================
# メイン
# =========================================================
st.title("SHOWROOM ルームステータス確認")

room_id_input = st.text_input("ルームIDを入力してください")

if room_id_input:
    with st.spinner("ルーム情報を取得中..."):
        profile = get_room_profile(room_id_input)

    if profile:
        display_room_basic_info(profile, room_id_input)
    else:
        st.error("ルーム情報の取得に失敗しました。")
