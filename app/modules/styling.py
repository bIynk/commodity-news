import streamlit as st
import pandas as pd
import os
from st_aggrid import AgGrid, GridOptionsBuilder, JsCode


def configure_page_style():
    """
    Applies custom CSS for the page with clean styling without background image.
    """
    page_style = f"""
    <style>
    
    @import url('https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;700&display=swap');

    /* Define color palette */
    :root {{
        --primary-teal: #00816D;
        --secondary-red: #e11d48;
        --accent-green: #10b981;
        --bg-light: #f8fafc;
        --bg-white: #ffffff;
    }}

    /* Apply font and base styles */
    html, body, .st-emotion-cache-10trblm {{
        font-family: 'Manrope', sans-serif;
    }}
    
    /* Main App Background - Clean light background */
    .stApp {{
        background-color: var(--bg-light);
    }}

    /* Sidebar Styling - Using default Streamlit background */
    /* [data-testid="stSidebar"] > div:first-child {{
        background-color: var(--primary-teal);
    }} */
    
    /* Sidebar text styling - Using default Streamlit colors */
    /* [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3,
    [data-testid="stSidebar"] h4,
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] .st-emotion-cache-16txtl3,
    [data-testid="stSidebar"] .st-emotion-cache-10trblm {{
        color: #FFFFFF;
    }}
    [data-testid="stSidebar"] .st-emotion-cache-1g8p9hb {{
         color: #E0E0E0;
    }} */
    
    /* Sidebar navigation links - Using default Streamlit colors */
    /* [data-testid="stSidebarNav"] a span {{
        color: #FFFFFF;
    }}
    [data-testid="stSidebarNav"] a[aria-current="page"] span {{
        color: #FFFFFF;
    }} */
    
    /* Hide sidebar collapse button text */
    [data-testid="stSidebarCollapseButton"] p {{
        display: none;
    }}

    /* Main Content Styling */
    .block-container {{
        background-color: var(--bg-white);
        padding: 2rem 3rem;
        border-radius: 0.75rem;
        margin: 1rem;
        box-shadow: 0 1px 3px 0 rgb(0 0 0 / 0.1);
    }}
    
    /* Header styles */
    h1, h2, h3 {{
        color: var(--primary-teal);
        font-weight: 700;
    }}
    .st-emotion-cache-10trblm, .st-emotion-cache-16txtl3 {{
        color: var(--primary-teal);
    }}
   
    /* Content wrapper styles */
    .metric-container-wrapper, .chart-wrapper {{
        background-color: var(--bg-white);
        padding: 1.5rem;
        border-radius: 0.75rem;
        box-shadow: 0 1px 3px 0 rgb(0 0 0 / 0.1);
        margin-bottom: 2rem;
        border: 1px solid #e2e8f0;
    }}
    
    </style>
    """
    st.markdown(page_style, unsafe_allow_html=True)

