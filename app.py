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
    "Beverages": ["Beverages"],
    "Tobacco Products": ["Tobacco Products"],
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
    "Paper And Paper Products": ["Paper And Paper Products"],
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
    "Rubber And Plastics Products": ["Rubber Products", "Plastics Products"],
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
        "Waste Collection",
        "Waste Treatment And Disposal",
        "Materials Recovery"
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

# =====================================================
# UTILITY FUNCTIONS
# =====================================================
def haversine_distance(lat1, lon1, lat2, lon2):
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat, dlon = lat2 - lat1, lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    return 2 * asin(sqrt(a)) * 6371

def get_sector_color(sector: str) -> str:
    hash_val = int(hashlib.md5(sector.encode()).hexdigest(), 16)
    return COLOR_PALETTE[hash_val % len(COLOR_PALETTE)]

def categorize_size(total_units):
    if total_units < 20:    return "Nano (0-20)"
    elif total_units < 50:  return "Micro (20-50)"
    elif total_units < 100: return "Small (50-100)"
    elif total_units < 500: return "Medium (100-500)"
    else:                   return "Large (500+)"

@st.cache_data
def load_data(path: str):
    if not os.path.exists(path):
        return None, None, None
    try:
        df = pd.read_excel(path, header=[0, 1])
        sector_row    = df.columns.get_level_values(0)
        subsector_row = df.columns.get_level_values(1)
        new_columns, subsector_to_sector = [], {}

        for i, (sector, subsector) in enumerate(zip(sector_row, subsector_row)):
            sector    = str(sector).strip()
            subsector = str(subsector).strip()
            if i < 4:
                if   'State'     in sector or 'State'     in subsector: new_columns.append('State')
                elif 'District'  in sector or 'District'  in subsector: new_columns.append('District')
                elif 'Latitude'  in sector or 'Latitude'  in subsector: new_columns.append('Latitude')
                elif 'Longitude' in sector or 'Longitude' in subsector: new_columns.append('Longitude')
                else: new_columns.append(sector if sector != 'nan' else subsector)
            else:
                col_name = subsector if subsector not in ('nan', '') else sector
                new_columns.append(col_name)
                subsector_to_sector[col_name] = sector

        df.columns = [str(c).strip() for c in new_columns]
        required = ["State", "District", "Latitude", "Longitude"]
        if not all(c in df.columns for c in required):
            st.error(f"Missing columns: {required}"); st.stop()

        df["State"]    = df["State"].astype(str).str.strip()
        df["District"] = df["District"].astype(str).str.strip()
        sub_cols = [c for c in df.columns if c not in required]
        df[sub_cols] = df[sub_cols].fillna(0).apply(pd.to_numeric, errors='coerce').fillna(0)
        df = df.dropna(subset=["Latitude", "Longitude"])
        return df, sub_cols, subsector_to_sector
    except Exception as e:
        import traceback
        st.error(f"Error: {e}\n{traceback.format_exc()}"); st.stop()

# =====================================================
# DATA LOADING
# =====================================================
DATA_FILE = os.getenv("DATA_FILE_PATH", "Annexure with 3digit.xlsx")
df, subsector_columns, subsector_to_sector = load_data(DATA_FILE)

if df is None:
    st.warning(f"⚠️ Data file `{DATA_FILE}` not found."); st.stop()

# =====================================================
# SIDEBAR
# =====================================================
st.sidebar.title("🌍 Filters")

# ── 1. Geographic ──────────────────────────────────
state_options  = ["India"] + sorted(df["State"].unique())
selected_state = st.sidebar.selectbox("Select State", state_options)

if selected_state == "India":
    df_filtered      = df.copy()
    district_options = ["All Districts"]
else:
    df_filtered      = df[df["State"] == selected_state].copy()
    district_options = ["All Districts"] + sorted(df_filtered["District"].unique())

selected_district = st.sidebar.selectbox("Select District", district_options)
if selected_district != "All Districts":
    df_filtered = df_filtered[df_filtered["District"] == selected_district]

st.sidebar.markdown("---")

# ── 2. Distance-Based Radius Filter (original) ────
st.sidebar.subheader("📍 Radius Filter")
enable_radius = st.sidebar.checkbox("Enable Distance-Based Filter", value=False)
center_lat = center_lon = center_district = radius_km = None

