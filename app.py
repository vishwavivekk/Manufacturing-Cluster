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
def load_india_boundary(path="india_adm0.geojson"):
    with open(path,"r",encoding="utf-8") as f:
        gj = json.load(f)
    poly = shape(gj["features"][0]["geometry"])
    return gj, poly

# =========================
# LOAD
# =========================
DATA_FILE = os.getenv("DATA_FILE_PATH", "Annexure with 3digit.xlsx")
df, subsector_columns, subsector_to_sector = load_data(DATA_FILE)
india_geojson, india_polygon = load_india_boundary()

# =========================
# SIDEBAR
# =========================
st.sidebar.title("🌍 Filters")
state_opts = ["India"] + sorted(df["State"].unique())
selected_state = st.sidebar.selectbox("Select State", state_opts)

df_filtered = df.copy() if selected_state=="India" else df[df["State"]==selected_state].copy()
district_opts = ["All Districts"] + sorted(df_filtered["District"].unique())
selected_district = st.sidebar.selectbox("Select District", district_opts)
if selected_district!="All Districts":
    df_filtered = df_filtered[df_filtered["District"]==selected_district]

st.sidebar.subheader("📍 Radius Filter")
enable_radius = st.sidebar.checkbox("Enable Distance Filter", value=False)
if enable_radius:
    center_district = st.sidebar.selectbox("Center District", sorted(df_filtered["District"].unique()))
    radius_km = st.sidebar.slider("Radius (km)", 5, 500, 50, 5)
    cdf = df[df["District"]==center_district]
    if not cdf.empty:
        center_lat, center_lon = cdf["Latitude"].mean(), cdf["Longitude"].mean()
        df_filtered["Distance_km"] = df_filtered.apply(lambda r: haversine_distance(center_lat, center_lon, r["Latitude"], r["Longitude"]), axis=1)
        df_filtered = df_filtered[df_filtered["Distance_km"]<=radius_km]

st.sidebar.subheader("🏭 Sector/Subsector")
sector_options = ["All Sectors"] + sorted(set(subsector_to_sector.values()))
selected_sector = st.sidebar.selectbox("Sector", sector_options)
subsector_options = ["All Subsectors"] + sorted(subsector_columns)
selected_subsector = st.sidebar.selectbox("Subsector", subsector_options)

st.sidebar.subheader("📏 Size")
sizes = ["Nano (0-20)","Micro (20-50)","Small (50-100)","Medium (100-500)","Large (500+)"]
selected_sizes = st.sidebar.multiselect("Filter by Size", sizes, default=sizes)

map_mode = st.sidebar.radio("Mode", ["Detailed Markers","Density Heatmap"])

# =========================
# APPLY FILTERS
# =========================
if selected_sector!="All Sectors":
    cols = [c for c,s in subsector_to_sector.items() if s==selected_sector]
else:
    cols = subsector_columns.copy()

if selected_subsector!="All Subsectors":
    cols = [selected_subsector] if selected_subsector in subsector_columns else []

if cols:
    df_filtered["Total_Selected"] = df_filtered[cols].sum(axis=1)
    df_filtered["Size_Category"] = df_filtered["Total_Selected"].apply(categorize_size)
    df_filtered = df_filtered[df_filtered["Size_Category"].isin(selected_sizes)]
    df_filtered = df_filtered[df_filtered["Total_Selected"]>0]

# Clip to India only
df_filtered = df_filtered[
    df_filtered.apply(lambda r: india_polygon.contains(Point(r["Longitude"], r["Latitude"])), axis=1)
]

# =========================
# MAP
# =========================
if enable_radius and 'center_lat' in locals():
    center, zoom = [center_lat, center_lon], 9
elif selected_district!="All Districts" and not df_filtered.empty:
    center, zoom = [df_filtered["Latitude"].mean(), df_filtered["Longitude"].mean()], 10
elif selected_state!="India" and not df_filtered.empty:
    center, zoom = [df_filtered["Latitude"].mean(), df_filtered["Longitude"].mean()], 7
else:
    center, zoom = [22.0,78.0], 5

m = folium.Map(location=center, zoom_start=zoom, tiles="cartodbpositron", control_scale=True)
Fullscreen().add_to(m)

# Solid India boundary
folium.GeoJson(
    india_geojson,
    name="India Boundary",
    style_function=lambda x: {"fillColor":"#ffffff","color":"#000000","weight":2,"fillOpacity":0.08}
).add_to(m)

# Grouping
cluster = MarkerCluster(name="Clusters").add_to(m)
state_groups = {}
for s in df_filtered["State"].unique():
    fg = folium.FeatureGroup(name=s)
    fg.add_to(m)
    state_groups[s] = fg

if enable_radius and 'center_lat' in locals():
    folium.Circle([center_lat, center_lon], radius=radius_km*1000, color='blue', fill=True, fillOpacity=0.1).add_to(m)

if map_mode=="Density Heatmap" and not df_filtered.empty:
    heat_data = df_filtered[["Latitude","Longitude","Total_Selected"]].values.tolist()
    HeatMap(heat_data, radius=20, blur=15, min_opacity=0.3).add_to(m)
else:
    max_val = max(1, df_filtered["Total_Selected"].max() if not df_filtered.empty else 1)
    for _, r in df_filtered.iterrows():
        dominant_item = r[cols].idxmax() if cols else "All"
        color_key = subsector_to_sector.get(dominant_item, dominant_item)
        rad = 5 + (r["Total_Selected"]/max_val)*15
        html = f"""
        <b>{r['District']}</b><br>{r['State']}<hr>
        Size: {r['Size_Category']}<br>
        Total: {int(r['Total_Selected'])}
        """
        cm = folium.CircleMarker(
            [r["Latitude"], r["Longitude"]],
            radius=rad,
            color=get_sector_color(color_key),
            fill=True, fill_opacity=0.7,
            popup=html
        )
        cm.add_to(cluster)
        cm.add_to(state_groups.get(r["State"]))

folium.LayerControl(collapsed=True).add_to(m)
st_folium(m, height=650, use_container_width=True)

# =========================
# EXPORT
# =========================
with st.expander("📊 View & Download"):
    if not df_filtered.empty and cols:
        out = df_filtered[["State","District","Size_Category"] + cols].copy()
        out["Total_Selected"] = out[cols].sum(axis=1)
        st.dataframe(out, use_container_width=True)
        st.download_button("Download CSV", out.to_csv(index=False).encode("utf-8"), "filtered.csv", "text/csv")
    else:
        st.info("No data for current filters.")