def display_market_metrics(df: pd.DataFrame):
    """
    Displays the Key Market Metrics with smaller cards.
    """
    if df.empty:
        st.info("No data available to display Key Market Metrics for the selected filters.")
        return

    css_style = """
    <style>
        .metrics-section {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 30px;
            margin-bottom: 30px;
        }
        .metric-container {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 15px;
        }
        .metric-card {
            background-color: #FFFFFF;
            border-radius: 8px;
            padding: 10px;
            text-align: center;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            height: 90px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
            border-top: 4px solid;
            color: #333;
        }
        
        .metric-card .title {
            font-size: 10px;
            font-weight: 500;
            text-transform: uppercase;
            margin-bottom: 5px;
        }
        .metric-card .commodity-name {
            font-size: 14px;
            font-weight: 600;
            margin: auto 0;
            line-height: 1.1;
        }
        .metric-card .value {
            font-size: 13px;
            font-weight: 600;
        }
        .empty-card {
            background-color: #f8fafc;
            border: 2px dashed #cbd5e1;
            color: #64748b;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 11px;
            font-weight: 500;
        }
        .bullish-card .title { color: var(--accent-green); }
        .bullish-card { border-color: var(--accent-green); }
        .bullish-card .value { color: var(--accent-green); }
        .bearish-card .title { color: var(--secondary-red); }
        .bearish-card { border-color: var(--secondary-red); }
        .bearish-card .value { color: var(--secondary-red); }

        .avg-card .title { color: #ea580c; }
        .avg-card { border-color: #ea580c; }
        .avg-card .value { color: #ea580c; }

        .leader-card .title { color: #7c3aed; }
        .leader-card { border-color: #7c3aed; }
        .leader-card .value { color: #7c3aed; }
    </style>
    """
    
    # Section headers
    headers_html = """
    <div class="metrics-section">
        <div>
            <h3 style='
                color: #00816D; 
                font-size: 1.3rem; 
                font-weight: 500;
                text-align: left;
                margin-bottom: 15px;
            '>
                Key Market Metrics
            </h3>
        </div>
        <div>
            <h3 style='
                color: #00816D; 
                font-size: 1.3rem; 
                font-weight: 500;
                text-align: left;
                margin-bottom: 15px;
            '>
                Sector Metrics
            </h3>
        </div>
    </div>
    """
    
    # Calculations - Filter out invalid values first
    # Filter for valid %Week values (not NaN, not infinite, not -1.0 which shows as -100%)
    # Also exclude calculated tickers from KPI metrics
    # Also exclude stale data (> 7 days old)
    valid_week_df = df[
        df['%Week'].notna() & 
        ~df['%Week'].isin([float('inf'), float('-inf'), -1.0]) &
        (df['%Week'] != -1.0) &  # Exclude -100% (no historical price)
        df['Commodities'].notna() &  # Ensure commodity name exists
        (~df['Is_Calculated'] if 'Is_Calculated' in df.columns else True) &  # Exclude calculated tickers
        (~df['Is_Stale'] if 'Is_Stale' in df.columns else True)  # Exclude stale data
    ].copy()
    
    
    most_bullish = valid_week_df.loc[valid_week_df['%Week'].idxmax()] if not valid_week_df.empty and valid_week_df['%Week'].notna().any() else None
    most_bearish = valid_week_df.loc[valid_week_df['%Week'].idxmin()] if not valid_week_df.empty and valid_week_df['%Week'].notna().any() else None
    
    # Placeholder for highest volatility (to be calculated later)
    highest_volatility = "TBD"
    
    # Filter for valid %Month values
    valid_month_df = df[
        df['%Month'].notna() & 
        ~df['%Month'].isin([float('inf'), float('-inf'), -1.0]) &
        (df['%Month'] != -1.0) &  # Exclude -100% (no historical price)
        df['Commodities'].notna() &  # Ensure commodity name exists
        (~df['Is_Calculated'] if 'Is_Calculated' in df.columns else True) &  # Exclude calculated tickers
        (~df['Is_Stale'] if 'Is_Stale' in df.columns else True)  # Exclude stale data
    ].copy()
    
    monthly_leader = valid_month_df.loc[valid_month_df['%Month'].idxmax()] if not valid_month_df.empty and valid_month_df['%Month'].notna().any() else None
    
    # Sector calculations - use only valid data
    sector_performance = valid_week_df.groupby('Sector')['%Week'].mean()
    strongest_sector = sector_performance.idxmax() if not sector_performance.empty else 'N/A'
    strongest_sector_perf = sector_performance.max() if not sector_performance.empty else 0
    
    # Count commodities with extreme moves (>±2%) - exclude invalid values
    extreme_moves_count = len(valid_week_df[abs(valid_week_df['%Week']) > 0.02]) if not valid_week_df.empty else 0

    # HTML Content
    html_content = f"""
    <div class="metrics-section">
        <div class="metric-container">
            <div class="metric-card bullish-card">
                <div class="title">↑ Most Bullish</div>
                <div class="commodity-name">{most_bullish['Commodities'] if most_bullish is not None else 'N/A'}</div>
                <div class="value">{f"{most_bullish['%Week']:.1%}" if most_bullish is not None and pd.notna(most_bullish['%Week']) else 'N/A'}</div>
            </div>
            <div class="metric-card bearish-card">
                <div class="title">↓ Most Bearish</div>
                <div class="commodity-name">{most_bearish['Commodities'] if most_bearish is not None else 'N/A'}</div>
                <div class="value">{f"{most_bearish['%Week']:.1%}" if most_bearish is not None and pd.notna(most_bearish['%Week']) else 'N/A'}</div>
            </div>
            <div class="metric-card avg-card">
                <div class="title">Highest Volatility</div>
                <div class="commodity-name" style="font-size: 20px;">{highest_volatility}</div>
                <div class="value">To Calculate</div>
            </div>
            <div class="metric-card leader-card">
                <div class="title">🏆 Monthly Leader</div>
                <div class="commodity-name">{monthly_leader['Commodities'] if monthly_leader is not None else 'N/A'}</div>
                <div class="value">{f"{monthly_leader['%Month']:.1%}" if monthly_leader is not None and pd.notna(monthly_leader['%Month']) else 'N/A'}</div>
            </div>
        </div>
        <div class="metric-container">
            <div class="metric-card leader-card">
                <div class="title">Strongest Sector</div>
                <div class="commodity-name">{strongest_sector}</div>
                <div class="value">{f"{strongest_sector_perf:.1%}" if pd.notna(strongest_sector_perf) else 'N/A'}</div>
            </div>
            <div class="metric-card avg-card">
                <div class="title">Extreme Moves (>±2%)</div>
                <div class="commodity-name" style="font-size: 20px;">{extreme_moves_count}</div>
                <div class="value">Commodities</div>
            </div>
            <div class="metric-card empty-card">
                <div>Future KPI 3</div>
            </div>
            <div class="metric-card empty-card">
                <div>Future KPI 4</div>
            </div>
        </div>
    </div>
    """
    
    st.markdown(css_style + headers_html + html_content, unsafe_allow_html=True)