if enable_radius:
    radius_district_options = (
        sorted(df["District"].unique()) if selected_state == "India"
        else sorted(df[df["State"] == selected_state]["District"].unique())
    )
    center_district = st.sidebar.selectbox("Select Center District", options=radius_district_options)
    radius_km = st.sidebar.slider("Radius (km)", 5, 500, 50, 5)
    cdd = df[df["District"] == center_district]
    if not cdd.empty:
        center_lat, center_lon = cdd["Latitude"].mean(), cdd["Longitude"].mean()
        df_filtered["Distance_km"] = df_filtered.apply(
            lambda r: haversine_distance(center_lat, center_lon, r["Latitude"], r["Longitude"]), axis=1
        )
        df_filtered = df_filtered[df_filtered["Distance_km"] <= radius_km]
        st.sidebar.info(f"📏 Within {radius_km} km of {center_district}")
    else:
        st.sidebar.warning("⚠️ Center district not found")

st.sidebar.markdown("---")

# ── 3. Sector / Subsector ─────────────────────────
st.sidebar.subheader("🏭 Industry Sectors & Subsectors")

sector_subsector_available = {
    sector: [s for s in subs if s in subsector_columns and df_filtered[s].sum() > 0]
    for sector, subs in SECTOR_SUBSECTOR_MAP.items()
    if any(s in subsector_columns and df_filtered[s].sum() > 0 for s in subs)
}

sector_options  = ["All Sectors"] + sorted(sector_subsector_available.keys())
selected_sector = st.sidebar.selectbox("Select Sector", sector_options)

if selected_sector == "All Sectors":
    subsector_options = ["All Subsectors"] + sorted(
        set(s for subs in sector_subsector_available.values() for s in subs)
    )
else:
    subsector_options = ["All Subsectors"] + sorted(sector_subsector_available.get(selected_sector, []))

selected_subsector = st.sidebar.selectbox("Select Subsector", subsector_options)

if selected_sector == "All Sectors":
    if selected_subsector == "All Subsectors":
        selected_columns = [c for c in subsector_columns if df_filtered[c].sum() > 0]
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

st.sidebar.markdown("---")

# ── 4. Size Category Multiselect ──────────────────
st.sidebar.subheader("📏 Unit Size By Number Of Employees")
size_categories = ["Nano (0-20)", "Micro (20-50)", "Small (50-100)", "Medium (100-500)", "Large (500+)"]
selected_sizes  = st.sidebar.multiselect("Filter by Size", size_categories, default=size_categories)

st.sidebar.markdown("---")

# ── 5. ★ NEW: Sector Cluster Explorer ─────────────
st.sidebar.subheader("🔍 Sector Cluster Explorer")
st.sidebar.caption(
    "Explore sector clustering independently of the district filter. "
    "Uses all-India data. Anchor = highest-density location in the sector."
)
enable_cluster_explorer = st.sidebar.checkbox("Enable Cluster Explorer", value=False)

# Explorer state — reset defaults
cluster_sector        = None
cluster_unit_min      = 0
cluster_radius_km     = 150
cluster_selected_cols = []
cluster_anchor_lat    = None
cluster_anchor_lon    = None
cluster_df            = pd.DataFrame()
anchor_district       = ""

