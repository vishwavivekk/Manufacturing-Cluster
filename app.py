import pandas as pd
import numpy as np
import streamlit as st
import folium
from folium.plugins import HeatMap
from streamlit_folium import st_folium

# =====================================================
# APP CONFIG
# =====================================================
st.set_page_config(
    page_title="Manufacturing Cluster Intelligence",
    layout="wide"
)

DATA_FILE = "forPYthon.xlsx"

# =====================================================
# LOAD DATA
# =====================================================
@st.cache_data
def load_data():
    df = pd.read_excel(DATA_FILE)

    required = ["State", "District", "Latitude", "Longitude"]
    for col in required:
        if col not in df.columns:
            raise ValueError(f"Missing required column: {col}")

    manufacturing_cols = df.columns[7:44].tolist()
    manufacturing_cols = [c for c in manufacturing_cols if isinstance(c, str)]

    df[manufacturing_cols] = df[manufacturing_cols].fillna(0)
    df = df.dropna(subset=["Latitude", "Longitude"])

    df["Total_Manufacturing"] = df[manufacturing_cols].sum(axis=1)

    return df, manufacturing_cols


df, manufacturing_columns = load_data()

# =====================================================
# SIDEBAR — GEOGRAPHY
# =====================================================
st.sidebar.title("🌍 Geography")

state_options = ["All India"] + sorted(df["State"].unique())
selected_state = st.sidebar.selectbox("State", state_options)

if selected_state == "All India":
    df_state = df.copy()
else:
    df_state = df[df["State"] == selected_state]

district_options = ["All Districts"] + sorted(df_state["District"].unique())
selected_district = st.sidebar.selectbox("District / City", district_options)

if selected_district == "All Districts":
    df_geo = df_state.copy()
else:
    df_geo = df_state[df_state["District"] == selected_district]

# =====================================================
# SECTOR FILTERING (DATA-DRIVEN)
# =====================================================
available_sectors = [
    col for col in manufacturing_columns
    if df_geo[col].sum() > 0
]

st.sidebar.markdown("### 🏭 Manufacturing Sectors")

if not available_sectors:
    st.sidebar.warning("No manufacturing data available for this geography.")
    selected_sectors = []
else:
    selected_sectors = st.sidebar.multiselect(
        "Select one or more sectors",
        options=sorted(available_sectors),
        default=available_sectors[:1]
    )

# =====================================================
# MAP OPTIONS
# =====================================================
map_mode = st.sidebar.radio(
    "Map Mode",
    ["Heatmap (Pattern)", "Pointer Map (Detailed)"]
)

# =====================================================
# HEADER
# =====================================================
st.title("🏭 Manufacturing Cluster Intelligence")
st.caption(
    f"View: {selected_state} → {selected_district}"
    if selected_state != "All India"
    else "View: All India"
)

# =====================================================
# MAP CENTER & ZOOM LOGIC
# =====================================================
if selected_state == "All India":
    center = [22.5, 79.0]
    zoom = 5
elif selected_district == "All Districts":
    center = [df_state["Latitude"].mean(), df_state["Longitude"].mean()]
    zoom = 6
else:
    center = [df_geo["Latitude"].mean(), df_geo["Longitude"].mean()]
    zoom = 9

# =====================================================
# CREATE MAP (ALWAYS)
# =====================================================
m = folium.Map(
    location=center,
    zoom_start=zoom,
    tiles="CartoDB positron"
)

# =====================================================
# DATA OVERLAY
# =====================================================
if selected_sectors:
    df_overlay = df_geo.copy()
    df_overlay["Sector_Sum"] = df_overlay[selected_sectors].sum(axis=1)
    df_overlay = df_overlay[df_overlay["Sector_Sum"] > 0]

    if map_mode == "Heatmap (Pattern)":
        HeatMap(
            [
                [r["Latitude"], r["Longitude"], r["Sector_Sum"]]
                for _, r in df_overlay.iterrows()
            ],
            radius=20,
            blur=15,
            min_opacity=0.4
        ).add_to(m)

    else:
        for _, r in df_overlay.iterrows():
            folium.CircleMarker(
                location=[r["Latitude"], r["Longitude"]],
                radius=6,
                color="#1f77b4",
                fill=True,
                fill_opacity=0.8,
                popup=f"""
                <b>State:</b> {r['State']}<br>
                <b>District:</b> {r['District']}<br>
                <b>Total Activity:</b> {int(r['Sector_Sum'])}<br>
                <b>Sectors:</b><br>
                {", ".join(selected_sectors)}
                """
            ).add_to(m)

else:
    # Geography-only fallback
    for _, r in df_geo.iterrows():
        folium.CircleMarker(
            location=[r["Latitude"], r["Longitude"]],
            radius=3,
            color="#cccccc",
            fill=True,
            fill_opacity=0.4,
            popup=f"{r['District']}, {r['State']}"
        ).add_to(m)

# =====================================================
# RENDER MAP
# =====================================================
st_folium(m, height=600, use_container_width=True)

# =====================================================
# DATA TABLE
# =====================================================
with st.expander("📄 View data used in map"):
    if selected_sectors:
        st.dataframe(
            df_overlay[
                ["State", "District"] + selected_sectors
            ].sort_values(by=selected_sectors[0], ascending=False),
            use_container_width=True
        )
    else:
        st.dataframe(
            df_geo[["State", "District"]],
            use_container_width=True
        )
