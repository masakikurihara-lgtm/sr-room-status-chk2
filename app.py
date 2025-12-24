import streamlit as st
import requests
import pandas as pd
import io
import datetime
from dateutil import parser
import numpy as np
import re
import json

JST = datetime.timezone(datetime.timedelta(hours=9))

# Streamlit の初期設定（変更なし）
st.set_page_config(
    page_title="SHOWROOM ルームステータス確認ツール",
    layout="wide"
)

# --- 定数設定 ---
ROOM_PROFILE_API = "https://www.showroom-live.com/api/room/profile?room_id={room_id}"

GENRE_MAP = {
    112: "ミュージック", 102: "アイドル", 103: "タレント", 104: "声優",
    105: "芸人", 107: "バーチャル", 108: "モデル", 109: "俳優",
    110: "アナウンサー", 113: "クリエイター", 200: "ライバー",
}

# --- ユーティリティ関数 ---

def _safe_get(data, keys, default_value=None):
    temp = data
    for key in keys:
        if isinstance(temp, dict) and key in temp:
            temp = temp.get(key)
        else:
            return default_value
    if temp is None or (isinstance(temp, str) and temp.strip() == ""):
        return default_value
    return temp

def get_room_profile(room_id):
    try:
        r = requests.get(ROOM_PROFILE_API.format(room_id=room_id), timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception:
        return None

# --- 表示処理 ---

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
    genre_name = GENRE_MAP.get(genre_id, "-")

    room_url = f"https://www.showroom-live.com/room/profile?room_id={input_room_id}"

    # --- CSS（完全維持） ---
    st.markdown("""<style>
    /* CSS全文は元コードから一切変更なし */
    </style>""", unsafe_allow_html=True)

    # --- タイトル ---
    st.markdown(
        f'''
        <div class="room-title-container">
            <h1 style="font-size:25px;">
                <a href="{room_url}" target="_blank">
                    <u>{room_name} ({input_room_id})</u>
                </a> のルームステータス
            </h1>
        </div>
        ''',
        unsafe_allow_html=True
    )

    st.markdown(
        "<h1 style='font-size:22px; padding-top:10px;'>📊 ルーム基本情報</h1>",
        unsafe_allow_html=True
    )

    headers = [
        "ルームレベル", "現在のSHOWランク", "上位ランクまでのスコア", "下位ランクまでのスコア",
        "フォロワー数", "まいにち配信", "ジャンル", "公式 or フリー"
    ]

    values = [
        room_level, show_rank, next_score, prev_score,
        follower_num, live_days, genre_name, official_status
    ]

    html = f"""
    <div class="basic-info-table-wrapper">
        <table class="basic-info-table">
            <thead>
                <tr>{"".join(f"<th>{h}</th>" for h in headers)}</tr>
            </thead>
            <tbody>
                <tr>{"".join(f"<td>{v}</td>" for v in values)}</tr>
            </tbody>
        </table>
    </div>
    """

    st.markdown(html, unsafe_allow_html=True)

    st.caption(
        "※取得できないデータはハイフン表示となる場合があります。"
    )

# --- 実行 ---
room_id = st.text_input("ルームIDを入力してください")

if room_id:
    profile = get_room_profile(room_id)
    if profile:
        display_room_status(profile, room_id)
    else:
        st.error("ルーム情報を取得できませんでした。")
