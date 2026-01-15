
import os
import hashlib
import pandas as pd
import streamlit as st
import folium
from folium.plugins import HeatMap, Fullscreen
from streamlit_folium import st_folium
from math import radians, cos, sin, asin, sqrt

st.set_page_config(
    page_title="Manufacturing Cluster Intelligence",
    layout="wide",
    initial_sidebar_state="expanded"
)

hide_streamlit_style = """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    div[data-testid="stToolbar"] { visibility: hidden; height: 0px; }
    </style>
"""

st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# =====================================================
# CONFIGURATION & STYLING
# =====================================================

st.markdown("""
    <style>
    .block-container { padding-top: 2rem; padding-bottom: 2rem; }
    div[data-testid="stMetric"] {
        background-color: #f8f9fa;
        border: 1px solid #e0e0e0;
        padding: 10px;
        border-radius: 8px;
    }
    </style>
""", unsafe_allow_html=True)

COLOR_PALETTE = [
    "#E63946", "#1D3557", "#457B9D", "#A8DADC", "#2A9D8F",
    "#F4A261", "#E76F51", "#6A4C93", "#8AC926", "#FFCA3A"
]

# =====================================================
# UTILITY FUNCTIONS
# =====================================================
def haversine_distance(lat1, lon1, lat2, lon2):
    """
    Calculate the great circle distance in kilometers between two points 
    on the earth (specified in decimal degrees)
    """
    # Convert decimal degrees to radians
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    
    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    
    # Radius of earth in kilometers
    r = 6371
    
    return c * r

def get_sector_color(sector: str) -> str:
    hash_val = int(hashlib.md5(sector.encode()).hexdigest(), 16)
    return COLOR_PALETTE[hash_val % len(COLOR_PALETTE)]

def categorize_size(total_units):
    if total_units < 20:
        return "Nano (0-20)"
    elif total_units < 50:
        return "Micro (20-50)"
    elif total_units < 100:
        return "Small (50-100)"
    elif total_units < 500:
        return "Medium (100-500)"
    else:
        return "Large (500+)"

@st.cache_data
def load_data(path: str):
    """Loads and cleans the manufacturing data."""
    if not os.path.exists(path):
        return None, None

    try:
        df = pd.read_excel(path)
        
        # Standardize column names
        df.columns = [str(c).strip() for c in df.columns]

        required_cols = ["State", "District", "Latitude", "Longitude"]
        if not all(col in df.columns for col in required_cols):
            st.error(f"Data missing required columns: {required_cols}")
            st.stop()

        df["State"] = df["State"].astype(str).str.strip()
        df["District"] = df["District"].astype(str).str.strip()

        # Identify manufacturing columns
        manuf_cols = [str(c) for c in df.columns[7:44]]
        
        # Fill NaNs and ensure numeric types
        df[manuf_cols] = df[manuf_cols].fillna(0).apply(pd.to_numeric, errors='coerce').fillna(0)
        
        # Drop rows without geo-coordinates
        df = df.dropna(subset=["Latitude", "Longitude"])
        
        return df, manuf_cols
    except Exception as e:
        st.error(f"Error reading file: {e}")
        st.stop()

# =====================================================
# DATA LOADING
# =====================================================
DATA_FILE = os.getenv("DATA_FILE_PATH", "MOSPI DATA.xlsx")
df, manufacturing_columns = load_data(DATA_FILE)

if df is None:
    st.warning(f"⚠️ Data file `{DATA_FILE}` not found. Please place it in the root directory.")
    st.info("Expecting columns: State, District, Latitude, Longitude, and sector data columns (indices 7-44).")
    st.stop()

# =====================================================
# SIDEBAR CONTROLS
# =====================================================
st.sidebar.title("🌍 Filters")

# 1. Geographic Filters
state_options = ["India"] + sorted(df["State"].unique())
selected_state = st.sidebar.selectbox("Select State", state_options)

if selected_state == "India":
    df_filtered = df.copy()
    district_options = ["All Districts"]
else:
    df_filtered = df[df["State"] == selected_state].copy()
    district_options = ["All Districts"] + sorted(df_filtered["District"].unique())

selected_district = st.sidebar.selectbox("Select District", district_options)

if selected_district != "All Districts":
    df_filtered = df_filtered[df_filtered["District"] == selected_district]

st.sidebar.markdown("---")

# 2. Radius Filter (NEW FEATURE)
st.sidebar.subheader("📍 Radius Filter")
enable_radius = st.sidebar.checkbox("Enable Distance-Based Filter", value=False)

