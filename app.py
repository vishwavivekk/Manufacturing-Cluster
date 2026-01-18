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
    .stActionButton {visibility: hidden;}
    button[kind="header"] {visibility: hidden;}
    [data-testid="stHeaderActionElements"] {visibility: hidden;}
    </style>
"""

st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# =====================================================
# CONFIGURATION & STYLING
# =====================================================

st.markdown("""
    <style>
    .block-container { padding-top: 2rem; padding-bottom: 2rem; }
    </style>
""", unsafe_allow_html=True)

COLOR_PALETTE = [
    "#E63946", "#1D3557", "#457B9D", "#A8DADC", "#2A9D8F",
    "#F4A261", "#E76F51", "#6A4C93", "#8AC926", "#FFCA3A"
]

# =====================================================
# SECTOR-SUBSECTOR MAPPING
# =====================================================
SECTOR_SUBSECTOR_MAP = {
    "Crop And Animal Production, Hunting And Related Service Activities": [
        "Support Activities To Agriculture And Post-Harvest Crop Activities"
    ],
    "Other Mining And Quarrying": [
        "Mining And Quarrying N.E.C."
    ],
    "Food Products": [
        "Processing And Preserving Of Meat",
        "Processing And Preserving Of Fish, Crustaceans And Molluscs",
        "Processing And Preserving Of Fruit And Vegetables",
        "Vegetable And Animal Oils And Fats",
        "Dairy Products",
        "Grain Mill Products, Starches And Starch Products",
        "Other Food Products",
        "Prepared Animal Feeds"
    ],
    "Beverages": [
        "Beverages"
    ],
    "Tobacco Products": [
        "Tobacco Products"
    ],
    "Textiles": [
        "Spinning, Weaving And Finishing Of Textiles",
        "Other Textiles"
    ],
    "Wearing Apparel": [
        "Wearing Apparel, Except Fur Apparel",
        "Articles Of Fur",
        "Knitted And Crocheted Apparel"
    ],
    "Leather And Related Products": [
        "Tanning And Dressing Of Leather; Luggage, Handbags, Saddlery And Harness; Dressing And Dyeing Of Fur",
        "Footwear"
    ],
    "Wood And Products Of Wood And Cork": [
        "Sawmilling And Planing Of Wood",
        "Products Of Wood, Cork, Straw And Plaiting Materials"
    ],
    "Paper And Paper Products": [
        "Paper And Paper Products"
    ],
    "Printing And Reproduction Of Recorded Media": [
        "Printing And Service Activities Related To Printing",
        "Reproduction Of Recorded Media"
    ],
    "Coke And Refined Petroleum Products": [
        "Coke Oven Products",
        "Refined Petroleum Products"
    ],
    "Chemicals And Chemical Products": [
        "Basic Chemicals, Fertilizer And Nitrogen Compounds, Plastics And Synthetic Rubber In Primary Forms",
        "Other Chemical Products",
        "Man-Made Fibres"
    ],
    "Pharmaceuticals, Medicinal Chemical And Botanical Products": [
        "Pharmaceuticals, Medicinal Chemical And Botanical Products"
    ],
    "Rubber And Plastics Products": [
        "Rubber Products",
        "Plastics Products"
    ],
    "Other Non-Metallic Mineral Products": [
        "Glass And Glass Products",
        "Non-Metallic Mineral Products N.E.C."
    ],
    "Basic Metals": [
        "Basic Iron And Steel",
        "Basic Precious And Other Non-Ferrous Metals",
        "Casting Of Metals"
    ],
    "Fabricated Metal Products": [
        "Structural Metal Products, Tanks, Reservoirs And Steam Generators",
        "Weapons And Ammunition",
        "Other Fabricated Metal Products; Metalworking Service Activities"
    ],
    "Computer, Electronic And Optical Products": [
        "Electronic Components",
        "Computers And Peripheral Equipment",
        "Communication Equipment",
        "Consumer Electronics",
        "Measuring, Testing, Navigating And Control Equipment; Watches And Clocks",
        "Irradiation, Electromedical And Electrotherapeutic Equipment",
        "Optical Instruments And Equipment",
        "Magnetic And Optical Media"
    ],
    "Electrical Equipment": [
        "Electric Motors, Generators, Transformers And Electricity Distribution And Control Apparatus",
        "Batteries And Accumulators",
        "Wiring And Wiring Devices",
        "Electric Lighting Equipment",
        "Domestic Appliances",
        "Other Electrical Equipment"
    ],
    "Machinery And Equipment N.E.C.": [
        "General Purpose Machinery",
        "Special-Purpose Machinery"
    ],
    "Motor Vehicles, Trailers And Semi-Trailers": [
        "Motor Vehicles",
        "Bodies (Coachwork) For Motor Vehicles; Trailers And Semi-Trailers",
        "Parts And Accessories For Motor Vehicles"
    ],
    "Other Transport Equipment": [
        "Building Of Ships And Boats",
        "Railway Locomotives And Rolling Stock",
        "Air And Spacecraft And Related Machinery",
        "Military Fighting Vehicles",
        "Transport Equipment N.E.C."
    ],
    "Furniture": [
        "Furniture"
    ],
    "Other Manufacturing": [
        "Jewellery, Bijouterie And Related Articles",
        "Musical Instruments",
        "Sports Goods",
        "Games And Toys",
        "Medical And Dental Instruments And Supplies",
        "Other Manufacturing N.E.C."
    ],
    "Repair And Installation Of Machinery And Equipment": [
        "Repair Of Fabricated Metal Products, Machinery And Equipment",
        "Installation Of Industrial Machinery And Equipment"
    ],
    "Electricity, Gas, Steam And Air Conditioning Supply": [
        "Electric Power Generation, Transmission And Distribution",
        "Gas; Distribution Of Gaseous Fuels Through Mains",
        "Steam And Air Conditioning Supply"
    ],
    "Water Collection, Treatment And Supply": [
        "Water Collection, Treatment And Supply"
    ],
    "Sewerage": [
        "Sewerage"
    ],
    "Waste Collection, Treatment And Disposal Activities": [
        "Waste Collection",
        "Waste Treatment And Disposal",
        "Materials Recovery"
    ],
    "Wholesale And Retail Trade And Repair Of Motor Vehicles And Motorcycles": [
        "Maintenance And Repair Of Motor Vehicles",
        "Sale, Maintenance And Repair Of Motorcycles And Related Parts And Accessories"
    ],
    "Warehousing And Support Activities For Transportation": [
        "Warehousing And Storage"
    ],
    "Publishing Activities": [
        "Publishing Of Books, Periodicals And Other Publishing Activities"
    ],
    "Motion Picture, Video And Television Programme Production": [
        "Motion Picture, Video And Television Programme Activities",
        "Sound Recording And Music Publishing Activities"
    ],
    "Other Professional, Scientific And Technical Activities": [
        "Photographic Activities",
        "Business Support Service Activities N.E.C."
    ],
    "Office Administrative, Office Support And Other Business Support Activities": [
        "Business Support Service Activities N.E.C."
    ],
    "Repair Of Computers And Personal And Household Goods": [
        "Repair Of Computers And Communication Equipment",
        "Repair Of Personal And Household Goods"
    ],
    "Other Personal Service Activities": [
        "Other Personal Service Activities"
    ]
}

# =====================================================
# UTILITY FUNCTIONS
# =====================================================
def haversine_distance(lat1, lon1, lat2, lon2):
    """Calculate the great circle distance in kilometers between two points"""
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
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
    """Loads and cleans the manufacturing data with sector-subsector structure."""
    if not os.path.exists(path):
        return None, None, None

    try:
        df = pd.read_excel(path)
        df.columns = [str(c).strip() for c in df.columns]

        required_cols = ["State/UT Name", "District Name", "Latitude", "Longitude"]
        if not all(col in df.columns for col in required_cols):
            st.error(f"Data missing required columns: {required_cols}")
            st.stop()

        df = df.rename(columns={
            "State/UT Name": "State",
            "District Name": "District"
        })

        df["State"] = df["State"].astype(str).str.strip()
        df["District"] = df["District"].astype(str).str.strip()

        # Get all subsector columns (everything after Longitude)
        subsector_cols = [col for col in df.columns if col not in ["State", "District", "Latitude", "Longitude"]]
        
        # Fill NaNs and ensure numeric types
        df[subsector_cols] = df[subsector_cols].fillna(0).apply(pd.to_numeric, errors='coerce').fillna(0)
        
        # Drop rows without geo-coordinates
        df = df.dropna(subset=["Latitude", "Longitude"])
        
        # Create a mapping of subsector to sector
        subsector_to_sector = {}
        for sector, subsectors in SECTOR_SUBSECTOR_MAP.items():
            for subsector in subsectors:
                subsector_to_sector[subsector] = sector
        
        return df, subsector_cols, subsector_to_sector
    except Exception as e:
        st.error(f"Error reading file: {e}")
        st.stop()

# =====================================================
# DATA LOADING
# =====================================================
DATA_FILE = os.getenv("DATA_FILE_PATH", "MOSPI DATA.xlsx")
df, subsector_columns, subsector_to_sector = load_data(DATA_FILE)

if df is None:
    st.warning(f"⚠️ Data file `{DATA_FILE}` not found. Please place it in the root directory.")
    st.info("Expecting columns: State/UT Name, District Name, Latitude, Longitude, and subsector data columns.")
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

# 2. Radius Filter
st.sidebar.subheader("📍 Radius Filter")
enable_radius = st.sidebar.checkbox("Enable Distance-Based Filter", value=False)

if enable_radius:
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
    
    center_district_data = df[df["District"] == center_district]
    if not center_district_data.empty:
        center_lat = center_district_data["Latitude"].mean()
        center_lon = center_district_data["Longitude"].mean()
        
        df_filtered["Distance_km"] = df_filtered.apply(
            lambda row: haversine_distance(center_lat, center_lon, row["Latitude"], row["Longitude"]),
            axis=1
        )
        
        df_filtered = df_filtered[df_filtered["Distance_km"] <= radius_km]
        st.sidebar.info(f"📏 Showing units within {radius_km} km of {center_district}")
    else:
        st.sidebar.warning("⚠️ Center district not found in data")

st.sidebar.markdown("---")

# 3. Sector-Subsector Filters
st.sidebar.subheader("🏭 Industry Sectors & Subsectors")

filter_mode = st.sidebar.radio(
    "Filter By:",
    ["Sectors (Aggregated)", "Subsectors (Detailed)"],
    help="Choose to filter by main sectors or detailed subsectors"
)

if filter_mode == "Sectors (Aggregated)":
    # Get active sectors based on subsector data
    active_sectors = []
    for sector, subsectors in SECTOR_SUBSECTOR_MAP.items():
        sector_total = 0
        for subsector in subsectors:
            if subsector in subsector_columns:
                sector_total += df_filtered[subsector].sum()
        if sector_total > 0:
            active_sectors.append(sector)
    
    selected_sectors = st.sidebar.multiselect(
        "Choose Sectors",
        options=sorted(active_sectors),
        default=sorted(active_sectors)[:1] if active_sectors else [],
        help="Select main sectors - data will be aggregated from subsectors"
    )
    
    # Get all subsectors for selected sectors
    selected_columns = []
    for sector in selected_sectors:
        for subsector in SECTOR_SUBSECTOR_MAP.get(sector, []):
            if subsector in subsector_columns:
                selected_columns.append(subsector)

else:  # Subsectors (Detailed)
    # Get active subsectors
    if not df_filtered.empty:
        current_subsector_sums = df_filtered[subsector_columns].sum()
        active_subsectors = current_subsector_sums[current_subsector_sums > 0].index.tolist()
    else:
        active_subsectors = []
    
    selected_columns = st.sidebar.multiselect(
        "Choose Subsectors",
        options=sorted(active_subsectors),
        default=sorted(active_subsectors)[:1] if active_subsectors else [],
        help="Select specific subsectors for detailed analysis"
    )
    
    # Determine which sectors are represented
    selected_sectors = list(set([subsector_to_sector.get(col, "Unknown") for col in selected_columns]))

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
if selected_columns and not df_filtered.empty:
    df_filtered["Total_Units"] = df_filtered[selected_columns].sum(axis=1)
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

# Display filter mode info
if selected_sectors:
    filter_info = f"**View Mode:** {filter_mode} | **Selected:** {', '.join(selected_sectors[:3])}"
    if len(selected_sectors) > 3:
        filter_info += f" + {len(selected_sectors) - 3} more"
    st.caption(filter_info)

# 1. Key Metrics Row
if selected_columns and not df_filtered.empty:
    total_units = df_filtered[selected_columns].sum().sum()
    
    district_sums = df_filtered.groupby("District")[selected_columns].sum().sum(axis=1)
    if not district_sums.empty:
        top_district = district_sums.idxmax()
    else:
        top_district = "N/A"
        
    active_locs = len(df_filtered[df_filtered[selected_columns].sum(axis=1) > 0])
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

if enable_radius and 'center_lat' in locals():
    folium.Circle(
        location=[center_lat, center_lon],
        radius=radius_km * 1000,
        color='blue',
        fill=True,
        fillColor='blue',
        fillOpacity=0.1,
        weight=2,
        popup=f"{center_district} - {radius_km}km radius"
    ).add_to(m)
    
    folium.Marker(
        location=[center_lat, center_lon],
        popup=f"<b>Center: {center_district}</b>",
        icon=folium.Icon(color='blue', icon='info-sign')
    ).add_to(m)

if selected_columns and not df_filtered.empty:
    df_map = df_filtered.copy()
    df_map["Total_Selected"] = df_map[selected_columns].sum(axis=1)
    df_map = df_map[df_map["Total_Selected"] > 0]

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
             aggregated volume of selected sectors/subsectors
             </div>
        '''
        m.get_root().html.add_child(folium.Element(legend_html))

    else:
        max_val = df_map["Total_Selected"].max() if not df_map.empty else 1
        
        for idx, row in df_map.iterrows():
            row_data = row[selected_columns]
            dominant_item = row_data.idxmax()
            dominant_val = row_data.max()
            
            # Determine sector for coloring
            if filter_mode == "Sectors (Aggregated)":
                color_key = subsector_to_sector.get(dominant_item, dominant_item)
            else:
                color_key = dominant_item
            
            radius = 5 + (dominant_val / max_val) * 15

            tooltip_html = f"""
                <div style="font-family: sans-serif; min-width: 200px;">
                    <h4 style="margin:0;">{row['District']}</h4>
                    <small style="color:gray;">{row['State']}</small>
                    <hr style="margin: 5px 0;">
                    <b>Size:</b> {row['Size_Category']}<br>
                    <b>Dominant:</b> {dominant_item}<br>
                    <b>Total Selected:</b> {int(row['Total_Selected'])}<br>
            """
            
            if enable_radius and 'Distance_km' in row:
                tooltip_html += f"<b>Distance:</b> {row['Distance_km']:.1f} km<br>"
            
            tooltip_html += "<div style='margin-top:5px; max-height:150px; overflow-y:auto;'>"
            
            for col in selected_columns:
                val = row[col]
                if val > 0:
                    tooltip_html += f"<div style='display:flex; justify-content:space-between;'><span style='font-size:11px;'>{col}:</span> <b>{int(val)}</b></div>"
            tooltip_html += "</div></div>"

            folium.CircleMarker(
                location=[row["Latitude"], row["Longitude"]],
                radius=radius,
                color=get_sector_color(color_key),
                fill=True,
                fill_color=get_sector_color(color_key),
                fill_opacity=0.7,
                weight=1,
                popup=folium.Popup(tooltip_html, max_width=350),
                tooltip=f"{row['District']}: {int(row['Total_Selected'])} units ({row['Size_Category']})"
            ).add_to(m)

        # CUSTOM LEGEND
        legend_items = ""
        legend_keys = selected_sectors if filter_mode == "Sectors (Aggregated)" else selected_columns[:10]
        
        for item in legend_keys:
            color = get_sector_color(item)
            display_name = item if len(item) < 40 else item[:37] + "..."
            legend_items += f"""
                <div style='display: flex; align-items: center; margin-bottom: 4px;'>
                    <span style='background:{color}; width:12px; height:12px; border-radius:50%; display:inline-block; margin-right:8px;'></span>
                    <span style='font-size:11px;'>{display_name}</span>
                </div>
            """
        
        if filter_mode == "Subsectors (Detailed)" and len(selected_columns) > 10:
            legend_items += f"<div style='font-size:10px; color:gray; margin-top:5px;'>+ {len(selected_columns) - 10} more subsectors</div>"
        
        legend_html = f"""
        <div style="
            position: fixed; 
            bottom: 20px; left: 20px; width: 250px; max-height: 350px; 
            background-color: rgba(255, 255, 255, 0.95); 
            z-index: 9999; border-radius: 8px; padding: 10px; 
            box-shadow: 0 0 15px rgba(0,0,0,0.1); overflow-y: auto;
            border: 1px solid #ddd;">
            <div style="font-weight: bold; margin-bottom: 5px;">Legend - {filter_mode.split()[0]}</div>
            {legend_items}
        </div>
        """
        m.get_root().html.add_child(folium.Element(legend_html))

else:
    st.info("👈 Please select at least one sector or subsector from the sidebar to visualize data.")

st_folium(m, height=600, use_container_width=True)

# =====================================================
# DATA EXPORT
# =====================================================
with st.expander("📊 View & Download Data", expanded=False):
    if selected_columns and not df_filtered.empty:
        cols_to_show = ["State", "District", "Size_Category"] + selected_columns
        if enable_radius and 'Distance_km' in df_filtered.columns:
            cols_to_show.insert(3, "Distance_km")
        
        export_df = df_filtered[cols_to_show].copy()
        
        export_df["Total_Selected"] = export_df[selected_columns].sum(axis=1)
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
