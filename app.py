# =====================================================
# NEIGHBOURHOOD ANALYSIS SECTION
# (Paste this block at the END of your app.py,
#  after the existing Data Export expander)
# =====================================================

st.markdown("---")
st.markdown("## 🔍 Neighbourhood Analysis")
st.caption("Independent of all filters above. Explore sector clustering and proximity patterns.")

# ─── Build sector list from subsector_to_sector mapping ───────────────────────
all_sectors_in_data = sorted(set(subsector_to_sector.values()))

na_col_left, na_col_right = st.columns([1, 2])

with na_col_left:
    # ── Sector selector ────────────────────────────────────────────────────────
    na_sector = st.selectbox(
        "Select Sector",
        options=["— Pick a sector —"] + all_sectors_in_data,
        key="na_sector"
    )

na_sector_selected = na_sector != "— Pick a sector —"

if na_sector_selected:
    # ── Resolve columns for chosen sector ─────────────────────────────────────
    na_cols = [
        col for col, sec in subsector_to_sector.items()
        if sec == na_sector and col in subsector_columns
    ]

    # ── Compute per-district totals for this sector (uses FULL df, no filters) ─
    na_df = df.copy()
    na_df["_sector_total"] = na_df[na_cols].sum(axis=1)
    na_df = na_df[na_df["_sector_total"] > 0].copy()

    # ══════════════════════════════════════════════════════
    # SLIDER 1 — Min Units Threshold
    # ══════════════════════════════════════════════════════
    st.markdown("---")
    enable_min_units = st.checkbox(
        "🔢 Activate Min Units Threshold",
        value=False,
        key="na_enable_min_units",
        help="Filter to show only districts with at least N units in this sector"
    )

    if enable_min_units:
        max_units = int(na_df["_sector_total"].max()) if not na_df.empty else 100
        na_min_units = st.slider(
            "Minimum Units in Sector",
            min_value=1,
            max_value=max(max_units, 1),
            value=min(10, max_units),
            step=1,
            key="na_min_units"
        )
        na_df = na_df[na_df["_sector_total"] >= na_min_units]

    # ══════════════════════════════════════════════════════
    # SLIDER 2 — Neighbourhood Radius
    # ══════════════════════════════════════════════════════
    enable_radius_na = st.checkbox(
        "📡 Activate Neighbourhood Radius",
        value=False,
        key="na_enable_radius",
        help="For every visible district, count how many other same-sector districts fall within the chosen radius"
    )

    if enable_radius_na:
        na_radius_km = st.slider(
            "Neighbourhood Radius (km)",
            min_value=5,
            max_value=500,
            value=100,
            step=5,
            key="na_radius_km"
        )

        # Count neighbours for each district
        lats = na_df["Latitude"].values
        lons = na_df["Longitude"].values
        neighbour_counts = []
        for i in range(len(na_df)):
            count = 0
            for j in range(len(na_df)):
                if i != j:
                    d = haversine_distance(lats[i], lons[i], lats[j], lons[j])
                    if d <= na_radius_km:
                        count += 1
            neighbour_counts.append(count)
        na_df["_neighbours"] = neighbour_counts
    else:
        na_df["_neighbours"] = None

    # ══════════════════════════════════════════════════════
    # KPI ROW
    # ══════════════════════════════════════════════════════
    st.markdown("")
    kpi1, kpi2, kpi3 = st.columns(3)
    kpi1.metric("Sector", na_sector.split(" ")[0] + "…" if len(na_sector) > 30 else na_sector)
    kpi2.metric("Districts Shown", len(na_df))
    kpi3.metric(
        "Total Units (Sector)",
        f"{int(na_df['_sector_total'].sum()):,}" if not na_df.empty else "—"
    )

    # ══════════════════════════════════════════════════════
    # MAP
    # ══════════════════════════════════════════════════════
    na_sector_color = get_sector_color(na_sector)  # single color for whole sector

    if not na_df.empty:
        na_center = [na_df["Latitude"].mean(), na_df["Longitude"].mean()]
        na_zoom = 5 if len(na_df) > 50 else 6
    else:
        na_center = [22.0, 78.0]
        na_zoom = 5

    na_map = folium.Map(
        location=na_center,
        zoom_start=na_zoom,
        tiles="CartoDB Voyager",
        control_scale=True
    )
    Fullscreen().add_to(na_map)

    if not na_df.empty:
        max_val_na = na_df["_sector_total"].max() or 1

        for _, row in na_df.iterrows():
            radius_px = 5 + (row["_sector_total"] / max_val_na) * 18

            # Tooltip
            tt = f"""
            <div style="font-family:sans-serif; min-width:180px;">
                <b>{row['District']}</b><br>
                <small style="color:gray;">{row['State']}</small>
                <hr style="margin:4px 0;">
                <b>Sector Units:</b> {int(row['_sector_total'])}
            """
            if enable_radius_na:
                tt += f"<br><b>Neighbours within {na_radius_km} km:</b> {int(row['_neighbours'])}"
            tt += "</div>"

            folium.CircleMarker(
                location=[row["Latitude"], row["Longitude"]],
                radius=radius_px,
                color=na_sector_color,
                fill=True,
                fill_color=na_sector_color,
                fill_opacity=0.72,
                weight=1.2,
                popup=folium.Popup(tt, max_width=280),
                tooltip=(
                    f"{row['District']}: {int(row['_sector_total'])} units"
                    + (f" | {int(row['_neighbours'])} neighbours" if enable_radius_na else "")
                )
            ).add_to(na_map)

    st_folium(na_map, height=520, use_container_width=True, key="na_map")

    # ══════════════════════════════════════════════════════
    # DATA TABLE & DOWNLOAD
    # ══════════════════════════════════════════════════════
    with st.expander("📊 Neighbourhood Data Table & Download", expanded=False):
        if not na_df.empty:
            display_cols = ["State", "District"] + na_cols + ["_sector_total"]
            col_rename = {"_sector_total": "Total Units (Sector)"}

            if enable_radius_na:
                display_cols.append("_neighbours")
                col_rename["_neighbours"] = f"Neighbours within {na_radius_km}km"

            table_df = (
                na_df[display_cols]
                .rename(columns=col_rename)
                .sort_values("Total Units (Sector)", ascending=False)
                .reset_index(drop=True)
            )

            st.dataframe(table_df, use_container_width=True)

            csv_na = table_df.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="📥 Download Neighbourhood Data as CSV",
                data=csv_na,
                file_name=f"neighbourhood_{na_sector[:30].replace(' ','_')}.csv",
                mime="text/csv",
                key="na_download"
            )
        else:
            st.info("No districts match current filters.")

else:
    st.info("👆 Select a sector above to begin Neighbourhood Analysis.")
