import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import streamlit.components.v1 as components

# --- サイト設定 ---
st.set_page_config(page_title="バスナビゲーター", page_icon="🚌", layout="centered")

# --- 【確定データ】 ---
BUS_DATA = {
    "平日": {
        "行き": {7:[10,23,36,49], 8:[3,17,31,45,59], 9:[14,29,44], 10:[0,20,40,59], 11:[19,39,59], 12:[19,39,59], 13:[19,39,59], 14:[19,39,59], 15:[19,39,54], 16:[4,23,42,59], 17:[16,33,50], 18:[7,24,41,58], 19:[15,33,52], 20:[17,35,53], 21:[25,45], 22:[6,29]},
        "帰り": {7:[10,24,35,48], 8:[3,18,33,48], 9:[5,25,45], 10:[5,25,45], 11:[5,25,45], 12:[5,25,45], 13:[5,25,45], 14:[5,25,45], 15:[5,25,45], 16:[3,20,37,54], 17:[11,28,45], 18:[2,19,36,53], 19:[10,27,44], 20:[2,21,40], 21:[1,22,45], 22:[5,26,46]}
    },
    "土曜": {
        "行き": {7:[6,28,44], 8:[0,17,34,52], 9:[11,30,49], 10:[8,27,46], 11:[5,24,43], 12:[3,22,42], 13:[2,22,41], 14:[1,21,41], 15:[0,20,41], 16:[2,22,42], 17:[3,24,44], 18:[3,23,42], 19:[2,22,42], 20:[11,34,55], 21:[23], 22:[0]},
        "帰り": {7:[29,50], 8:[6,23,40,58], 9:[16,35,54], 10:[13,32,51], 11:[10,29,49], 12:[8,28,47], 13:[7,27,47], 14:[6,26,46], 15:[6,26,46], 16:[7,28,48], 17:[9,29,50], 18:[10,29,48], 19:[7,25,48], 20:[11,34,55], 21:[16,46], 22:[16]}
    },
    "休日": {
        "行き": {7:[10,36], 8:[7,24,42], 9:[9,34,58], 10:[13,28,50], 11:[12,31,50], 12:[10,30,49], 13:[8,27,46], 14:[5,24,43], 15:[2,21,40,59], 16:[18,37,56], 17:[15,34,53], 18:[14,36], 19:[7,29,50], 20:[19,56], 21:[28], 22:[0]},
        "帰り": {7:[27,57], 8:[27,49], 9:[11,35,59], 10:[23,41,59], 11:[17,37,57], 12:[17,36,55], 13:[14,33,52], 14:[11,30,49], 15:[8,27,46], 16:[5,24,43], 17:[2,21,41], 18:[1,21,43], 19:[6,29,51], 20:[12,44], 21:[16,46], 22:[16]}
    }
}

WALK_HOME_TO_STOP = 10
TOTAL_BUS_TO_SCHOOL = 30 

# --- デザインを完全に標準ボタンと一致させたコピーボタン ---
def copy_button_html(text, label):
    html_code = f"""
    <div style="margin-top: -14px; margin-bottom: 10px;">
        <button onclick="copyToClipboard()" style="
            width: 100%;
            height: 38.4px;
            background-color: rgb(255, 255, 255);
            border: 1px solid rgba(49, 51, 63, 0.2);
            color: rgb(49, 51, 63);
            border-radius: 8px;
            cursor: pointer;
            font-size: 16px;
            font-family: 'Source Sans Pro', sans-serif;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 10px;
            line-height: 1.6;
            outline: none;
        ">
            <span style="font-size: 18px;">📋</span> {label}
        </button>
    </div>

    <script>
    function copyToClipboard() {{
        const text = `{text}`;
        const tempTextArea = document.createElement("textarea");
        tempTextArea.value = text;
        document.body.appendChild(tempTextArea);
        tempTextArea.select();
        try {{
            document.execCommand('copy');
            alert('コピーしました！');
        }} catch (err) {{
            console.error('fallback copy failed', err);
        }}
        document.body.removeChild(tempTextArea);
    }}
    </script>
    """
    return components.html(html_code, height=50)

