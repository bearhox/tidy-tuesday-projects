from shiny import App, ui, render, reactive
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px

# ============================================================================
# DATA LOADING AND PREPROCESSING
# ============================================================================

# Load the data
station_meta = pd.read_csv('https://raw.githubusercontent.com/rfordatascience/tidytuesday/main/data/2025/2025-10-21/station_meta.csv')
historic_weather = pd.read_csv('https://raw.githubusercontent.com/rfordatascience/tidytuesday/main/data/2025/2025-10-21/historic_station_met.csv')

# Clean column names
station_meta.columns = station_meta.columns.str.strip()
historic_weather.columns = historic_weather.columns.str.strip()

# Calculate annual aggregates
annual_data = historic_weather.groupby(['station', 'year']).agg({
    'tmax': 'mean',
    'tmin': 'mean',
    'rain': 'sum',
    'sun': 'sum',
    'af': 'sum'
}).reset_index()

# Merge with station metadata
data = annual_data.merge(station_meta, on='station', how='left')

# Add region classification based on latitude
def classify_region(lat):
    if lat >= 57:
        return 'Scotland (North)'
    elif lat >= 55:
        return 'Scotland (South)'
    elif lat >= 53:
        return 'Northern England'
    elif lat >= 51.5:
        return 'Midlands'
    elif lat >= 50:
        return 'Southern England'
    else:
        return 'Southwest England'

data['region'] = data['lat'].apply(classify_region)

# Get available years and stations
years = sorted(data['year'].unique())
stations = sorted(data['station'].unique())
station_names = dict(zip(data['station'], data['station_name']))
regions = sorted(data['region'].unique())

# Metric information
METRICS = {
    'tmax': {'name': 'Max Temperature', 'unit': '°C', 'color': 'RdYlBu_r'},
    'tmin': {'name': 'Min Temperature', 'unit': '°C', 'color': 'RdYlBu_r'},
    'rain': {'name': 'Total Rainfall', 'unit': 'mm', 'color': 'Blues'},
    'sun': {'name': 'Total Sunshine', 'unit': 'hours', 'color': 'YlOrRd'},
    'af': {'name': 'Air Frost Days', 'unit': 'days', 'color': 'Purples'}
}

# Store monthly data separately for pattern analysis
monthly_data = historic_weather.copy()
monthly_data = monthly_data.merge(station_meta[['station', 'station_name', 'lat', 'lng']], on='station', how='left')
monthly_data['region'] = monthly_data['lat'].apply(classify_region)

# ============================================================================
# SHINY UI
# ============================================================================

