# =========================================================
# CRIME ANALYTICS DASHBOARD
# =========================================================
import streamlit as st
import pandas as pd
import folium

from streamlit_folium import st_folium
from folium.plugins import MarkerCluster, HeatMap

# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title="Crime Analytics Dashboard",
    layout="wide"
)

# =========================================================
# CUSTOM CSS
# =========================================================

st.markdown("""
<style>

.stApp {
    background: linear-gradient(to right, #0f172a, #1e293b);
    color: white;
}

section[data-testid="stSidebar"] {
    background: linear-gradient(to bottom, #020617, #0f172a);
    border-right: 1px solid #334155;
}

.card {
    background: rgba(255,255,255,0.08);
    padding: 20px;
    border-radius: 18px;
    backdrop-filter: blur(10px);
    box-shadow: 0 0 20px rgba(0,0,0,0.35);
}

.title {
    font-size: 42px;
    font-weight: bold;
    text-align: center;
    color: white;
}

.subtitle {
    text-align: center;
    color: #cbd5e1;
    margin-bottom: 20px;
}

h1,h2,h3,h4 {
    color: white;
}

.metric {
    font-size: 40px;
    font-weight: bold;
}

</style>
""", unsafe_allow_html=True)

# =========================================================
# HEADER
# =========================================================

st.markdown(
    "<div class='title'>🚔 Crime Analytics Dashboard</div>",
    unsafe_allow_html=True
)

st.markdown(
    "<div class='subtitle'>Interactive monitoring with filters, maps & insights</div>",
    unsafe_allow_html=True
)

# =========================================================
# LOAD DATA
# =========================================================

df = pd.read_csv("crime_india_dataset.csv")

df.columns = df.columns.str.strip()

df['Date_Time'] = pd.to_datetime(df['Date_Time'])

df['date'] = df['Date_Time'].dt.date
df['hour'] = df['Date_Time'].dt.hour

# =========================================================
# FIXED CITY COORDINATES
# =========================================================

city_coords = {

    "Delhi": [28.6139, 77.2090],

    "Mumbai": [19.0760, 72.8777],

    "Jaipur": [26.9124, 75.7873],

    "Lucknow": [26.8467, 80.9462],

    "Chandigarh": [30.7333, 76.7794],

    "Panipat": [29.3909, 76.9635]
}

# =========================================================
# SIDEBAR
# =========================================================

st.sidebar.markdown("# 🎛️ Control Panel")
st.sidebar.markdown("---")

# AREA
area = st.sidebar.selectbox(
    "📍 Area",
    ["All"] + sorted(df['Area'].unique())
)

# CRIME TYPE
crime = st.sidebar.multiselect(
    "🚨 Crime Type",
    sorted(df['Crime_Type'].unique()),
    default=sorted(df['Crime_Type'].unique())
)

# DATE
date_range = st.sidebar.date_input(
    "📅 Date Range",
    [df['date'].min(), df['date'].max()]
)

# HOUR
hour_range = st.sidebar.slider(
    "⏱️ Hour of Day",
    0,
    23,
    (0, 23)
)

# SEARCH
search = st.sidebar.text_input(
    "🔎 Search"
)

# MAP STYLE
tile = st.sidebar.selectbox(
    "🧭 Map Style",
    [
        "OpenStreetMap",
        "CartoDB positron",
        "CartoDB dark_matter"
    ]
)

# =========================================================
# FILTER DATA
# =========================================================

f = df.copy()

if area != "All":
    f = f[f['Area'] == area]

if crime:
    f = f[f['Crime_Type'].isin(crime)]

f = f[
    (f['date'] >= date_range[0]) &
    (f['date'] <= date_range[1])
]

f = f[
    (f['hour'] >= hour_range[0]) &
    (f['hour'] <= hour_range[1])
]

if search:
    f = f[
        f['Area'].str.contains(search, case=False, na=False) |
        f['Crime_Type'].str.contains(search, case=False, na=False)
    ]

# =========================================================
# KPI CARDS
# =========================================================

c1, c2, c3, c4 = st.columns(4)

