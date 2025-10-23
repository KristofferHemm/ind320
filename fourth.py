import streamlit as st
import plotly.express as px
from load_data import load_data_from_mongodb

def fourth_page():

    df = load_data_from_mongodb()

    col1, col2 = st.columns(2)

    # Set a fixed height for containers
    CONTAINER_HEIGHT = 300  # Height in pixels for selection areas
    PLOT_HEIGHT = 600       # Height in pixels for plots

    with col1:
        st.header("Energy Produciton by Price Area")
        # Radio buttons to select price area
        # Get unique price areas
        price_areas = sorted(df['pricearea'].unique())

        with st.container(height=CONTAINER_HEIGHT):
            st.subheader("Select Price Area:")
            selected_area = st.radio(
                '',
                options=price_areas,
                horizontal=True
            )
        # Filter data by selected price area
        filtered_df = df[df['pricearea'] == selected_area]

        # Group by productiongroup and sum quantitykwh
        grouped_data = filtered_df.groupby('productiongroup')['quantitykwh'].sum().reset_index()

        # Create pie chart
        fig = px.pie(
                grouped_data,
                values='quantitykwh',
                names='productiongroup',
                title=f'Energy Production Distribution in {selected_area}'
            )
            
        # Legend position
        
        fig.update_layout(
            height=PLOT_HEIGHT,
            legend=dict(
                orientation="h",
                yanchor="top",
                y=-0.1,  # Negative value positions it below the chart
                xanchor="center",
                x=0.5
            )
        )
        
        # Display the chart - use_container_width=True to fit the column
        st.plotly_chart(fig, use_container_width=True)
    


    with col2:
        
        st.header("Energy Production Analysis")
        
        df['year_month'] = df['starttime'].dt.to_period('M').astype(str)

        # Get unique values for filters
        production_groups = sorted(df['productiongroup'].unique().tolist())
        available_months = sorted(df['year_month'].unique().tolist())

        with st.container(height=CONTAINER_HEIGHT):
            # Production Groups filter
            st.subheader("Select Production Groups")
            selected_groups = st.pills(
                "Production Groups",
                options=production_groups,
                selection_mode="multi",
                default=production_groups[0] if production_groups else None,
                label_visibility="collapsed"
            )

            # Month filter
            st.subheader("Select Month")
            selected_month = st.selectbox(
                "Month",
                options=available_months,
                index=len(available_months) - 1 if available_months else 0,
                label_visibility="collapsed"
            )

        # Filter data based on selections
        if selected_groups and selected_month:
            # Convert single selection to list if needed
            if not isinstance(selected_groups, list):
                selected_groups = [selected_groups]
            
            filtered_df = df[
                (df['productiongroup'].isin(selected_groups)) & 
                (df['year_month'] == selected_month)
            ].copy()
            
            if not filtered_df.empty:
                # Sum across all price areas - only group by productiongroup and starttime
                plot_df = filtered_df.groupby(
                    ['productiongroup', 'starttime'], as_index=False
                )['quantitykwh'].sum()
                
                # Create line plot - color only by production group
                fig = px.line(
                    plot_df,
                    x='starttime',
                    y='quantitykwh',
                    color='productiongroup',
                    title=f'Energy Production - {selected_month}',
                    labels={
                        'starttime': 'Time',
                        'quantitykwh': 'Quantity (kWh)',
                        'productiongroup': 'Production Group'
                    }
                )
                
                fig.update_layout(
                    height=PLOT_HEIGHT,
                    hovermode='x unified',
                    legend=dict(
                        orientation="h",
                        yanchor="top",
                        y=-0.2,  # Negative value positions it below the chart
                        xanchor="center",
                        x=0.5
                    )
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
            else:
                st.warning("No data available for the selected filters.")
        else:
            st.info("Please select at least one production group and a month to display the chart.")