def style_dataframe(df: pd.DataFrame):
    df_to_style = df.copy()

    # Định dạng hiển thị (giữ nguyên)
    format_dict = {
        'Current Price': '{:,.0f}',
        '30D Avg': '{:,.0f}',
        '52W High': '{:,.0f}',
        '52W Low': '{:,.0f}',
        '%Day': '{:.1%}',
        '%Week': '{:.1%}',
        '%Month': '{:.1%}',
        '%Quarter': '{:.1%}',
        '%YTD': '{:.1%}',
    }
    percent_cols = ['%Day', '%Week', '%Month', '%Quarter', '%YTD']

    # Hàm style (giữ nguyên)
    def style_percent_cell(val):
        if pd.isna(val):
            return 'font-weight: 300;'
        
        if val > 0:
            bg_intensity = min(abs(val) * 10, 1.5)
            return f'background-color: rgba(16, 185, 129, {bg_intensity}); font-weight: 300;'
        elif val < 0:
            bg_intensity = min(abs(val) * 10, 1.5)
            return f'background-color: rgba(225, 29, 72, {bg_intensity}); font-weight: 300;'
        else:
            return 'background-color: #FFFFFF; font-weight: 300;'

    styler = df_to_style.style.format(format_dict, na_rep='—')
    
    for col in percent_cols:
        if col in df_to_style.columns:
            styler = styler.map(style_percent_cell, subset=[col])
    
    text_columns = ['Commodities', 'Sector', 'Nation', 'Change type', 'Impact']
    
    table_styles = [
        {
            'selector': '',
            'props': [
                ('font-family', 'Manrope, sans-serif'),
                ('color', '#000000'),
                ('font-size', '12px'),
            ]
        },
        # ĐÃ XÓA selector 'table' khỏi đây
        {
            'selector': 'td',
            'props': [
                ('padding', '8px'),
                ('border-bottom', '1px solid #f0f0f0'),
                ('font-weight', '400'),
                ('text-align', 'right'),
            ]
        },
        {
            'selector': 'th',
            'props': [
                # 1. Các dòng mới để cố định header
                ('position', 'sticky'),
                ('top', '0'),
                ('z-index', '1'), # Đảm bảo header luôn nằm trên các dòng khác
                
                # 2. Các style cũ (giữ nguyên và rất quan trọng)
                ('font-weight', '600'),
                ('padding', '10px'),
                ('background-color', '#00816D'), # Màu nền là bắt buộc cho sticky header
                ('color', '#f5f5f5'),
                ('text-align', 'center'),
            ]
        },
        {
            'selector': 'tr:hover',
            'props': [('background-color', '#f5f5f5')]
        }
    ]

    for i, col_name in enumerate(df_to_style.columns):
        if col_name in text_columns:
            table_styles.append({
                'selector': f'td:nth-child({i + 1})',
                'props': [('text-align', 'left')]
            })

    styler = styler.set_table_styles(table_styles)

    # --- THAY ĐỔI QUAN TRỌNG NHẤT TẠI ĐÂY ---
    # Gắn style trực tiếp vào thẻ <table> để đảm bảo được áp dụng
    styler = styler.set_table_attributes('style="width:100%; background-color:white; border-collapse: collapse;"')
    
    styler = styler.hide(axis="index")
    
    return styler

