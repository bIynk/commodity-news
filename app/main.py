import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime
import re
import logging
from st_aggrid import AgGrid, GridOptionsBuilder, JsCode

# Configure logging once at application entry point
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s:%(name)s:%(message)s',
    force=True  # Override any existing configurations
)
logger = logging.getLogger(__name__)
from modules.data_loader import load_data_from_database
from modules.calculations import calculate_price_changes, compute_zscore, detect_frequency, compute_frequency_aware_zscore
from modules.styling import configure_page_style, style_dataframe, display_market_metrics, display_aggrid_table
from modules.stock_data import fetch_multiple_stocks, get_stock_tickers_from_impact
from modules.db_connection import get_connection_string

# AI Integration Imports
from modules.ai_integration import (
    PerplexityClient,
    TimeFrame,
    CommodityQueryOrchestrator,
    DataProcessor as AIDataProcessor,
    AIDatabase
)
from modules.config import PERPLEXITY_API_KEY, DEFAULT_TIMEFRAME, MAX_NEWS_ITEMS, AI_ZSCORE_THRESHOLD
from modules.ai_section import render_ai_intelligence_section

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Commodity Dashboard",
    page_icon="💹",
    layout="wide"
)

# --- APPLY CUSTOM STYLES ---
configure_page_style()

# --- TITLE ---
st.markdown("""
    <h1 style='text-align: center; color: #00816D; font-size: 2.5rem; font-weight: 700; margin-bottom: 0.5rem;'>
        Commodity Market Dashboard
    </h1>
    <p style='text-align: center; color: #6B7280; font-size: 1rem; margin-bottom: 2rem;'>
        Real-time commodity prices and market analysis
    </p>
""", unsafe_allow_html=True)

# --- DATA LOADING ---
df_data, df_list = load_data_from_database()

if df_data is None or df_list is None:
    st.error("❌ Failed to load data from database. Please check your connection.")
    st.info("Set the DC_DB_STRING environment variable with your database connection string.")
    st.code("""
# Windows (PowerShell)
$env:DC_DB_STRING="DRIVER={ODBC Driver 17 for SQL Server};SERVER=your_server;DATABASE=CommodityDB;UID=your_user;PWD=your_password"

# Linux/Mac
export DC_DB_STRING="DRIVER={ODBC Driver 17 for SQL Server};SERVER=your_server;DATABASE=CommodityDB;UID=your_user;PWD=your_password"
    """)
    st.stop()

# Check if data is loaded
if df_data.empty or df_list.empty:
    st.warning("⚠️ No data available in the database.")
    st.stop()

# --- INITIALIZE AI SERVICES ---
@st.cache_resource
def initialize_ai_services():
    """Initialize AI services with caching"""
    try:
        client = PerplexityClient(api_key=PERPLEXITY_API_KEY)
        ai_db = AIDatabase()
        # Get connection string for database commodity loading
        connection_string = get_connection_string()
        # Pass connection string to orchestrator for database commodity loading
        orchestrator = CommodityQueryOrchestrator(
            client,
            ai_db,
            zscore_threshold=AI_ZSCORE_THRESHOLD,
            connection_string=connection_string
        )
        processor = AIDataProcessor()
        return orchestrator, processor, ai_db
    except Exception as e:
        st.error(f"Failed to initialize AI services: {e}")
        return None, None, None

ai_orchestrator, ai_processor, ai_database = initialize_ai_services()

# --- SIDEBAR FILTERS ---
st.sidebar.markdown("### 🔍 Advanced Filters")