with c1:

    st.markdown(f"""
    <div class='card'>
        <h3>📊 Total Crimes</h3>
        <div class='metric'>{len(f)}</div>
    </div>
    """, unsafe_allow_html=True)

with c2:

    top_area = f['Area'].value_counts().idxmax()

    st.markdown(f"""
    <div class='card'>
        <h3>📍 Top Area</h3>
        <div class='metric'>{top_area}</div>
    </div>
    """, unsafe_allow_html=True)

with c3:

    top_crime = f['Crime_Type'].value_counts().idxmax()

    st.markdown(f"""
    <div class='card'>
        <h3>🚨 Top Crime</h3>
        <div class='metric'>{top_crime}</div>
    </div>
    """, unsafe_allow_html=True)

with c4:

    st.markdown(f"""
    <div class='card'>
        <h3>🧭 Areas Covered</h3>
        <div class='metric'>{f['Area'].nunique()}</div>
    </div>
    """, unsafe_allow_html=True)

# =========================================================
# TABS
# =========================================================

tab1, tab2, tab3 = st.tabs([
    "📊 Overview",
    "🗺️ Maps",
    "📋 Data"
])

# =========================================================
# OVERVIEW TAB
# =========================================================

with tab1:

    col1, col2 = st.columns(2)

    with col1:

        st.subheader("📊 Crime Rate by Area")

        area_chart = (
            f.groupby('Area')
            .size()
            .sort_values(ascending=False)
        )

        st.bar_chart(area_chart)

    with col2:

        st.subheader("🚨 Crime Type Distribution")

        crime_chart = (
            f['Crime_Type']
            .value_counts()
        )

        st.bar_chart(crime_chart)

    st.subheader("📈 Crime Trend")

    trend = (
        f.groupby('date')
        .size()
    )

    st.line_chart(trend)

# =========================================================
# MAP TAB
# =========================================================

with tab2:

    col1, col2 = st.columns(2)

    # =====================================================
    # CLUSTER MAP
    # =====================================================

    with col1:

        st.markdown("## 🗺️ Cluster Map")

        m1 = folium.Map(
            location=[23.5, 78.9],
            zoom_start=5,
            tiles=tile
        )

        cluster = MarkerCluster().add_to(m1)   # map lag fixing

        # USE FIXED CITY COORDS
        for _, row in f.iterrows():

            area_name = row['Area']

            if area_name in city_coords:

                lat = city_coords[area_name][0]
                lon = city_coords[area_name][1]

                popup_text = f"""
                <b>Area:</b> {row['Area']}<br>
                <b>Crime:</b> {row['Crime_Type']}<br>
                <b>Time:</b> {row['Date_Time']}
                """

                folium.Marker(
                    location=[lat, lon],
                    popup=popup_text
                ).add_to(cluster)

        st_folium(
            m1,
            width=700,
            height=500
        )

    # =====================================================
    # HEATMAP
    # =====================================================

    with col2:

        st.markdown("## 🔥 Crime Density Heatmap")

        m2 = folium.Map(
            location=[23.5, 78.9],
            zoom_start=5,
            tiles=tile
        )

        # CRIME COUNT BY AREA
        area_counts = (
            f.groupby('Area')
            .size()
            .reset_index(name='Crime_Count')
        )

        heat_data = []

        for _, row in area_counts.iterrows():

            area_name = row['Area']

            if area_name in city_coords:

                lat = city_coords[area_name][0]
                lon = city_coords[area_name][1]

                heat_data.append([
                    lat,
                    lon,
                    int(row['Crime_Count']) * 50
                ])

        HeatMap(
            heat_data,
            radius=40,
            blur=25,
            min_opacity=0.5
        ).add_to(m2)

        st_folium(
            m2,
            width=700,
            height=500
        )

# =========================================================
# DATA TAB
# =========================================================

with tab3:

    st.subheader("📋 Crime Records")

    st.dataframe(
        f,
        use_container_width=True
    )

    csv = f.to_csv(index=False).encode('utf-8')

    st.download_button(
        "⬇️ Download CSV",
        data=csv,
        file_name="crime_records.csv",
        mime="text/csv"
    )