if enable_radius:
    # Get available districts for radius center selection
    if selected_state == "India":
        radius_district_options = sorted(df["District"].unique())
    else:
        radius_district_options = sorted(df[df["State"] == selected_state]["District"].unique())
    
    center_district = st.sidebar.selectbox(
        "Select Center District",
        options=radius_district_options,
        help="Select the district to use as the center point"
    )
    
    radius_km = st.sidebar.slider(
        "Radius (km)",
        min_value=5,
        max_value=500,
        value=50,
        step=5,
        help="Show manufacturing units within this distance from the center district"
    )
    
    # Get center coordinates for the selected district
    center_district_data = df[df["District"] == center_district]
    if not center_district_data.empty:
        center_lat = center_district_data["Latitude"].mean()
        center_lon = center_district_data["Longitude"].mean()
        
        # Calculate distance for all points in df_filtered
        df_filtered["Distance_km"] = df_filtered.apply(
            lambda row: haversine_distance(center_lat, center_lon, row["Latitude"], row["Longitude"]),
            axis=1
        )
        
        # Filter by radius
        df_filtered = df_filtered[df_filtered["Distance_km"] <= radius_km]
        
        st.sidebar.info(f"📏 Showing units within {radius_km} km of {center_district}")
    else:
        st.sidebar.warning("⚠️ Center district not found in data")

st.sidebar.markdown("---")

# 3. Sector Filters (Dynamic)
if not df_filtered.empty:
    current_sector_sums = df_filtered[manufacturing_columns].sum()
    active_sectors = current_sector_sums[current_sector_sums > 0].index.tolist()
else:
    active_sectors = []

st.sidebar.subheader("🏭 Industry Sectors")
selected_sectors = st.sidebar.multiselect(
    "Choose Sectors to Visualize",
    options=sorted(active_sectors),
    default=sorted(active_sectors)[:1] if active_sectors else [],
    help="Select one or more sectors to see their distribution."
)

st.sidebar.markdown("---")

# 4. Size Category Filter
st.sidebar.subheader("📏 Unit Size By Number Of Employees")
size_categories = ["Nano (0-20)", "Micro (20-50)", "Small (50-100)", "Medium (100-500)", "Large (500+)"]
selected_sizes = st.sidebar.multiselect(
    "Filter by Size",
    options=size_categories,
    default=size_categories,
    help="Filter locations based on total manufacturing units"
)

st.sidebar.markdown("---")

map_mode = st.sidebar.radio("Visualization Mode", ["Detailed Markers", "Density Heatmap"])

# =====================================================
# APPLY SIZE FILTER
# =====================================================
if selected_sectors and not df_filtered.empty:
    df_filtered["Total_Units"] = df_filtered[selected_sectors].sum(axis=1)
    df_filtered["Size_Category"] = df_filtered["Total_Units"].apply(categorize_size)
    
    if selected_sizes:
        df_filtered = df_filtered[df_filtered["Size_Category"].isin(selected_sizes)]

# =====================================================
# MAIN DASHBOARD
# =====================================================

# Dynamic Title
if enable_radius:
    cluster_title = f"Manufacturing Units within {radius_km}km of {center_district}"
elif selected_state == "India":
    cluster_title = "India Manufacturing Overview"
elif selected_district == "All Districts":
    cluster_title = f"{selected_state} Manufacturing Overview"
else:
    cluster_title = f"{selected_district} ({selected_state}) Cluster Overview"

st.title(f"🏭 {cluster_title}")

# 1. Key Metrics Row
if selected_sectors and not df_filtered.empty:
    total_units = df_filtered[selected_sectors].sum().sum()
    
    district_sums = df_filtered.groupby("District")[selected_sectors].sum().sum(axis=1)
    if not district_sums.empty:
        top_district = district_sums.idxmax()
    else:
        top_district = "N/A"
        
    active_locs = len(df_filtered[df_filtered[selected_sectors].sum(axis=1) > 0])
else:
    total_units = 0
    top_district = "N/A"
    active_locs = 0

col1, col2, col3, col4 = st.columns(4)
col1.metric("Selected Region", selected_district if selected_district != "All Districts" else selected_state)
col2.metric("Total Units", f"{int(total_units):,}")
col3.metric("Active Clusters", active_locs)
col4.metric("Top District", top_district)

st.markdown("---")

# =====================================================
# MAP GENERATION
# =====================================================
# Determine Map Center and Zoom
if enable_radius and 'center_lat' in locals():
    center = [center_lat, center_lon]
    zoom = 9
elif selected_district != "All Districts":
    center = [df_filtered["Latitude"].mean(), df_filtered["Longitude"].mean()] if not df_filtered.empty else [22.0, 78.0]
    zoom = 10
elif selected_state != "India":
    center = [df_filtered["Latitude"].mean(), df_filtered["Longitude"].mean()] if not df_filtered.empty else [22.0, 78.0]
    zoom = 7
else:
    center = [22.0, 78.0]
    zoom = 5

m = folium.Map(location=center, zoom_start=zoom, tiles="CartoDB positron", control_scale=True)
Fullscreen().add_to(m)

# Add radius circle if enabled
if enable_radius and 'center_lat' in locals():
    folium.Circle(
        location=[center_lat, center_lon],
        radius=radius_km * 1000,  # Convert km to meters
        color='blue',
        fill=True,
        fillColor='blue',
        fillOpacity=0.1,
        weight=2,
        popup=f"{center_district} - {radius_km}km radius"
    ).add_to(m)
    
    # Add center marker
    folium.Marker(
        location=[center_lat, center_lon],
        popup=f"<b>Center: {center_district}</b>",
        icon=folium.Icon(color='blue', icon='info-sign')
    ).add_to(m)