def get_best_bus(direction_data, target_h, target_m, is_arrival_limit=True):
    now = datetime.now()
    target_dt = now.replace(hour=target_h, minute=target_m, second=0, microsecond=0)
    deadline = target_dt - timedelta(minutes=TOTAL_BUS_TO_SCHOOL) if is_arrival_limit else target_dt
    all_buses = [now.replace(hour=h, minute=m, second=0, microsecond=0) for h, mins in direction_data.items() for m in mins]
    all_buses.sort()
    if is_arrival_limit:
        suitable = [b for b in all_buses if b <= deadline]
        return suitable[-1] if suitable else None
    else:
        suitable = [b for b in all_buses if b >= deadline]
        return suitable[0] if suitable else None

# --- UI ---
st.subheader("🚌 バスナビゲーター")

# 曜日のデフォルト設定
wd = datetime.now().weekday()
day_idx = 0 if wd < 5 else 1 if wd == 5 else 2
day_type = st.radio("", ["平日", "土曜", "休日"], index=day_idx, horizontal=True)

main_tab1, main_tab2, main_tab3 = st.tabs(["🏠 ➡ 🏫 塾へ", "🏫 ➡ 🏠 帰り", "📋 時刻表"])

# --- デフォルト時刻の修正 ---
now_h = datetime.now().hour
HOUR_CHOICES = list(range(7, 23))
# 現在時刻が 7-22時 の間ならその時間を、そうでなければ7時か22時をセット
target_default_h = max(7, min(22, now_h))
default_h_idx = HOUR_CHOICES.index(target_default_h)

with main_tab1:
    st.write("**📍 塾に何時までに着きたい？**")
    c1, c2 = st.columns(2)
    h1 = c1.selectbox("時", HOUR_CHOICES, index=default_h_idx, key="h1")
    m1 = c2.selectbox("分", range(0, 60, 5), index=0, key="m1")
    if st.button("出発時間を計算", key="btn1", use_container_width=True):
        bus = get_best_bus(BUS_DATA[day_type]["行き"], h1, m1, True)
        if bus:
            leave_time = (bus - timedelta(minutes=WALK_HOME_TO_STOP)).strftime('%H:%M')
            bus_time = bus.strftime('%H:%M')
            st.success(f"🏠 **{leave_time}** に出発！")
            st.info(f"🚌 バス: {bus_time}\n\n🏫 到着: {(bus + timedelta(minutes=TOTAL_BUS_TO_SCHOOL)).strftime('%H:%M')}")
            
            st.link_button("💙 Google Tasks を開く", "https://tasks.google.com/", use_container_width=True)
            copy_button_html(f"{leave_time} に出発！\\nバス: {bus_time}", "コピー")

with main_tab2:
    st.write("**📍 塾を何時に出る？**")
    c1, c2 = st.columns(2)
    h2 = c1.selectbox("時", HOUR_CHOICES, index=default_h_idx, key="h2")
    m2 = c2.selectbox("分", range(0, 60, 5), index=0, key="m2")
    if st.button("帰りのバスを計算", key="btn2", use_container_width=True):
        bus = get_best_bus(BUS_DATA[day_type]["帰り"], h2, m2, False)
        if bus:
            bus_time = bus.strftime('%H:%M')
            pick_time = (bus + timedelta(minutes=15)).strftime('%H:%M')
            st.success(f"🚌 **{bus_time}** のバス")
            st.warning(f"🏃 **{pick_time}** にお迎え！")
            st.info(f"🏠 家到着: {(bus + timedelta(minutes=25)).strftime('%H:%M')}")
            
            st.link_button("💙 Google Tasks を開く", "https://tasks.google.com/", use_container_width=True)
            copy_button_html(f"{bus_time} のバス\\n{pick_time} にお迎え！", "コピー")

with main_tab3:
    def create_combined_timetable(direction):
        h_range = range(7, 23)
        table_data = []
        for h in h_range:
            row = {"時": h}
            for d in ["平日", "土曜", "休日"]:
                row[d] = " ".join([f"{m:02d}" for m in BUS_DATA[d][direction].get(h, [])])
            table_data.append(row)
        return pd.DataFrame(table_data).set_index("時")
    sub_tab1, sub_tab2 = st.tabs(["🏫 行き", "🏠 帰り"])
    with sub_tab1: st.table(create_combined_timetable("行き"))
    with sub_tab2: st.table(create_combined_timetable("帰り"))
