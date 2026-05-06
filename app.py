import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from folium.plugins import MarkerCluster, HeatMap

# -----------------------------
# PAGE CONFIG
# -----------------------------
st.set_page_config(
    page_title="Crime Dashboard",
    layout="wide"
)

# -----------------------------
# CUSTOM CSS
# -----------------------------
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

h1, h2, h3, h4 {
    color: white;
}

.card {
    background: rgba(255,255,255,0.08);
    padding: 20px;
    border-radius: 18px;
    backdrop-filter: blur(10px);
    box-shadow: 0 0 15px rgba(0,0,0,0.3);
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

</style>
""", unsafe_allow_html=True)

# -----------------------------
# HEADER
# -----------------------------
st.markdown(
    "<div class='title'>🚔 Crime Analytics Dashboard</div>",
    unsafe_allow_html=True
)

st.markdown(
    "<div class='subtitle'>Interactive monitoring with filters, maps & insights</div>",
    unsafe_allow_html=True
)

# -----------------------------
# LOAD DATA
# -----------------------------
df = pd.read_csv("crime_india_dataset.csv")

df.columns = df.columns.str.strip()

df['Date_Time'] = pd.to_datetime(df['Date_Time'])

df['date'] = df['Date_Time'].dt.date
df['hour'] = df['Date_Time'].dt.hour

# -----------------------------
# SIDEBAR
# -----------------------------
st.sidebar.markdown("## 🎛️ Control Panel")
st.sidebar.markdown("---")

# Area filter
area = st.sidebar.selectbox(
    "📍 Area",
    ["All"] + sorted(df['Area'].unique())
)

# Crime type filter
crime = st.sidebar.multiselect(
    "🚨 Crime Type",
    sorted(df['Crime_Type'].unique()),
    default=sorted(df['Crime_Type'].unique())
)

# Date range
date_range = st.sidebar.date_input(
    "📅 Date Range",
    [df['date'].min(), df['date'].max()]
)

# Hour slider
hour_range = st.sidebar.slider(
    "⏱️ Hour of Day",
    0,
    23,
    (0, 23)
)

# Search box
search = st.sidebar.text_input(
    "🔎 Search (area/crime keyword)"
)

# Map style
tile = st.sidebar.selectbox(
    "🧭 Map Style",
    [
        "OpenStreetMap",
        "CartoDB positron",
        "CartoDB dark_matter"
    ]
)

# -----------------------------
# FILTER DATA
# -----------------------------
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

# -----------------------------
# KPI CARDS
# -----------------------------
c1, c2, c3, c4 = st.columns(4)

with c1:
    st.markdown(
        f"<div class='card'><h3>📊 Total</h3><h2>{len(f)}</h2></div>",
        unsafe_allow_html=True
    )

with c2:
    top_area = f['Area'].value_counts().idxmax() if len(f) else "-"
    st.markdown(
        f"<div class='card'><h3>📍 Top Area</h3><h2>{top_area}</h2></div>",
        unsafe_allow_html=True
    )

with c3:
    top_crime = f['Crime_Type'].value_counts().idxmax() if len(f) else "-"
    st.markdown(
        f"<div class='card'><h3>🚨 Top Crime</h3><h2>{top_crime}</h2></div>",
        unsafe_allow_html=True
    )

with c4:
    st.markdown(
        f"<div class='card'><h3>🧭 Areas Covered</h3><h2>{f['Area'].nunique()}</h2></div>",
        unsafe_allow_html=True
    )

# -----------------------------
# TABS
# -----------------------------
tab1, tab2, tab3 = st.tabs([
    "📊 Overview",
    "🗺️ Maps",
    "📋 Data"
])

# -----------------------------
# OVERVIEW TAB
# -----------------------------
with tab1:

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📊 Crime Rate by Area")
        st.bar_chart(f.groupby('Area').size())

    with col2:
        st.subheader("🚨 Crime Type Distribution")
        st.bar_chart(f['Crime_Type'].value_counts())

    st.subheader("📈 Crime Trend")
    trend = f.groupby('date').size()
    st.line_chart(trend)

# -----------------------------
# MAP TAB
# -----------------------------
with tab2:

    col1, col2 = st.columns(2)

    center = [20.5937, 78.9629]

    # -------------------------
    # CLUSTER MAP
    # -------------------------
    with col1:

        st.markdown("## 🗺️ Cluster Map")

        m1 = folium.Map(
            location=center,
            zoom_start=5,
            tiles=tile
        )

        cluster = MarkerCluster().add_to(m1)

        for _, row in f.iterrows():

            popup_text = f"""
            <b>Area:</b> {row['Area']}<br>
            <b>Crime:</b> {row['Crime_Type']}<br>
            <b>Time:</b> {row['Date_Time']}
            """

            folium.Marker(
                location=[
                    float(row['Latitude']),
                    float(row['Longitude'])
                ],
                popup=popup_text
            ).add_to(cluster)

        st_folium(
            m1,
            width=700,
            height=500
        )

    # -------------------------
    # HEATMAP
    # -------------------------
    with col2:

        st.markdown("## 🔥 Heatmap")

        m2 = folium.Map(
            location=center,
            zoom_start=5,
            tiles=tile
        )

        heat_data = []

        for _, row in f.iterrows():

            heat_data.append([
                float(row['Latitude']),
                float(row['Longitude'])
            ])

        if len(heat_data) > 0:

            HeatMap(
                heat_data,
                radius=18,
                blur=12,
                min_opacity=0.4
            ).add_to(m2)

        st_folium(
            m2,
            width=700,
            height=500
        )

# -----------------------------
# DATA TAB
# -----------------------------
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