if selected_sectors and not df_filtered.empty:
    df_map = df_filtered.copy()
    df_map["Total_Selected"] = df_map[selected_sectors].sum(axis=1)
    df_map = df_map[df_map["Total_Selected"] > 0]

    # HEATMAP MODE
    if map_mode == "Density Heatmap":
        heat_data = df_map[["Latitude", "Longitude", "Total_Selected"]].values.tolist()
        HeatMap(
            heat_data, 
            radius=20, 
            blur=15, 
            min_opacity=0.3,
            gradient={0.4: 'blue', 0.65: 'lime', 1: 'red'}
        ).add_to(m)
        
        legend_html = '''
             <div style="position: fixed; bottom: 50px; left: 50px; z-index:9999; font-size:14px;
             background-color: white; padding: 10px; border-radius: 5px; border: 1px solid grey;">
             <b>Heatmap Intensity</b><br>
             aggregated volume of selected sectors
             </div>
        '''
        m.get_root().html.add_child(folium.Element(legend_html))

    # DETAILED MARKERS MODE
    else:
        max_val = df_map["Total_Selected"].max() if not df_map.empty else 1
        
        for idx, row in df_map.iterrows():
            row_sectors = row[selected_sectors]
            dominant_sector = row_sectors.idxmax()
            dominant_val = row_sectors.max()
            
            radius = 5 + (dominant_val / max_val) * 15

            tooltip_html = f"""
                <div style="font-family: sans-serif; min-width: 150px;">
                    <h4 style="margin:0;">{row['District']}</h4>
                    <small style="color:gray;">{row['State']}</small>
                    <hr style="margin: 5px 0;">
                    <b>Size:</b> {row['Size_Category']}<br>
                    <b>Dominant:</b> {dominant_sector}<br>
                    <b>Total Selected:</b> {int(row['Total_Selected'])}<br>
            """
            
            if enable_radius and 'Distance_km' in row:
                tooltip_html += f"<b>Distance:</b> {row['Distance_km']:.1f} km<br>"
            
            tooltip_html += "<div style='margin-top:5px; max-height:100px; overflow-y:auto;'>"
            
            for s in selected_sectors:
                val = row[s]
                if val > 0:
                    tooltip_html += f"<div style='display:flex; justify-content:space-between;'><span>{s}:</span> <b>{int(val)}</b></div>"
            tooltip_html += "</div></div>"

            folium.CircleMarker(
                location=[row["Latitude"], row["Longitude"]],
                radius=radius,
                color=get_sector_color(dominant_sector),
                fill=True,
                fill_color=get_sector_color(dominant_sector),
                fill_opacity=0.7,
                weight=1,
                popup=folium.Popup(tooltip_html, max_width=300),
                tooltip=f"{row['District']}: {int(row['Total_Selected'])} units ({row['Size_Category']})"
            ).add_to(m)

        # CUSTOM LEGEND
        legend_items = ""
        for s in selected_sectors:
            color = get_sector_color(s)
            legend_items += f"""
                <div style='display: flex; align-items: center; margin-bottom: 4px;'>
                    <span style='background:{color}; width:12px; height:12px; border-radius:50%; display:inline-block; margin-right:8px;'></span>
                    <span style='font-size:12px;'>{s}</span>
                </div>
            """
        
        legend_html = f"""
        <div style="
            position: fixed; 
            bottom: 20px; left: 20px; width: 200px; max-height: 300px; 
            background-color: rgba(255, 255, 255, 0.9); 
            z-index: 9999; border-radius: 8px; padding: 10px; 
            box-shadow: 0 0 15px rgba(0,0,0,0.1); overflow-y: auto;
            border: 1px solid #ddd;">
            <div style="font-weight: bold; margin-bottom: 5px;">Legend</div>
            {legend_items}
        </div>
        """
        m.get_root().html.add_child(folium.Element(legend_html))

else:
    st.info("👈 Please select at least one sector from the sidebar to visualize data.")

# Render the Map
st_folium(m, height=600, use_container_width=True)

# =====================================================
# DATA EXPORT
# =====================================================
with st.expander("📊 View & Download Data", expanded=False):
    if selected_sectors and not df_filtered.empty:
        cols_to_show = ["State", "District", "Size_Category"] + selected_sectors
        if enable_radius and 'Distance_km' in df_filtered.columns:
            cols_to_show.insert(3, "Distance_km")
        
        export_df = df_filtered[cols_to_show].copy()
        
        export_df["Total_Selected"] = export_df[selected_sectors].sum(axis=1)
        export_df = export_df[export_df["Total_Selected"] > 0].sort_values("Total_Selected", ascending=False)
        
        st.dataframe(export_df, use_container_width=True)
        
        csv = export_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download Filtered Data as CSV",
            data=csv,
            file_name=f"manufacturing_data_{selected_state}_{selected_district}.csv",
            mime="text/csv",
        )
    else:
        st.write("No data available for the current selection.")
