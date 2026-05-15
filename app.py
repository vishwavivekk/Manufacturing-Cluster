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

# ── Hide Streamlit chrome ──────────────────────────────────────────
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    div[data-testid="stToolbar"] { visibility: hidden; height: 0px; }
    .stActionButton {visibility: hidden;}
    button[kind="header"] {visibility: hidden;}
    [data-testid="stHeaderActionElements"] {visibility: hidden;}
    .block-container { padding-top: 2rem; padding-bottom: 2rem; }
    </style>
""", unsafe_allow_html=True)

# =====================================================
# CONSTANTS
# =====================================================
COLOR_PALETTE = [
    "#E63946", "#1D3557", "#457B9D", "#A8DADC", "#2A9D8F",
    "#F4A261", "#E76F51", "#6A4C93", "#8AC926", "#FFCA3A"
]

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

# =====================================================
# UTILITY FUNCTIONS
# =====================================================
def haversine_distance(lat1, lon1, lat2, lon2):
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon  = lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    return 2 * asin(sqrt(a)) * 6371

def get_sector_color(sector: str) -> str:
    return COLOR_PALETTE[int(hashlib.md5(sector.encode()).hexdigest(), 16) % len(COLOR_PALETTE)]

def categorize_size(n):
    if n < 20:   return "Nano (0-20)"
    if n < 50:   return "Micro (20-50)"
    if n < 100:  return "Small (50-100)"
    if n < 500:  return "Medium (100-500)"
    return "Large (500+)"

@st.cache_data
def load_data(path: str):
    if not os.path.exists(path):
        return None, None, None
    try:
        df = pd.read_excel(path, header=[0, 1])
        sector_row    = df.columns.get_level_values(0)
        subsector_row = df.columns.get_level_values(1)

        new_columns, s2s = [], {}
        for i, (sec, sub) in enumerate(zip(sector_row, subsector_row)):
            sec, sub = str(sec).strip(), str(sub).strip()
            if i < 4:
                if   'State'     in sec or 'State'     in sub: new_columns.append('State')
                elif 'District'  in sec or 'District'  in sub: new_columns.append('District')
                elif 'Latitude'  in sec or 'Latitude'  in sub: new_columns.append('Latitude')
                elif 'Longitude' in sec or 'Longitude' in sub: new_columns.append('Longitude')
                else: new_columns.append(sec if sec != 'nan' else sub)
            else:
                col = sub if sub not in ('nan', '') else sec
                new_columns.append(col)
                s2s[col] = sec

        df.columns = [str(c).strip() for c in new_columns]
        req = ["State", "District", "Latitude", "Longitude"]
        if not all(c in df.columns for c in req):
            st.error(f"Missing required columns: {req}")
            st.stop()

        df["State"]    = df["State"].astype(str).str.strip()
        df["District"] = df["District"].astype(str).str.strip()

        sub_cols = [c for c in df.columns if c not in req]
        df[sub_cols] = df[sub_cols].fillna(0).apply(pd.to_numeric, errors='coerce').fillna(0)
        df = df.dropna(subset=["Latitude", "Longitude"])
        return df, sub_cols, s2s
    except Exception as e:
        st.error(f"Error reading file: {e}")
        import traceback
        st.error(traceback.format_exc())
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
st.sidebar.title("🌍 Controls")

# ── Mode Toggle ────────────────────────────────────────────────────
na_mode = st.sidebar.toggle(
    "🔍 Neighbourhood Analysis Mode",
    value=False,
    help="Switch between standard cluster view and Neighbourhood Analysis. "
         "In NA mode, only the selected sector is shown on the map with its own filters."
)

st.sidebar.markdown("---")

# =====================================================
# ─────────── NEIGHBOURHOOD ANALYSIS MODE ───────────
# =====================================================
if na_mode:
    st.sidebar.subheader("🔍 Neighbourhood Analysis")
    st.sidebar.caption("Independent of geographic filters. Covers all India.")

    # Sector selector
    na_all_sectors = sorted(SECTOR_SUBSECTOR_MAP.keys())
    na_sector = st.sidebar.selectbox(
        "Select Sector",
        options=["— Choose a sector —"] + na_all_sectors,
        key="na_sector_sb"
    )

    # ── Slider 1 — Min Units ──────────────────────────────────────
    st.sidebar.markdown("---")
    st.sidebar.markdown("**Slider 1 — Min Units Threshold**")
    enable_s1 = st.sidebar.checkbox(
        "Activate Min Units Filter",
        value=False, key="na_s1_enable",
        help="Only show locations where this sector has at least N units"
    )
    min_units_val = None
    if enable_s1 and na_sector != "— Choose a sector —":
        na_sub_tmp = [s for s in SECTOR_SUBSECTOR_MAP.get(na_sector, []) if s in subsector_columns]
        if na_sub_tmp:
            tmp_df = df.copy()
            tmp_df["_u"] = tmp_df[na_sub_tmp].sum(axis=1)
            max_u = int(tmp_df["_u"].max())
        else:
            max_u = 100
        min_units_val = st.sidebar.slider(
            "Minimum Units", min_value=1, max_value=max(max_u, 1),
            value=min(10, max(max_u, 1)), step=1, key="na_s1_slider"
        )

    # ── Slider 2 — Radius ─────────────────────────────────────────
    st.sidebar.markdown("---")
    st.sidebar.markdown("**Slider 2 — Neighbour Radius**")
    enable_s2 = st.sidebar.checkbox(
        "Activate Radius Neighbour Count",
        value=False, key="na_s2_enable",
        help="Draw a radius circle on each dot. Count how many same-sector locations fall within."
    )
    na_radius_km = None
    if enable_s2:
        na_radius_km = st.sidebar.slider(
            "Radius (km)", min_value=5, max_value=500,
            value=100, step=5, key="na_s2_slider"
        )

# =====================================================
# ─────────── STANDARD MODE ──────────────────────────
# =====================================================
else:
    # Geographic filters
    st.sidebar.subheader("📍 Geographic Filter")
    state_options = ["India"] + sorted(df["State"].unique())
    selected_state = st.sidebar.selectbox("Select State", state_options)

    if selected_state == "India":
        df_filtered   = df.copy()
        district_opts = ["All Districts"]
    else:
        df_filtered   = df[df["State"] == selected_state].copy()
        district_opts = ["All Districts"] + sorted(df_filtered["District"].unique())

    selected_district = st.sidebar.selectbox("Select District", district_opts)
    if selected_district != "All Districts":
        df_filtered = df_filtered[df_filtered["District"] == selected_district]

    st.sidebar.markdown("---")

    # Radius Filter
    st.sidebar.subheader("📍 Radius Filter")
    enable_radius = st.sidebar.checkbox("Enable Distance-Based Filter", value=False)

    std_center_lat = std_center_lon = std_center_district = std_radius_km = None

    if enable_radius:
        r_opts = sorted(df["District"].unique()) if selected_state == "India" else sorted(df[df["State"] == selected_state]["District"].unique())
        std_center_district = st.sidebar.selectbox("Select Center District", options=r_opts)
        std_radius_km = st.sidebar.slider("Radius (km)", min_value=5, max_value=500, value=50, step=5)

        cdd = df[df["District"] == std_center_district]
        if not cdd.empty:
            std_center_lat = cdd["Latitude"].mean()
            std_center_lon = cdd["Longitude"].mean()
            df_filtered["_dist"] = df_filtered.apply(
                lambda r: haversine_distance(std_center_lat, std_center_lon, r["Latitude"], r["Longitude"]), axis=1
            )
            df_filtered = df_filtered[df_filtered["_dist"] <= std_radius_km]
            st.sidebar.info(f"📏 Within {std_radius_km} km of {std_center_district}")
        else:
            st.sidebar.warning("⚠️ District not found")

    st.sidebar.markdown("---")

    # Sector / Subsector
    st.sidebar.subheader("🏭 Industry Sectors & Subsectors")
    ssa_available = {}
    for sec, subs in SECTOR_SUBSECTOR_MAP.items():
        avail = [s for s in subs if s in subsector_columns and df_filtered[s].sum() > 0]
        if avail:
            ssa_available[sec] = avail

    sec_opts = ["All Sectors"] + sorted(ssa_available.keys())
    selected_sector = st.sidebar.selectbox("Select Sector", options=sec_opts)

    if selected_sector == "All Sectors":
        sub_opts = ["All Subsectors"] + sorted(set(s for subs in ssa_available.values() for s in subs))
    else:
        sub_opts = ["All Subsectors"] + sorted(ssa_available.get(selected_sector, []))

    selected_subsector = st.sidebar.selectbox("Select Subsector", options=sub_opts)

    if selected_sector == "All Sectors":
        if selected_subsector == "All Subsectors":
            selected_columns = [c for c in subsector_columns if df_filtered[c].sum() > 0]
        else:
            selected_columns = [selected_subsector] if selected_subsector in subsector_columns else []
    else:
        if selected_subsector == "All Subsectors":
            selected_columns = ssa_available.get(selected_sector, [])
        else:
            selected_columns = [selected_subsector] if selected_subsector in subsector_columns else []

    st.sidebar.markdown("---")

    # Size Filter
    st.sidebar.subheader("📏 Unit Size")
    size_cats = ["Nano (0-20)", "Micro (20-50)", "Small (50-100)", "Medium (100-500)", "Large (500+)"]
    selected_sizes = st.sidebar.multiselect("Filter by Size", options=size_cats, default=size_cats)

    st.sidebar.markdown("---")
    map_mode = st.sidebar.radio("Visualization Mode", ["Detailed Markers", "Density Heatmap"])

    if selected_columns and not df_filtered.empty:
        df_filtered["Total_Units"]    = df_filtered[selected_columns].sum(axis=1)
        df_filtered["Size_Category"]  = df_filtered["Total_Units"].apply(categorize_size)
        if selected_sizes:
            df_filtered = df_filtered[df_filtered["Size_Category"].isin(selected_sizes)]

# =====================================================
# MAIN CONTENT
# =====================================================

# ─── NEIGHBOURHOOD ANALYSIS UI ────────────────────────────────────
if na_mode:
    st.title("🔍 Neighbourhood Analysis")
    st.caption(
        "Analysis mode is **independent** of all geographic filters. "
        "Covers all India. Use the sidebar controls to configure."
    )
    st.markdown("---")

    if na_sector == "— Choose a sector —":
        st.info("👈 Select a sector in the sidebar to begin.")
        st.stop()

    # Build NA dataframe
    na_subsectors = [s for s in SECTOR_SUBSECTOR_MAP.get(na_sector, []) if s in subsector_columns]
    na_color      = get_sector_color(na_sector)

    na_df = df.copy()
    na_df["NA_Units"] = na_df[na_subsectors].sum(axis=1) if na_subsectors else 0
    na_df = na_df[na_df["NA_Units"] > 0].copy()

    # Apply Slider 1 — min units
    na_df_s1 = na_df.copy()
    if enable_s1 and min_units_val is not None:
        na_df_s1 = na_df_s1[na_df_s1["NA_Units"] >= min_units_val]

    # Apply Slider 2 — radius neighbour count
    na_df_final = na_df_s1.copy()
    neighbour_counts = None

    if enable_s2 and na_radius_km and not na_df_s1.empty:
        lats = na_df_s1["Latitude"].values
        lons = na_df_s1["Longitude"].values
        counts = []
        for i in range(len(na_df_s1)):
            c = sum(
                1 for j in range(len(na_df_s1))
                if i != j and haversine_distance(lats[i], lons[i], lats[j], lons[j]) <= na_radius_km
            )
            counts.append(c)
        na_df_final = na_df_s1.copy()
        na_df_final["Neighbour_Count"] = counts
        neighbour_counts = counts

    # ── KPIs ──────────────────────────────────────────────────────
    # Always show: total units in sector (whole India)
    kpi_sector_total   = int(na_df["NA_Units"].sum())
    # After slider 1: locations visible on map
    kpi_visible_locs   = len(na_df_final)
    kpi_visible_units  = int(na_df_final["NA_Units"].sum())

    if enable_s1 and min_units_val:
        # Clusters = distinct visible locations (each ≥ threshold)
        kpi_label3 = f"Locations ≥ {min_units_val} Units"
        kpi_val3   = kpi_visible_locs
    else:
        kpi_label3 = "Total Locations"
        kpi_val3   = kpi_visible_locs

    if enable_s2 and neighbour_counts is not None and na_radius_km:
        # Count locations that have at least 1 neighbour within radius (they form a cluster)
        clustered = sum(1 for c in neighbour_counts if c > 0)
        isolated  = kpi_visible_locs - clustered
        kpi_label4 = f"Clustered (≥1 nbr/{na_radius_km}km)"
        kpi_val4   = clustered
    else:
        kpi_label4 = "Avg Units / Location"
        kpi_val4   = round(na_df_final["NA_Units"].mean(), 1) if kpi_visible_locs > 0 else 0

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Total Units in Sector",   f"{kpi_sector_total:,}")
    k2.metric("Units on Map (Filtered)", f"{kpi_visible_units:,}")
    k3.metric(kpi_label3,                f"{kpi_val3:,}")
    k4.metric(kpi_label4,                f"{kpi_val4:,}" if isinstance(kpi_val4, int) else f"{kpi_val4}")

    # Extra neighbour KPIs when S2 active
    if enable_s2 and neighbour_counts is not None:
        avg_nb = round(sum(neighbour_counts) / len(neighbour_counts), 1) if neighbour_counts else 0
        max_nb = max(neighbour_counts) if neighbour_counts else 0
        nb_k1, nb_k2, nb_k3, _ = st.columns(4)
        nb_k1.metric("Avg Neighbours / Location", avg_nb)
        nb_k2.metric("Max Neighbours (any dot)",  max_nb)
        nb_k3.metric("Isolated Locations",        isolated)

    st.markdown("---")

    # ── SINGLE MAP — Neighbourhood ─────────────────────────────────
    caption_parts = [f"Sector: **{na_sector}**"]
    if enable_s1 and min_units_val:
        caption_parts.append(f"Min units: **{min_units_val}**")
    if enable_s2 and na_radius_km:
        caption_parts.append(f"Radius circles: **{na_radius_km} km**")
    st.caption(" · ".join(caption_parts))

    if na_df_final.empty:
        st.warning("No locations match the current filters.")
    else:
        na_center = [na_df_final["Latitude"].mean(), na_df_final["Longitude"].mean()]
        na_zoom   = 5 if len(na_df_final) > 50 else 6

        m = folium.Map(location=na_center, zoom_start=na_zoom, tiles="CartoDB positron", control_scale=True)
        Fullscreen().add_to(m)

        max_units = na_df_final["NA_Units"].max() if not na_df_final.empty else 1

        for _, row in na_df_final.iterrows():
            bubble_r = 5 + (row["NA_Units"] / max_units) * 18
            nb_val   = int(row["Neighbour_Count"]) if "Neighbour_Count" in row else None

            tip = (
                f"<div style='font-family:sans-serif; min-width:190px;'>"
                f"<b>{row['District']}</b><br>"
                f"<small style='color:gray;'>{row['State']}</small>"
                f"<hr style='margin:4px 0;'>"
                f"<b>Units ({na_sector[:25]}…):</b> {int(row['NA_Units'])}"
            )
            if nb_val is not None:
                tip += f"<br><b>Neighbours within {na_radius_km} km:</b> {nb_val}"
            tip += "</div>"

            short_tip = f"{row['District']}: {int(row['NA_Units'])} units"
            if nb_val is not None:
                short_tip += f" | {nb_val} neighbours"

            # Draw radius circle on map (same as screenshot 1 style)
            if enable_s2 and na_radius_km:
                folium.Circle(
                    location=[row["Latitude"], row["Longitude"]],
                    radius=na_radius_km * 1000,
                    color=na_color,
                    fill=True,
                    fillColor=na_color,
                    fillOpacity=0.04,
                    weight=1.2,
                    opacity=0.5,
                    tooltip=f"{row['District']}: {nb_val} neighbours within {na_radius_km} km"
                ).add_to(m)

            folium.CircleMarker(
                location=[row["Latitude"], row["Longitude"]],
                radius=bubble_r,
                color=na_color,
                fill=True, fill_color=na_color, fill_opacity=0.80, weight=1.5,
                popup=folium.Popup(tip, max_width=300),
                tooltip=short_tip
            ).add_to(m)

        st_folium(m, height=600, use_container_width=True, key="na_map")

    # ── Data Table & Download ──────────────────────────────────────
    st.markdown("---")
    st.markdown("#### 📋 Neighbourhood Data")

    if not na_df_final.empty:
        disp_cols = ["State", "District", "NA_Units"]
        if "Neighbour_Count" in na_df_final.columns:
            disp_cols.append("Neighbour_Count")

        na_table = na_df_final[disp_cols].copy()
        rename_map = {"NA_Units": f"Units — {na_sector[:45]}"}
        if "Neighbour_Count" in na_table.columns:
            rename_map["Neighbour_Count"] = f"Neighbours (within {na_radius_km} km)"
        na_table = na_table.rename(columns=rename_map)
        na_table = na_table.sort_values(f"Units — {na_sector[:45]}", ascending=False).reset_index(drop=True)

        st.dataframe(na_table, use_container_width=True)

        csv = na_table.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="📥 Download Neighbourhood Data as CSV",
            data=csv,
            file_name=f"neighbourhood_{na_sector[:30].replace(' ', '_')}.csv",
            mime="text/csv",
            key="na_download"
        )
    else:
        st.write("No data to display.")

# ─── STANDARD MODE UI ─────────────────────────────────────────────
else:
    # Dynamic title
    if enable_radius and std_center_lat is not None:
        cluster_title = f"Manufacturing Units within {std_radius_km} km of {std_center_district}"
    elif selected_state == "India":
        cluster_title = "India Manufacturing Overview"
    elif selected_district == "All Districts":
        cluster_title = f"{selected_state} Manufacturing Overview"
    else:
        cluster_title = f"{selected_district} ({selected_state}) Cluster Overview"

    st.title(f"🏭 {cluster_title}")

    if selected_columns:
        if selected_sector == "All Sectors" and selected_subsector == "All Subsectors":
            filter_info = "**View:** All Sectors & Subsectors"
        elif selected_subsector == "All Subsectors":
            filter_info = f"**Sector:** {selected_sector} (All Subsectors)"
        else:
            filter_info = f"**Sector:** {selected_sector} | **Subsector:** {selected_subsector}"
        st.caption(filter_info)

    # KPIs
    if selected_columns and not df_filtered.empty:
        total_units = df_filtered[selected_columns].sum().sum()
        active_locs = len(df_filtered[df_filtered[selected_columns].sum(axis=1) > 0])
    else:
        total_units = 0
        active_locs = 0

    c1, c2, c3 = st.columns(3)
    c1.metric("Selected Region", selected_district if selected_district != "All Districts" else selected_state)
    c2.metric("Total Units",     f"{int(total_units):,}" if total_units > 0 else "—")
    c3.metric("Active Clusters", active_locs if active_locs > 0 else "—")

    st.markdown("---")

    # Map center
    if enable_radius and std_center_lat is not None:
        map_center = [std_center_lat, std_center_lon]
        zoom = 9
    elif selected_district != "All Districts":
        map_center = [df_filtered["Latitude"].mean(), df_filtered["Longitude"].mean()] if not df_filtered.empty else [22.0, 78.0]
        zoom = 10
    elif selected_state != "India":
        map_center = [df_filtered["Latitude"].mean(), df_filtered["Longitude"].mean()] if not df_filtered.empty else [22.0, 78.0]
        zoom = 7
    else:
        map_center = [22.0, 78.0]
        zoom = 5

    m = folium.Map(location=map_center, zoom_start=zoom, tiles="CartoDB positron", control_scale=True)
    Fullscreen().add_to(m)

    # Radius circle + center pin (standard mode)
    if enable_radius and std_center_lat is not None:
        folium.Circle(
            location=[std_center_lat, std_center_lon],
            radius=std_radius_km * 1000,
            color='blue', fill=True, fillColor='blue', fillOpacity=0.08, weight=2,
            popup=f"{std_center_district} — {std_radius_km} km radius"
        ).add_to(m)
        folium.Marker(
            location=[std_center_lat, std_center_lon],
            popup=f"<b>Center: {std_center_district}</b>",
            icon=folium.Icon(color='blue', icon='info-sign')
        ).add_to(m)

    # Plot data
    if selected_columns and not df_filtered.empty:
        df_map = df_filtered.copy()
        df_map["Total_Selected"] = df_map[selected_columns].sum(axis=1)
        df_map = df_map[df_map["Total_Selected"] > 0]

        if map_mode == "Density Heatmap":
            heat_data = df_map[["Latitude", "Longitude", "Total_Selected"]].values.tolist()
            HeatMap(heat_data, radius=20, blur=15, min_opacity=0.3,
                    gradient={0.4: 'blue', 0.65: 'lime', 1: 'red'}).add_to(m)
        else:
            max_val = df_map["Total_Selected"].max() if not df_map.empty else 1
            for _, row in df_map.iterrows():
                row_data      = row[selected_columns]
                dominant_item = row_data.idxmax()
                dominant_val  = row_data.max()

                if selected_subsector == "All Subsectors":
                    color_key = subsector_to_sector.get(dominant_item, dominant_item)
                else:
                    color_key = selected_sector if selected_sector != "All Sectors" else subsector_to_sector.get(dominant_item, dominant_item)

                r_marker = 5 + (dominant_val / max_val) * 15

                tip_html = (
                    f"<div style='font-family:sans-serif; min-width:200px;'>"
                    f"<h4 style='margin:0;'>{row['District']}</h4>"
                    f"<small style='color:gray;'>{row['State']}</small>"
                    f"<hr style='margin:5px 0;'>"
                    f"<b>Size:</b> {row['Size_Category']}<br>"
                    f"<b>Dominant:</b> {dominant_item}<br>"
                    f"<b>Total:</b> {int(row['Total_Selected'])}<br>"
                )
                if enable_radius and '_dist' in row:
                    tip_html += f"<b>Distance:</b> {row['_dist']:.1f} km<br>"
                tip_html += "<div style='margin-top:5px; max-height:150px; overflow-y:auto;'>"
                for col in selected_columns:
                    v = row[col]
                    if v > 0:
                        tip_html += (
                            f"<div style='display:flex; justify-content:space-between;'>"
                            f"<span style='font-size:11px;'>{col}:</span> <b>{int(v)}</b></div>"
                        )
                tip_html += "</div></div>"

                folium.CircleMarker(
                    location=[row["Latitude"], row["Longitude"]],
                    radius=r_marker,
                    color=get_sector_color(color_key),
                    fill=True, fill_color=get_sector_color(color_key),
                    fill_opacity=0.7, weight=1,
                    popup=folium.Popup(tip_html, max_width=350),
                    tooltip=f"{row['District']}: {int(row['Total_Selected'])} units ({row['Size_Category']})"
                ).add_to(m)
    else:
        st.info("👈 Select a sector from the sidebar to see data on the map.")

    st_folium(m, height=600, use_container_width=True, key="std_map")

    # Data export
    with st.expander("📊 View & Download Data", expanded=False):
        if selected_columns and not df_filtered.empty:
            cols_show = ["State", "District", "Size_Category"] + selected_columns
            if enable_radius and '_dist' in df_filtered.columns:
                cols_show.insert(3, "_dist")
            exp_df = df_filtered[cols_show].copy()
            if "_dist" in exp_df.columns:
                exp_df = exp_df.rename(columns={"_dist": "Distance_km"})
            exp_df["Total_Selected"] = exp_df[selected_columns].sum(axis=1)
            exp_df = exp_df[exp_df["Total_Selected"] > 0].sort_values("Total_Selected", ascending=False)
            st.dataframe(exp_df, use_container_width=True)
            csv = exp_df.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="📥 Download Filtered Data as CSV",
                data=csv,
                file_name=f"manufacturing_{selected_state}_{selected_district}.csv",
                mime="text/csv"
            )
        else:
            st.write("No data for current selection.")
