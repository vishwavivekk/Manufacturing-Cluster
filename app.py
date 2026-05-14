# =====================================================
# NEIGHBOURHOOD ANALYSIS SECTION
# Paste this block at the END of your app.py,
# after the existing "📊 View & Download Data" expander.
# =====================================================

st.markdown("---")
st.markdown("## 🔍 Neighbourhood Analysis")
st.caption("Independent of all filters above. Explore sector clustering and proximity patterns.")

# ─── Build sector → subsector column mapping from SECTOR_SUBSECTOR_MAP ────────
# This uses the hardcoded SECTOR_SUBSECTOR_MAP (already defined above in app.py)
# and cross-references with subsector_columns (columns actually present in the Excel)
na_sector_to_cols = {}
for sector, subsectors in SECTOR_SUBSECTOR_MAP.items():
    matched = [s for s in subsectors if s in subsector_columns]
    if matched:
        na_sector_to_cols[sector] = matched

na_available_sectors = sorted(na_sector_to_cols.keys())

# ─── Sector selector (left-aligned, not full width) ───────────────────────────
na_sel_col, _ = st.columns([1, 2])
with na_sel_col:
    na_sector = st.selectbox(
        "Select Sector",
        options=["— Pick a sector —"] + na_available_sectors,
        key="na_sector"
    )

na_sector_active = (na_sector != "— Pick a sector —")

if not na_sector_active:
    st.info("👆 Select a sector above to begin Neighbourhood Analysis.")
