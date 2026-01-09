import os
import hashlib
import pandas as pd
import streamlit as st
import folium
from folium.plugins import HeatMap, Fullscreen
from streamlit_folium import st_folium

# =====================================================
# CONFIGURATION & STYLING
# =====================================================
st.set_page_config(
    page_title="Manufacturing Cluster Intelligence",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better spacing and metrics styling
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

# Distinct color palette for sectors to ensure visibility
COLOR_PALETTE = [
    "#E63946", "#1D3557", "#457B9D", "#A8DADC", "#2A9D8F",
    "#F4A261", "#E76F51", "#6A4C93", "#8AC926", "#FFCA3A"
]

# =====================================================
# UTILITY FUNCTIONS
# =====================================================
def get_sector_color(sector: str) -> str:
    """Deterministically map a sector name to a color from the palette."""
    hash_val = int(hashlib.md5(sector.encode()).hexdigest(), 16)
    return COLOR_PALETTE[hash_val % len(COLOR_PALETTE)]

@st.cache_data
def load_data(path: str):
    """Loads and cleans the manufacturing data."""
    if not os.path.exists(path):
        return None, None

    try:
        df = pd.read_excel(path)
        
        # Standardize column names (optional cleaning)
        # Convert to string first to handle cases where headers are numbers/floats
        df.columns = [str(c).strip() for c in df.columns]

        required_cols = ["State", "District", "Latitude", "Longitude"]
        if not all(col in df.columns for col in required_cols):
            st.error(f"Data missing required columns: {required_cols}")
            st.stop()

        # Identify manufacturing columns (assuming index 7 to 44 based on original code)
        # We ensure they are strings to avoid index errors
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
DATA_FILE = os.getenv("DATA_FILE_PATH", "forPYthon.xlsx")
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
state_options = ["All India"] + sorted(df["State"].astype(str).unique())
selected_state = st.sidebar.selectbox("Select State", state_options)

if selected_state == "All India":
    df_filtered = df
    district_options = ["All Districts"]
else:
    df_filtered = df[df["State"] == selected_state]
    district_options = ["All Districts"] + sorted(df_filtered["District"].astype(str).unique())

selected_district = st.sidebar.selectbox("Select District", district_options)

if selected_district != "All Districts":
    df_filtered = df_filtered[df_filtered["District"] == selected_district]

st.sidebar.markdown("---")

# 2. Sector Filters (Dynamic)
# Only show sectors that have non-zero data in the current filtered view
current_sector_sums = df_filtered[manufacturing_columns].sum()
active_sectors = current_sector_sums[current_sector_sums > 0].index.tolist()

st.sidebar.subheader("🏭 Industry Sectors")
selected_sectors = st.sidebar.multiselect(
    "Choose Sectors to Visualize",
    options=sorted(active_sectors),
    default=sorted(active_sectors)[:1] if active_sectors else [],
    help="Select one or more sectors to see their distribution."
)

map_mode = st.sidebar.radio("Visualization Mode", ["Detailed Markers", "Density Heatmap"])

# =====================================================
# MAIN DASHBOARD
# =====================================================
st.title("🏭 Manufacturing Cluster Intelligence")

# 1. Key Metrics Row
if selected_sectors:
    # Calculate totals for the selected view
    total_units = df_filtered[selected_sectors].sum().sum()
    top_district = df_filtered.groupby("District")[selected_sectors].sum().sum(axis=1).idxmax() if not df_filtered.empty else "N/A"
    active_locs = len(df_filtered[df_filtered[selected_sectors].sum(axis=1) > 0])
else:
    total_units = 0
    top_district = "N/A"
    active_locs = 0

col1, col2, col3, col4 = st.columns(4)
col1.metric("Selected State", selected_state)
col2.metric("Total Units (Selected)", f"{int(total_units):,}")
col3.metric("Active Clusters", active_locs)
col4.metric("Top District", top_district)

st.markdown("---")

# =====================================================
# MAP GENERATION
# =====================================================
# Determine Map Center and Zoom
if selected_district != "All Districts":
    center = [df_filtered["Latitude"].mean(), df_filtered["Longitude"].mean()]
    zoom = 10
elif selected_state != "All India":
    center = [df_filtered["Latitude"].mean(), df_filtered["Longitude"].mean()]
    zoom = 7
else:
    center = [22.0, 78.0] # Center of India
    zoom = 5

m = folium.Map(location=center, zoom_start=zoom, tiles="CartoDB positron", control_scale=True)
Fullscreen().add_to(m)

# Logic to filter data for the map based on selection
if selected_sectors and not df_filtered.empty:
    df_map = df_filtered.copy()
    df_map["Total_Selected"] = df_map[selected_sectors].sum(axis=1)
    df_map = df_map[df_map["Total_Selected"] > 0] # Only show locations with data

    # ---------------------------
    # HEATMAP MODE
    # ---------------------------
    if map_mode == "Density Heatmap":
        # Prepare data: Lat, Lon, Intensity (Total of selected sectors)
        heat_data = df_map[["Latitude", "Longitude", "Total_Selected"]].values.tolist()
        HeatMap(
            heat_data, 
            radius=20, 
            blur=15, 
            min_opacity=0.3,
            gradient={0.4: 'blue', 0.65: 'lime', 1: 'red'}
        ).add_to(m)
        
        # Add a simple legend for context
        legend_html = '''
             <div style="position: fixed; bottom: 50px; left: 50px; z-index:9999; font-size:14px;
             background-color: white; padding: 10px; border-radius: 5px; border: 1px solid grey;">
             <b>Heatmap Intensity</b><br>
             aggregated volume of selected sectors
             </div>
        '''
        m.get_root().html.add_child(folium.Element(legend_html))

    # ---------------------------
    # DETAILED MARKERS MODE
    # ---------------------------
    else:
        max_val = df_map["Total_Selected"].max() if not df_map.empty else 1
        
        for idx, row in df_map.iterrows():
            # Find the dominant sector for this specific point to color-code it
            row_sectors = row[selected_sectors]
            dominant_sector = row_sectors.idxmax()
            dominant_val = row_sectors.max()
            
            # Dynamic radius based on volume
            radius = 5 + (dominant_val / max_val) * 15

            # Detailed HTML Popup
            tooltip_html = f"""
                <div style="font-family: sans-serif; min-width: 150px;">
                    <h4 style="margin:0;">{row['District']}</h4>
                    <small style="color:gray;">{row['State']}</small>
                    <hr style="margin: 5px 0;">
                    <b>Dominant:</b> {dominant_sector}<br>
                    <b>Total Selected:</b> {int(row['Total_Selected'])}<br>
                    <div style="margin-top:5px; max-height:100px; overflow-y:auto;">
            """
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
                tooltip=f"{row['District']}: {int(row['Total_Selected'])} units"
            ).add_to(m)

        # ---------------------------
        # CUSTOM LEGEND
        # ---------------------------
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
    # Fallback if no data/sectors selected
    st.info("👈 Please select at least one sector from the sidebar to visualize data.")

# Render the Map
st_folium(m, height=600, use_container_width=True)

# =====================================================
# DATA EXPORT
# =====================================================
with st.expander("📊 View & Download Data", expanded=False):
    if selected_sectors and not df_filtered.empty:
        # Prepare export frame
        cols_to_show = ["State", "District"] + selected_sectors
        export_df = df_filtered[cols_to_show].copy()
        
        # Add total column for convenience
        export_df["Total_Selected"] = export_df[selected_sectors].sum(axis=1)
        export_df = export_df[export_df["Total_Selected"] > 0].sort_values("Total_Selected", ascending=False)
        
        st.dataframe(export_df, use_container_width=True)
        
        # CSV Download
        csv = export_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download Filtered Data as CSV",
            data=csv,
            file_name=f"manufacturing_data_{selected_state}_{selected_district}.csv",
            mime="text/csv",
        )
    else:
        st.write("No data available for the current selection.")
