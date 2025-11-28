import streamlit as st
import folium
from datetime import date
from folium import GeoJson
from shapely.geometry import shape, Point
from streamlit_folium import st_folium
from load_data import load_json, load_data_from_mongodb
import pandas as pd
import geopandas as gpd

# Initialize session state for storing results
if 'database' not in st.session_state:
    st.session_state.database = None
if 'group_selected' not in st.session_state:
    st.session_state.group_selected = None
if 'query_results' not in st.session_state:
    st.session_state.query_results = None

def controls():
    st.subheader("Choropleth Controls")

   
    st.session_state.database = st.radio(
        "Dataset",
        ["Production", "Consumption"],
        horizontal=True
    )

    productiongroups = ['hydro', 'other', 'solar', 'thermal', 'wind']
    consumptiongroups = ['cabin', 'household', 'primary', 'secondary', 'tertiary']

    # Select column names depending on selected database
    if st.session_state.database == "Production":
        namespace = "production_NO1"
        groups = productiongroups
        

    else:
        namespace = "consumption_NO1"
        groups = consumptiongroups

    st.session_state.group_selected  = st.selectbox("Select group", sorted(groups))

    st.subheader("Select Time Interval")
    col1, col2 = st.columns(2)

    with col1:
        from_date = st.date_input(
            "From date",
            value=date(2021, 1, 1),
            min_value=date(2021, 1, 1),
            max_value=date(2024, 12, 31)
        )

    with col2:
        to_date = st.date_input(
            "To date",
            value=date(2024, 12, 31),
            min_value=date(2021, 1, 1),
            max_value=date(2024, 12, 31)
        )

    # Add validation to ensure from_date is before to_date
    if from_date > to_date:
        st.error("Error: 'From date' must be before 'To date'")
    else:
        st.write(f"Date range: {from_date} to {to_date}")

    # Query MongoDB
    if st.button("Query Data"):
        if from_date > to_date:
            st.error("Error: 'From date' must be before 'To date'")
        elif not st.session_state.group_selected :
            st.error("Please enter a group name")
        else:
            with st.spinner("Querying database..."):
                st.session_state.query_results = load_data_from_mongodb(
                    namespace,
                    st.session_state.group_selected,
                    from_date,
                    to_date
                )
                
                st.success(f"Found {len(st.session_state.query_results)} records")

def choropleth():

    # Load GeoJSON data
    data = load_json("data/energydata.geojson")
    gdf = gpd.read_file("data/energydata.geojson")

    # Initialize session state for clicked location
    if 'clicked_lat' not in st.session_state:
        st.session_state.clicked_lat = None
    if 'clicked_lon' not in st.session_state:
        st.session_state.clicked_lon = None
    if 'clicked_area' not in st.session_state:
        st.session_state.clicked_area = None

    # Check if query results exist
    if st.session_state.query_results is not None:
        df = st.session_state.query_results
        
        # Aggregate data by pricearea - calculate mean quantitykwh
        aggregated_data = df.groupby('pricearea').agg({
            'quantitykwh': 'mean'
        }).reset_index()
        
        # Add a column with space to match GeoJSON format "NO 1"
        aggregated_data['pricearea_with_space'] = aggregated_data['pricearea'].str.replace('NO', 'NO ')

        # Create the folium map centered on Norway
        m = folium.Map(
            location=[65, 8],  # Center of Norway
            zoom_start=4,
            tiles='OpenStreetMap'
        )
        
        # Create choropleth layer with visible coloring
        choropleth = folium.Choropleth(
            geo_data=data,
            name='choropleth',
            data=aggregated_data,
            columns=['pricearea_with_space', 'quantitykwh'],  # Use the column with space
            key_on='feature.properties.ElSpotOmr',
            fill_color='YlOrRd',
            fill_opacity=0.7,
            line_color='#00008B',
            line_weight=2,
            line_opacity=0.8,
            legend_name=f'Mean Energy {st.session_state.database} (kWh)',
            highlight=True,
            nan_fill_color='lightgray',
            nan_fill_opacity=0.4
        ).add_to(m)
        
        # Add highlight for selected area if one is clicked
        if st.session_state.clicked_area is not None:
            selected_area = gdf[gdf['ElSpotOmr'] == st.session_state.clicked_area]
            if not selected_area.empty:
                folium.GeoJson(
                    selected_area,
                    style_function=lambda x: {
                        'fillColor': 'transparent',
                        'color': '#FF0000',
                        'weight': 3,
                        'fillOpacity': 0.5
                    },
                    name='selected_area'
                ).add_to(m)

        folium.LayerControl().add_to(m)
        
        # Display the map and capture output
        map_data = st_folium(m, width=700, height=500, key="map")
        
        # Capture click events
        if map_data and map_data.get('last_clicked'):
            clicked_lat = map_data['last_clicked']['lat']
            clicked_lon = map_data['last_clicked']['lng']
            
            # Find which area was clicked using spatial join
            point = Point(clicked_lon, clicked_lat)
            for idx, row in gdf.iterrows():
                if row['geometry'].contains(point):
                    st.session_state.clicked_area = row['ElSpotOmr']
                    st.session_state.clicked_lat = clicked_lat
                    st.session_state.clicked_lon = clicked_lon
                    st.rerun()
                    break
        
        # Display clicked information if available
        if st.session_state.clicked_area is not None:
            st.info(f"Selected area: {st.session_state.clicked_area}")
            st.write(f"Coordinates: Lat: {st.session_state.clicked_lat:.4f}, Lon: {st.session_state.clicked_lon:.4f}")
            
            # Remove space to match original pricearea format for lookup
            clicked_area_no_space = st.session_state.clicked_area.replace(' ', '')
            area_data = aggregated_data[aggregated_data['pricearea'] == clicked_area_no_space]
            if not area_data.empty:
                mean_value = area_data['quantitykwh'].values[0]
                st.write(f"Mean Energy {st.session_state.database} : {mean_value:.2f} kWh")
                    
    else:
        st.info("Please query the database first to display the map")


def map_page():
    controls()
    choropleth()