if enable_cluster_explorer:
    # A) Sector pick
    ce_sector_options = ["— select a sector —"] + sorted(
        {
            sector: [s for s in subs if s in subsector_columns and df[s].sum() > 0]
            for sector, subs in SECTOR_SUBSECTOR_MAP.items()
            if any(s in subsector_columns and df[s].sum() > 0 for s in subs)
        }.keys()
    )
    cluster_sector = st.sidebar.selectbox(
        "Cluster Sector", options=ce_sector_options, key="ce_sector"
    )

    if cluster_sector and cluster_sector != "— select a sector —":
        # All subsectors for this sector, across the full national dataset
        ce_available_cols = [
            s for s in SECTOR_SUBSECTOR_MAP.get(cluster_sector, [])
            if s in subsector_columns and df[s].sum() > 0
        ]

        if ce_available_cols:
            df["_ce_total"] = df[ce_available_cols].sum(axis=1)
            ce_full = df[df["_ce_total"] > 0].copy()

            # Compute dynamic range for the unit slider
            max_units = int(ce_full["_ce_total"].max())

            # B) Unit-size threshold slider ─────────────────
            st.sidebar.markdown("**① Min Unit Count (size threshold)**")
            st.sidebar.caption(
                "Only locations with **at least** this many units in the sector "
                "appear on the map. Slide right to surface larger clusters only."
            )
            cluster_unit_min = st.sidebar.slider(
                "Min units per location",
                min_value=0,
                max_value=max(max_units, 1),
                value=0,
                step=max(1, max_units // 100),
                key="ce_unit_slider",
            )

            # C) KM radius slider ─────────────────────────
            st.sidebar.markdown("**② Cluster Radius (km)**")
            st.sidebar.caption(
                "Draws a dashed ring around the highest-density anchor location. "
                "All same-sector locations inside the ring are highlighted; "
                "outside are shown as grey ghosts."
            )
            cluster_radius_km = st.sidebar.slider(
                "Radius from anchor (km)",
                min_value=10,
                max_value=2000,
                value=150,
                step=10,
                key="ce_radius_slider",
            )

            # Apply unit threshold
            cluster_df = ce_full[ce_full["_ce_total"] >= cluster_unit_min].copy()
            cluster_selected_cols = ce_available_cols

            if not cluster_df.empty:
                anchor_idx         = cluster_df["_ce_total"].idxmax()
                cluster_anchor_lat = cluster_df.loc[anchor_idx, "Latitude"]
                cluster_anchor_lon = cluster_df.loc[anchor_idx, "Longitude"]
                anchor_district    = cluster_df.loc[anchor_idx, "District"]

                cluster_df["_dist_anchor"] = cluster_df.apply(
                    lambda r: haversine_distance(
                        cluster_anchor_lat, cluster_anchor_lon, r["Latitude"], r["Longitude"]
                    ), axis=1
                )
                n_in = int((cluster_df["_dist_anchor"] <= cluster_radius_km).sum())
                st.sidebar.success(
                    f"📌 Anchor: **{anchor_district}**  \n"
                    f"**{n_in}** locations within {cluster_radius_km} km  \n"
                    f"(≥ {cluster_unit_min} units threshold)"
                )
            else:
                st.sidebar.warning("No locations match this unit threshold.")
        else:
            st.sidebar.info("No active data columns found for this sector.")

st.sidebar.markdown("---")
map_mode = st.sidebar.radio("Visualization Mode", ["Detailed Markers", "Density Heatmap"])

# =====================================================
# APPLY SIZE FILTER (main flow)
# =====================================================
if selected_columns and not df_filtered.empty:
    df_filtered["Total_Units"]   = df_filtered[selected_columns].sum(axis=1)
    df_filtered["Size_Category"] = df_filtered["Total_Units"].apply(categorize_size)
    if selected_sizes:
        df_filtered = df_filtered[df_filtered["Size_Category"].isin(selected_sizes)]

# =====================================================
# MAIN CONTENT
# =====================================================
if enable_cluster_explorer and cluster_sector and cluster_sector != "— select a sector —":
    page_title = f"🔍 Cluster Explorer — {cluster_sector}"
elif enable_radius and center_district:
    page_title = f"Manufacturing Units within {radius_km} km of {center_district}"
elif selected_state == "India":
    page_title = "India Manufacturing Overview"
elif selected_district == "All Districts":
    page_title = f"{selected_state} Manufacturing Overview"
else:
    page_title = f"{selected_district} ({selected_state}) Cluster Overview"

st.title(f"🏭 {page_title}")

if enable_cluster_explorer and cluster_sector and cluster_sector != "— select a sector —":
    st.caption(
        f"**Sector:** {cluster_sector} · "
        f"**Min units:** {cluster_unit_min} · "
        f"**Radius:** {cluster_radius_km} km from anchor ({anchor_district})"
    )
elif selected_columns:
    if selected_sector == "All Sectors" and selected_subsector == "All Subsectors":
        st.caption("**View:** All Sectors & Subsectors")
    elif selected_subsector == "All Subsectors":
        st.caption(f"**Sector:** {selected_sector} (All Subsectors)")
    else:
        st.caption(f"**Sector:** {selected_sector} | **Subsector:** {selected_subsector}")

# KPI row
col1, col2, col3 = st.columns(3)
if enable_cluster_explorer and cluster_sector and cluster_sector != "— select a sector —" and not cluster_df.empty:
    within_r   = cluster_df[cluster_df["_dist_anchor"] <= cluster_radius_km]
    total_in_r = int(within_r["_ce_total"].sum())
    col1.metric("Anchor Location", anchor_district)
    col2.metric("Total Units (in radius)", f"{total_in_r:,}")
    col3.metric("Locations in Radius", len(within_r))
else:
    total_units = int(df_filtered[selected_columns].sum().sum()) if selected_columns and not df_filtered.empty else 0
    active_locs = int((df_filtered[selected_columns].sum(axis=1) > 0).sum()) if selected_columns and not df_filtered.empty else 0
    col1.metric("Selected Region", selected_district if selected_district != "All Districts" else selected_state)
    col2.metric("Total Units", f"{total_units:,}" if total_units else "-")
    col3.metric("Active Clusters", active_locs if active_locs else "-")

st.markdown("---")

# =====================================================
# MAP
# =====================================================
if enable_cluster_explorer and cluster_sector and cluster_sector != "— select a sector —" and cluster_anchor_lat:
    map_center = [cluster_anchor_lat, cluster_anchor_lon]
    zoom = max(4, min(10, int(10 - cluster_radius_km / 100)))
elif enable_radius and center_lat is not None:
    map_center = [center_lat, center_lon]; zoom = 9
elif selected_district != "All Districts" and not df_filtered.empty:
    map_center = [df_filtered["Latitude"].mean(), df_filtered["Longitude"].mean()]; zoom = 10
elif selected_state != "India" and not df_filtered.empty:
    map_center = [df_filtered["Latitude"].mean(), df_filtered["Longitude"].mean()]; zoom = 7
else:
    map_center = [22.0, 78.0]; zoom = 5

m = folium.Map(location=map_center, zoom_start=zoom, tiles="CartoDB Voyager", control_scale=True)
Fullscreen().add_to(m)

# ── CLUSTER EXPLORER LAYER ─────────────────────────
if enable_cluster_explorer and cluster_sector and cluster_sector != "— select a sector —" and not cluster_df.empty:
    sc = get_sector_color(cluster_sector)

    if cluster_anchor_lat:
        folium.Circle(
            location=[cluster_anchor_lat, cluster_anchor_lon],
            radius=cluster_radius_km * 1000,
            color=sc, fill=True, fill_color=sc, fill_opacity=0.06,
            weight=2.5, dash_array="10 5",
            popup=f"Cluster radius: {cluster_radius_km} km around {anchor_district}"
        ).add_to(m)

        folium.Marker(
            location=[cluster_anchor_lat, cluster_anchor_lon],
            popup=f"<b>⭐ Anchor: {anchor_district}</b><br>{int(cluster_df['_ce_total'].max())} units",
            icon=folium.Icon(color="red", icon="star", prefix="fa")
        ).add_to(m)

    max_val = cluster_df["_ce_total"].max() or 1

    for _, row in cluster_df.iterrows():
        dist      = row.get("_dist_anchor", float("inf"))
        in_radius = dist <= cluster_radius_km

        marker_r     = 5 + (row["_ce_total"] / max_val) * 20
        fill_color   = sc if in_radius else "#bbbbbb"
        fill_opacity = 0.80 if in_radius else 0.30
        weight       = 2   if in_radius else 1
        edge_color   = sc  if in_radius else "#888888"

        subs_html = "".join(
            f"<div style='display:flex;justify-content:space-between;gap:12px;'>"
            f"<span style='font-size:11px;color:#555;'>{col}:</span>"
            f"<b>{int(row[col])}</b></div>"
            for col in cluster_selected_cols if row.get(col, 0) > 0
        )

        tt = (
            f"<div style='font-family:sans-serif;min-width:210px;'>"
            f"<h4 style='margin:0 0 2px;'>{row['District']}</h4>"
            f"<small style='color:#888;'>{row['State']}</small>"
            f"<hr style='margin:6px 0;'>"
            f"<b>Total units:</b> {int(row['_ce_total'])}<br>"
            f"<b>Distance from anchor:</b> {dist:.1f} km<br>"
            f"<b>In radius:</b> {'✅' if in_radius else '❌ Outside ring'}<br>"
            f"<div style='margin-top:6px;max-height:130px;overflow-y:auto;'>{subs_html}</div>"
            f"</div>"
        )

        folium.CircleMarker(
            location=[row["Latitude"], row["Longitude"]],
            radius=marker_r,
            color=edge_color, fill=True, fill_color=fill_color,
            fill_opacity=fill_opacity, weight=weight,
            popup=folium.Popup(tt, max_width=360),
            tooltip=(
                f"{row['District']}: {int(row['_ce_total'])} units — {dist:.0f} km"
                + (" ✅" if in_radius else " (outside)")
            )
        ).add_to(m)

# ── ORIGINAL MAP LAYER ─────────────────────────────
elif not enable_cluster_explorer:
    if enable_radius and center_lat is not None:
        folium.Circle(
            location=[center_lat, center_lon], radius=radius_km * 1000,
            color="blue", fill=True, fill_color="blue", fill_opacity=0.1, weight=2,
            popup=f"{center_district} — {radius_km} km radius"
        ).add_to(m)
        folium.Marker(
            location=[center_lat, center_lon],
            popup=f"<b>Center: {center_district}</b>",
            icon=folium.Icon(color="blue", icon="info-sign")
        ).add_to(m)

    if selected_columns and not df_filtered.empty:
        df_map = df_filtered.copy()
        df_map["Total_Selected"] = df_map[selected_columns].sum(axis=1)
        df_map = df_map[df_map["Total_Selected"] > 0]

        if map_mode == "Density Heatmap":
            HeatMap(
                df_map[["Latitude", "Longitude", "Total_Selected"]].values.tolist(),
                radius=20, blur=15, min_opacity=0.3,
                gradient={0.4: "blue", 0.65: "lime", 1: "red"}
            ).add_to(m)
            m.get_root().html.add_child(folium.Element(
                "<div style='position:fixed;bottom:50px;left:50px;z-index:9999;font-size:14px;"
                "background:white;padding:10px;border-radius:5px;border:1px solid grey;'>"
                "<b>Heatmap Intensity</b><br>aggregated volume of selected sectors/subsectors</div>"
            ))
        else:
            max_val = df_map["Total_Selected"].max() or 1
            for _, row in df_map.iterrows():
                row_data      = row[selected_columns]
                dominant_item = row_data.idxmax()
                color_key     = (
                    subsector_to_sector.get(dominant_item, dominant_item)
                    if selected_subsector == "All Subsectors"
                    else (selected_sector if selected_sector != "All Sectors"
                          else subsector_to_sector.get(dominant_item, dominant_item))
                )
                radius = 5 + (row["Total_Selected"] / max_val) * 15

                subs_html = "".join(
                    f"<div style='display:flex;justify-content:space-between;'>"
                    f"<span style='font-size:11px;'>{col}:</span><b>{int(row[col])}</b></div>"
                    for col in selected_columns if row[col] > 0
                )
                dist_line = (
                    f"<b>Distance:</b> {row['Distance_km']:.1f} km<br>"
                    if enable_radius and "Distance_km" in row else ""
                )
                tt = (
                    f"<div style='font-family:sans-serif;min-width:200px;'>"
                    f"<h4 style='margin:0;'>{row['District']}</h4>"
                    f"<small style='color:gray;'>{row['State']}</small>"
                    f"<hr style='margin:5px 0;'>"
                    f"<b>Size:</b> {row['Size_Category']}<br>"
                    f"<b>Dominant:</b> {dominant_item}<br>"
                    f"<b>Total:</b> {int(row['Total_Selected'])}<br>"
                    f"{dist_line}"
                    f"<div style='margin-top:5px;max-height:150px;overflow-y:auto;'>{subs_html}</div>"
                    f"</div>"
                )
                folium.CircleMarker(
                    location=[row["Latitude"], row["Longitude"]],
                    radius=radius, color=get_sector_color(color_key),
                    fill=True, fill_color=get_sector_color(color_key),
                    fill_opacity=0.7, weight=1,
                    popup=folium.Popup(tt, max_width=350),
                    tooltip=f"{row['District']}: {int(row['Total_Selected'])} units ({row['Size_Category']})"
                ).add_to(m)
    else:
        st.info("👈 Select at least one sector or subsector from the sidebar to visualize data.")

st_folium(m, height=600, use_container_width=True)

# =====================================================
# DATA EXPORT
# =====================================================
with st.expander("📊 View & Download Data", expanded=False):
    if enable_cluster_explorer and cluster_sector and cluster_sector != "— select a sector —" and not cluster_df.empty:
        within_r = cluster_df[cluster_df["_dist_anchor"] <= cluster_radius_km].copy()
        show_cols = ["State", "District", "_ce_total", "_dist_anchor"] + cluster_selected_cols
        export_df = within_r[show_cols].rename(
            columns={"_ce_total": "Total_Units", "_dist_anchor": "Distance_from_Anchor_km"}
        ).sort_values("Total_Units", ascending=False)
        st.dataframe(export_df, use_container_width=True)
        csv = export_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            "📥 Download Cluster Data as CSV", data=csv,
            file_name=f"cluster_{cluster_sector[:30].replace(' ', '_')}.csv", mime="text/csv"
        )
    elif selected_columns and not df_filtered.empty:
        cols_to_show = ["State", "District", "Size_Category"] + selected_columns
        if enable_radius and "Distance_km" in df_filtered.columns:
            cols_to_show.insert(3, "Distance_km")
        export_df = df_filtered[cols_to_show].copy()
        export_df["Total_Selected"] = export_df[selected_columns].sum(axis=1)
        export_df = export_df[export_df["Total_Selected"] > 0].sort_values("Total_Selected", ascending=False)
        st.dataframe(export_df, use_container_width=True)
        csv = export_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            "📥 Download Filtered Data as CSV", data=csv,
            file_name=f"manufacturing_data_{selected_state}_{selected_district}.csv", mime="text/csv"
        )
    else:
        st.write("No data available for the current selection.")
