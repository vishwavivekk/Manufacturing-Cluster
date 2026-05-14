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

def count_nearby_locations(df_map, row_lat, row_lon, radius_km):
    """Count how many locations (other than self) fall within radius_km."""
    count = 0
    for _, other in df_map.iterrows():
        dist = haversine_distance(row_lat, row_lon, other["Latitude"], other["Longitude"])
        if dist <= radius_km and not (other["Latitude"] == row_lat and other["Longitude"] == row_lon):
            count += 1
    return count

@st.cache_data
def load_data(path: str):
    """Loads and cleans the manufacturing data with sector-subsector structure."""
    if not os.path.exists(path):
        return None, None, None

    try:
        df = pd.read_excel(path, header=[0, 1])
        
        sector_row = df.columns.get_level_values(0)
        subsector_row = df.columns.get_level_values(1)
        
        new_columns = []
        subsector_to_sector = {}
        
        for i, (sector, subsector) in enumerate(zip(sector_row, subsector_row)):
            sector = str(sector).strip()
            subsector = str(subsector).strip()
            
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
                col_name = subsector if subsector != 'nan' and subsector != '' else sector
                new_columns.append(col_name)
                subsector_to_sector[col_name] = sector
        
        df.columns = new_columns
        df.columns = [str(c).strip() for c in df.columns]
        
        required_cols = ["State", "District", "Latitude", "Longitude"]
        if not all(col in df.columns for col in required_cols):
            st.error(f"Data missing required columns: {required_cols}")
            st.error(f"Found columns: {df.columns.tolist()}")
            st.stop()

        df["State"] = df["State"].astype(str).str.strip()
        df["District"] = df["District"].astype(str).str.strip()

        subsector_cols = [col for col in df.columns if col not in ["State", "District", "Latitude", "Longitude"]]
        
        df[subsector_cols] = df[subsector_cols].fillna(0).apply(pd.to_numeric, errors='coerce').fillna(0)
        
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

# 2. Radius Filter (existing anchor-based filter)
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

# =====================================================
# NEW: Neighbourhood Analysis Sliders
# (appear only when a specific sector is selected)
# =====================================================
enable_neighbourhood = False
min_units_threshold = 1
neighbourhood_km = 50