if df_data is not None and df_list is not None:
    # Display data last update date
    latest_date = df_data['Date'].max()
    st.sidebar.info(f"📅 **Data last updated:** {latest_date.strftime('%B %d, %Y')}")
    # Add tooltip explaining what this date means
    st.sidebar.caption("This is the most recent date with price data in the database. All percentage changes are calculated relative to this date.")
    st.sidebar.markdown("---")
    # Sector Filter
    unique_sectors = sorted(df_list['Sector'].astype(str).unique())
    selected_sectors = st.sidebar.multiselect(
        "Sector",
        options=unique_sectors,
        default=[]
    )
    
    # Filter df_list based on selected sectors
    if selected_sectors:
        df_list_filtered = df_list[df_list['Sector'].isin(selected_sectors)]
    else:
        df_list_filtered = df_list

    # Change Type Filter
    change_types = ["Positive", "Negative", "Neutral"]
    selected_change_types = st.sidebar.multiselect(
        "Change Type",
        options=change_types,
        default=[]
    )
    
    # Commodity Filter (filtered by selected sectors)
    commodity_options = sorted(df_list_filtered['Commodities'].dropna().unique())
    selected_commodities = st.sidebar.multiselect(
        "Commodity",
        options=commodity_options,
        default=[]
    )

    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📊 Chart Options")
    
    # Date Range
    min_date = df_data['Date'].min()
    max_date = df_data['Date'].max()
    
    col1, col2 = st.sidebar.columns(2)
    with col1:
        start_date = st.date_input(
            "Start Date",
            value=min_date,
            min_value=min_date,
            max_value=max_date
        )
    with col2:
        end_date = st.date_input(
            "End Date",
            value=max_date,
            min_value=min_date,
            max_value=max_date
        )
    
    # Interval Selection
    interval_options = ["Daily", "Weekly", "Monthly", "Quarterly"]
    selected_interval = st.sidebar.selectbox(
        "Interval",
        options=interval_options,
        index=1  # Default to Weekly
    )

    # --- AI INTELLIGENCE CONTROLS ---
    if ai_orchestrator:
        st.sidebar.markdown("---")
        st.sidebar.markdown("### 🤖 AI Intelligence")

        ai_timeframe = st.sidebar.radio(
            "AI Analysis Period",
            options=["1 week", "1 month"],
            index=0 if DEFAULT_TIMEFRAME == "1 week" else 1,
            help="Period for AI market analysis"
        )

        # Note: AI Intelligence will analyze commodities based on the filters above
        st.sidebar.caption("AI will analyze commodities matching the filters above")

        # Buttons disabled for now
        # col1, col2 = st.sidebar.columns(2)
        # with col1:
        #     # Disable refresh if no write access
        #     refresh_disabled = ai_database and not ai_database.has_write_access
        #     if st.button("🔄 Refresh AI", width='stretch', disabled=refresh_disabled,
        #                 help="Write access required to fetch new data" if refresh_disabled else "Fetch latest AI data"):
        #         st.session_state.ai_refresh = True
        # with col2:
        #     # Clear cache only works with write access
        #     clear_disabled = ai_database and not ai_database.has_write_access
        #     if st.button("🗑️ Clear Cache", width='stretch', disabled=clear_disabled,
        #                 help="Write access required to clear cache" if clear_disabled else "Clear cached AI data"):
        #         if ai_orchestrator:
        #             ai_orchestrator.daily_cache.clear()
        #             if ai_database:
        #                 ai_database.clear_cache()
        #         st.success("Cache cleared!")

        # Show cache status and threshold info
        if hasattr(st.session_state, 'ai_last_update'):
            time_diff = datetime.now() - st.session_state.ai_last_update
            st.sidebar.caption(f"AI data: {int(time_diff.total_seconds()/60)}m ago")
            st.sidebar.caption(f"Z-score threshold: ±{AI_ZSCORE_THRESHOLD}")
    
    # --- DATA CALCULATION ---
    # Use latest date for all current sections (already calculated in sidebar)
    analysis_df = calculate_price_changes(df_data, df_list, latest_date)

    # Store the last updated date from the data for AI cache purposes
    data_last_updated = latest_date if not df_data.empty else None

    # Count stale data
    if 'Is_Stale' in analysis_df.columns and 'Update_Frequency' in analysis_df.columns:
        stale_df = analysis_df[analysis_df['Is_Stale']]
        stale_count = len(stale_df)
        total_count = len(analysis_df)
        if stale_count > 0:
            # Count by frequency type
            daily_stale = len(stale_df[stale_df['Update_Frequency'] == 'daily'])
            weekly_stale = len(stale_df[stale_df['Update_Frequency'] == 'weekly'])

            stale_msg = f"ℹ️ {stale_count} out of {total_count} commodities have stale data and are excluded from KPI metrics"
            if daily_stale > 0 and weekly_stale > 0:
                stale_msg += f" ({daily_stale} daily >7 days, {weekly_stale} weekly >14 days)"
            elif daily_stale > 0:
                stale_msg += f" (daily commodities >7 days old)"
            elif weekly_stale > 0:
                stale_msg += f" (weekly commodities >14 days old)"
            st.info(stale_msg)

    # --- MAIN CONTENT ---
    
    if not analysis_df.empty:
        # Apply filters
        filtered_df = analysis_df.copy()
        
        if selected_sectors:
            filtered_df = filtered_df[filtered_df['Sector'].isin(selected_sectors)]
        if selected_change_types:
            filtered_df = filtered_df[filtered_df['Change type'].isin(selected_change_types)]
            
        if selected_commodities:
            filtered_df = filtered_df[filtered_df['Commodities'].isin(selected_commodities)]

        # --- Display Key Market Metrics ---
        display_market_metrics(filtered_df)
        
        # --- SECTION 2: DETAILED PRICE TABLE ---
        st.markdown("### 📊 Detailed Price Table")
        
        if not filtered_df.empty:
            display_aggrid_table(filtered_df)
        else:
            st.warning("No data matches your filter criteria.")

        # --- DYNAMIC BAR CHART SECTION (using Plotly) ---
        st.markdown("""
         <h3 style='
        color: #00816D; 
        font-size: 1rem; 
        font-weight: 400;
        text-align: left;
         '>
        Performance Chart & Impact
          </h3>
        """, unsafe_allow_html=True)
       

        if not filtered_df.empty:
            # Create tabs for chart selection
            tab1, tab2, tab3, tab4, tab5 = st.tabs(["📈 Daily", "📊 Weekly", "📅 Monthly", "🗓️ Quarterly", "📈 YTD"])
            
            chart_options = {
                "Daily": ("%Day", tab1),
                "Weekly": ("%Week", tab2), 
                "Monthly": ("%Month", tab3),
                "Quarterly": ("%Quarter", tab4),
                "YTD": ("%YTD", tab5)
            }
            
            for chart_label, (selected_column, tab) in chart_options.items():
                with tab:
                    if selected_column in filtered_df.columns:
                        chart_data = filtered_df[['Commodities', selected_column, 'Impact', 'Direct Impact', 'Inverse Impact']].copy()
                        chart_data.dropna(subset=[selected_column], inplace=True)
                        
                        # Filter out commodities with 0% change
                        chart_data = chart_data[chart_data[selected_column] != 0]
                        
                        # Filter out invalid values: NaN, infinite, and exactly -1.0 (which shows as -100%)
                        chart_data = chart_data[chart_data[selected_column].notna()]  # Remove NaN
                        chart_data = chart_data[~chart_data[selected_column].isin([float('inf'), float('-inf')])]  # Remove infinite
                        chart_data = chart_data[chart_data[selected_column] != -1.0]  # Remove -100% (no historical price)
                        
                        if not chart_data.empty:
                            # Separate positive and negative values
                            positive_data = chart_data[chart_data[selected_column] > 0].copy()
                            negative_data = chart_data[chart_data[selected_column] < 0].copy()
                            
                            # Sort positive data descending, negative data ascending (so worst performers are at top)
                            positive_data = positive_data.sort_values(by=selected_column, ascending=False)
                            negative_data = negative_data.sort_values(by=selected_column, ascending=True)
                            
                            # Balance the number of bars between both sides
                            max_items = max(len(positive_data), len(negative_data)) if len(positive_data) > 0 or len(negative_data) > 0 else 0
                            
                            # Pad shorter side with empty entries - ensuring consistent indexing
                            if len(positive_data) < max_items:
                                padding_needed = max_items - len(positive_data)
                                empty_rows = pd.DataFrame({
                                    'Commodities': [''] * padding_needed,
                                    selected_column: [0] * padding_needed,
                                    'Impact': [''] * padding_needed,
                                    'Direct Impact': [''] * padding_needed,
                                    'Inverse Impact': [''] * padding_needed
                                })
                                positive_data = pd.concat([positive_data, empty_rows], ignore_index=True)
                                positive_data = positive_data.reset_index(drop=True)
                            
                            if len(negative_data) < max_items:
                                padding_needed = max_items - len(negative_data)
                                empty_rows = pd.DataFrame({
                                    'Commodities': [''] * padding_needed,
                                    selected_column: [0] * padding_needed,
                                    'Impact': [''] * padding_needed,
                                    'Direct Impact': [''] * padding_needed,
                                    'Inverse Impact': [''] * padding_needed
                                })
                                negative_data = pd.concat([negative_data, empty_rows], ignore_index=True)
                                negative_data = negative_data.reset_index(drop=True)
                            
                            # Create subplot with 2 columns: negative (left) and positive (right)
                            fig = make_subplots(
                                rows=1, cols=2,
                                horizontal_spacing=0.25,
                                column_widths=[0.49, 0.49]
                            )
                            
                            # Calculate max range for consistent positioning
                            max_negative_abs = abs(negative_data[selected_column].min()) if len(negative_data) > 0 and negative_data[selected_column].min() < 0 else 0.01
                            max_positive = positive_data[selected_column].max() if len(positive_data) > 0 and positive_data[selected_column].max() > 0 else 0.01
                            max_range = max(max_negative_abs, max_positive) * 1.5
                            
                            # Add negative performance bars (left side)
                            if len(negative_data) > 0:
                                # Create labels for different positions
                                negative_impact_labels = []  # For outside position (left)
                                negative_percent_labels = []  # For inside position (center)
                                negative_commodities = []     # For annotations (right)
                                
                                for idx, row in negative_data.iterrows():
                                    if row['Commodities'] == '':
                                        negative_impact_labels.append('')
                                        negative_percent_labels.append('')
                                        negative_commodities.append('')
                                    else:
                                        # Impact for outside (left of bar) - NEW LOGIC
                                        # For negative charts: Direct Impact -> stock - negative, Inverse Impact -> stock - positive
                                        direct_impact = row.get('Direct Impact', '') if pd.notna(row.get('Direct Impact', '')) else ''
                                        inverse_impact = row.get('Inverse Impact', '') if pd.notna(row.get('Inverse Impact', '')) else ''
                                        
                                        # Combine impact and percentage into single label
                                        impact_parts = []
                                        if direct_impact:
                                            impact_parts.append(f"{direct_impact} - negative")
                                        if inverse_impact:
                                            impact_parts.append(f"{inverse_impact} - positive")
                                        
                                        if impact_parts:
                                            combined_text = f"{',  '.join(impact_parts)}   {row[selected_column]:.1%}"
                                        else:
                                            combined_text = f"{row[selected_column]:.1%}"
                                        
                                        negative_impact_labels.append(combined_text)
                                        negative_percent_labels.append('')  # Empty since we combined
                                        
                                        # Commodity name for annotation (right of bar)
                                        negative_commodities.append(row['Commodities'])
                                
                                # Main bar with percentage inside
                                fig.add_trace(go.Bar(
                                    y=list(range(len(negative_data))),
                                    x=negative_data[selected_column],
                                    orientation='h',
                                    marker_color=['rgba(225, 29, 72, 0.6)' if x != 0 else 'rgba(0,0,0,0)' for x in negative_data[selected_column]],
                                    text='',  # No text on main bar since we combined
                                    textposition='inside',
                                    hovertemplate='<b>%{customdata}</b>: %{x:.1%}<extra></extra>',
                                    customdata=negative_commodities,
                                    showlegend=False,
                                    name="Decreasing"
                                ), row=1, col=1)
                                
                                # Add impact labels as outside text (using separate invisible bars)
                                fig.add_trace(go.Bar(
                                    y=list(range(len(negative_data))),
                                    x=negative_data[selected_column],
                                    orientation='h',
                                    marker_color='rgba(0,0,0,0)',  # Invisible
                                    text=negative_impact_labels,
                                    textposition='outside',
                                    textfont=dict(size=10),
                                    hoverinfo='skip',
                                    showlegend=False,
                                    name="Impact_Left"
                                ), row=1, col=1)
                                
                                # Add commodity names as annotations at center (x=0, left side)
                                for i in range(len(negative_data)):
                                    if negative_data.iloc[i]['Commodities'] != '':
                                        fig.add_annotation(
                                            x=0,  # Exactly at center
                                            y=i,  # Row index matches bar position
                                            text=negative_data.iloc[i]['Commodities'],
                                            xanchor="left",  # Text extends to the right
                                            yanchor="middle",
                                            font=dict(size=10),
                                            showarrow=False,
                                            xref="x", yref="y"
                                        )
                            
                            # Add positive performance bars (right side)
                            if len(positive_data) > 0:
                                # Create labels for different positions
                                positive_commodity_labels = []  # For outside position (right)
                                positive_percent_labels = []     # For inside position (center)
                                positive_impacts = []            # For annotations (left)
                                
                                for idx, row in positive_data.iterrows():
                                    if row['Commodities'] == '':
                                        positive_commodity_labels.append('')
                                        positive_percent_labels.append('')
                                        positive_impacts.append('')
                                    else:
                                        # Commodity for outside (right of bar)
                                        positive_commodity_labels.append(row['Commodities'])
                                        
                                        # Percentage for inside (center of bar)
                                        positive_percent_labels.append(f"{row[selected_column]:.1%}")
                                        
                                        # Impact for annotation (left of bar) - NEW LOGIC
                                        # For positive charts: Direct Impact -> stock - positive, Inverse Impact -> stock - negative
                                        direct_impact = row.get('Direct Impact', '') if pd.notna(row.get('Direct Impact', '')) else ''
                                        inverse_impact = row.get('Inverse Impact', '') if pd.notna(row.get('Inverse Impact', '')) else ''
                                        
                                        # Combine percentage and impact into single label (percentage first for positive)
                                        impact_parts = []
                                        if direct_impact:
                                            impact_parts.append(f"{direct_impact} - positive")
                                        if inverse_impact:
                                            impact_parts.append(f"{inverse_impact} - negative")
                                        
                                        if impact_parts:
                                            combined_text = f"{row[selected_column]:.1%}   {',  '.join(impact_parts)}"
                                        else:
                                            combined_text = f"{row[selected_column]:.1%}"
                                        
                                        positive_impacts.append(combined_text)
                                
                                # Main bar with percentage inside
                                fig.add_trace(go.Bar(
                                    y=list(range(len(positive_data))),
                                    x=positive_data[selected_column],
                                    orientation='h',
                                    marker_color=['rgba(16, 185, 129, 0.6)' if x != 0 else 'rgba(0,0,0,0)' for x in positive_data[selected_column]],
                                    text='',  # No text on main bar since we combined
                                    textposition='inside',
                                    hovertemplate='<b>%{customdata}</b>: %{x:.1%}<extra></extra>',
                                    customdata=positive_commodity_labels,
                                    showlegend=False,
                                    name="Increasing"
                                ), row=1, col=2)
                                
                                # Add impact labels as outside text (using separate invisible bars)
                                fig.add_trace(go.Bar(
                                    y=list(range(len(positive_data))),
                                    x=positive_data[selected_column],
                                    orientation='h',
                                    marker_color='rgba(0,0,0,0)',  # Invisible
                                    text=positive_impacts,  # Changed to impacts for outside
                                    textposition='outside',
                                    textfont=dict(size=10),
                                    hoverinfo='skip',
                                    showlegend=False,
                                    name="Impact_Right"
                                ), row=1, col=2)
                                
                                # Add commodity names as annotations at center (x=0, right side)
                                for i in range(len(positive_data)):
                                    if positive_data.iloc[i]['Commodities'] != '':
                                        fig.add_annotation(
                                            x=0,  # Exactly at center
                                            y=i,  # Row index matches bar position
                                            text=positive_data.iloc[i]['Commodities'],
                                            xanchor="right",  # Text extends to the left
                                            yanchor="middle",
                                            font=dict(size=10),
                                            showarrow=False,
                                            xref="x2", yref="y2"
                                        )
                            
                            chart_height = max(300, max_items * 20)
                            
                            # Update layout
                            fig.update_layout(
                                barmode='overlay',
                                template="plotly_white",
                                height=chart_height,
                                margin=dict(l=200, r=200, t=60, b=20),
                                font=dict(family="Manrope, sans-serif", size=11),
                                title=dict(
                                    text=f"<b>{chart_label} Performance </b>",
                                    x=0.5,
                                    xanchor='center',
                                    y=0.97
                                ),
                                showlegend=False
                            )
                            
                            # Update axes - Hide x-axis completely and use autoscale
                            
                            # For negative values (left side), autoscale
                            fig.update_xaxes(
                                visible=False,
                                showgrid=False,
                                zeroline=False,
                                autorange=True,
                                row=1, col=1
                            )
                            # For positive values (right side), autoscale
                            fig.update_xaxes(
                                visible=False,
                                showgrid=False,
                                zeroline=False,
                                autorange=True,
                                row=1, col=2
                            )
                            # Hide y-axis ticks and labels since we show info in text
                            fig.update_yaxes(
                                autorange="reversed", 
                                showticklabels=False, 
                                showgrid=False,
                                zeroline=False,
                                row=1, col=1
                            )
                            fig.update_yaxes(
                                autorange="reversed", 
                                showticklabels=False, 
                                showgrid=False,
                                zeroline=False,
                                row=1, col=2
                            )
                            
                            st.plotly_chart(fig, width='stretch')
                        else:
                            st.info(f"No data available for {chart_label} performance with the selected filters (after removing 0% changes).")
                    else:
                        st.warning(f"Could not generate chart. The required data column '{selected_column}' is missing.")
        else:
            st.warning("No data to display in the chart with the current filters.")

        # --- COMMODITY PRICE TRENDS SECTION ---
        st.markdown("""
            <h3 style='
                color: #00816D; 
                font-size: 1rem; 
                font-weight: 400;
                text-align: left;
            '>
                Commodity Price Trends
            </h3>
        """, unsafe_allow_html=True)

        # Multi-select for commodities with alphabetical ordering
        if not filtered_df.empty:
            available_commodities = sorted(filtered_df['Commodities'].unique())
            selected_commodities_chart = st.multiselect(
                "Select commodities to display (Max 5)",
                available_commodities,
                default=available_commodities[:min(2, len(available_commodities))],
                max_selections=5
            )
            
            if selected_commodities_chart:
                # Get stock tickers for selected commodities - filter the dataframe first
                chart_filtered_df = filtered_df[filtered_df['Commodities'].isin(selected_commodities_chart)]
                stock_tickers = get_stock_tickers_from_impact(chart_filtered_df)
                
                # Determine if we need to show stock charts
                show_stocks = len(stock_tickers) > 0
                
                if show_stocks:
                    # Create two columns for side-by-side charts
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("#### 📈 Commodity Prices")
                else:
                    # Single column for commodity chart only
                    col1 = st.container()
                    with col1:
                        pass  # Just commodity chart, no header needed
                
                # Filter data for selected commodities and date range
                filtered_chart_data = df_data[
                    (df_data['Commodities'].isin(selected_commodities_chart)) &
                    (df_data['Date'] >= pd.to_datetime(start_date)) &
                    (df_data['Date'] <= pd.to_datetime(end_date))
                ].copy()
                
                # Apply interval grouping
                if selected_interval == "Weekly":
                    filtered_chart_data['Date'] = pd.to_datetime(filtered_chart_data['Date']).dt.to_period('W').dt.to_timestamp()
                    filtered_chart_data = filtered_chart_data.groupby(['Date', 'Commodities'])['Price'].mean().reset_index()
                elif selected_interval == "Monthly":
                    filtered_chart_data['Date'] = pd.to_datetime(filtered_chart_data['Date']).dt.to_period('M').dt.to_timestamp()
                    filtered_chart_data = filtered_chart_data.groupby(['Date', 'Commodities'])['Price'].mean().reset_index()
                elif selected_interval == "Quarterly":
                    filtered_chart_data['Date'] = pd.to_datetime(filtered_chart_data['Date']).dt.to_period('Q').dt.to_timestamp()
                    filtered_chart_data = filtered_chart_data.groupby(['Date', 'Commodities'])['Price'].mean().reset_index()
                
                # Create commodity price chart
                fig_commodity = go.Figure()
                
                # Updated soft colors for commodities
                commodity_colors = [
                    'rgba(0, 129, 109, 0.7)',    # Teal
                    'rgba(59, 130, 246, 0.7)',   # Blue
                    'rgba(168, 85, 247, 0.7)',   # Purple
                    'rgba(251, 146, 60, 0.7)',   # Orange
                    'rgba(236, 72, 153, 0.7)'    # Pink
                ]
                
                for i, commodity in enumerate(selected_commodities_chart):
                    commodity_data = filtered_chart_data[filtered_chart_data['Commodities'] == commodity]
                    if not commodity_data.empty:
                        fig_commodity.add_trace(go.Scatter(
                            x=commodity_data['Date'],
                            y=commodity_data['Price'],
                            mode='lines',
                            name=commodity,
                            line=dict(width=2, color=commodity_colors[i % len(commodity_colors)]),
                            hovertemplate='<b>%{fullData.name}</b><br>Date: %{x}<br>Price: %{y:,.2f}<extra></extra>'
                        ))
                
                fig_commodity.update_layout(
                    xaxis_title="Date",
                    yaxis_title="Price",
                    hovermode='x unified',
                    height=400,
                    plot_bgcolor='white',
                    paper_bgcolor='white',
                    font=dict(family="Inter, sans-serif", size=12),
                    xaxis=dict(
                        showgrid=True,
                        gridcolor='#F3F4F6',
                        zeroline=False
                    ),
                    yaxis=dict(
                        showgrid=True,
                        gridcolor='#F3F4F6',
                        zeroline=False
                    ),
                    legend=dict(
                        orientation="h",
                        yanchor="bottom",
                        y=1.02,
                        xanchor="right",
                        x=1
                    ),
                    margin=dict(l=50, r=20, t=40, b=50)
                )
                
                # Display commodity chart
                with col1:
                    st.plotly_chart(fig_commodity, width='stretch')
                
                # Display stock charts if available
                if show_stocks:
                    with col2:
                        st.markdown("#### 💹 Related Vietnamese Stocks")
                        
                        # Progress bar for stock data fetching
                        progress_bar = st.progress(0)
                        status_text = st.empty()
                        
                        # Fetch stock data
                        status_text.text("Fetching stock data...")
                        stock_data = fetch_multiple_stocks(
                            stock_tickers, 
                            start_date, 
                            end_date, 
                            selected_interval,
                            progress_callback=lambda i, total: progress_bar.progress(i / total)
                        )
                        
                        # Clear progress indicators
                        progress_bar.empty()
                        status_text.empty()
                        
                        if stock_data:
                            # Create stock price chart
                            fig_stocks = go.Figure()
                            
                            # Soft colors for stocks
                            stock_colors = [
                                'rgba(239, 68, 68, 0.6)',    # Red
                                'rgba(34, 197, 94, 0.6)',    # Green
                                'rgba(251, 191, 36, 0.6)',   # Amber
                                'rgba(99, 102, 241, 0.6)',   # Indigo
                                'rgba(236, 72, 153, 0.6)'    # Pink
                            ]
                            
                            for j, (ticker, stock_df) in enumerate(stock_data.items()):
                                if not stock_df.empty:
                                    # Ensure datetime type for comparison
                                    stock_df['Date'] = pd.to_datetime(stock_df['Date'])
                                    
                                    # Filter by date range (with datetime objects)
                                    stock_df = stock_df[
                                        (stock_df['Date'] >= pd.to_datetime(start_date)) &
                                        (stock_df['Date'] <= pd.to_datetime(end_date))
                                    ]
                                    
                                    if not stock_df.empty:
                                        fig_stocks.add_trace(go.Scatter(
                                            x=stock_df['Date'],
                                            y=stock_df['Close'],
                                            mode='lines',
                                            name=ticker,
                                            line=dict(width=2, color=stock_colors[j % len(stock_colors)]),
                                            hovertemplate=f'<b>{ticker}</b><br>Date: %{{x}}<br>Price: %{{y:,.0f}} VND<extra></extra>'
                                        ))
                            
                            fig_stocks.update_layout(
                                xaxis_title="Date",
                                yaxis_title="Price (VND)",
                                hovermode='x unified',
                                height=400,
                                plot_bgcolor='white',
                                paper_bgcolor='white',
                                font=dict(family="Inter, sans-serif", size=12),
                                xaxis=dict(
                                    showgrid=True,
                                    gridcolor='#F3F4F6',
                                    zeroline=False
                                ),
                                yaxis=dict(
                                    showgrid=True,
                                    gridcolor='#F3F4F6',
                                    zeroline=False
                                ),
                                legend=dict(
                                    orientation="h",
                                    yanchor="bottom",
                                    y=1.02,
                                    xanchor="right",
                                    x=1
                                ),
                                margin=dict(l=50, r=20, t=40, b=50)
                            )
                            
                            st.plotly_chart(fig_stocks, width='stretch')
                        else:
                            st.info("No stock data available for the selected period")
            else:
                st.info("Please select at least one commodity to display the price trend chart.")
        else:
            st.warning("No data available for price trends with the selected filters.")

        # --- AI INTELLIGENCE SECTION ---
        # Render AI Intelligence as a separate fragment that loads independently
        if ai_orchestrator and ai_processor:
            force_refresh = st.session_state.get('ai_refresh', False)
            render_ai_intelligence_section(
                ai_orchestrator=ai_orchestrator,
                ai_processor=ai_processor,
                ai_database=ai_database,
                analysis_df=filtered_df,
                df_data=df_data,
                ai_timeframe=ai_timeframe if 'ai_timeframe' in locals() else DEFAULT_TIMEFRAME,
                selected_ai_commodities=None,  # Now using main filters instead of separate AI commodity filter
                data_last_updated=data_last_updated,
                force_refresh=force_refresh
            )
        # --- Z-SCORE ANALYSIS SECTION (DEBUGGING) ---
        st.markdown("---")
        st.markdown("""
            <h3 style='
                color: #00816D;
                font-size: 1rem;
                font-weight: 400;
                text-align: left;
            '>
                📊 Z-Score Analysis (Debugging Table)
            </h3>
        """, unsafe_allow_html=True)
        
        # Add controls
        col1, col2, col3 = st.columns([1, 1, 2])
        with col1:
            zscore_window = st.slider(
                "Z-Score Window",
                min_value=30,
                max_value=60,
                value=30,
                step=5,
                help="Number of observations for rolling statistics"
            )

        with col2:
            frequency_aware = st.checkbox(
                "Frequency-Aware Mode",
                value=True,
                help="Adjust Z-scores based on detected update frequency (daily/weekly)"
            )

        if frequency_aware:
            st.info(f"🎯 **Frequency-Aware Mode**: Z-scores are calculated using {zscore_window} observations at each commodity's native frequency (daily/weekly), providing accurate volatility measures.")
        else:
            st.info(f"📊 **Raw Mode**: Z-scores show how many standard deviations today's return is from the {zscore_window}-day rolling mean. Weekly commodities may show inflated values.")

        # Calculate Z-scores for all commodities
        zscore_results = []

        for commodity in filtered_df['Commodities'].unique():
            # Get price series for this commodity
            commodity_data = df_data[df_data['Commodities'] == commodity].copy()

            if not commodity_data.empty and len(commodity_data) > 1:
                # Sort by date and set index
                commodity_data = commodity_data.sort_values('Date')
                price_series = commodity_data.set_index('Date')['Price']
                price_series.name = commodity

                if frequency_aware:
                    # Use frequency-aware Z-score calculation
                    zscore_df = compute_frequency_aware_zscore(price_series, lookback=90, window=zscore_window)

                    if not zscore_df.empty:
                        latest_row = zscore_df.iloc[-1]
                        frequency = latest_row['Frequency'].capitalize() if 'Frequency' in zscore_df.columns else 'Unknown'

                        # Determine window label based on frequency
                        window_label = f"{zscore_window}W" if frequency == 'Weekly' else f"{zscore_window}D"

                        zscore_results.append({
                            'Commodity': commodity,
                            'Update Frequency': frequency,
                            'Latest Price': latest_row['Price'],
                            'Return (%)': latest_row['Return'] * 100 if pd.notna(latest_row['Return']) else None,
                            f'{window_label} Mean (%)': latest_row['RollingMean'] * 100 if pd.notna(latest_row['RollingMean']) else None,
                            f'{window_label} Std Dev (%)': latest_row['RollingStd'] * 100 if pd.notna(latest_row['RollingStd']) else None,
                            'Adjusted Z-Score': latest_row['ZScore'],
                            'Flag': latest_row['Flag'] if 'Flag' in zscore_df.columns else '',
                            'Alert Level': latest_row['Flag'].capitalize() if 'Flag' in zscore_df.columns and latest_row['Flag'] else 'Normal'
                        })
                else:
                    # Use original Z-score calculation
                    frequency = detect_frequency(price_series, lookback=90)
                    zscore_df = compute_zscore(price_series, window=zscore_window)

                    if not zscore_df.empty:
                        latest_row = zscore_df.iloc[-1]

                        zscore_results.append({
                            'Commodity': commodity,
                            'Update Frequency': frequency.capitalize(),
                            'Latest Price': latest_row['Price'],
                            'Daily Return (%)': latest_row['Return'] * 100 if pd.notna(latest_row['Return']) else None,
                            f'{zscore_window}D Mean Return (%)': latest_row['RollingMean'] * 100 if pd.notna(latest_row['RollingMean']) else None,
                            f'{zscore_window}D Std Dev (%)': latest_row['RollingStd'] * 100 if pd.notna(latest_row['RollingStd']) else None,
                            'Raw Z-Score': latest_row['ZScore'],
                            'Status': 'Unusual' if pd.notna(latest_row['ZScore']) and abs(latest_row['ZScore']) > 2 else 'Normal'
                        })
        
        # Create DataFrame and display
        if zscore_results:
            zscore_table = pd.DataFrame(zscore_results)
            
            # Sort by absolute Z-score (most unusual first)
            if frequency_aware:
                zscore_col = 'Adjusted Z-Score'
            else:
                zscore_col = 'Raw Z-Score'

            zscore_table['Abs_ZScore'] = zscore_table[zscore_col].abs()
            zscore_table = zscore_table.sort_values('Abs_ZScore', ascending=False)
            zscore_table = zscore_table.drop('Abs_ZScore', axis=1)
            
            # Format the display
            st.markdown("#### Latest Z-Scores for All Commodities")
            
            # Apply styling to highlight unusual values
            def highlight_zscore(val):
                if pd.isna(val):
                    return ''
                if abs(val) > 3:
                    return 'background-color: #ff4444; color: white'
                elif abs(val) > 2:
                    return 'background-color: #ffaa00; color: white'
                elif abs(val) > 1:
                    return 'background-color: #ffff44'
                return ''

            # Apply styling to frequency column
            def style_frequency(val):
                if val == 'Daily':
                    return 'color: #00816D; font-weight: bold'
                elif val == 'Weekly':
                    return 'color: #1f77b4; font-weight: bold'
                return ''

            # Apply styling to alert levels (for frequency-aware mode)
            def style_alert(val):
                if val == 'Extreme':
                    return 'background-color: #ff4444; color: white; font-weight: bold'
                elif val == 'Notable':
                    return 'background-color: #ffaa00; color: white; font-weight: bold'
                elif val == 'Notice':
                    return 'background-color: #ffff44; font-weight: bold'
                return ''
            
            # Format numeric columns based on mode
            if frequency_aware:
                # Build dynamic format dict for frequency-aware mode
                format_dict = {'Latest Price': '{:.2f}', 'Return (%)': '{:.2f}', 'Adjusted Z-Score': '{:.2f}'}

                # Add dynamic column formatting
                for col in zscore_table.columns:
                    if 'Mean (%)' in col or 'Std Dev (%)' in col:
                        format_dict[col] = '{:.3f}'

                styled_table = zscore_table.style.map(
                    highlight_zscore,
                    subset=['Adjusted Z-Score']
                ).map(
                    style_frequency,
                    subset=['Update Frequency']
                ).map(
                    style_alert,
                    subset=['Alert Level'] if 'Alert Level' in zscore_table.columns else []
                ).format(format_dict, na_rep='-')
            else:
                format_dict = {
                    'Latest Price': '{:.2f}',
                    'Daily Return (%)': '{:.2f}',
                    f'{zscore_window}D Mean Return (%)': '{:.3f}',
                    f'{zscore_window}D Std Dev (%)': '{:.3f}',
                    'Raw Z-Score': '{:.2f}'
                }

                styled_table = zscore_table.style.map(
                    highlight_zscore,
                    subset=['Raw Z-Score']
                ).map(
                    style_frequency,
                    subset=['Update Frequency']
                ).format(format_dict, na_rep='-')
            
            st.dataframe(styled_table, width='stretch', height=400)
            
            # Summary statistics
            col1, col2, col3, col4 = st.columns(4)

            if frequency_aware:
                with col1:
                    extreme_count = (zscore_table['Alert Level'] == 'Extreme').sum() if 'Alert Level' in zscore_table.columns else 0
                    notable_count = (zscore_table['Alert Level'] == 'Notable').sum() if 'Alert Level' in zscore_table.columns else 0
                    st.metric("Alerts", f"Extreme:{extreme_count} Notable:{notable_count}")
                with col2:
                    avg_zscore = zscore_table['Adjusted Z-Score'].mean()
                    st.metric("Avg Adjusted Z-Score", f"{avg_zscore:.2f}" if pd.notna(avg_zscore) else "-")
                with col3:
                    max_zscore = zscore_table['Adjusted Z-Score'].abs().max()
                    st.metric("Max |Adjusted Z-Score|", f"{max_zscore:.2f}" if pd.notna(max_zscore) else "-")
            else:
                with col1:
                    unusual_count = (zscore_table['Status'] == 'Unusual').sum() if 'Status' in zscore_table.columns else 0
                    st.metric("Unusual Movements (|Z| > 2)", unusual_count)
                with col2:
                    avg_zscore = zscore_table['Raw Z-Score'].mean()
                    st.metric("Average Raw Z-Score", f"{avg_zscore:.2f}" if pd.notna(avg_zscore) else "-")
                with col3:
                    max_zscore = zscore_table['Raw Z-Score'].abs().max()
                    st.metric("Max |Raw Z-Score|", f"{max_zscore:.2f}" if pd.notna(max_zscore) else "-")

            with col4:
                daily_count = (zscore_table['Update Frequency'] == 'Daily').sum()
                weekly_count = (zscore_table['Update Frequency'] == 'Weekly').sum()
                st.metric("Update Frequency", f"Daily: {daily_count} | Weekly: {weekly_count}")
            
            # Additional insights
            st.markdown("#### Interpretation Guide:")

            if frequency_aware:
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"""
                    **Frequency-Adjusted Z-Score:**
                    - **Z = 0**: Return equals historical average at native frequency
                    - **|Z| ≥ 1**: 📢 **Notice** - Worth monitoring
                    - **|Z| ≥ 2**: 🔶 **Notable** - Significant move
                    - **|Z| ≥ 3**: 🔴 **Extreme** - Very unusual move

                    *Z-scores use {zscore_window} observations at each commodity's native frequency*
                    """)

                with col2:
                    st.markdown("""
                    **Update Frequency Detection:**
                    - **Daily**: >50% of days have price changes
                    - **Weekly**: ≤50% of days have price changes

                    **Advantage**: Weekly commodities are resampled to weekly frequency,
                    eliminating inflated volatility from forward-filled zeros.
                    """)
            else:
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"""
                    **Raw Z-Score Interpretation:**
                    - **Z-Score = 0**: Return is exactly at the {zscore_window}-day average
                    - **|Z-Score| < 1**: Normal daily movement (within 1 standard deviation)
                    - **1 < |Z-Score| < 2**: Moderately unusual movement
                    - **2 < |Z-Score| < 3**: Unusual movement (highlighted in orange)
                    - **|Z-Score| > 3**: Very unusual movement (highlighted in red)
                    """)

                with col2:
                    st.markdown("""
                    **Update Frequency:**
                    - **Daily**: >50% of days have price changes
                    - **Weekly**: ≤50% of days have price changes

                    ⚠️ **Warning**: Weekly commodities may show inflated Z-scores due to
                    forward-filled zeros affecting volatility calculations.
                    """)

            # Price Bands Chart Section
            st.markdown("---")
            st.markdown("""
            <h3 style='
                color: #00816D;
                font-size: 1rem;
                font-weight: 400;
                text-align: left;
            '>
                📈 Price Bands Analysis
            </h3>
            """, unsafe_allow_html=True)

            # Chart controls
            col1, col2, col3 = st.columns([2, 1, 1])

            with col1:
                # Commodity selector
                available_commodities = sorted(filtered_df['Commodities'].unique())
                selected_commodity = st.selectbox(
                    "Select Commodity for Analysis",
                    available_commodities,
                    index=0 if available_commodities else None,
                    key="price_bands_commodity"
                )

            with col2:
                # N-value selector for standard deviations
                n_std = st.slider(
                    "Std Dev Bands (n)",
                    min_value=1.0,
                    max_value=3.0,
                    value=2.0,
                    step=0.5,
                    help="Number of standard deviations for price bands"
                )

            with col3:
                # Window selector (same as zscore window)
                band_window = st.slider(
                    "Moving Avg Window",
                    min_value=30,
                    max_value=60,
                    value=zscore_window,
                    step=5,
                    help="Window for calculating moving average and bands"
                )

            if selected_commodity:
                # Get data for selected commodity
                commodity_data = df_data[df_data['Commodities'] == selected_commodity].copy()

                if not commodity_data.empty and len(commodity_data) > band_window:
                    # Sort by date
                    commodity_data = commodity_data.sort_values('Date')
                    commodity_data = commodity_data.set_index('Date')

                    # Calculate rolling statistics on price (not returns)
                    commodity_data['MA'] = commodity_data['Price'].rolling(window=band_window).mean()
                    commodity_data['Std'] = commodity_data['Price'].rolling(window=band_window).std()

                    # Calculate bands
                    commodity_data['Upper_Band'] = commodity_data['MA'] + (n_std * commodity_data['Std'])
                    commodity_data['Lower_Band'] = commodity_data['MA'] - (n_std * commodity_data['Std'])

                    # Create the plot
                    fig = go.Figure()

                    # Add price line
                    fig.add_trace(go.Scatter(
                        x=commodity_data.index,
                        y=commodity_data['Price'],
                        mode='lines',
                        name='Spot Price',
                        line=dict(color='#1f77b4', width=2),
                        hovertemplate='Date: %{x|%Y-%m-%d}<br>Price: $%{y:.2f}<extra></extra>'
                    ))

                    # Add moving average
                    fig.add_trace(go.Scatter(
                        x=commodity_data.index,
                        y=commodity_data['MA'],
                        mode='lines',
                        name=f'{band_window}D Moving Avg',
                        line=dict(color='#ff7f0e', width=2, dash='dash'),
                        hovertemplate='Date: %{x|%Y-%m-%d}<br>MA: $%{y:.2f}<extra></extra>'
                    ))

                    # Add upper band
                    fig.add_trace(go.Scatter(
                        x=commodity_data.index,
                        y=commodity_data['Upper_Band'],
                        mode='lines',
                        name=f'Upper Band (+{n_std}σ)',
                        line=dict(color='#2ca02c', width=1.5, dash='dot'),
                        hovertemplate='Date: %{x|%Y-%m-%d}<br>Upper: $%{y:.2f}<extra></extra>'
                    ))

                    # Add lower band
                    fig.add_trace(go.Scatter(
                        x=commodity_data.index,
                        y=commodity_data['Lower_Band'],
                        mode='lines',
                        name=f'Lower Band (-{n_std}σ)',
                        line=dict(color='#d62728', width=1.5, dash='dot'),
                        fill='tonexty',
                        fillcolor='rgba(128, 128, 128, 0.1)',
                        hovertemplate='Date: %{x|%Y-%m-%d}<br>Lower: $%{y:.2f}<extra></extra>'
                    ))

                    # Update layout
                    fig.update_layout(
                        title=f"{selected_commodity} - Price Bands Analysis",
                        xaxis_title="Date",
                        yaxis_title="Price",
                        height=500,
                        hovermode='x unified',
                        showlegend=True,
                        legend=dict(
                            yanchor="top",
                            y=0.99,
                            xanchor="left",
                            x=0.01,
                            bgcolor="rgba(255, 255, 255, 0.8)"
                        ),
                        xaxis=dict(
                            rangeslider=dict(visible=True, thickness=0.05),
                            type="date"
                        )
                    )

                    # Display the chart
                    st.plotly_chart(fig, use_container_width=True)

                    # Show current position relative to bands
                    latest = commodity_data.iloc[-1]
                    if pd.notna(latest['MA']) and pd.notna(latest['Std']):
                        col1, col2, col3, col4 = st.columns(4)

                        with col1:
                            st.metric("Current Price", f"${latest['Price']:.2f}")

                        with col2:
                            st.metric(f"{band_window}D Average", f"${latest['MA']:.2f}")

                        with col3:
                            # Calculate position within bands
                            if latest['Price'] > latest['Upper_Band']:
                                position = "Above Upper Band"
                                color = "🔴"
                            elif latest['Price'] < latest['Lower_Band']:
                                position = "Below Lower Band"
                                color = "🔵"
                            else:
                                position = "Within Bands"
                                color = "🟢"
                            st.metric("Band Position", f"{color} {position}")

                        with col4:
                            # Calculate how many std devs from mean
                            if latest['Std'] > 0:
                                current_z = (latest['Price'] - latest['MA']) / latest['Std']
                                st.metric("Current σ from Mean", f"{current_z:.2f}σ")
                            else:
                                st.metric("Current σ from Mean", "N/A")

                else:
                    st.warning(f"Not enough data points (need >{band_window}) to calculate price bands for {selected_commodity}.")
            else:
                st.info("Please select a commodity to view price bands analysis.")

        else:
            st.warning("Not enough data to calculate Z-scores.")
            
    else:
        st.warning("No data available for analysis.")
else:
    st.error("Failed to load data. Please check your data source.")