else:
    # ── Resolve subsector columns for chosen sector ────────────────────────────
    na_cols = na_sector_to_cols.get(na_sector, [])

    # ── Build base dataframe (FULL df, completely independent of other filters) ─
    na_base = df.copy()
    if na_cols:
        na_base["_sector_total"] = na_base[na_cols].sum(axis=1)
    else:
        na_base["_sector_total"] = 0
    na_base = na_base[na_base["_sector_total"] > 0].copy()

    # ══════════════════════════════════════════════════════
    # SLIDER 1 — Min Units Threshold
    # ══════════════════════════════════════════════════════
    st.markdown("---")
    enable_min_units = st.checkbox(
        "🔢 Activate Min Units Threshold",
        value=False,
        key="na_enable_min_units",
        help="Show only districts with at least N units in this sector"
    )

    na_df = na_base.copy()

    if enable_min_units:
        max_possible = int(na_df["_sector_total"].max()) if not na_df.empty else 100
        max_possible = max(max_possible, 2)
        na_min_units = st.slider(
            "Minimum Units in Sector",
            min_value=1,
            max_value=max_possible,
            value=min(5, max_possible),
            step=1,
            key="na_min_units"
        )
        na_df = na_df[na_df["_sector_total"] >= na_min_units].copy()

    # ══════════════════════════════════════════════════════
    # SLIDER 2 — Neighbourhood Radius
    # ══════════════════════════════════════════════════════
    enable_radius_na = st.checkbox(
        "📡 Activate Neighbourhood Radius",
        value=False,
        key="na_enable_radius",
        help="For every visible district, count how many other same-sector districts lie within the chosen radius"
    )

    na_radius_km = None
    if enable_radius_na:
        na_radius_km = st.slider(
            "Neighbourhood Radius (km)",
            min_value=5,
            max_value=500,
            value=100,
            step=5,
            key="na_radius_km"
        )

        if not na_df.empty:
            lats = na_df["Latitude"].values
            lons = na_df["Longitude"].values
            neighbour_counts = []
            for i in range(len(na_df)):
                count = sum(
                    1 for j in range(len(na_df))
                    if i != j and haversine_distance(lats[i], lons[i], lats[j], lons[j]) <= na_radius_km
                )
                neighbour_counts.append(count)
            na_df = na_df.copy()
            na_df["_neighbours"] = neighbour_counts
        else:
            na_df["_neighbours"] = []
    else:
        na_df["_neighbours"] = None

    # ══════════════════════════════════════════════════════
    # KPI ROW
    # ══════════════════════════════════════════════════════
    st.markdown("")
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)

    short_sector = (na_sector[:28] + "…") if len(na_sector) > 30 else na_sector
    kpi1.metric("Sector", short_sector)
    kpi2.metric("Districts Shown", len(na_df))
    kpi3.metric(
        "Total Sector Units",
        f"{int(na_df['_sector_total'].sum()):,}" if not na_df.empty else "—"
    )
    if enable_radius_na and na_radius_km and not na_df.empty and "_neighbours" in na_df.columns:
        avg_nb = na_df["_neighbours"].mean()
        kpi4.metric("Avg Neighbours", f"{avg_nb:.1f}" if na_df["_neighbours"].notna().any() else "—")
    else:
        kpi4.metric("Subsectors", len(na_cols))

    # ══════════════════════════════════════════════════════
    # MAP
    # ══════════════════════════════════════════════════════
    na_sector_color = get_sector_color(na_sector)

    if not na_df.empty:
        na_center = [na_df["Latitude"].mean(), na_df["Longitude"].mean()]
        na_zoom = 5 if len(na_df) > 40 else 6
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

    if na_df.empty:
        st.warning("⚠️ No districts found for the current selection. Try lowering the Min Units threshold.")
    else:
        max_val_na = na_df["_sector_total"].max() or 1

        for _, row in na_df.iterrows():
            radius_px = 5 + (row["_sector_total"] / max_val_na) * 18

            # Build tooltip HTML
            tt = (
                f'<div style="font-family:sans-serif; min-width:190px;">'
                f'<b style="font-size:13px;">{row["District"]}</b><br>'
                f'<small style="color:gray;">{row["State"]}</small>'
                f'<hr style="margin:5px 0;">'
                f'<b>Sector Units:</b> {int(row["_sector_total"])}'
            )
            if enable_radius_na and na_radius_km and row["_neighbours"] is not None:
                tt += f'<br><b>Neighbours within {na_radius_km} km:</b> {int(row["_neighbours"])}'
            tt += "</div>"

            tooltip_text = f"{row['District']}: {int(row['_sector_total'])} units"
            if enable_radius_na and na_radius_km and row["_neighbours"] is not None:
                tooltip_text += f" | {int(row['_neighbours'])} neighbours"

            folium.CircleMarker(
                location=[row["Latitude"], row["Longitude"]],
                radius=radius_px,
                color=na_sector_color,
                fill=True,
                fill_color=na_sector_color,
                fill_opacity=0.72,
                weight=1.5,
                popup=folium.Popup(tt, max_width=280),
                tooltip=tooltip_text
            ).add_to(na_map)

    st_folium(na_map, height=520, use_container_width=True, key="na_map")

    # ══════════════════════════════════════════════════════
    # DATA TABLE & DOWNLOAD
    # ══════════════════════════════════════════════════════
    with st.expander("📊 Neighbourhood Data Table & Download", expanded=False):
        if not na_df.empty:
            # Build display columns — only subsectors with any data
            active_na_cols = [c for c in na_cols if na_df[c].sum() > 0]
            display_cols = ["State", "District"] + active_na_cols + ["_sector_total"]
            col_rename = {"_sector_total": "Total Units (Sector)"}

            if enable_radius_na and na_radius_km and "_neighbours" in na_df.columns:
                display_cols.append("_neighbours")
                col_rename["_neighbours"] = f"Neighbours within {na_radius_km}km"

            # Only keep cols that actually exist in na_df
            display_cols = [c for c in display_cols if c in na_df.columns]

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
                file_name=f"neighbourhood_{na_sector[:30].replace(' ', '_')}.csv",
                mime="text/csv",
                key="na_download"
            )
        else:
            st.info("No districts match the current selection.")
