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
        # Read Excel with multi-row header (sector in row 0, subsector in row 1)
        df = pd.read_excel(path, header=[0, 1])
        
        # Extract sector and subsector names
        sector_row = df.columns.get_level_values(0)
        subsector_row = df.columns.get_level_values(1)
        
        # Create new column names - use subsector name as primary, keep sector for mapping
        new_columns = []
        subsector_to_sector = {}
        
        for i, (sector, subsector) in enumerate(zip(sector_row, subsector_row)):
            sector = str(sector).strip()
            subsector = str(subsector).strip()
            
            # For the first 4 columns (State, District, Lat, Lon)
            if i < 4:
                if 'State' in sector or 'State' in subsector:
                    new_columns.append('State')
                elif 'District' in sector or 'District' in subsector:
                    new_columns.append('District')
                elif 'Latitude' in sector or 'Latitude' in subsector:
                    new_columns.append('Latitude')
                elif 'Longitude' in sector or 'Longitude' in subsector:
                    new_columns.append('Longitude')
                else:
                    new_columns.append(sector if sector != 'nan' else subsector)
            else:
                # For manufacturing columns, use subsector name
                col_name = subsector if subsector != 'nan' and subsector != '' else sector
                new_columns.append(col_name)
                subsector_to_sector[col_name] = sector
        
        # Apply new column names
        df.columns = new_columns
        
        # Standardize column names
        df.columns = [str(c).strip() for c in df.columns]
        
        required_cols = ["State", "District", "Latitude", "Longitude"]
        if not all(col in df.columns for col in required_cols):
            st.error(f"Data missing required columns: {required_cols}")
            st.error(f"Found columns: {df.columns.tolist()}")
            st.stop()

        df["State"] = df["State"].astype(str).str.strip()
        df["District"] = df["District"].astype(str).str.strip()

        # Get all subsector columns (everything after Longitude)
        subsector_cols = [col for col in df.columns if col not in ["State", "District", "Latitude", "Longitude"]]
        
        # Fill NaNs and ensure numeric types
        df[subsector_cols] = df[subsector_cols].fillna(0).apply(pd.to_numeric, errors='coerce').fillna(0)
        
        # Drop rows without geo-coordinates
        df = df.dropna(subset=["Latitude", "Longitude"])
        
        return df, subsector_cols, subsector_to_sector
    except Exception as e:
        st.error(f"Error reading file: {e}")
        import traceback
        st.error(traceback.format_exc())
        st.stop()

# =====================================================
# DATA LOADING
# =====================================================
DATA_FILE = os.getenv("DATA_FILE_PATH", "Annexure with 3digit.xlsx")
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

# Build sector options with subsector counts
sector_subsector_available = {}
for sector, subsectors in SECTOR_SUBSECTOR_MAP.items():
    available_subsectors = []
    for subsector in subsectors:
        if subsector in subsector_columns and df_filtered[subsector].sum() > 0:
            available_subsectors.append(subsector)
    if available_subsectors:
        sector_subsector_available[sector] = available_subsectors

# Sector Selection
sector_options = ["All Sectors"] + sorted(sector_subsector_available.keys())
selected_sector = st.sidebar.selectbox(
    "Select Sector",
    options=sector_options,
    help="Choose a main industry sector"
)

# Subsector Selection based on selected sector
if selected_sector == "All Sectors":
    subsector_options = ["All Subsectors"]
    # Get all available subsectors across all sectors
    all_subsectors = []
    for subsectors in sector_subsector_available.values():
        all_subsectors.extend(subsectors)
    subsector_options.extend(sorted(set(all_subsectors)))
else:
    subsector_options = ["All Subsectors"] + sorted(sector_subsector_available.get(selected_sector, []))

selected_subsector = st.sidebar.selectbox(
    "Select Subsector",
    options=subsector_options,
    help="Choose a specific subsector (or All to aggregate)"
)

# Determine which columns to use based on selection
if selected_sector == "All Sectors":
    if selected_subsector == "All Subsectors":
        # Show all available subsectors
        selected_columns = [col for col in subsector_columns if df_filtered[col].sum() > 0]
        selected_sectors = list(sector_subsector_available.keys())
    else:
        # Show specific subsector across all sectors
        selected_columns = [selected_subsector] if selected_subsector in subsector_columns else []
        selected_sectors = [subsector_to_sector.get(selected_subsector, "Unknown")]
else:
    if selected_subsector == "All Subsectors":
        # Show all subsectors within the selected sector
        selected_columns = sector_subsector_available.get(selected_sector, [])
        selected_sectors = [selected_sector]
    else:
        # Show specific subsector
        selected_columns = [selected_subsector] if selected_subsector in subsector_columns else []
        selected_sectors = [selected_sector]

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
if selected_columns:
    if selected_sector == "All Sectors" and selected_subsector == "All Subsectors":
        filter_info = f"**View:** All Sectors & Subsectors"
    elif selected_subsector == "All Subsectors":
        filter_info = f"**Sector:** {selected_sector} (All Subsectors)"
    else:
        filter_info = f"**Sector:** {selected_sector} | **Subsector:** {selected_subsector}"
    st.caption(filter_info)

# 1. Key Metrics Row
if selected_columns and not df_filtered.empty:
    total_units = df_filtered[selected_columns].sum().sum()
    active_locs = len(df_filtered[df_filtered[selected_columns].sum(axis=1) > 0])
else:
    total_units = 0
    active_locs = 0

col1, col2, col3 = st.columns(3)
col1.metric("Selected Region", selected_district if selected_district != "All Districts" else selected_state)
col2.metric("Total Units", f"{int(total_units):,}" if total_units > 0 else "-")
col3.metric("Active Clusters", active_locs if active_locs > 0 else "-")

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

# =====================================================
# START INDUSTRIAL CORRIDOR OVERLAY
# =====================================================

# 1. Define Coordinates (Major Nodes approximation)
CORRIDOR_DATA = {
    "Amritsar Kolkata Industrial Corridor (AKIC)": [
        (31.6340, 74.8723), # Amritsar
        (30.9010, 75.8573), # Ludhiana
        (30.3782, 76.7767), # Ambala
        (28.6139, 77.2090), # New Delhi
        (27.8974, 78.0880), # Aligarh
        (26.4499, 80.3319), # Kanpur
        (25.4358, 81.8463), # Prayagraj
        (25.3176, 82.9739), # Varanasi
        (24.7914, 85.0002), # Gaya
        (23.7957, 86.4304), # Dhanbad
        (22.5726, 88.3639)  # Kolkata
    ],
    "Bengaluru Mumbai Industrial Corridor (BMIC)": [
        (19.0760, 72.8777), # Mumbai
        (18.5204, 73.8567), # Pune
        (16