app_ui = ui.page_fluid(
    ui.tags.head(
        ui.tags.style("""
            .card {
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                margin-bottom: 20px;
            }
            .metric-card {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 20px;
                border-radius: 8px;
                text-align: center;
            }
            .analysis-card {
                background: #f8f9fa;
                padding: 15px;
                border-radius: 8px;
                border-left: 4px solid #667eea;
                margin: 10px 0;
            }
        """)
    ),
    
    # Header
    ui.panel_title("🌦️ UK Weather Stations Interactive Dashboard"),
    ui.markdown(f"Explore weather data from **{len(stations)} stations** across the UK ({years[0]}-{years[-1]})"),
    ui.hr(),
    
    # Main layout with tabs
    ui.navset_tab(
        # TAB 1: Interactive Map
        ui.nav_panel(
            "📍 Interactive Map",
            ui.layout_sidebar(
                ui.sidebar(
                    ui.input_slider(
                        "map_year",
                        "Select Year",
                        min=years[0],
                        max=years[-1],
                        value=years[-1],
                        step=1,
                        animate=True,
                        sep=""
                    ),
                    ui.input_select(
                        "map_metric",
                        "Select Metric",
                        choices={k: v['name'] for k, v in METRICS.items()},
                        selected='tmax'
                    ),
                    ui.hr(),
                    ui.output_ui("map_stats"),
                    width=300
                ),
                ui.card(
                    ui.card_header("Weather Station Map"),
                    ui.output_ui("weather_map"),
                    full_screen=True
                )
            )
        ),
        
        # TAB 2: Regional Analysis (NEW)
        ui.nav_panel(
            "🗺️ Regional Analysis",
            ui.layout_sidebar(
                ui.sidebar(
                    ui.input_select(
                        "regional_metric",
                        "Select Metric",
                        choices={k: v['name'] for k, v in METRICS.items()},
                        selected='rain'
                    ),
                    ui.input_slider(
                        "regional_year_range",
                        "Year Range",
                        min=years[0],
                        max=years[-1],
                        value=[years[0], years[-1]],
                        step=1,
                        sep=""
                    ),
                    ui.hr(),
                    ui.markdown("**Analysis Questions:**"),
                    ui.markdown("- Which regions are rainiest/sunniest/hottest?"),
                    ui.markdown("- Has this changed over time?"),
                    width=300
                ),
                ui.card(
                    ui.card_header("Regional Comparison Over Time"),
                    ui.output_ui("regional_trends")
                ),
                ui.row(
                    ui.column(6, ui.card(
                        ui.card_header("Average by Region"),
                        ui.output_ui("regional_rankings")
                    )),
                    ui.column(6, ui.card(
                        ui.card_header("Regional Statistics"),
                        ui.output_ui("regional_stats_table")
                    ))
                )
            )
        ),
        
        # TAB 3: Historic Years Analysis (NEW)
        ui.nav_panel(
            "📅 Historic Years",
            ui.layout_sidebar(
                ui.sidebar(
                    ui.input_select(
                        "historic_metric",
                        "Select Metric",
                        choices={k: v['name'] for k, v in METRICS.items()},
                        selected='rain'
                    ),
                    ui.input_numeric(
                        "top_n_years",
                        "Number of Top Years to Show",
                        value=5,
                        min=3,
                        max=10
                    ),
                    ui.hr(),
                    ui.markdown("**Analysis Questions:**"),
                    ui.markdown("- Which years were particularly extreme?"),
                    ui.markdown("- Did extremes apply to all regions?"),
                    width=300
                ),
                ui.card(
                    ui.card_header("Extreme Years Identification"),
                    ui.output_ui("extreme_years_plot")
                ),
                ui.card(
                    ui.card_header("Regional Consistency in Extreme Years"),
                    ui.output_ui("extreme_years_regional")
                ),
                ui.card(
                    ui.card_header("Extreme Years Summary"),
                    ui.output_ui("extreme_years_summary")
                )
            )
        ),
        
        # TAB 4: Monthly Patterns (NEW)
        ui.nav_panel(
            "📆 Monthly Patterns",
            ui.layout_sidebar(
                ui.sidebar(
                    ui.input_select(
                        "monthly_metric",
                        "Select Metric",
                        choices={k: v['name'] for k, v in METRICS.items()},
                        selected='tmax'
                    ),
                    ui.input_selectize(
                        "monthly_stations",
                        "Select Stations",
                        choices={s: station_names.get(s, s) for s in stations},
                        selected=[stations[0]] if stations else [],
                        multiple=True
                    ),
                    ui.input_slider(
                        "compare_years",
                        "Compare These Years",
                        min=years[0],
                        max=years[-1],
                        value=[years[0], years[-1]],
                        step=1,
                        sep=""
                    ),
                    ui.hr(),
                    ui.markdown("**Analysis Question:**"),
                    ui.markdown("- Have monthly patterns changed year-on-year?"),
                    width=300
                ),
                ui.card(
                    ui.card_header("Monthly Pattern Comparison"),
                    ui.output_ui("monthly_pattern_plot")
                ),
                ui.card(
                    ui.card_header("Year-on-Year Monthly Changes"),
                    ui.output_ui("monthly_change_heatmap")
                )
            )
        ),
        
        # TAB 5: Time Series Analysis
        ui.nav_panel(
            "📈 Time Series",
            ui.layout_sidebar(
                ui.sidebar(
                    ui.input_select(
                        "ts_metric",
                        "Select Metric",
                        choices={k: v['name'] for k, v in METRICS.items()},
                        selected='tmax'
                    ),
                    ui.input_selectize(
                        "ts_stations",
                        "Select Stations (max 10)",
                        choices={s: station_names.get(s, s) for s in stations},
                        selected=stations[:5] if len(stations) >= 5 else stations,
                        multiple=True
                    ),
                    ui.input_action_button("select_random", "Select 5 Random", class_="btn-primary"),
                    ui.input_action_button("clear_selection", "Clear All", class_="btn-secondary"),
                    width=300
                ),
                ui.card(
                    ui.card_header("Time Series Comparison"),
                    ui.output_ui("timeseries_plot"),
                    full_screen=True
                )
            )
        ),
        
        # TAB 6: Trends & Statistics
        ui.nav_panel(
            "📉 Trends",
            ui.layout_sidebar(
                ui.sidebar(
                    ui.input_select(
                        "trend_metric",
                        "Select Metric",
                        choices={k: v['name'] for k, v in METRICS.items()},
                        selected='tmax'
                    ),
                    ui.input_radio_buttons(
                        "trend_aggregation",
                        "Aggregation",
                        choices={"mean": "Average", "median": "Median"},
                        selected="mean"
                    ),
                    ui.input_checkbox("show_trend_line", "Show Trend Line", value=True),
                    width=300
                ),
                ui.card(
                    ui.card_header("Overall Trend Across All Stations"),
                    ui.output_ui("trend_plot"),
                    full_screen=True
                ),
                ui.card(
                    ui.card_header("Distribution by Decade"),
                    ui.output_ui("distribution_plot")
                )
            )
        )
    )
)