def display_aggrid_table(df: pd.DataFrame):
    """
    Display a modern AG-Grid table with light theme and conditional formatting.
    """
    if df.empty:
        st.warning("No data to display")
        return
    
    # Prepare dataframe with only specified columns
    display_columns = ['Commodities', 'Sector', 'Current Price', 
                      '%Day', '%Week', '%Month', '%Quarter', '%YTD',
                      'Is_Stale', 'Current_Date']
    
    # Filter to only columns that exist
    available_columns = [col for col in display_columns if col in df.columns]
    df_display = df[available_columns].copy()
    
    # Rename columns for display
    column_renames = {
        'Commodities': 'Commodity',
        'Is_Stale': 'Stale',
        'Current_Date': 'Last Updated'
    }
    df_display.rename(columns=column_renames, inplace=True)
    
    # Format the Last Updated date to YYYY-MM-DD format
    if 'Last Updated' in df_display.columns:
        df_display['Last Updated'] = pd.to_datetime(df_display['Last Updated']).dt.strftime('%Y-%m-%d')
    
    # Convert percent columns to display format (2.34 instead of 0.0234)
    percent_cols = ["%Day", "%Week", "%Month", "%Quarter", "%YTD"]
    for col in percent_cols:
        if col in df_display.columns:
            df_display[col] = df_display[col].apply(lambda x: round(x * 100, 2) if pd.notna(x) else x)

    # JavaScript conditional color for percentage columns - light theme
    color_cells = JsCode("""
    function(params) {
        if (params.value > 0) {
            let alpha = Math.min(Math.abs(params.value) / 15, 1);
            return {
                'color': 'black',
                'backgroundColor': `rgba(34,197,94,${alpha})`
            };
        } else if (params.value < 0) {
            let alpha = Math.min(Math.abs(params.value) / 15, 1);
            return {
                'color': 'black',
                'backgroundColor': `rgba(239,68,68,${alpha})`
            };
        }
        return {
            'color': 'black',
            'backgroundColor': '#ffffff'
        };
    }
    """)

    # Custom CSS for light theme AG-Grid - matching original format
    st.markdown("""
        <style>
        /* AG-Grid light theme styling */
        .ag-root-wrapper, .ag-root-wrapper-body, .ag-center-cols-container,
        .ag-header, .ag-row, .ag-cell {
            background-color: #ffffff !important;
            color: #1f2937 !important;
            border-color: #e5e7eb !important;
        }

        /* Header styling */
        .ag-header {
            background-color: #f8fafc !important;
            font-weight: 600 !important;
            color: #374151 !important;
        }

        /* Row striping */
        .ag-row-even {
            background-color: #ffffff !important;
        }
        .ag-row-odd {
            background-color: #f9fafb !important;
        }

        /* Hover effects */
        .ag-row:hover {
            background-color: #f3f4f6 !important;
        }

        /* Input fields */
        .ag-floating-filter-input, .ag-input-field-input {
            background-color: #ffffff !important;
            color: #1f2937 !important;
            border: 1px solid #d1d5db !important;
        }

        /* Icons */
        .ag-icon, .ag-icon svg {
            fill: #6b7280 !important;
        }

        /* Cell styling - compact and dense */
        .ag-cell {
            font-weight: 400;
            border-bottom: 1px solid #f3f4f6 !important;
            font-family: 'Manrope', sans-serif;
            font-size: 13px !important;
            padding: 6px 8px !important;
        }

        /* Header cells */
        .ag-header-cell {
            font-size: 12px !important;
            padding: 8px !important;
        }

        /* Row height */
        .ag-row {
            height: 32px !important;
        }

        /* Sort indicators */
        .ag-header-cell-sortable .ag-header-cell-menu-button {
            color: #6b7280 !important;
        }
        </style>
        """, unsafe_allow_html=True)

    # Build AG-Grid options
    gb = GridOptionsBuilder.from_dataframe(df_display)
    gb.configure_default_column(resizable=True, filter=True, sortable=True)

    # Apply conditional formatting for percentage columns
    percent_formatter = JsCode("""
        function(params) { 
            if (params.value == null || params.value === undefined || isNaN(params.value)) {
                return '-';
            }
            return params.value.toFixed(2);
        }
    """)
    
    for col in percent_cols:
        if col in df_display.columns:
            gb.configure_column(col, cellStyle=color_cells, type=["numericColumn", "rightAligned"],
                valueFormatter=percent_formatter)

    # Format Price column with thousand separators and 2 decimals (with null check)
    price_formatter = JsCode("""
        function(params) { 
            if (params.value == null || params.value === undefined || isNaN(params.value)) {
                return '-';
            }
            return params.value.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2}); 
        }
    """)
    
    price_columns = ["Price", "Current Price", "30D Avg", "52W High", "52W Low"]
    for col in price_columns:
        if col in df_display.columns:
            gb.configure_column(col, type=["numericColumn", "rightAligned"],
                valueFormatter=price_formatter)

    # Configure specific columns with icons and formatting
    column_mappings = {
        "Commodity": "📦 Commodity",
        "Sector": "🏭 Sector",
        "Stale": "⚠️ Stale",
        "Last Updated": "📅 Last Updated"
    }
    
    for col, header_name in column_mappings.items():
        if col in df_display.columns:
            gb.configure_column(col, headerName=header_name)
    
    # Configure the Stale column to show Yes/No instead of True/False
    if "Stale" in df_display.columns:
        stale_formatter = JsCode("""
            function(params) {
                if (params.value === true) {
                    return 'Yes';
                } else if (params.value === false) {
                    return 'No';
                } else {
                    return '-';
                }
            }
        """)
        gb.configure_column("Stale", valueFormatter=stale_formatter, width=80)

    # Configure grid options with scroll (no pagination)
    gb.configure_pagination(enabled=False)
    gb.configure_grid_options(domLayout='normal', rowHeight=32, headerHeight=40)
    
    # Set default column widths
    gb.configure_default_column(width=120, minWidth=100)

    # Display the grid with light theme and scroll
    # Use a unique key to maintain state across reruns
    return AgGrid(
        df_display,
        gridOptions=gb.build(),
        allow_unsafe_jscode=True,
        fit_columns_on_grid_load=True,
        height=400,
        theme='streamlit',
        update_mode='NO_UPDATE',
        key='main_price_table'  # Unique key to maintain grid state
    )


# News-related functions have been removed as vnstock is no longer used

def display_news_section(stock_news: dict, selected_stocks: list = None):
    """
    Display news section with expandable news items
    
    Args:
        stock_news (dict): Dictionary of stock news data
        selected_stocks (list): List of selected stock tickers to filter news
    """
    # This function is now a placeholder - news functionality has been removed
    # vnstock is no longer used in this project
    pass


# create_expandable_news_item function removed - vnstock no longer used