if selected_sector != "All Sectors":
    st.sidebar.markdown("---")
    st.sidebar.subheader("🔍 Neighbourhood Analysis")
    st.sidebar.caption(
        "Filter locations by minimum units, then see how many same-sector "
        "locations are within a given radius of each dot."
    )

    min_units_threshold = st.sidebar.slider(
        "Min Units (show locations with ≥ this many units)",
        min_value=1,
        max_value=500,
        value=1,
        step=1,
        help="Only locations with at least this many units in the selected sector will appear on the map."
    )

    neighbourhood_km = st.sidebar.slider(
        "Nearby KM Radius (count neighbours within this distance)",
        min_value=5,
        max_value=500,
        value=50,
        step=5,
        help="For each visible dot, count how many other same-sector loimport os
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

st.markdown("""
    <style>
    .block-container { padding-top: 2rem; padding-bottom: 2rem; }
    </style>
""", unsafe_allow_html=True)

COLOR_PALETTE = [
    "#E63946", "#1D3557", "#457B9D", "#A8DADC", "#2A9D8F",
    "#F4A261", "#E76F51", "#6A4C93", "#8AC926", "#FFCA3A"
]

NEIGHBOURHOOD_COLOR = "#009688"

SECTOR_SUBSECTOR_MAP = {
    "Crop And Animal Production, Hunting And Related Service Activities": [
        "Support Activities To Agriculture And Post-Harvest Crop Activities"
    ],
    "Other Mining And Quarrying": ["Mining And Quarrying N.E.C."],
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
    "Beverages": ["Beverages"],
    "Tobacco Products": ["Tobacco Products"],
    "Textiles": ["Spinning, Weaving And Finishing Of Textiles", "Other Textiles"],
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
    "Paper And Paper Products": ["Paper And Paper Products"],
    "Printing And Reproduction Of Recorded Media": [
        "Printing And Service Activities Related To Printing",
        "Reproduction Of Recorded Media"
    ],
    "Coke And Refined Petroleum Products": ["Coke Oven Products", "Refined Petroleum Products"],
    "Chemicals And Chemical Products": [
        "Basic Chemicals, Fertilizer And Nitrogen Compounds, Plastics And Synthetic Rubber In Primary Forms",
        "Other Chemical Products",
        "Man-Made Fibres"
    ],
    "Pharmaceuticals, Medicinal Chemical And Botanical Products": [
        "Pharmaceuticals, Medicinal Chemical And Botanical Products"
    ],
    "Rubber And Plastics Products": ["Rubber Products", "Plastics Products"],
    "Other Non-Metallic Mineral Products": ["Glass And Glass Products", "Non-Metallic Mineral Products N.E.C."],
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
    "Machinery And Equipment N.E.C.": ["General Purpose Machinery", "Special-Purpose Machinery"],
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
    "Furniture": ["Furniture"],
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
    "Water Collection, Treatment And Supply": ["Water Collection, Treatment And Supply"],
    "Sewerage": ["Sewerage"],
    "Waste Collection, Treatment And Disposal Activities": [
        "Waste Collection", "Waste Treatment And Disposal", "Materials Recovery"
    ],
    "Wholesale And Retail Trade And Repair Of Motor Vehicles And Motorcycles": [
        "Maintenance And Repair Of Motor Vehicles",
        "Sale, Maintenance And Repair Of Motorcycles And Related Parts And Accessories"
    ],
    "Warehousing And Support Activities For Transportation": ["Warehousing And Storage"],
    "Publishing Activities": ["Publishing Of Books, Periodicals And Other Publishing Activities"],
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
    "Other Personal Service Activities": ["Other Personal Service Activities"]
}


def haversine_distance(lat1, lon1, lat2, lon2):
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    return 2 * asin(sqrt(a)) * 6371


def get_sector_color(sector: str) -> str:
    hash_val = int(hashlib.md5(sector.encode()).hexdigest(), 16)
    return COLOR_PALETTE[hash_val % len(COLOR_PALETTE)]


def categorize_size(total_units):
    if total_units < 20:   return "Nano (0-20)"
    elif total_units < 50: return "Micro (20-50)"
    elif total_units < 100: return "Small (50-100)"
    elif total_units < 500: return "Medium (100-500)"
    else:                  return "Large (500+)"


@st.cache_data
def load_data(path: str):
    if not os.path.exists(path):
        return None, None, None
    try:
        df = pd.read_excel(path, header=[0, 1])
        sector_row = df.columns.get_level_values(0)
        subsector_row = df.columns.get_level_values(1)

        new_columns = []
        subsector_to_sector = {}

        for i, (sector, subsector) in enumerate(zip(sector_row, subsector_row)):
            sector = str(sector).strip()
            subsector = str(subsector).strip()
            if i < 4:
                if 'State' in sector or 'State' in subsector:      new_columns.append('State')
                elif 'District' in sector or 'District' in subsector: new_columns.append('District')
                elif 'Latitude' in sector or 'Latitude' in subsector: new_columns.append('Latitude')
                elif 'Longitude' in sector or 'Longitude' in subsector: new_columns.append('Longitude')
                else: new_columns.append(sector if sector != 'nan' else subsector)
            else:
                col_name = subsector if subsector != 'nan' and subsector != '' else sector
                new_columns.append(col_name)
                subsector_to_sector[col_name] = sector

        df.columns = [str(c).strip() for c in new_columns]
        required_cols = ["State", "District", "Latitude", "Longitude"]
        if not all(col in df.columns for col in required_cols):
            st.error(f"Data missing required columns.")
            st.stop()

        df["State"]    = df["State"].astype(str).str.strip()
        df["District"] = df["District"].astype(str).str.strip()
        subsector_cols = [c for c in df.columns if c not in required_cols]
        df[subsector_cols] = df[subsector_cols].fillna(0).apply(pd.to_numeric, errors='coerce').fillna(0)
        df = df.dropna(subset=["Latitude", "Longitude"])
        return df, subsector_cols, subsector_to_sector
    except Exception as e:
        st.error(f"Error reading file: {e}")
        import traceback; st.error(traceback.format_exc())
        st.stop()


# =====================================================
# LOAD DATA
# =====================================================
DATA_FILE = os.getenv("DATA_FILE_PATH", "Annexure with 3digit.xlsx")
df, subsector_columns, subsector_to_sector = load_data(DATA_FILE)

if df is None:
    st.warning(f"⚠️ Data file `{DATA_FILE}` not found.")
    st.stop()

# =====================================================
# SIDEBAR
# =====================================================
st.sidebar.title("🌍 Filters")

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
st.sidebar.subheader("📍 Radius Filter")
enable_radius = st.sidebar.checkbox("Enable Distance-Based Filter", value=False)

center_lat = center_lon = center_district = None
radius_km = 50

if enable_radius:
    if selected_state == "India":
        radius_district_options = sorted(df["District"].unique())
    else:
        radius_district_options = sorted(df[df["State"] == selected_state]["District"].unique())
    center_district = st.sidebar.selectbox("Select Center District", options=radius_district_options)
    radius_km = st.sidebar.slider("Radius (km)", min_value=5, max_value=500, value=50, step=5)
    center_district_data = df[df["District"] == center_district]
    if not center_district_data.empty:
        center_lat = center_district_data["Latitude"].mean()
        center_lon = center_district_data["Longitude"].mean()
        df_filtered["Distance_km"] = df_filtered.apply(
            lambda row: haversine_distance(center_lat, center_lon, row["Latitude"], row["Longitude"]), axis=1
        )
        df_filtered = df_filtered[df_filtered["Distance_km"] <= radius_km]
        st.sidebar.info(f"📏 Showing units within {radius_km} km of {center_district}")

st.sidebar.markdown("---")
st.sidebar.subheader("🏭 Industry Sectors & Subsectors")

sector_subsector_available = {}
for sector, subsectors in SECTOR_SUBSECTOR_MAP.items():
    avail = [s for s in subsectors if s in subsector_columns and df_filtered[s].sum() > 0]
    if avail:
        sector_subsector_available[sector] = avail

sector_options = ["All Sectors"] + sorted(sector_subsector_available.keys())
selected_sector = st.sidebar.selectbox("Select Sector", options=sector_options)

if selected_sector == "All Sectors":
    subsector_options = ["All Subsectors"] + sorted(set(
        s for subs in sector_subsector_available.values() for s in subs
    ))
else:
    subsector_options = ["All Subsectors"] + sorted(sector_subsector_available.get(selected_sector, []))

selected_subsector = st.sidebar.selectbox("Select Subsector", options=subsector_options)

if selected_sector == "All Sectors":
    if selected_subsector == "All Subsectors":
        selected_columns = [col for col in subsector_columns if df_filtered[col].sum() > 0]
    else:
        selected_columns = [selected_subsector] if selected_subsector in subsector_columns else []
else:
    if selected_subsector == "All Subsectors":
        selected_columns = sector_subsector_available.get(selected_sector, [])
    else:
        selected_columns = [selected_subsector] if selected_subsector in subsector_columns else []

st.sidebar.markdown("---")
st.sidebar.subheader("📏 Unit Size By Number Of Employees")
size_categories = ["Nano (0-20)", "Micro (20-50)", "Small (50-100)", "Medium (100-500)", "Large (500+)"]
selected_sizes = st.sidebar.multiselect("Filter by Size", options=size_categories, default=size_categories)

st.sidebar.markdown("---")
map_mode = st.sidebar.radio("Visualization Mode", ["Detailed Markers", "Density Heatmap"])

if selected_columns and not df_filtered.empty:
    df_filtered["Total_Units"]    = df_filtered[selected_columns].sum(axis=1)
    df_filtered["Size_Category"]  = df_filtered["Total_Units"].apply(categorize_size)
    if selected_sizes:
        df_filtered = df_filtered[df_filtered["Size_Category"].isin(selected_sizes)]

# =====================================================
# MAIN DASHBOARD
# =====================================================
if enable_radius and center_district:
    cluster_title = f"Manufacturing Units within {radius_km}km of {center_district}"
elif selected_state == "India":
    cluster_title = "India Manufacturing Overview"
elif selected_district == "All Districts":
    cluster_title = f"{selected_state} Manufacturing Overview"
else:
    cluster_title = f"{selected_district} ({selected_state}) Cluster Overview"

st.title(f"🏭 {cluster_title}")

if selected_columns:
    if selected_sector == "All Sectors" and selected_subsector == "All Subsectors":
        st.caption("**View:** All Sectors & Subsectors")
    elif selected_subsector == "All Subsectors":
        st.caption(f"**Sector:** {selected_sector} (All Subsectors)")
    else:
        st.caption(f"**Sector:** {selected_sector} | **Subsector:** {selected_subsector}")

total_units = int(df_filtered[selected_columns].sum().sum()) if selected_columns and not df_filtered.empty else 0
active_locs = len(df_filtered[df_filtered[selected_columns].sum(axis=1) > 0]) if selected_columns and not df_filtered.empty else 0

col1, col2, col3 = st.columns(3)
col1.metric("Selected Region", selected_district if selected_district != "All Districts" else selected_state)
col2.metric("Total Units", f"{total_units:,}" if total_units > 0 else "-")
col3.metric("Active Clusters", active_locs if active_locs > 0 else "-")

st.markdown("---")

# Map centre & zoom
if enable_radius and center_lat is not None:
    map_center = [center_lat, center_lon]; zoom = 9
elif selected_district != "All Districts":
    map_center = [df_filtered["Latitude"].mean(), df_filtered["Longitude"].mean()] if not df_filtered.empty else [22.0, 78.0]; zoom = 10
elif selected_state != "India":
    map_center = [df_filtered["Latitude"].mean(), df_filtered["Longitude"].mean()] if not df_filtered.empty else [22.0, 78.0]; zoom = 7
else:
    map_center = [22.0, 78.0]; zoom = 5

m = folium.Map(location=map_center, zoom_start=zoom, tiles="CartoDB Voyager", control_scale=True)
Fullscreen().add_to(m)

if enable_radius and center_lat is not None:
    folium.Circle(location=[center_lat, center_lon], radius=radius_km*1000,
                  color='blue', fill=True, fillColor='blue', fillOpacity=0.1, weight=2,
                  popup=f"{center_district} - {radius_km}km radius").add_to(m)
    folium.Marker(location=[center_lat, center_lon], popup=f"<b>Center: {center_district}</b>",
                  icon=folium.Icon(color='blue', icon='info-sign')).add_to(m)

if selected_columns and not df_filtered.empty:
    df_map = df_filtered.copy()
    df_map["Total_Selected"] = df_map[selected_columns].sum(axis=1)
    df_map = df_map[df_map["Total_Selected"] > 0]

    if map_mode == "Density Heatmap":
        HeatMap(df_map[["Latitude","Longitude","Total_Selected"]].values.tolist(),
                radius=20, blur=15, min_opacity=0.3,
                gradient={0.4:'blue',0.65:'lime',1:'red'}).add_to(m)
        m.get_root().html.add_child(folium.Element('''
            <div style="position:fixed;bottom:50px;left:50px;z-index:9999;font-size:14px;
            background-color:white;padding:10px;border-radius:5px;border:1px solid grey;">
            <b>Heatmap Intensity</b><br>aggregated volume of selected sectors/subsectors</div>
        '''))
    else:
        max_val = df_map["Total_Selected"].max() or 1
        for _, row in df_map.iterrows():
            row_data = row[selected_columns]
            dominant_item = row_data.idxmax()
            color_key = (
                subsector_to_sector.get(dominant_item, dominant_item)
                if selected_subsector == "All Subsectors"
                else (selected_sector if selected_sector != "All Sectors"
                      else subsector_to_sector.get(dominant_item, dominant_item))
            )
            radius = 5 + (row_data.max() / max_val) * 15
            tip_html = f"""<div style="font-family:sans-serif;min-width:200px;">
                <h4 style="margin:0;">{row['District']}</h4>
                <small style="color:gray;">{row['State']}</small>
                <hr style="margin:5px 0;">
                <b>Size:</b> {row['Size_Category']}<br>
                <b>Dominant:</b> {dominant_item}<br>
                <b>Total Selected:</b> {int(row['Total_Selected'])}<br>
                {'<b>Distance:</b> '+str(round(row["Distance_km"],1))+' km<br>' if enable_radius and 'Distance_km' in row else ''}
                <div style='margin-top:5px;max-height:150px;overflow-y:auto;'>
                {''.join(f"<div style='display:flex;justify-content:space-between;'><span style='font-size:11px;'>{col}:</span> <b>{int(row[col])}</b></div>" for col in selected_columns if row[col]>0)}
                </div></div>"""
            folium.CircleMarker(
                location=[row["Latitude"], row["Longitude"]],
                radius=radius, color=get_sector_color(color_key),
                fill=True, fill_color=get_sector_color(color_key), fill_opacity=0.7, weight=1,
                popup=folium.Popup(tip_html, max_width=350),
                tooltip=f"{row['District']}: {int(row['Total_Selected'])} units ({row['Size_Category']})"
            ).add_to(m)
else:
    st.info("👈 Please select at least one sector or subsector from the sidebar to visualize data.")

st_folium(m, height=600, use_container_width=True)

with st.expander("📊 View & Download Data", expanded=False):
    if selected_columns and not df_filtered.empty:
        cols_to_show = ["State", "District", "Size_Category"] + selected_columns
        if enable_radius and 'Distance_km' in df_filtered.columns:
            cols_to_show.insert(3, "Distance_km")
        export_df = df_filtered[cols_to_show].copy()
        export_df["Total_Selected"] = export_df[selected_columns].sum(axis=1)
        export_df = export_df[export_df["Total_Selected"] > 0].sort_values("Total_Selected", ascending=False)
        st.dataframe(export_df, use_container_width=True)
        st.download_button("📥 Download Filtered Data as CSV",
                           export_df.to_csv(index=False).encode('utf-8'),
                           f"manufacturing_data_{selected_state}_{selected_district}.csv", "text/csv")
    else:
        st.write("No data available for the current selection.")


# =====================================================
#  NEIGHBOURHOOD ANALYSIS  — fully independent section
# =====================================================
st.markdown("---")
st.header("🔍 Neighbourhood Analysis")
st.caption(
    "Independent of all sidebar filters above. "
    "Explore how same-sector manufacturing clusters are spatially distributed across India."
)

# Build sector list from full dataset
na_sector_subsector_available = {}
for sector, subsectors in SECTOR_SUBSECTOR_MAP.items():
    avail = [s for s in subsectors if s in subsector_columns and df[s].sum() > 0]
    if avail:
        na_sector_subsector_available[sector] = avail

na_sector_options = sorted(na_sector_subsector_available.keys())

na_selected_sector = st.selectbox(
    "Select Sector",
    options=["— choose a sector —"] + na_sector_options,
    key="na_sector",
    help="Unit counts are aggregated across all subsectors of this sector."
)

if na_selected_sector == "— choose a sector —":
    st.info("☝️ Select a sector above to begin Neighbourhood Analysis.")
    st.stop()

na_subsector_cols = na_sector_subsector_available[na_selected_sector]

# Base data: entire India, this sector only
na_df = df.copy()
na_df["NA_Sector_Units"] = na_df[na_subsector_cols].sum(axis=1)
na_df = (
    na_df[na_df["NA_Sector_Units"] > 0][["State", "District", "Latitude", "Longitude", "NA_Sector_Units"]]
    .copy()
    .reset_index(drop=True)
)

# ---- SLIDER 1: Min Units ----
st.markdown("#### Slider 1 — Minimum Units Threshold")
enable_min_units = st.checkbox(
    "Activate Min Units filter",
    value=False,
    key="na_enable_min_units",
    help="Only show districts whose unit count in the selected sector meets or exceeds this value."
)

na_min_units = 1
if enable_min_units:
    max_possible = int(na_df["NA_Sector_Units"].max()) if not na_df.empty else 100
    na_min_units = st.slider(
        "Minimum units in sector",
        min_value=1,
        max_value=max(max_possible, 2),
        value=max(1, max_possible // 10),
        step=1,
        key="na_min_units_slider"
    )
    na_df = na_df[na_df["NA_Sector_Units"] >= na_min_units].reset_index(drop=True)

# ---- SLIDER 2: Neighbourhood Radius ----
st.markdown("#### Slider 2 — Neighbourhood Radius")
enable_radius_na = st.checkbox(
    "Activate Neighbourhood Radius",
    value=False,
    key="na_enable_radius",
    help="For every visible district, count how many other same-sector districts lie within this radius."
)

na_radius_km = 100
if enable_radius_na:
    na_radius_km = st.slider(
        "Neighbourhood radius (km)",
        min_value=10,
        max_value=500,
        value=100,
        step=10,
        key="na_radius_slider"
    )

# Compute neighbour counts
if enable_radius_na and not na_df.empty:
    lats = na_df["Latitude"].values
    lons = na_df["Longitude"].values
    na_df["Neighbours_In_Radius"] = [
        sum(1 for j in range(len(na_df))
            if j != i and haversine_distance(lats[i], lons[i], lats[j], lons[j]) <= na_radius_km)
        for i in range(len(na_df))
    ]
else:
    na_df["Neighbours_In_Radius"] = None

# KPIs
st.markdown("---")
kc1, kc2, kc3, kc4 = st.columns(4)
kc1.metric("Sector", (na_selected_sector[:38] + "…") if len(na_selected_sector) > 40 else na_selected_sector)
kc2.metric("Districts Visible", len(na_df))
kc3.metric("Total Sector Units", f"{int(na_df['NA_Sector_Units'].sum()):,}" if not na_df.empty else "—")

if enable_radius_na and not na_df.empty:
    kc4.metric("Avg Neighbours / District", f"{na_df['Neighbours_In_Radius'].mean():.1f}")
else:
    kc4.metric("Avg Neighbours / District", "—")

# Map
if na_df.empty:
    st.warning("No districts match the current Neighbourhood Analysis settings.")
else:
    na_center = [na_df["Latitude"].mean(), na_df["Longitude"].mean()]
    na_map = folium.Map(location=na_center, zoom_start=5, tiles="CartoDB Voyager", control_scale=True)
    Fullscreen().add_to(na_map)

    max_units_na = na_df["NA_Sector_Units"].max() or 1

    for _, row in na_df.iterrows():
        bubble_r = 5 + (row["NA_Sector_Units"] / max_units_na) * 18

        if enable_radius_na:
            nb = int(row["Neighbours_In_Radius"])
            tooltip_text = (
                f"{row['District']}, {row['State']} "
                f"| Units: {int(row['NA_Sector_Units'])} "
                f"| Neighbours ({na_radius_km} km): {nb}"
            )
            popup_html = (
                f"<div style='font-family:sans-serif;min-width:180px;'>"
                f"<h4 style='margin:0;color:#009688;'>{row['District']}</h4>"
                f"<small style='color:gray;'>{row['State']}</small>"
                f"<hr style='margin:5px 0;'>"
                f"<b>Sector Units:</b> {int(row['NA_Sector_Units'])}<br>"
                f"<b>Neighbours ({na_radius_km} km):</b> {nb}"
                f"</div>"
            )
        else:
            tooltip_text = f"{row['District']}, {row['State']} | Units: {int(row['NA_Sector_Units'])}"
            popup_html = (
                f"<div style='font-family:sans-serif;min-width:180px;'>"
                f"<h4 style='margin:0;color:#009688;'>{row['District']}</h4>"
                f"<small style='color:gray;'>{row['State']}</small>"
                f"<hr style='margin:5px 0;'>"
                f"<b>Sector Units:</b> {int(row['NA_Sector_Units'])}"
                f"</div>"
            )

        folium.CircleMarker(
            location=[row["Latitude"], row["Longitude"]],
            radius=bubble_r,
            color=NEIGHBOURHOOD_COLOR,
            fill=True, fill_color=NEIGHBOURHOOD_COLOR, fill_opacity=0.72, weight=1.5,
            popup=folium.Popup(popup_html, max_width=280),
            tooltip=tooltip_text
        ).add_to(na_map)

    st_folium(na_map, height=580, use_container_width=True, key="na_map")

    # Data table + download
    with st.expander("📊 View & Download Neighbourhood Data", expanded=False):
        display_cols = ["State", "District", "NA_Sector_Units"]
        if enable_radius_na:
            display_cols.append("Neighbours_In_Radius")

        na_export = na_df[display_cols].rename(columns={
            "NA_Sector_Units": f"{na_selected_sector[:30]} — Units",
            "Neighbours_In_Radius": f"Neighbours (within {na_radius_km} km)"
        })
        sort_col = f"Neighbours (within {na_radius_km} km)" if enable_radius_na else f"{na_selected_sector[:30]} — Units"
        na_export = na_export.sort_values(sort_col, ascending=False)

        st.dataframe(na_export, use_container_width=True)
        st.download_button(
            label="📥 Download Neighbourhood Data as CSV",
            data=na_export.to_csv(index=False).encode("utf-8"),
            file_name=f"neighbourhood_{na_selected_sector[:30].replace(' ','_')}.csv",
            mime="text/csv",
            key="na_download"
        )cations fall within this radius. The count is shown on the circle."
    )

    enable_neighbourhood = True

st.sidebar.markdown("---")

# Determine which columns to use based on selection
if selected_sector == "All Sectors":
    if selected_subsector == "All Subsectors":
        selected_columns = [col for col in subsector_columns if df_filtered[col].sum() > 0]
        selected_sectors = list(sector_subsector_available.keys())
    else:
        selected_columns = [selected_subsector] if selected_subsector in subsector_columns else []
        selected_sectors = [subsector_to_sector.get(selected_subsector, "Unknown")]
else:
    if selected_subsector == "All Subsectors":
        selected_columns = sector_subsector_available.get(selected_sector, [])
        selected_sectors = [selected_sector]
    else:
        selected_columns = [selected_subsector] if selected_subsector in subsector_columns else []
        selected_sectors = [selected_sector]

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

if enable_radius and 'center_lat' in locals():
    cluster_title = f"Manufacturing Units within {radius_km}km of {center_district}"
elif selected_state == "India":
    cluster_title = "India Manufacturing Overview"
elif selected_district == "All Districts":
    cluster_title = f"{selected_state} Manufacturing Overview"
else:
    cluster_title = f"{selected_district} ({selected_state}) Cluster Overview"

st.title(f"🏭 {cluster_title}")

if selected_columns:
    if selected_sector == "All Sectors" and selected_subsector == "All Subsectors":
        filter_info = f"**View:** All Sectors & Subsectors"
    elif selected_subsector == "All Subsectors":
        filter_info = f"**Sector:** {selected_sector} (All Subsectors)"
    else:
        filter_info = f"**Sector:** {selected_sector} | **Subsector:** {selected_subsector}"
    st.caption(filter_info)

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

    # ── Apply Min Units threshold when neighbourhood analysis is active ──
    if enable_neighbourhood:
        df_map = df_map[df_map["Total_Selected"] >= min_units_threshold]

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

        # Pre-compute neighbour counts for every visible row (vectorised distance loop)
        if enable_neighbourhood and not df_map.empty:
            lats = df_map["Latitude"].values
            lons = df_map["Longitude"].values

            neighbour_counts = []
            for i in range(len(df_map)):
                cnt = 0
                for j in range(len(df_map)):
                    if i != j:
                        d = haversine_distance(lats[i], lons[i], lats[j], lons[j])
                        if d <= neighbourhood_km:
                            cnt += 1
                neighbour_counts.append(cnt)
            df_map = df_map.copy()
            df_map["Neighbour_Count"] = neighbour_counts

        for idx, row in df_map.iterrows():
            row_data = row[selected_columns]
            dominant_item = row_data.idxmax()
            dominant_val = row_data.max()
            
            if selected_subsector == "All Subsectors":
                color_key = subsector_to_sector.get(dominant_item, dominant_item)
            else:
                color_key = selected_sector if selected_sector != "All Sectors" else subsector_to_sector.get(dominant_item, dominant_item)
            
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

            # ── Neighbourhood count line in popup ──
            if enable_neighbourhood:
                nb = int(row.get("Neighbour_Count", 0))
                tooltip_html += f"<b>Nearby Locations (≤{neighbourhood_km} km):</b> {nb}<br>"
            
            tooltip_html += "<div style='margin-top:5px; max-height:150px; overflow-y:auto;'>"
            for col in selected_columns:
                val = row[col]
                if val > 0:
                    tooltip_html += f"<div style='display:flex; justify-content:space-between;'><span style='font-size:11px;'>{col}:</span> <b>{int(val)}</b></div>"
            tooltip_html += "</div></div>"

            marker_color = get_sector_color(color_key)

            # ── When neighbourhood mode is on, show neighbour count on circle ──
            if enable_neighbourhood:
                nb = int(row.get("Neighbour_Count", 0))

                # Outer CircleMarker (coloured ring)
                folium.CircleMarker(
                    location=[row["Latitude"], row["Longitude"]],
                    radius=radius,
                    color=marker_color,
                    fill=True,
                    fill_color=marker_color,
                    fill_opacity=0.55,
                    weight=2,
                    popup=folium.Popup(tooltip_html, max_width=350),
                    tooltip=f"{row['District']}: {int(row['Total_Selected'])} units | {nb} nearby (≤{neighbourhood_km} km)"
                ).add_to(m)

                # Count label via DivIcon placed at same lat/lon
                label_html = f"""
                    <div style="
                        background: {marker_color};
                        color: #fff;
                        font-size: 10px;
                        font-weight: bold;
                        font-family: sans-serif;
                        border-radius: 50%;
                        width: 22px;
                        height: 22px;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        border: 2px solid rgba(255,255,255,0.8);
                        box-shadow: 0 1px 4px rgba(0,0,0,0.4);
                        transform: translate(-50%, -50%);
                    ">{nb}</div>
                """
                folium.Marker(
                    location=[row["Latitude"], row["Longitude"]],
                    icon=folium.DivIcon(
                        html=label_html,
                        icon_size=(22, 22),
                        icon_anchor=(11, 11),
                    ),
                    popup=folium.Popup(tooltip_html, max_width=350),
                ).add_to(m)

            else:
                # Standard marker (original behaviour)
                folium.CircleMarker(
                    location=[row["Latitude"], row["Longitude"]],
                    radius=radius,
                    color=marker_color,
                    fill=True,
                    fill_color=marker_color,
                    fill_opacity=0.7,
                    weight=1,
                    popup=folium.Popup(tooltip_html, max_width=350),
                    tooltip=f"{row['District']}: {int(row['Total_Selected'])} units ({row['Size_Category']})"
                ).add_to(m)

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