# ============================================================================
# SERVER LOGIC
# ============================================================================

def server(input, output, session):
    
    # ========================================================================
    # TAB 1: INTERACTIVE MAP
    # ========================================================================
    
    @output
    @render.ui
    def weather_map():
        year = input.map_year()
        metric = input.map_metric()
        
        year_data = data[data['year'] == year].dropna(subset=[metric])
        
        if len(year_data) == 0:
            return ui.p("No data available for this year and metric")
        
        fig = px.scatter_mapbox(
            year_data,
            lat='lat',
            lon='lng',
            color=metric,
            size=metric,
            hover_name='station_name',
            hover_data={
                'station': True,
                'lat': ':.3f',
                'lng': ':.3f',
                metric: ':.1f',
                'region': True
            },
            color_continuous_scale=METRICS[metric]['color'],
            size_max=20,
            zoom=5,
            center={"lat": 54.5, "lon": -3.5},
            mapbox_style="open-street-map",
            title=f"{METRICS[metric]['name']} - {year}"
        )
        
        fig.update_layout(
            height=600,
            margin={"r": 0, "t": 40, "l": 0, "b": 0},
            coloraxis_colorbar=dict(title=METRICS[metric]['unit'])
        )
        
        return ui.HTML(fig.to_html(include_plotlyjs='cdn', full_html=False))
    
    @output
    @render.ui
    def map_stats():
        year = input.map_year()
        metric = input.map_metric()
        
        year_data = data[data['year'] == year].dropna(subset=[metric])
        
        if len(year_data) == 0:
            return ui.p("No data available")
        
        avg_val = year_data[metric].mean()
        min_val = year_data[metric].min()
        max_val = year_data[metric].max()
        
        min_station = year_data.loc[year_data[metric].idxmin(), 'station_name']
        max_station = year_data.loc[year_data[metric].idxmax(), 'station_name']
        
        return ui.TagList(
            ui.h4(f"Statistics for {year}"),
            ui.p(f"Average: {avg_val:.1f} {METRICS[metric]['unit']}"),
            ui.p(f"Range: {min_val:.1f} - {max_val:.1f}"),
            ui.hr(),
            ui.p(ui.strong("Lowest:"), f" {min_station}"),
            ui.p(ui.strong("Highest:"), f" {max_station}")
        )
    
    # ========================================================================
    # TAB 2: REGIONAL ANALYSIS
    # ========================================================================
    
    @output
    @render.ui
    def regional_trends():
        metric = input.regional_metric()
        year_range = input.regional_year_range()
        
        filtered_data = data[(data['year'] >= year_range[0]) & (data['year'] <= year_range[1])]
        regional_yearly = filtered_data.groupby(['region', 'year'])[metric].mean().reset_index()
        
        fig = px.line(
            regional_yearly,
            x='year',
            y=metric,
            color='region',
            markers=True,
            title=f"{METRICS[metric]['name']} by Region Over Time"
        )
        
        fig.update_layout(
            xaxis_title="Year",
            yaxis_title=f"{METRICS[metric]['name']} ({METRICS[metric]['unit']})",
            template='plotly_white',
            height=500,
            legend_title="Region"
        )
        
        return ui.HTML(fig.to_html(include_plotlyjs='cdn', full_html=False))
    
    @output
    @render.ui
    def regional_rankings():
        metric = input.regional_metric()
        year_range = input.regional_year_range()
        
        filtered_data = data[(data['year'] >= year_range[0]) & (data['year'] <= year_range[1])]
        regional_avg = filtered_data.groupby('region')[metric].mean().sort_values(ascending=False)
        
        fig = go.Figure(go.Bar(
            x=regional_avg.values,
            y=regional_avg.index,
            orientation='h',
            marker_color='#667eea'
        ))
        
        fig.update_layout(
            xaxis_title=f"{METRICS[metric]['name']} ({METRICS[metric]['unit']})",
            yaxis_title="Region",
            template='plotly_white',
            height=400
        )
        
        return ui.HTML(fig.to_html(include_plotlyjs='cdn', full_html=False))
    
    @output
    @render.ui
    def regional_stats_table():
        metric = input.regional_metric()
        year_range = input.regional_year_range()
        
        filtered_data = data[(data['year'] >= year_range[0]) & (data['year'] <= year_range[1])]
        
        stats = filtered_data.groupby('region')[metric].agg(['mean', 'std', 'min', 'max']).round(1)
        stats.columns = ['Average', 'Std Dev', 'Min', 'Max']
        stats = stats.sort_values('Average', ascending=False)
        
        html_table = stats.to_html(classes='table table-striped', border=0)
        
        return ui.HTML(f"""
            <div style="overflow-x: auto;">
                {html_table}
            </div>
        """)
    
    # ========================================================================
    # TAB 3: HISTORIC YEARS ANALYSIS
    # ========================================================================
    
    @output
    @render.ui
    def extreme_years_plot():
        metric = input.historic_metric()
        top_n = input.top_n_years()
        
        yearly_avg = data.groupby('year')[metric].mean().sort_values(ascending=False)
        yearly_avg_low = data.groupby('year')[metric].mean().sort_values(ascending=True)
        
        fig = go.Figure()
        
        # All years
        fig.add_trace(go.Scatter(
            x=yearly_avg.index,
            y=yearly_avg.values,
            mode='lines+markers',
            name='All Years',
            line=dict(color='lightgray', width=1),
            marker=dict(size=4, color='lightgray')
        ))
        
        # Highlight top N highest
        top_years = yearly_avg.head(top_n)
        fig.add_trace(go.Scatter(
            x=top_years.index,
            y=top_years.values,
            mode='markers+text',
            name=f'Top {top_n} Highest',
            marker=dict(size=12, color='#ef4444'),
            text=top_years.index,
            textposition='top center'
        ))
        
        # Highlight top N lowest
        low_years = yearly_avg_low.head(top_n)
        fig.add_trace(go.Scatter(
            x=low_years.index,
            y=low_years.values,
            mode='markers+text',
            name=f'Top {top_n} Lowest',
            marker=dict(size=12, color='#3b82f6'),
            text=low_years.index,
            textposition='bottom center'
        ))
        
        fig.update_layout(
            title=f"Extreme Years for {METRICS[metric]['name']}",
            xaxis_title="Year",
            yaxis_title=f"{METRICS[metric]['name']} ({METRICS[metric]['unit']})",
            template='plotly_white',
            height=500,
            showlegend=True
        )
        
        return ui.HTML(fig.to_html(include_plotlyjs='cdn', full_html=False))
    
    @output
    @render.ui
    def extreme_years_regional():
        metric = input.historic_metric()
        top_n = input.top_n_years()
        
        # Get top extreme years
        yearly_avg = data.groupby('year')[metric].mean().sort_values(ascending=False)
        extreme_years = list(yearly_avg.head(top_n).index)
        
        # Get regional data for these years
        regional_data = data[data['year'].isin(extreme_years)].groupby(['year', 'region'])[metric].mean().reset_index()
        
        fig = px.bar(
            regional_data,
            x='year',
            y=metric,
            color='region',
            barmode='group',
            title=f"Regional Breakdown of Extreme Years"
        )
        
        fig.update_layout(
            xaxis_title="Year",
            yaxis_title=f"{METRICS[metric]['name']} ({METRICS[metric]['unit']})",
            template='plotly_white',
            height=400
        )
        
        return ui.HTML(fig.to_html(include_plotlyjs='cdn', full_html=False))
    
    @output
    @render.ui
    def extreme_years_summary():
        metric = input.historic_metric()
        top_n = input.top_n_years()
        
        yearly_avg = data.groupby('year')[metric].mean()
        top_years = yearly_avg.sort_values(ascending=False).head(top_n)
        low_years = yearly_avg.sort_values(ascending=True).head(top_n)
        
        html = "<div class='analysis-card'>"
        html += f"<h4>Highest {METRICS[metric]['name']} Years:</h4><ul>"
        for year, val in top_years.items():
            html += f"<li><strong>{year}</strong>: {val:.1f} {METRICS[metric]['unit']}</li>"
        html += "</ul></div>"
        
        html += "<div class='analysis-card'>"
        html += f"<h4>Lowest {METRICS[metric]['name']} Years:</h4><ul>"
        for year, val in low_years.items():
            html += f"<li><strong>{year}</strong>: {val:.1f} {METRICS[metric]['unit']}</li>"
        html += "</ul></div>"
        
        return ui.HTML(html)
    
    # ========================================================================
    # TAB 4: MONTHLY PATTERNS
    # ========================================================================
    
    @output
    @render.ui
    def monthly_pattern_plot():
        metric = input.monthly_metric()
        selected_stations = input.monthly_stations()
        years_to_compare = input.compare_years()
        
        if not selected_stations:
            return ui.p("Please select at least one station")
        
        # Filter data
        filtered = monthly_data[
            (monthly_data['station'].isin(selected_stations)) &
            (monthly_data['year'].isin(years_to_compare))
        ]
        
        if len(filtered) == 0:
            return ui.p("No data available for selected filters")
        
        # Group by month and year
        monthly_avg = filtered.groupby(['month', 'year'])[metric].mean().reset_index()
        
        fig = px.line(
            monthly_avg,
            x='month',
            y=metric,
            color='year',
            markers=True,
            title=f"Monthly {METRICS[metric]['name']} Pattern Comparison"
        )
        
        fig.update_layout(
            xaxis_title="Month",
            yaxis_title=f"{METRICS[metric]['name']} ({METRICS[metric]['unit']})",
            xaxis=dict(tickmode='linear', tick0=1, dtick=1),
            template='plotly_white',
            height=500
        )
        
        return ui.HTML(fig.to_html(include_plotlyjs='cdn', full_html=False))
    
    @output
    @render.ui
    def monthly_change_heatmap():
        metric = input.monthly_metric()
        selected_stations = input.monthly_stations()
        
        if not selected_stations:
            return ui.p("Please select at least one station")
        
        # Calculate year-on-year changes by month
        filtered = monthly_data[monthly_data['station'].isin(selected_stations)]
        monthly_yearly = filtered.groupby(['year', 'month'])[metric].mean().reset_index()
        
        # Pivot for heatmap
        pivot = monthly_yearly.pivot(index='month', columns='year', values=metric)
        
        # Calculate differences from previous year
        changes = pivot.diff(axis=1)
        
        fig = go.Figure(data=go.Heatmap(
            z=changes.values,
            x=changes.columns,
            y=changes.index,
            colorscale='RdBu_r',
            zmid=0,
            hovertemplate='Month: %{y}<br>Year: %{x}<br>Change: %{z:.1f}<extra></extra>'
        ))
        
        fig.update_layout(
            title=f"Year-on-Year Change in {METRICS[metric]['name']} by Month",
            xaxis_title="Year",
            yaxis_title="Month",
            yaxis=dict(tickmode='linear', tick0=1, dtick=1),
            height=500,
            template='plotly_white'
        )
        
        return ui.HTML(fig.to_html(include_plotlyjs='cdn', full_html=False))
    
    # ========================================================================
    # TAB 5: TIME SERIES
    # ========================================================================
    
    @reactive.Effect
    @reactive.event(input.select_random)
    def _():
        random_stations = np.random.choice(stations, size=min(5, len(stations)), replace=False).tolist()
        ui.update_selectize("ts_stations", selected=random_stations)
    
    @reactive.Effect
    @reactive.event(input.clear_selection)
    def _():
        ui.update_selectize("ts_stations", selected=[])
    
    @output
    @render.ui
    def timeseries_plot():
        selected_stations = input.ts_stations()
        metric = input.ts_metric()
        
        if not selected_stations or len(selected_stations) == 0:
            return ui.p("Please select at least one station")
        
        if len(selected_stations) > 10:
            return ui.p("Please select no more than 10 stations")
        
        fig = go.Figure()
        
        for station_id in selected_stations:
            station_data = data[data['station'] == station_id].sort_values('year')
            if len(station_data) > 0:
                fig.add_trace(go.Scatter(
                    x=station_data['year'],
                    y=station_data[metric],
                    mode='lines+markers',
                    name=station_names.get(station_id, station_id),
                    line=dict(width=2),
                    marker=dict(size=5)
                ))
        
        fig.update_layout(
            title=f"{METRICS[metric]['name']} Over Time",
            xaxis_title="Year",
            yaxis_title=f"{METRICS[metric]['name']} ({METRICS[metric]['unit']})",
            hovermode='x unified',
            template='plotly_white',
            height=600
        )
        
        return ui.HTML(fig.to_html(include_plotlyjs='cdn', full_html=False))
    
    # ========================================================================
    # TAB 6: TRENDS
    # ========================================================================
    
    @output
    @render.ui
    def trend_plot():
        metric = input.trend_metric()
        aggregation = input.trend_aggregation()
        show_trend = input.show_trend_line()
        
        if aggregation == 'mean':
            yearly_agg = data.groupby('year')[metric].mean()
        else:  # median
            yearly_agg = data.groupby('year')[metric].median()
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=yearly_agg.index,
            y=yearly_agg.values,
            mode='lines+markers',
            name=aggregation.capitalize(),
            line=dict(width=3, color='#667eea'),
            marker=dict(size=6)
        ))
        
        if show_trend:
            z = np.polyfit(yearly_agg.index, yearly_agg.values, 1)
            p = np.poly1d(z)
            trend_line = p(yearly_agg.index)
            
            fig.add_trace(go.Scatter(
                x=yearly_agg.index,
                y=trend_line,
                mode='lines',
                name=f'Trend (slope: {z[0]:.3f}/year)',
                line=dict(width=2, color='#ef4444', dash='dash')
            ))
        
        fig.update_layout(
            title=f"{aggregation.capitalize()} {METRICS[metric]['name']} Trend",
            xaxis_title="Year",
            yaxis_title=f"{METRICS[metric]['name']} ({METRICS[metric]['unit']})",
            template='plotly_white',
            height=500
        )
        
        return ui.HTML(fig.to_html(include_plotlyjs='cdn', full_html=False))
    
    @output
    @render.ui
    def distribution_plot():
        metric = input.trend_metric()
        
        # Create decade bins
        data['decade'] = (data['year'] // 10) * 10
        decades = sorted(data['decade'].unique())
        
        fig = go.Figure()
        
        for decade in decades:
            decade_data = data[data['decade'] == decade][metric].dropna()
            fig.add_trace(go.Box(
                y=decade_data,
                name=f"{decade}s",
                boxmean='sd'
            ))
        
        fig.update_layout(
            title=f"{METRICS[metric]['name']} Distribution by Decade",
            yaxis_title=f"{METRICS[metric]['name']} ({METRICS[metric]['unit']})",
            template='plotly_white',
            height=500,
            showlegend=False
        )
        
        return ui.HTML(fig.to_html(include_plotlyjs='cdn', full_html=False))


# Create the Shiny app
app = App(app_ui, server)
