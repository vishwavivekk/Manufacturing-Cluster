import os
import json
import hashlib
import pandas as pd
import streamlit as st
import folium
from folium.plugins import HeatMap, Fullscreen, MarkerCluster
from streamlit_folium import st_folium
from shapely.geometry import shape, Point
from math import radians, cos, sin, asin, sqrt

# =========================
# PAGE
# =========================
st.set_page_config(page_title="Manufacturing Cluster Intelligence", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
#MainMenu, footer, header {visibility: hidden;}
div[data-testid="stToolbar"] { visibility: hidden; height: 0px; }
.block-container { padding-top: 2rem; padding-bottom: 2rem; }
</style>
""", unsafe_allow_html=True)

COLOR_PALETTE = ["#E63946","#1D3557","#457B9D","#A8DADC","#2A9D8F","#F4A261","#E76F51","#6A4C93","#8AC926","#FFCA3A"]

# =========================
# UTILS
# =========================
df_filtered = df_filtered[
    (df_filtered["Latitude"].between(6.0, 37.5)) &
    (df_filtered["Longitude"].between(68.0, 97.5))
]

def haversine_distance(lat1, lon1, lat2, lon2):
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1; dlon = lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    return 2 * asin((a**0.5)) * 6371

def get_sector_color(key: str) -> str:
    h = int(hashlib.md5(key.encode()).hexdigest(), 16)
    return COLOR_PALETTE[h % len(COLOR_PALETTE)]

def categorize_size(n):
    if n < 20: return "Nano (0-20)"
    if n < 50: return "Micro (20-50)"
    if n < 100: return "Small (50-100)"
    if n < 500: return "Medium (100-500)"
    return "Large (500+)"

@st.cache_data
def load_data(path: str):
    df = pd.read_excel(path, header=[0,1])
    sector_row = df.columns.get_level_values(0)
    subsector_row = df.columns.get_level_values(1)

    new_cols, subsector_to_sector = [], {}
    for i,(sec,sub) in enumerate(zip(sector_row, subsector_row)):
        sec, sub = str(sec).strip(), str(sub).strip()
        if i < 4:
            if 'State' in sec or 'State' in sub: new_cols.append('State')
            elif 'District' in sec or 'District' in sub: new_cols.append('District')
            elif 'Latitude' in sec or 'Latitude' in sub: new_cols.append('Latitude')
            elif 'Longitude' in sec or 'Longitude' in sub: new_cols.append('Longitude')
            else: new_cols.append(sec if sec!='nan' else sub)
        else:
            name = sub if sub not in ['nan',''] else sec
            new_cols.append(name)
            subsector_to_sector[name] = sec

    df.columns = [c.strip() for c in new_cols]
    req = ["State","District","Latitude","Longitude"]
    for r in req:
        if r not in df.columns:
            st.error(f"Missing column: {r}")
            st.stop()

    df["State"] = df["State"].astype(str).str.strip()
    df["District"] = df["District"].astype(str).str.strip()

    subsector_cols = [c for c in df.columns if c not in req]
    df[subsector_cols] = df[subsector_cols].fillna(0).apply(pd.to_numeric, errors="coerce").fillna(0)
    df = df.dropna(subset=["Latitude","Longitude"])
    return df, subsector_cols, subsector_to_sector

@st.cache_data
def load_india_boundary
