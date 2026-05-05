import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from folium.plugins import MarkerCluster, HeatMap

# -----------------------------
# PAGE CONFIG
# -----------------------------
st.set_page_config(page_title="Crime Dashboard", layout="wide")

# -----------------------------
# CSS (subtle, clean)
# -----------------------------
st.markdown("""
<style>
.stApp {background: linear-gradient(120deg,#0f172a,#1f2937);}
section[data-testid="stSidebar"] {background: linear-gradient(#0b132b,#1c2541);}
.card {
  background: rgba(255,255,255,0.08);
  border-radius: 16px; padding: 16px; margin: 8px 0;
  backdrop-filter: blur(10px);
}
.title {font-size:36px;font-weight:700;text-align:center;color:#e5e7eb;}
.subtitle {text-align:center;color:#9ca3af;margin-bottom:10px;}
.badge {font-size:14px;color:#a7f3d0;}
</style>
""", unsafe_allow_html=True)

# -----------------------------
# HEADER
# -----------------------------
st.markdown("<div class='title'>🚔 Crime Analytics Dashboard</div>", unsafe_allow_html=True)
st.markdown("<div class='subtitle'>Interactive monitoring with filters, maps & insights</div>", unsafe_allow_html=True)

# -----------------------------
# LOAD DATA
# -----------------------------
df = pd.read_csv("crime_india_dataset.csv")
df.columns = df.columns.str.strip()
df['Date_Time'] = pd.to_datetime(df['Date_Time'])
df['date'] = df['Date_Time'].dt.date
df['hour'] = df['Date_Time'].dt.hour

# -----------------------------
# SIDEBAR (CONTROL PANEL)
# -----------------------------
st.sidebar.markdown("## 🎛️ Control Panel")
st.sidebar.markdown("---")

# Area
area = st.sidebar.selectbox("📍 Area", ["All"] + sorted(df['Area'].dropna().unique()))

# Crime
crime = st.sidebar.multiselect(
    "🚨 Crime Type",
    options=sorted(df['Crime_Type'].dropna().unique()),
    default=sorted(df['Crime_Type'].dropna().unique())
)

# Date
date_range = st.sidebar.date_input(
    "📅 Date Range",
    [df['date'].min(), df['date'].max()]
)

# Hour slider
hour_range = st.sidebar.slider("⏱️ Hour of Day", 0, 23, (0, 23))

# Search
query = st.sidebar.text_input("🔎 Search (area/crime keyword)")

# Map style
tile = st.sidebar.selectbox(
    "🧭 Map Style",
    ["OpenStreetMap", "CartoDB positron", "CartoDB dark_matter", "Stamen Terrain"]
)

# Reset
if st.sidebar.button("🔄 Reset Filters"):
    st.rerun()

# -----------------------------
# FILTER DATA
# -----------------------------
f = df.copy()

if area != "All":
    f = f[f['Area'] == area]

if crime:
    f = f[f['Crime_Type'].isin(crime)]

f = f[(f['date'] >= date_range[0]) & (f['date'] <= date_range[1])]
f = f[(f['hour'] >= hour_range[0]) & (f['hour'] <= hour_range[1])]

if query:
    q = query.lower()
    f = f[
        f['Area'].str.lower().str.contains(q, na=False) |
        f['Crime_Type'].str.lower().str.contains(q, na=False)
    ]

# -----------------------------
# SAFE HELPERS
# -----------------------------
def safe_idxmax(series):
    return series.idxmax() if len(series) else "—"

# -----------------------------
# KPI CARDS
# -----------------------------
c1, c2, c3, c4 = st.columns(4)

with c1:
    st.markdown(f"<div class='card'><b>📊 Total</b><br>{len(f)}</div>", unsafe_allow_html=True)

with c2:
    st.markdown(f"<div class='card'><b>📍 Top Area</b><br>{safe_idxmax(f['Area'].value_counts())}</div>", unsafe_allow_html=True)

with c3:
    st.markdown(f"<div class='card'><b>🚨 Top Crime</b><br>{safe_idxmax(f['Crime_Type'].value_counts())}</div>", unsafe_allow_html=True)

with c4:
    uniq = f['Area'].nunique() if len(f) else 0
    st.markdown(f"<div class='card'><b>🧭 Areas Covered</b><br>{uniq}</div>", unsafe_allow_html=True)

# -----------------------------
# TABS
# -----------------------------
tab1, tab2, tab3 = st.tabs(["📊 Overview", "🗺️ Maps", "📋 Data"])

# -----------------------------
# TAB 1: OVERVIEW
# -----------------------------
with tab1:
    colA, colB = st.columns(2)

    with colA:
        st.markdown("### 📊 Crime Rate by Area")
        st.bar_chart(f.groupby('Area').size())

        st.markdown("### 🏆 Top 5 Areas")
        st.table(f['Area'].value_counts().head(5))

    with colB:
        st.markdown("### 📊 Crime Type Distribution")
        st.bar_chart(f['Crime_Type'].value_counts())

        st.markdown("### 📈 Trend (by Date)")
        trend = f.groupby('date').size()
        st.line_chart(trend)

# -----------------------------
# TAB 2: MAPS
# -----------------------------
with tab2:
    col1, col2 = st.columns(2)

    center = [df['Latitude'].mean(), df['Longitude'].mean()]

    # Cluster Map
    with col1:
        st.markdown("### 🗺️ Cluster Map")
        m1 = folium.Map(location=center, zoom_start=5, tiles=tile)
        cluster = MarkerCluster().add_to(m1)

        for _, r in f.iterrows():
            folium.Marker(
                location=[r['Latitude'], r['Longitude']],
                popup=f"<b>{r['Area']}</b><br>{r['Crime_Type']}<br>{r['Date_Time']}"
            ).add_to(cluster)

        st_folium(m1, width=650, height=450)

    # Heatmap
    with col2:
        st.markdown("### 🔥 Heatmap")
        m2 = folium.Map(location=center, zoom_start=5, tiles=tile)
        heat_data = f[['Latitude', 'Longitude']].values.tolist()
        HeatMap(heat_data, radius=12, blur=15).add_to(m2)
        st_folium(m2, width=650, height=450)

# -----------------------------
# TAB 3: DATA
# -----------------------------
with tab3:
    st.markdown("### 📋 Records")
    st.dataframe(f, use_container_width=True)

    # Download
    csv = f.to_csv(index=False).encode('utf-8')
    st.download_button("⬇️ Download CSV", data=csv, file_name="filtered_crimes.csv", mime="text/csv")