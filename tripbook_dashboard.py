import dash
from dash import dcc, html, Input, Output, State, callback
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from statsmodels.tsa.holtwinters import ExponentialSmoothing
from prophet import Prophet
import os
import base64

# Import our metrics calculation module
from metrics_calculation import calculate_transport_metrics, summarize_metrics_by_route, generate_metrics_insights, get_optimization_recommendations

# Initialize the Dash app
app = dash.Dash(__name__, suppress_callback_exceptions=True)
server = app.server

# Evolution Inc. brand colors
EVOLUTION_DARK_GREEN = '#005a32'  # Dark green primary color
EVOLUTION_LIGHT_GREEN = '#00a86b'  # Lighter green accent
EVOLUTION_WHITE = '#ffffff'  # White
EVOLUTION_GREY = '#f0f2f5'  # Light grey for backgrounds
EVOLUTION_TEXT_COLOR = '#2c3e50'  # Dark color for text

# Define color scheme for routes
color_discrete_map = {
    "Kigali-Musanze": "#1f77b4", 
    "Musanze-Kigali": "#ff7f0e",
    "Kigali-Gisenyi": "#2ca02c", 
    "Gisenyi-Kigali": "#d62728",
    "Musanze-Gisenyi": "#9467bd", 
    "Gisenyi-Musanze": "#8c564b"
}

# Load and prepare data
def load_data():
    if not os.path.exists('tripbook_passenger_data.csv'):
        print("Data file not found. Run the data generation script first.")
        return None
    
    df = pd.read_csv('tripbook_passenger_data.csv', low_memory=False)
    df['datetime'] = pd.to_datetime(df['datetime'])
    
    # Calculate transport metrics
    df_with_metrics = calculate_transport_metrics(df)
    metrics_summary = summarize_metrics_by_route(df_with_metrics)
    
    return df, df_with_metrics, metrics_summary

# Global data
df, df_with_metrics, metrics_summary = load_data()
routes = df['route'].unique() if df is not None else []

# Calculate metrics insights for dashboard
if df is not None:
    metrics_insights = generate_metrics_insights(df_with_metrics, metrics_summary)
    optimization_recommendations = get_optimization_recommendations(metrics_insights)
else:
    metrics_insights = {}
    optimization_recommendations = []

# Function to encode the logo image
def encode_image(image_file):
    encoded = base64.b64encode(open(image_file, 'rb').read())
    return f'data:image/png;base64,{encoded.decode()}'

# Try to load the logo if it exists, otherwise use placeholder text
try:
    logo_src = encode_image('assets/evolution_logo.png')
    logo_element = html.Img(src=logo_src, style={'height': '80px', 'marginRight': '20px'})

    # Update the template for Plotly charts to use Evolution color scheme
    figure_template = go.layout.Template()
    figure_template.layout.colorway = [EVOLUTION_DARK_GREEN, EVOLUTION_LIGHT_GREEN, '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728']
    figure_template.layout.paper_bgcolor = EVOLUTION_WHITE
    figure_template.layout.plot_bgcolor = EVOLUTION_GREY
    figure_template.layout.font.color = EVOLUTION_TEXT_COLOR
    figure_template.layout.title.font.color = EVOLUTION_TEXT_COLOR
    figure_template.layout.legend.font.color = EVOLUTION_TEXT_COLOR
    figure_template.layout.xaxis.title.font.color = EVOLUTION_TEXT_COLOR
    figure_template.layout.yaxis.title.font.color = EVOLUTION_TEXT_COLOR
    figure_template.layout.coloraxis.colorbar.outlinewidth = 0

    # Helper function to style figures
    def apply_evolution_style(fig):
        fig.update_layout(
            template=figure_template,
            margin=dict(l=40, r=40, t=40, b=40),
            legend=dict(
                bgcolor=EVOLUTION_WHITE,
                bordercolor=EVOLUTION_DARK_GREEN,
                borderwidth=1
            ),
            font=dict(family="Arial, sans-serif")
        )
        return fig

    # Callback for Transport Metrics Tab
    @app.callback(
        [Output('metrics-chart', 'figure'),
        Output('time-pattern-chart', 'figure'),
        Output('optimization-recommendations', 'children')],
        [Input('route-selector-metrics', 'value'),
        Input('metrics-selector', 'value'),
        Input('time-pattern-selector', 'value')]
    )
    def update_metrics_charts(selected_routes, selected_metric, time_pattern):
        if not selected_routes:
            return [go.Figure() for _ in range(2)], "Please select routes to view metrics."
        
        # Filter data for selected routes
        filtered_df = df_with_metrics[df_with_metrics['route'].isin(selected_routes)]
        
        if filtered_df.empty:
            return [go.Figure() for _ in range(2)], "No data available for the selected routes."
        
        # Create metrics chart based on selection
        metrics_fig = go.Figure()
        
        if selected_metric == 'load_factor':
            # Load Factor by route
            route_summary = filtered_df.groupby('route')['load_factor'].mean().reset_index()
            metrics_fig = px.bar(
                route_summary, 
                x='route', 
                y='load_factor',
                color='route',
                color_discrete_map=color_discrete_map,
                title='Average Load Factor by Route (%)'
            )
            metrics_fig.add_shape(
                type="line",
                line=dict(dash="dash", color="red", width=2),
                y0=50, y1=50, x0=-0.5, x1=len(route_summary)-0.5
            )
            metrics_fig.add_shape(
                type="line",
                line=dict(dash="dash", color="green", width=2),
                y0=85, y1=85, x0=-0.5, x1=len(route_summary)-0.5
            )
            metrics_fig.update_layout(
                annotations=[
                    dict(
                        x=len(route_summary)-0.5,
                        y=50,
                        xref="x",
                        yref="y",
                        text="Min 50%",
                        showarrow=False,
                        font=dict(color="red")
                    ),
                    dict(
                        x=len(route_summary)-0.5,
                        y=85,
                        xref="x",
                        yref="y",
                        text="Optimal 85%",
                        showarrow=False,
                        font=dict(color="green")
                    )
                ]
            )
            metrics_fig.update_layout(xaxis_title='Route', yaxis_title='Load Factor (%)')
        
        elif selected_metric == 'ask_rpk':
            # ASK vs RPK by route
            route_summary = filtered_df.groupby('route').agg({
                'ask': 'sum',
                'rpk': 'sum'
            }).reset_index()
            
            # Scale to thousands for better readability
            route_summary['ask'] /= 1000
            route_summary['rpk'] /= 1000
            
            metrics_fig = go.Figure()
            metrics_fig.add_trace(go.Bar(
                x=route_summary['route'],
                y=route_summary['ask'],
                name='ASK',
                marker_color=EVOLUTION_LIGHT_GREEN
            ))
            metrics_fig.add_trace(go.Bar(
                x=route_summary['route'],
                y=route_summary['rpk'],
                name='RPK',
                marker_color=EVOLUTION_DARK_GREEN
            ))
            metrics_fig.update_layout(
                title='ASK vs RPK by Route (thousands)',
                xaxis_title='Route',
                yaxis_title='Seat Kilometers (thousands)',
                barmode='group'
            )
        
        elif selected_metric == 'rpkm_cpkm':
            # RPKM vs CPKM by route
            route_summary = filtered_df.groupby('route').agg({
                'rpkm': 'mean',
                'cpkm': 'mean'
            }).reset_index()
            
            metrics_fig = go.Figure()
            metrics_fig.add_trace(go.Bar(
                x=route_summary['route'],
                y=route_summary['rpkm'],
                name='RPKM',
                marker_color=EVOLUTION_LIGHT_GREEN
            ))
            metrics_fig.add_trace(go.Bar(
                x=route_summary['route'],
                y=route_summary['cpkm'],
                name='CPKM',
                marker_color='#d62728'
            ))
            metrics_fig.update_layout(
                title='RPKM vs CPKM by Route',
                xaxis_title='Route',
                yaxis_title='Amount per Kilometer (RWF)',
                barmode='group'
            )
        
        elif selected_metric == 'profitability_index':
            # Profitability Index by route
            route_summary = filtered_df.groupby('route')['profitability_index'].mean().reset_index()
            metrics_fig = px.bar(
                route_summary, 
                x='route', 
                y='profitability_index',
                color='route',
                color_discrete_map=color_discrete_map,
                title='Profitability Index by Route (RPKM/CPKM)'
            )
            # Add a line at profitability_index = 1
            metrics_fig.add_shape(
                type="line",
                line=dict(dash="dash", color="red", width=2),
                y0=1, y1=1, x0=-0.5, x1=len(route_summary)-0.5
            )
            metrics_fig.update_layout(
                annotations=[
                    dict(
                        x=len(route_summary)-0.5,
                        y=1,
                        xref="x",
                        yref="y",
                        text="Breakeven",
                        showarrow=False,
                        font=dict(color="red")
                    )
                ]
            )
            metrics_fig.update_layout(xaxis_title='Route', yaxis_title='Profitability Index')
        
        elif selected_metric == 'revenue_per_trip':
            # Revenue per Trip by route
            route_summary = filtered_df.groupby('route')['revenue_per_trip'].mean().reset_index()
            metrics_fig = px.bar(
                route_summary, 
                x='route', 
                y='revenue_per_trip',
                color='route',
                color_discrete_map=color_discrete_map,
                title='Average Revenue per Trip by Route'
            )
            metrics_fig.update_layout(xaxis_title='Route', yaxis_title='Revenue per Trip (RWF)')
        
        # Apply Evolution style to metrics chart
        metrics_fig = apply_evolution_style(metrics_fig)
        
        # Create time pattern chart
        time_pattern_fig = go.Figure()
        
        if time_pattern == 'hourly':
            # Hourly Load Factor patterns
            hourly_data = filtered_df.groupby(['hour', 'route'])['load_factor'].mean().reset_index()
            
            for route in selected_routes:
                route_data = hourly_data[hourly_data['route'] == route]
                if not route_data.empty:
                    time_pattern_fig.add_trace(go.Scatter(
                        x=route_data['hour'],
                        y=route_data['load_factor'],
                        mode='lines+markers',
                        name=route,
                        line=dict(color=color_discrete_map.get(route, EVOLUTION_DARK_GREEN))
                    ))
            
            time_pattern_fig.update_layout(
                title='Hourly Load Factor Patterns by Route',
                xaxis=dict(
                    title='Hour of Day',
                    tickmode='linear',
                    tick0=0,
                    dtick=2
                ),
                yaxis_title='Load Factor (%)'
            )
        
        elif time_pattern == 'daily':
            # Daily Load Factor patterns
            daily_data = filtered_df.groupby(['day_of_week', 'route'])['load_factor'].mean().reset_index()
            day_names = {0: 'Monday', 1: 'Tuesday', 2: 'Wednesday', 3: 'Thursday', 
                        4: 'Friday', 5: 'Saturday', 6: 'Sunday'}
            
            for route in selected_routes:
                route_data = daily_data[daily_data['route'] == route]
                if not route_data.empty:
                    time_pattern_fig.add_trace(go.Scatter(
                        x=route_data['day_of_week'],
                        y=route_data['load_factor'],
                        mode='lines+markers',
                        name=route,
                        line=dict(color=color_discrete_map.get(route, EVOLUTION_DARK_GREEN))
                    ))
            
            time_pattern_fig.update_layout(
                title='Daily Load Factor Patterns by Route',
                xaxis=dict(
                    title='Day of Week',
                    tickmode='array',
                    tickvals=list(range(7)),
                    ticktext=list(day_names.values())
                ),
                yaxis_title='Load Factor (%)'
            )
        
        elif time_pattern == 'monthly':
            # Monthly Load Factor patterns
            # First extract month from datetime
            filtered_df['month'] = filtered_df['datetime'].dt.month
            monthly_data = filtered_df.groupby(['month', 'route'])['load_factor'].mean().reset_index()
            month_names = {1: 'Jan', 2: 'Feb', 3: 'Mar', 4: 'Apr', 5: 'May', 6: 'Jun',
                        7: 'Jul', 8: 'Aug', 9: 'Sep', 10: 'Oct', 11: 'Nov', 12: 'Dec'}
            
            for route in selected_routes:
                route_data = monthly_data[monthly_data['route'] == route]
                if not route_data.empty:
                    time_pattern_fig.add_trace(go.Scatter(
                        x=route_data['month'],
                        y=route_data['load_factor'],
                        mode='lines+markers',
                        name=route,
                        line=dict(color=color_discrete_map.get(route, EVOLUTION_DARK_GREEN))
                    ))
            
            time_pattern_fig.update_layout(
                title='Monthly Load Factor Patterns by Route',
                xaxis=dict(
                    title='Month',
                    tickmode='array',
                    tickvals=list(range(1, 13)),
                    ticktext=list(month_names.values())
                ),
                yaxis_title='Load Factor (%)'
            )
        
        # Apply Evolution style to time pattern chart
        time_pattern_fig = apply_evolution_style(time_pattern_fig)
        
        # Generate optimization recommendations
        if len(optimization_recommendations) > 0:
            recommendations = []
            recommendations.append(html.H4("Fleet Optimization Recommendations", style={'color': EVOLUTION_DARK_GREEN}))
            
            for i, rec in enumerate(optimization_recommendations, 1):
                recommendations.append(
                    html.P(f"{i}. {rec}", style={'color': EVOLUTION_TEXT_COLOR, 'margin': '10px 0'})
                )
            
            # Add route-specific recommendations
            if len(selected_routes) == 1:
                route = selected_routes[0]
                route_data = filtered_df[filtered_df['route'] == route]
                
                avg_load_factor = route_data['load_factor'].mean()
                if avg_load_factor < 50:
                    recommendations.append(
                        html.P(f"Route {route} has a low average load factor of {avg_load_factor:.1f}%. Consider reducing frequency or using smaller buses.",
                            style={'color': '#d62728', 'fontWeight': 'bold', 'margin': '10px 0'})
                    )
                elif avg_load_factor > 85:
                    recommendations.append(
                        html.P(f"Route {route} has a high average load factor of {avg_load_factor:.1f}%. Consider increasing capacity during peak times.",
                            style={'color': '#2ca02c', 'fontWeight': 'bold', 'margin': '10px 0'})
                    )
                
                if route_data['rpkm'].mean() < route_data['cpkm'].mean():
                    recommendations.append(
                        html.P(f"Route {route} is currently unprofitable (RPKM < CPKM). Consider price adjustments or cost reduction strategies.",
                            style={'color': '#d62728', 'fontWeight': 'bold', 'margin': '10px 0'})
                    )
        else:
            recommendations = [html.P("No optimization recommendations available.", style={'color': EVOLUTION_TEXT_COLOR})]
        
        return metrics_fig, time_pattern_fig, recommendations
    
    
    # # Callback for Passenger Overview Tab
    # @app.callback(
    #     [Output('total-passengers-chart', 'figure'),
    #      Output('passenger-trend-chart', 'figure'),
    #      Output('hourly-patterns-chart', 'figure'),
    #      Output('weekly-patterns-chart', 'figure'),
    #      Output('monthly-patterns-chart', 'figure'),
    #      Output('yearly-trends-chart', 'figure'),
    #      Output('overview-insights', 'children')],
    #     [Input('route-selector-overview', 'value'),
    #      Input('date-range-overview', 'start_date'),
    #      Input('date-range-overview', 'end_date')]
    # )
    # def update_overview_charts(selected_routes, start_date, end_date):
    #     # Create empty figures for error cases
    #     empty_fig = go.Figure()
    #     empty_fig = apply_evolution_style(empty_fig)
    #     empty_message = html.P("No data available", style={'color': EVOLUTION_TEXT_COLOR})
    
    #     if not selected_routes or not start_date or not end_date:
    #         return [empty_fig for _ in range(6)], html.P("Please select routes and date range.", 
    #                                                    style={'color': EVOLUTION_TEXT_COLOR})
    
    #     # Filter data
    #     filtered_df = df[df['route'].isin(selected_routes)]
    #     filtered_df = filtered_df[(filtered_df['datetime'] >= start_date) & (filtered_df['datetime'] <= end_date)]
    
    #     if filtered_df.empty:
    #         return [empty_fig for _ in range(6)], html.P("No data available for the selected filters.", 
    #                                                    style={'color': EVOLUTION_TEXT_COLOR})
    
    #     # Total passengers by route
    #     total_passengers = filtered_df.groupby('route')['passengers'].sum().reset_index()
    #     total_fig = px.bar(
    #         total_passengers, 
    #         x='route', 
    #         y='passengers',
    #         color='route',
    #         color_discrete_map=color_discrete_map,
    #         title='Total Passengers by Route'
    #     )
    #     total_fig.update_layout(xaxis_title='Route', yaxis_title='Total Passengers')
    #     total_fig = apply_evolution_style(total_fig)
    
    #     # Passenger trend over time
    #     trend_df = filtered_df.groupby([pd.Grouper(key='datetime', freq='M'), 'route'])['passengers'].sum().reset_index()
    #     trend_fig = px.line(
    #         trend_df, 
    #         x='datetime', 
    #         y='passengers', 
    #         color='route',
    #         color_discrete_map=color_discrete_map,
    #         title='Monthly Passenger Trend'
    #     )
    #     trend_fig.update_layout(xaxis_title='Date', yaxis_title='Passengers')
    #     trend_fig = apply_evolution_style(trend_fig)
    
    #     # Hourly patterns
    #     hourly_df = filtered_df.groupby(['hour', 'route'])['passengers'].mean().reset_index()
    #     hourly_fig = px.line(
    #         hourly_df, 
    #         x='hour', 
    #         y='passengers', 
    #         color='route',
    #         color_discrete_map=color_discrete_map,
    #         title='Average Hourly Passenger Patterns'
    #     )
    #     hourly_fig.update_layout(
    #         xaxis=dict(
    #             tickmode='linear',
    #             tick0=0,
    #             dtick=2,
    #             title='Hour of Day'
    #         ),
    #         yaxis_title='Average Passengers'
    #     )
    #     hourly_fig = apply_evolution_style(hourly_fig)
    
    #     # Weekly patterns
    #     weekly_df = filtered_df.groupby(['day_of_week', 'route'])['passengers'].mean().reset_index()
    #     day_names = {0: 'Monday', 1: 'Tuesday', 2: 'Wednesday', 3: 'Thursday', 
    #                 4: 'Friday', 5: 'Saturday', 6: 'Sunday'}
    #     weekly_df['day_name'] = weekly_df['day_of_week'].map(day_names)
    #     weekly_fig = px.line(
    #         weekly_df, 
    #         x='day_of_week', 
    #         y='passengers', 
    #         color='route',
    #         color_discrete_map=color_discrete_map,
    #         title='Average Weekly Passenger Patterns'
    #     )
    #     weekly_fig.update_layout(
    #         xaxis=dict(
    #             tickmode='array',
    #             tickvals=list(range(7)),
    #             ticktext=list(day_names.values()),
    #             title='Day of Week'
    #         ),
    #         yaxis_title='Average Passengers'
    #     )
    #     weekly_fig = apply_evolution_style(weekly_fig)
    
    #     # Monthly patterns
    #     monthly_df = filtered_df.groupby(['month', 'route'])['passengers'].mean().reset_index()
    #     month_names = {1: 'Jan', 2: 'Feb', 3: 'Mar', 4: 'Apr', 5: 'May', 6: 'Jun',
    #                   7: 'Jul', 8: 'Aug', 9: 'Sep', 10: 'Oct', 11: 'Nov', 12: 'Dec'}
    #     monthly_df['month_name'] = monthly_df['month'].map(month_names)
    #     monthly_fig = px.line(
    #         monthly_df, 
    #         x='month', 
    #         y='passengers', 
    #         color='route',
    #         color_discrete_map=color_discrete_map,
    #         title='Average Monthly Passenger Patterns'
    #     )
    #     monthly_fig.update_layout(
    #         xaxis=dict(
    #             tickmode='array',
    #             tickvals=list(range(1, 13)),
    #             ticktext=list(month_names.values()),
    #             title='Month'
    #         ),
    #         yaxis_title='Average Passengers'
    #     )
    #     monthly_fig = apply_evolution_style(monthly_fig)
    
    #     # Yearly trends
    #     yearly_df = filtered_df.groupby(['year', 'route'])['passengers'].mean().reset_index()
    #     yearly_fig = px.line(
    #         yearly_df, 
    #         x='year', 
    #         y='passengers', 
    #         color='route',
    #         color_discrete_map=color_discrete_map,
    #         title='Yearly Passenger Trends'
    #     )
    #     yearly_fig.update_layout(xaxis_title='Year', yaxis_title='Average Passengers')
    #     yearly_fig = apply_evolution_style(yearly_fig)
    
    #     # Generate insights
    #     insights = []
    
    #     # Total passenger insight
    #     total_by_route = filtered_df.groupby('route')['passengers'].sum()
    #     top_route = total_by_route.idxmax()
    #     top_route_passengers = total_by_route.max()
    #     insights.append(
    #         html.P(f"✓ The busiest route is {top_route} with a total of {top_route_passengers:,.0f} passengers.", 
    #                style={'color': EVOLUTION_TEXT_COLOR})
    #     )
    
    #     # Peak hour insight
    #     hourly_avg = filtered_df.groupby('hour')['passengers'].mean()
    #     peak_hour = hourly_avg.idxmax()
    #     insights.append(
    #         html.P(f"✓ The peak hour across all routes is {peak_hour}:00 with an average of {hourly_avg.max():.0f} passengers.",
    #                style={'color': EVOLUTION_TEXT_COLOR})
    #     )
    
    #     # Peak day insight
    #     daily_avg = filtered_df.groupby('day_of_week')['passengers'].mean()
    #     peak_day = daily_avg.idxmax()
    #     insights.append(
    #         html.P(f"✓ The busiest day of the week is {day_names[peak_day]} with an average of {daily_avg.max():.0f} passengers.",
    #                style={'color': EVOLUTION_TEXT_COLOR})
    #     )
    
    #     # Peak month insight
    #     monthly_avg = filtered_df.groupby('month')['passengers'].mean()
    #     peak_month = monthly_avg.idxmax()
    #     insights.append(
    #         html.P(f"✓ The busiest month is {month_names[peak_month]} with an average of {monthly_avg.max():.0f} passengers.",
    #                style={'color': EVOLUTION_TEXT_COLOR})
    #     )
    
    #     # Growth insight
    #     if len(yearly_df['year'].unique()) > 1:
    #         first_year = yearly_df['year'].min()
    #         last_year = yearly_df['year'].max()
    #         yearly_totals = filtered_df.groupby('year')['passengers'].sum()
    #         first_year_total = yearly_totals.get(first_year, 0)
    #         last_year_total = yearly_totals.get(last_year, 0)
        
    #         if first_year_total > 0:  # Avoid division by zero
    #             years_diff = last_year - first_year
    #             if years_diff > 0:  # Ensure we're not dividing by zero
    #                 growth_rate = ((last_year_total / first_year_total) ** (1 / years_diff)) - 1
    #                 insights.append(
    #                     html.P(f"✓ The annual passenger growth rate is approximately {growth_rate * 100:.2f}% per year.",
    #                           style={'color': EVOLUTION_TEXT_COLOR, 'fontWeight': 'bold'})
    #                 )
    
    #     return total_fig, trend_fig, hourly_fig, weekly_fig, monthly_fig, yearly_fig, insights
    # Callback for Forecasting Tab
    @app.callback(
        [Output('forecast-chart', 'figure'),
        Output('forecast-components-chart', 'figure'),
        Output('forecast-insights', 'children')],
        [Input('generate-forecast-button', 'n_clicks')],
        [State('route-selector-forecast', 'value'),
        State('forecast-method', 'value'),
        State('forecast-horizon', 'value')]
    )
    def update_forecast_charts(n_clicks, selected_route, forecast_method, forecast_horizon):
        if n_clicks == 0 or not selected_route:
            return go.Figure(), go.Figure(), html.P("Please select a route and generate a forecast.", 
                                                style={'color': EVOLUTION_TEXT_COLOR})
        
        # Filter data for the selected route
        route_df = df[df['route'] == selected_route].copy()
        
        if route_df.empty:
            return go.Figure(), go.Figure(), html.P("No data available for the selected route.", 
                                                style={'color': EVOLUTION_TEXT_COLOR})
        
        # Resample to daily frequency for forecasting
        daily_data = route_df.set_index('datetime')['passengers'].resample('D').mean().reset_index()
        daily_data = daily_data.fillna(method='ffill')
        
        # Initialize figures
        forecast_fig = go.Figure()
        components_fig = go.Figure()
        insights = []
        
        # Generate forecast
        if forecast_method == 'prophet':
            # Prepare data for Prophet
            prophet_data = daily_data.rename(columns={'datetime': 'ds', 'passengers': 'y'})
            
            # Create and fit Prophet model
            model = Prophet(
                yearly_seasonality=True,
                weekly_seasonality=True,
                daily_seasonality=False,
                changepoint_prior_scale=0.05
            )
            
            # Add Rwanda holidays
            try:
                # Add major holidays that may affect travel
                new_years = pd.DataFrame({
                    'holiday': 'new_years',
                    'ds': pd.to_datetime(['2010-01-01', '2011-01-01', '2012-01-01', '2013-01-01', 
                                        '2014-01-01', '2015-01-01', '2016-01-01', '2017-01-01',
                                        '2018-01-01', '2019-01-01', '2020-01-01', '2021-01-01',
                                        '2022-01-01', '2023-01-01', '2024-01-01', '2025-01-01']),
                    'lower_window': 0,
                    'upper_window': 1,
                })
                    
                genocide_memorial = pd.DataFrame({
                    'holiday': 'genocide_memorial',
                    'ds': pd.to_datetime(['2010-04-07', '2011-04-07', '2012-04-07', '2013-04-07', 
                                        '2014-04-07', '2015-04-07', '2016-04-07', '2017-04-07',
                                        '2018-04-07', '2019-04-07', '2020-04-07', '2021-04-07',
                                        '2022-04-07', '2023-04-07', '2024-04-07', '2025-04-07']),
                    'lower_window': 0,
                    'upper_window': 0,
                })
                    
                liberation_day = pd.DataFrame({
                    'holiday': 'liberation_day',
                    'ds': pd.to_datetime(['2010-07-04', '2011-07-04', '2012-07-04', '2013-07-04', 
                                        '2014-07-04', '2015-07-04', '2016-07-04', '2017-07-04',
                                        '2018-07-04', '2019-07-04', '2020-07-04', '2021-07-04',
                                        '2022-07-04', '2023-07-04', '2024-07-04', '2025-07-04']),
                    'lower_window': 0,
                    'upper_window': 1,
                })
                    
                christmas = pd.DataFrame({
                    'holiday': 'christmas',
                    'ds': pd.to_datetime(['2010-12-25', '2011-12-25', '2012-12-25', '2013-12-25', 
                                        '2014-12-25', '2015-12-25', '2016-12-25', '2017-12-25',
                                        '2018-12-25', '2019-12-25', '2020-12-25', '2021-12-25',
                                        '2022-12-25', '2023-12-25', '2024-12-25', '2025-12-25']),
                    'lower_window': -1,
                    'upper_window': 1,
                })
                    
                # Add holidays to the model
                for holiday_df in [new_years, genocide_memorial, liberation_day, christmas]:
                    model.add_holidays(holiday_df)
            except Exception as e:
                print(f"Warning: Could not add custom holidays: {e}")
            
            model.fit(prophet_data)
            
            # Create future dataframe for forecasting
            future = model.make_future_dataframe(periods=forecast_horizon)
            
            # Make forecast
            forecast = model.predict(future)
            
            # Plot historical data
            forecast_fig.add_trace(go.Scatter(
                x=prophet_data['ds'],
                y=prophet_data['y'],
                mode='lines',
                name='Historical Data',
                line=dict(color='blue')
            ))
            
            # Plot forecast
            forecast_fig.add_trace(go.Scatter(
                x=forecast['ds'],
                y=forecast['yhat'],
                mode='lines',
                name='Forecast',
                line=dict(color=EVOLUTION_DARK_GREEN)
            ))
            
            # Plot confidence intervals
            forecast_fig.add_trace(go.Scatter(
                x=forecast['ds'].tolist() + forecast['ds'].tolist()[::-1],
                y=forecast['yhat_upper'].tolist() + forecast['yhat_lower'].tolist()[::-1],
                fill='toself',
                fillcolor=f'rgba({int(EVOLUTION_LIGHT_GREEN[1:3], 16)}, {int(EVOLUTION_LIGHT_GREEN[3:5], 16)}, {int(EVOLUTION_LIGHT_GREEN[5:7], 16)}, 0.2)',
                line=dict(color='rgba(0, 0, 0, 0)'),
                name='95% Confidence Interval'
            ))
            
            # Create subplots for components
            components_fig = make_subplots(rows=3, cols=1, 
                                        subplot_titles=('Trend', 'Yearly Seasonality', 'Weekly Seasonality'))
            
            # Add trend component
            trend_x = forecast['ds']
            trend_y = forecast['trend']
            components_fig.add_trace(go.Scatter(
                x=trend_x, 
                y=trend_y, 
                mode='lines', 
                name='Trend',
                line=dict(color=EVOLUTION_DARK_GREEN)
            ), row=1, col=1)
            
            # Add yearly seasonality
            yearly_x = [i for i in range(1, 13)]
            yearly_y = forecast.iloc[0:12]['yearly']
            components_fig.add_trace(go.Scatter(
                x=yearly_x,
                y=yearly_y,
                mode='lines',
                name='Yearly Seasonality',
                line=dict(color=EVOLUTION_DARK_GREEN)
            ), row=2, col=1)
            
            # Add weekly seasonality
            weekly_x = [i for i in range(7)]
            weekly_y = forecast.iloc[0:7]['weekly']
            components_fig.add_trace(go.Scatter(
                x=weekly_x,
                y=weekly_y,
                mode='lines',
                name='Weekly Seasonality',
                line=dict(color=EVOLUTION_DARK_GREEN)
            ), row=3, col=1)
            
            # Update layout
            components_fig.update_layout(height=600, title_text='Forecast Components')
            components_fig.update_xaxes(title_text="Month", row=2, col=1, tickvals=list(range(1, 13)), 
                                    ticktext=['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'])
            components_fig.update_xaxes(title_text="Day of Week", row=3, col=1, tickvals=list(range(7)), 
                                    ticktext=['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'])
            
            # Generate insights
            future_forecast = forecast.iloc[-forecast_horizon:]
            peak_day = future_forecast.loc[future_forecast['yhat'].idxmax()]
            
            insights.append(
                html.P(f"✓ Peak demand for {selected_route} is forecast on {peak_day['ds'].date()} with {peak_day['yhat']:.0f} passengers.",
                    style={'color': EVOLUTION_TEXT_COLOR})
            )
            
            avg_forecast = future_forecast['yhat'].mean()
            insights.append(
                html.P(f"✓ Average daily forecast for the next {forecast_horizon} days is {avg_forecast:.0f} passengers.",
                    style={'color': EVOLUTION_TEXT_COLOR})
            )
            
            # Identify growth trend
            if trend_y.iloc[-1] > trend_y.iloc[0]:
                growth_rate = (trend_y.iloc[-1] / trend_y.iloc[0] - 1) * 100
                insights.append(
                    html.P(f"✓ The route shows a growing trend with approximately {growth_rate:.2f}% increase in the forecast period.",
                        style={'color': EVOLUTION_TEXT_COLOR})
                )
            else:
                decline_rate = (1 - trend_y.iloc[-1] / trend_y.iloc[0]) * 100
                insights.append(
                    html.P(f"✓ The route shows a declining trend with approximately {decline_rate:.2f}% decrease in the forecast period.",
                        style={'color': EVOLUTION_TEXT_COLOR})
                )
            
        elif forecast_method == 'exponential_smoothing':
            # Prepare data for Exponential Smoothing
            ts_data = daily_data.set_index('datetime')['passengers']
            
            # Fit Exponential Smoothing model
            model = ExponentialSmoothing(
                ts_data, 
                seasonal_periods=7,
                trend='add',
                seasonal='add', 
                damped=True
            ).fit()
            
            # Make forecast
            forecast = model.forecast(forecast_horizon)
            
            # Plot historical data
            forecast_fig.add_trace(go.Scatter(
                x=ts_data.index,
                y=ts_data.values,
                mode='lines',
                name='Historical Data',
                line=dict(color='blue')
            ))
            
            # Plot forecast
            forecast_fig.add_trace(go.Scatter(
                x=pd.date_range(start=ts_data.index[-1] + pd.Timedelta(days=1), periods=forecast_horizon),
                y=forecast.values,
                mode='lines',
                name='Forecast',
                line=dict(color=EVOLUTION_DARK_GREEN)
            ))
            
            # Create a simple decomposition for the components chart
            # This is simplified since ExponentialSmoothing doesn't provide components directly
            components_fig.add_annotation(
                text="Components visualization is only available for Prophet forecasts",
                xref="paper", yref="paper",
                x=0.5, y=0.5,
                showarrow=False,
                font=dict(size=16, color=EVOLUTION_TEXT_COLOR)
            )
            
            # Generate insights
            peak_day_index = forecast.argmax()
            peak_day_date = (ts_data.index[-1] + pd.Timedelta(days=peak_day_index + 1)).date()
            peak_value = forecast.max()
            
            insights.append(
                html.P(f"✓ Peak demand for {selected_route} is forecast on {peak_day_date} with {peak_value:.0f} passengers.",
                    style={'color': EVOLUTION_TEXT_COLOR})
            )
            
            avg_forecast = forecast.mean()
            insights.append(
                html.P(f"✓ Average daily forecast for the next {forecast_horizon} days is {avg_forecast:.0f} passengers.",
                    style={'color': EVOLUTION_TEXT_COLOR})
            )
        
        # Update layouts
        forecast_fig.update_layout(
            title=f'Passenger Demand Forecast for {selected_route}',
            xaxis_title='Date',
            yaxis_title='Number of Passengers',
            legend=dict(x=0, y=1),
            hovermode='x'
        )
        forecast_fig = apply_evolution_style(forecast_fig)
        components_fig = apply_evolution_style(components_fig)
        
        insights.append(
            html.P(f"✓ Based on the forecast, this route requires careful capacity planning, especially for peak demand periods.",
                style={'color': EVOLUTION_TEXT_COLOR, 'fontWeight': 'bold'})
        )
        
        return forecast_fig, components_fig, insights
    
    
    
    
    # Callback for Bus Allocation Tab
    @app.callback(
        [Output('bus-allocation-chart', 'figure'),
        Output('financial-impact-chart', 'figure'),
        Output('allocation-recommendations', 'children')],
        [Input('optimize-allocation-button', 'n_clicks')],
        [State('route-selector-allocation', 'value'),
        State('optimization-target', 'value')]
    )
    def update_allocation_charts(n_clicks, selected_route, optimization_target):
        if n_clicks == 0 or not selected_route:
            return go.Figure(), go.Figure(), html.P("Please select a route and optimize allocation.", 
                                                style={'color': EVOLUTION_TEXT_COLOR})
        
        # Filter data for the selected route
        route_df = df[df['route'] == selected_route].copy()
        
        if route_df.empty:
            return go.Figure(), go.Figure(), html.P("No data available for the selected route.", 
                                                style={'color': EVOLUTION_TEXT_COLOR})
        
        # Get the most recent data for forecasting (last 365 days)
        recent_data = route_df.sort_values('datetime').tail(24 * 365)  # Hourly data for the last year
        
        # Resample to daily frequency
        daily_data = recent_data.set_index('datetime')['passengers'].resample('D').mean().reset_index()
        daily_data = daily_data.fillna(method='ffill')
        
        # Simple forecast with Prophet for the next 30 days
        prophet_data = daily_data.rename(columns={'datetime': 'ds', 'passengers': 'y'})
        
        model = Prophet(yearly_seasonality=True, weekly_seasonality=True)
        model.fit(prophet_data)
        
        future = model.make_future_dataframe(periods=30)  # 30 day forecast
        forecast = model.predict(future)
        future_forecast = forecast.iloc[-30:]  # Just the forecast part
        
        # Bus types and their capacities
        bus_types = {
            "Mini": 16,
            "Medium": 30,
            "Large": 50
        }
        
        # Define cost per kilometer for each bus type
        cost_per_km = {
            "Mini": 150,
            "Medium": 250,
            "Large": 400
        }
        
        # Get route distance
        route_distance = route_df['route_distance_km'].iloc[0]
        
        # Get ticket price
        ticket_price = route_df['ticket_price'].iloc[0]
        
        # Optimize allocation for each day
        allocation_results = []
        
        for _, row in future_forecast.iterrows():
            demand = row['yhat']
            best_score = float('-inf') if optimization_target != 'unserved_demand' else float('inf')
            best_allocation = None
            
            # Try different bus combinations
            for bus_type, capacity in bus_types.items():
                # Calculate minimum number of buses needed
                min_buses = max(1, int(np.ceil(demand / capacity)))
                
                # Try a range around this minimum
                for num_buses in range(max(1, min_buses-1), min_buses+3):
                    # Calculate metrics
                    potential_revenue = min(demand, num_buses * capacity) * ticket_price
                    operating_cost = num_buses * cost_per_km[bus_type] * route_distance
                    profit = potential_revenue - operating_cost
                    capacity_util = min(100, (min(demand, num_buses * capacity) / (num_buses * capacity)) * 100)
                    unserved_demand = max(0, demand - num_buses * capacity)
                    
                    # Determine score based on optimization target
                    if optimization_target == 'profit':
                        score = profit
                    elif optimization_target == 'capacity_util':
                        score = capacity_util
                    else:  # unserved_demand
                        score = -unserved_demand  # Negative because we want to minimize
                    
                    # Update best allocation if score is better
                    if (optimization_target != 'unserved_demand' and score > best_score) or \
                    (optimization_target == 'unserved_demand' and score > best_score):
                        best_score = score
                        best_allocation = {
                            'date': row['ds'],
                            'forecast': demand,
                            'bus_type': bus_type,
                            'num_buses': num_buses,
                            'capacity': num_buses * capacity,
                            'potential_revenue': potential_revenue,
                            'operating_cost': operating_cost,
                            'profit': profit,
                            'capacity_utilization': capacity_util,
                            'passengers_served': min(demand, num_buses * capacity),
                            'unserved_demand': unserved_demand
                        }
            
            allocation_results.append(best_allocation)
        
        # Convert to dataframe
        allocation_df = pd.DataFrame(allocation_results)
        
        # Create allocation chart
        allocation_fig = make_subplots(specs=[[{"secondary_y": True}]])
        
        # Add forecasted demand
        allocation_fig.add_trace(
            go.Scatter(
                x=allocation_df['date'],
                y=allocation_df['forecast'],
                mode='lines',
                name='Forecasted Demand',
                line=dict(color='blue')
            ),
            secondary_y=False
        )
        
        # Add allocated capacity
        allocation_fig.add_trace(
            go.Scatter(
                x=allocation_df['date'],
                y=allocation_df['capacity'],
                mode='lines',
                name='Allocated Capacity',
                line=dict(color=EVOLUTION_LIGHT_GREEN)
            ),
            secondary_y=False
        )
        
        # Add number of buses (secondary axis)
        allocation_fig.add_trace(
            go.Bar(
                x=allocation_df['date'],
                y=allocation_df['num_buses'],
                name='Number of Buses',
                marker=dict(
                    color=allocation_df['bus_type'].map({
                        'Mini': EVOLUTION_LIGHT_GREEN, 
                        'Medium': EVOLUTION_DARK_GREEN, 
                        'Large': '#2c3e50'
                    })
                )
            ),
            secondary_y=True
        )
        
        # Update layout
        allocation_fig.update_layout(
            title=f'Optimized Bus Allocation for {selected_route}',
            xaxis_title='Date',
            legend=dict(x=0, y=1)
        )
        
        allocation_fig.update_yaxes(title_text="Passengers / Capacity", secondary_y=False)
        allocation_fig.update_yaxes(title_text="Number of Buses", secondary_y=True)
        allocation_fig = apply_evolution_style(allocation_fig)
        
        # Create financial impact chart
        financial_fig = go.Figure()
        
        # Add revenue
        financial_fig.add_trace(
            go.Scatter(
                x=allocation_df['date'],
                y=allocation_df['potential_revenue'],
                mode='lines',
                name='Revenue',
                line=dict(color=EVOLUTION_LIGHT_GREEN)
            )
        )
        
        # Add operating cost
        financial_fig.add_trace(
            go.Scatter(
                x=allocation_df['date'],
                y=allocation_df['operating_cost'],
                mode='lines',
                name='Operating Cost',
                line=dict(color='red')
            )
        )
        
        # Add profit
        financial_fig.add_trace(
            go.Scatter(
                x=allocation_df['date'],
                y=allocation_df['profit'],
                mode='lines',
                name='Profit',
                line=dict(color=EVOLUTION_DARK_GREEN)
            )
        )
        
        # Update layout
        financial_fig.update_layout(
            title=f'Financial Impact of Optimized Allocation for {selected_route}',
            xaxis_title='Date',
            yaxis_title='Amount (RWF)',
            legend=dict(x=0, y=1)
        )
        financial_fig = apply_evolution_style(financial_fig)
        
        # Generate recommendations
        recommendations = []
        
        # Bus type distribution
        bus_type_counts = allocation_df['bus_type'].value_counts()
        recommendations.append(html.H4("Bus Fleet Recommendations:", style={'color': EVOLUTION_DARK_GREEN, 'marginBottom': '10px'}))
        
        for bus_type, count in bus_type_counts.items():
            percentage = count / len(allocation_df) * 100
            recommendations.append(
                html.P(f"✓ {bus_type} buses: {percentage:.1f}% of the time ({count} days)",
                    style={'color': EVOLUTION_TEXT_COLOR})
            )
        
        # Average metrics
        avg_buses = allocation_df['num_buses'].mean()
        avg_profit = allocation_df['profit'].mean()
        avg_capacity_util = allocation_df['capacity_utilization'].mean()
        
        recommendations.append(html.H4("Operational Metrics:", style={'color': EVOLUTION_DARK_GREEN, 'marginBottom': '10px', 'marginTop': '20px'}))
        recommendations.append(
            html.P(f"✓ Average number of buses needed: {avg_buses:.2f}",
                style={'color': EVOLUTION_TEXT_COLOR})
        )
        recommendations.append(
            html.P(f"✓ Average daily profit: {avg_profit:.2f} RWF",
                style={'color': EVOLUTION_TEXT_COLOR})
        )
        recommendations.append(
            html.P(f"✓ Average capacity utilization: {avg_capacity_util:.2f}%",
                style={'color': EVOLUTION_TEXT_COLOR})
        )
        
        # Peak demand days
        peak_days = allocation_df.nlargest(3, 'forecast')
        recommendations.append(html.H4("Peak Demand Planning:", style={'color': EVOLUTION_DARK_GREEN, 'marginBottom': '10px', 'marginTop': '20px'}))
        recommendations.append(html.P("Top 3 highest demand days:", style={'color': EVOLUTION_TEXT_COLOR, 'fontWeight': 'bold'}))
        
        for i, (_, day) in enumerate(peak_days.iterrows()):
            recommendations.append(
                html.P(f"✓ {day['date'].date()}: {day['forecast']:.0f} passengers, requiring {day['num_buses']} {day['bus_type']} buses",
                    style={'color': EVOLUTION_TEXT_COLOR})
            )
        
        # Strategic recommendation
        if optimization_target == 'profit':
            recommendations.append(html.H4("Strategic Recommendations:", style={'color': EVOLUTION_DARK_GREEN, 'marginBottom': '10px', 'marginTop': '20px'}))
            recommendations.append(
                html.P("✓ Focus on maximizing vehicle utilization to reduce operational waste",
                    style={'color': EVOLUTION_TEXT_COLOR})
            )
            recommendations.append(
                html.P("✓ Consider implementing dynamic pricing to encourage ridership during off-peak hours",
                    style={'color': EVOLUTION_TEXT_COLOR})
            )
        else:  # unserved_demand
            recommendations.append(html.H4("Strategic Recommendations:", style={'color': EVOLUTION_DARK_GREEN, 'marginBottom': '10px', 'marginTop': '20px'}))
            recommendations.append(
                html.P("✓ Focus on customer service by ensuring all demand is met",
                    style={'color': EVOLUTION_TEXT_COLOR})
            )
            recommendations.append(
                html.P("✓ Consider partnerships with other operators during peak demand periods",
                    style={'color': EVOLUTION_TEXT_COLOR})
            )
        return allocation_fig, financial_fig, recommendations
        
    # Callback for Financial Performance Tab
    @app.callback(
        [Output('revenue-by-route-chart', 'figure'),
        Output('profit-margin-chart', 'figure'),
        Output('revenue-cost-trend-chart', 'figure'),
        Output('capacity-util-profit-chart', 'figure'),
        Output('financial-insights', 'children')],
        [Input('route-selector-financial', 'value'),
        Input('date-range-financial', 'start_date'),
        Input('date-range-financial', 'end_date')]
    )
    def update_financial_charts(selected_routes, start_date, end_date):
        if not selected_routes or not start_date or not end_date:
            return [go.Figure() for _ in range(4)], html.P("Please select routes and date range.", 
                                                        style={'color': EVOLUTION_TEXT_COLOR})
        
        # Filter data
        filtered_df = df[df['route'].isin(selected_routes)]
        filtered_df = filtered_df[(filtered_df['datetime'] >= start_date) & (filtered_df['datetime'] <= end_date)]
        
        if filtered_df.empty:
            return [go.Figure() for _ in range(4)], html.P("No data available for the selected filters.", 
                                                        style={'color': EVOLUTION_TEXT_COLOR})
        
        # Revenue by route
        revenue_by_route = filtered_df.groupby('route')['revenue'].sum().reset_index()
        revenue_fig = px.bar(
            revenue_by_route, 
            x='route', 
            y='revenue',
            color='route',
            color_discrete_map=color_discrete_map,
            title='Total Revenue by Route'
        )
        revenue_fig.update_layout(xaxis_title='Route', yaxis_title='Total Revenue (RWF)')
        revenue_fig = apply_evolution_style(revenue_fig)
        
        # Profit margin by route
        financial_metrics = filtered_df.groupby('route').agg({
            'revenue': 'sum',
            'operating_cost': 'sum',
            'profit': 'sum',
            'passengers': 'sum'
        }).reset_index()
        
        financial_metrics['profit_margin'] = financial_metrics['profit'] / financial_metrics['revenue'] * 100
        financial_metrics['revenue_per_passenger'] = financial_metrics['revenue'] / financial_metrics['passengers']
        financial_metrics['cost_per_passenger'] = financial_metrics['operating_cost'] / financial_metrics['passengers']
        
        margin_fig = px.bar(
            financial_metrics, 
            x='route', 
            y='profit_margin',
            color='route',
            color_discrete_map=color_discrete_map,
            title='Profit Margin by Route'
        )
        margin_fig.update_layout(xaxis_title='Route', yaxis_title='Profit Margin (%)')
        margin_fig = apply_evolution_style(margin_fig)
        
        # Revenue vs Cost trend
        monthly_financials = filtered_df.groupby([pd.Grouper(key='datetime', freq='ME'), 'route']).agg({
            'revenue': 'sum',
            'operating_cost': 'sum',
            'profit': 'sum'
        }).reset_index()
        
        trend_fig = go.Figure()
        
        for route in selected_routes:
            route_data = monthly_financials[monthly_financials['route'] == route]
            
            # Add revenue
            trend_fig.add_trace(
                go.Scatter(
                    x=route_data['datetime'],
                    y=route_data['revenue'],
                    mode='lines',
                    name=f'{route} Revenue',
                    line=dict(dash='solid')
                )
            )
            
            # Add operating cost
            trend_fig.add_trace(
                go.Scatter(
                    x=route_data['datetime'],
                    y=route_data['operating_cost'],
                    mode='lines',
                    name=f'{route} Cost',
                    line=dict(dash='dash')
                )
            )
        
        trend_fig.update_layout(
            title='Monthly Revenue vs Operating Cost by Route',
            xaxis_title='Month',
            yaxis_title='Amount (RWF)',
            legend=dict(x=0, y=1)
        )
        trend_fig = apply_evolution_style(trend_fig)
        
        # Capacity utilization vs profit
        capacity_profit = filtered_df.groupby(['route', pd.Grouper(key='datetime', freq='D')]).agg({
            'capacity_utilization': 'mean',
            'profit': 'sum'
        }).reset_index()
        
        util_profit_fig = px.scatter(
            capacity_profit,
            x='capacity_utilization',
            y='profit',
            color='route',
            color_discrete_map=color_discrete_map,
            title='Capacity Utilization vs Daily Profit',
            trendline='ols'  # Add trend line
        )
        
        util_profit_fig.update_layout(
            xaxis_title='Average Capacity Utilization (%)',
            yaxis_title='Daily Profit (RWF)'
        )
        util_profit_fig = apply_evolution_style(util_profit_fig)
        
        # Generate financial insights
        insights = []
        
        # Most profitable route
        most_profitable = financial_metrics.loc[financial_metrics['profit'].idxmax()]
        insights.append(
            html.P(f"✓ The most profitable route is {most_profitable['route']} with a total profit of {most_profitable['profit']:,.0f} RWF and a profit margin of {most_profitable['profit_margin']:.2f}%.",
                style={'color': EVOLUTION_TEXT_COLOR})
        )
        
        # Highest revenue route
        highest_revenue = financial_metrics.loc[financial_metrics['revenue'].idxmax()]
        insights.append(
            html.P(f"✓ The highest revenue route is {highest_revenue['route']} with a total revenue of {highest_revenue['revenue']:,.0f} RWF.",
                style={'color': EVOLUTION_TEXT_COLOR})
        )
        
        # Best and worst profit margins
        best_margin = financial_metrics.loc[financial_metrics['profit_margin'].idxmax()]
        worst_margin = financial_metrics.loc[financial_metrics['profit_margin'].idxmin()]
        insights.append(
            html.P(f"✓ The best profit margin is on the {best_margin['route']} route at {best_margin['profit_margin']:.2f}%, while the worst is {worst_margin['route']} at {worst_margin['profit_margin']:.2f}%.",
                style={'color': EVOLUTION_TEXT_COLOR})
        )
        
        # Revenue per passenger
        highest_rpp = financial_metrics.loc[financial_metrics['revenue_per_passenger'].idxmax()]
        insights.append(
            html.P(f"✓ The highest revenue per passenger is on the {highest_rpp['route']} route at {highest_rpp['revenue_per_passenger']:.2f} RWF per passenger.",
                style={'color': EVOLUTION_TEXT_COLOR})
        )
        
        # Cost efficiency
        most_efficient = financial_metrics.loc[financial_metrics['cost_per_passenger'].idxmin()]
        insights.append(
            html.P(f"✓ The most cost-efficient route is {most_efficient['route']} with an operating cost of {most_efficient['cost_per_passenger']:.2f} RWF per passenger.",
                style={'color': EVOLUTION_TEXT_COLOR})
        )
        
        # Overall financial performance
        total_revenue = financial_metrics['revenue'].sum()
        total_cost = financial_metrics['operating_cost'].sum()
        total_profit = financial_metrics['profit'].sum()
        overall_margin = (total_profit / total_revenue) * 100
        
        insights.append(
            html.P(f"✓ Overall financial performance: Revenue: {total_revenue:,.0f} RWF, Cost: {total_cost:,.0f} RWF, Profit: {total_profit:,.0f} RWF, Margin: {overall_margin:.2f}%.",
                style={'color': EVOLUTION_TEXT_COLOR, 'fontWeight': 'bold'})
        )
        
        # Recommendation based on capacity utilization vs profit analysis
        insights.append(
            html.P(f"✓ The data suggests an optimal capacity utilization target of 70-80% to maximize profitability while maintaining service quality.",
                style={'color': EVOLUTION_TEXT_COLOR, 'fontWeight': 'bold'})
        )
        
        return revenue_fig, margin_fig, trend_fig, util_profit_fig, insights


except:
    logo_element = html.Div([
        html.H3("EVOLUTION", style={'margin': '0', 'color': EVOLUTION_WHITE, 'letterSpacing': '2px'})
    ], style={'marginRight': '20px', 'backgroundColor': EVOLUTION_LIGHT_GREEN, 'padding': '10px 15px', 'borderRadius': '5px'})

# Function to get KPI summary values
def get_kpi_values():
    if metrics_summary is None or len(metrics_summary) == 0:
        return {
            'overall_load_factor': "N/A",
            'avg_rpkm': "N/A",
            'avg_cpkm': "N/A",
            'avg_profitability': "N/A",
            'avg_revenue_per_trip': "N/A",
            'most_efficient_route': "N/A",
            'most_profitable_route': "N/A",
            'profitable_routes': 0,
            'total_routes': 0
        }
    
    # Calculate KPIs from metrics_summary
    overall_load_factor = (metrics_summary['rpk'].sum() / metrics_summary['ask'].sum()) * 100
    avg_rpkm = metrics_summary['rpkm'].mean()
    avg_cpkm = metrics_summary['cpkm'].mean()
    avg_profitability = metrics_summary['profitability_index'].mean()
    avg_revenue_per_trip = metrics_summary['revenue_per_trip'].mean()
    
    most_efficient_route = metrics_summary.loc[metrics_summary['load_factor'].idxmax()]['route']
    most_profitable_route = metrics_summary.loc[metrics_summary['profitability_index'].idxmax()]['route']
    
    return {
        'overall_load_factor': f"{overall_load_factor:.1f}%",
        'avg_rpkm': f"{avg_rpkm:.1f} RWF/km",
        'avg_cpkm': f"{avg_cpkm:.1f} RWF/km",
        'avg_profitability': f"{avg_profitability:.2f}",
        'avg_revenue_per_trip': f"{avg_revenue_per_trip:.0f} RWF",
        'most_efficient_route': most_efficient_route,
        'most_profitable_route': most_profitable_route,
        'profitable_routes': len(metrics_summary[metrics_summary['profitability_index'] > 1]),
        'total_routes': len(metrics_summary)
    }
    
# Create a metric box component
def create_metric_card(title, value, subtitle="", icon=None, color=EVOLUTION_DARK_GREEN):
    return html.Div([
        html.Div([
            html.Div([
                html.H4(title, style={'fontSize': '14px', 'margin': '0', 'color': EVOLUTION_TEXT_COLOR}),
                html.H3(value, style={'fontSize': '24px', 'fontWeight': 'bold', 'margin': '10px 0 5px 0', 'color': color}),
                html.P(subtitle, style={'fontSize': '12px', 'margin': '0', 'color': EVOLUTION_TEXT_COLOR})
            ], style={'flex': '1'}),
            html.Div([
                html.I(className=icon, style={'fontSize': '28px', 'color': color}) if icon else None
            ], style={'marginLeft': '10px'})
        ], style={'display': 'flex', 'alignItems': 'center'})
    ], style={
        'backgroundColor': EVOLUTION_WHITE,
        'padding': '15px',
        'borderRadius': '10px',
        'boxShadow': '0 2px 4px rgba(0, 0, 0, 0.05)',
        'height': '100%'
    })
    
    
# Create a metrics description card
def create_metric_info_card(title, description, formula=None):
    return html.Div([
        html.H4(title, style={'fontSize': '16px', 'fontWeight': 'bold', 'margin': '0 0 10px 0', 'color': EVOLUTION_DARK_GREEN}),
        html.P(description, style={'fontSize': '14px', 'margin': '0 0 10px 0', 'color': EVOLUTION_TEXT_COLOR}),
        html.P(formula, style={'fontSize': '14px', 'fontStyle': 'italic', 'margin': '0', 'color': EVOLUTION_TEXT_COLOR}) if formula else None
    ], style={
        'backgroundColor': EVOLUTION_WHITE,
        'padding': '15px',
        'borderRadius': '10px',
        'boxShadow': '0 2px 4px rgba(0, 0, 0, 0.05)',
        'height': '100%',
        'marginBottom': '15px'
    })


# Get KPI values for the dashboard
kpi_values = get_kpi_values()

# App layout with Evolution Inc. branding
app.layout = html.Div([
    # Header with logo
    html.Div([
        # Logo and title container
        html.Div([
            # Logo on the left
            logo_element,
            # Header text on the right
            html.Div([
                html.H1('TripBook Fleet Management', 
                      style={'color': EVOLUTION_WHITE, 'fontSize': 32, 'margin': '0px'}),
                html.P('Powered by Evolution Inc.',
                     style={'color': EVOLUTION_WHITE, 'fontSize': 16, 'margin': '5px 0px'})
            ])
        ], style={'display': 'flex', 'alignItems': 'center'}),
        
        # Subtitle
        html.P('Passenger Analytics • Demand Forecasting • Bus Allocation Optimization',
               style={'color': EVOLUTION_WHITE, 'fontSize': 18, 'margin': '10px 0px 5px 0px'})
    ], style={
        'backgroundColor': EVOLUTION_DARK_GREEN, 
        'padding': '20px 30px',
        'borderRadius': '10px',
        'boxShadow': '0 4px 6px rgba(0, 0, 0, 0.1)',
        'margin': '10px 0px 20px 0px'
    }),
    
    # KPI Dashboard Summary
    html.Div([
        html.H3('Key Performance Indicators', 
                style={'color': EVOLUTION_DARK_GREEN, 'margin': '0 0 15px 0'}),
        
        # KPI Metric Cards - First Row
        html.Div([
            # Overall Load Factor
            html.Div([
                create_metric_card(
                    "Overall Load Factor",
                    kpi_values['overall_load_factor'],
                    "Fleet-wide capacity utilization")
            ], className="four columns", style={'width': '32%', 'display': 'inline-block'}),
            
            # Average RPKM
            html.Div([
                create_metric_card(
                    "Revenue per Kilometer",
                    kpi_values['avg_rpkm'],
                    "Average revenue generated per km",
                    color=EVOLUTION_LIGHT_GREEN)
            ], className="four columns", style={'width': '32%', 'display': 'inline-block', 'marginLeft': '2%'}),
            
            # Average CPKM
            html.Div([
                create_metric_card(
                    "Cost per Kilometer",
                    kpi_values['avg_cpkm'],
                    "Average operational cost per km",
                    color="#d62728")
            ], className="four columns", style={'width': '32%', 'display': 'inline-block', 'marginLeft': '2%'})
        ], className="row", style={'marginBottom': '15px'}),
        
        # KPI Metric Cards - Second Row
        html.Div([
            # Profitability Index
            html.Div([
                create_metric_card(
                    "Profitability Index",
                    kpi_values['avg_profitability'],
                    "Revenue to cost ratio (>1 is profitable)",
                    color=EVOLUTION_DARK_GREEN)
            ], className="four columns", style={'width': '32%', 'display': 'inline-block'}),
            
            # Average Revenue per Trip
            html.Div([
                create_metric_card(
                    "Revenue per Trip",
                    kpi_values['avg_revenue_per_trip'],
                    "Average revenue per bus trip",
                    color=EVOLUTION_LIGHT_GREEN)
            ], className="four columns", style={'width': '32%', 'display': 'inline-block', 'marginLeft': '2%'}),
            
            # Profitable Routes
            html.Div([
                create_metric_card(
                    "Profitable Routes",
                    f"{kpi_values['profitable_routes']}/{kpi_values['total_routes']}",
                    "Routes generating positive returns",
                    color="#2ca02c")
            ], className="four columns", style={'width': '32%', 'display': 'inline-block', 'marginLeft': '2%'})
        ], className="row")
    ], style={
        'backgroundColor': EVOLUTION_GREY,
        'padding': '20px',
        'borderRadius': '10px',
        'margin': '0 0 20px 0',
        'boxShadow': '0 2px 4px rgba(0, 0, 0, 0.05)'
    }),
    
    # Main content tabs
    dcc.Tabs([
        # Transport Metrics Tab (New)
        dcc.Tab(label='Transport Metrics', style={'backgroundColor': EVOLUTION_DARK_GREEN, 'color': EVOLUTION_WHITE},
                selected_style={'backgroundColor': EVOLUTION_LIGHT_GREEN, 'color': EVOLUTION_WHITE, 'fontWeight': 'bold'},
                children=[
            html.Div([
                # Left side - Metrics explanations
                html.Div([
                    html.H3('Transport Metrics Explained', 
                            style={'color': EVOLUTION_DARK_GREEN, 'margin': '0 0 15px 0'}),
                    
                    create_metric_info_card(
                        "Available Seat Kilometers (ASK)",
                        "Measures the total available transport capacity in terms of seat-distance.",
                        "ASK = Total Seats × Distance Traveled"
                    ),
                    
                    create_metric_info_card(
                        "Revenue Passenger Kilometers (RPK)",
                        "Measures actual usage by passengers who paid for their trips.",
                        "RPK = Revenue Paying Passengers × Distance"
                    ),
                    
                    create_metric_info_card(
                        "Load Factor (%)",
                        "A direct measure of how efficiently bus capacity is being utilized.",
                        "Load Factor = (RPK / ASK) × 100"
                    ),
                    
                    create_metric_info_card(
                        "Revenue per Kilometer (RPKM)",
                        "Evaluates financial efficiency in terms of revenue per distance.",
                        "RPKM = Total Revenue / Total Distance Traveled"
                    ),
                    
                    create_metric_info_card(
                        "Cost per Kilometer (CPKM)",
                        "Evaluates financial efficiency in terms of operating costs per distance.",
                        "CPKM = Total Operational Costs / Total Distance Traveled"
                    ),
                    
                    create_metric_info_card(
                        "Passenger Revenue per Trip",
                        "Tracks how much revenue is generated per bus trip.",
                        "Revenue per Trip = Total Revenue / Total Trips"
                    ),
                ], style={'width': '30%', 'display': 'inline-block', 'verticalAlign': 'top'}),
                
                # Right side - Metrics charts
                html.Div([
                    # Filters for metrics analysis
                    html.Div([
                        html.H3('Metrics Analysis Filters', style={'margin': '0 0 15px 0', 'color': EVOLUTION_TEXT_COLOR}),
                        html.Label('Select Routes:', style={'fontWeight': 'bold'}),
                        dcc.Dropdown(
                            id='route-selector-metrics',
                            options=[{'label': route, 'value': route} for route in routes],
                            value=routes,
                            multi=True,
                            style={'marginBottom': '15px'}
                        ),
                        html.Label('Metrics to Compare:', style={'fontWeight': 'bold'}),
                        dcc.Dropdown(
                            id='metrics-selector',
                            options=[
                                {'label': 'Load Factor', 'value': 'load_factor'},
                                {'label': 'ASK vs RPK', 'value': 'ask_rpk'},
                                {'label': 'RPKM vs CPKM', 'value': 'rpkm_cpkm'},
                                {'label': 'Profitability Index', 'value': 'profitability_index'},
                                {'label': 'Revenue per Trip', 'value': 'revenue_per_trip'}
                            ],
                            value='load_factor',
                            style={'marginBottom': '15px'}
                        ),
                    ], style={'padding': '15px', 'backgroundColor': EVOLUTION_WHITE, 'borderRadius': '10px', 'marginBottom': '15px'}),
                    
                    # Metrics charts
                    html.Div([
                        dcc.Graph(id='metrics-chart')
                    ], style={'padding': '15px', 'backgroundColor': EVOLUTION_WHITE, 'borderRadius': '10px', 'marginBottom': '15px'}),
                    
                    # Time patterns chart
                    html.Div([
                        html.H4('Load Factor Time Patterns', style={'textAlign': 'center', 'color': EVOLUTION_TEXT_COLOR}),
                        dcc.Dropdown(
                            id='time-pattern-selector',
                            options=[
                                {'label': 'Hourly Pattern', 'value': 'hourly'},
                                {'label': 'Daily Pattern', 'value': 'daily'},
                                {'label': 'Monthly Pattern', 'value': 'monthly'}
                            ],
                            value='hourly',
                            style={'marginBottom': '15px'}
                        ),
                        dcc.Graph(id='time-pattern-chart')
                    ], style={'padding': '15px', 'backgroundColor': EVOLUTION_WHITE, 'borderRadius': '10px'}),
                    
                ], style={'width': '68%', 'display': 'inline-block', 'verticalAlign': 'top', 'marginLeft': '2%'}),
                
                # Bottom section - Optimization recommendations
                html.Div([
                    html.H3('Optimization Recommendations', 
                            style={'color': EVOLUTION_DARK_GREEN, 'margin': '15px 0'}),
                    html.Div(id='optimization-recommendations', style={'padding': '15px', 'backgroundColor': EVOLUTION_WHITE, 'borderRadius': '10px'})
                ], style={'marginTop': '15px'})
            ], style={'padding': '20px'})
        ]),
        
        
        # # Passenger Overview Tab
        # dcc.Tab(label='Passenger Overview', style={'backgroundColor': EVOLUTION_DARK_GREEN, 'color': EVOLUTION_WHITE},
        #         selected_style={'backgroundColor': EVOLUTION_LIGHT_GREEN, 'color': EVOLUTION_WHITE, 'fontWeight': 'bold'},
        #         children=[
        #     html.Div([
        #         # Filters and controls
        #         html.Div([
        #             html.H3('Filters', style={'margin': '10px 0px', 'color': EVOLUTION_TEXT_COLOR}),
        #             html.Label('Select Routes:', style={'fontWeight': 'bold'}),
        #             dcc.Dropdown(
        #                 id='route-selector-overview',
        #                 options=[{'label': route, 'value': route} for route in routes],
        #                 value=routes,
        #                 multi=True,
        #                 style={'marginBottom': '15px'}
        #             ),
        #             html.Label('Date Range:', style={'fontWeight': 'bold'}),
        #             dcc.DatePickerRange(
        #                 id='date-range-overview',
        #                 start_date=df['datetime'].min() if df is not None else None,
        #                 end_date=df['datetime'].max() if df is not None else None,
        #                 display_format='YYYY-MM-DD'
        #             ),
        #         ], style={'padding': '20px', 'backgroundColor': EVOLUTION_GREY, 'borderRadius': '10px', 'margin': '10px 20px', 'boxShadow': '0 2px 4px rgba(0, 0, 0, 0.05)'}),
        
        #         # First row of charts
        #         html.Div([
        #             # Total passengers by route
        #             html.Div([
        #                 html.H4('Total Passengers by Route', style={'textAlign': 'center', 'color': EVOLUTION_TEXT_COLOR}),
        #                 dcc.Graph(id='total-passengers-chart')
        #             ], style={'width': '48%', 'display': 'inline-block', 'verticalAlign': 'top', 'backgroundColor': EVOLUTION_WHITE, 'padding': '15px', 'borderRadius': '10px', 'boxShadow': '0 2px 4px rgba(0, 0, 0, 0.05)'}),
            
        #             # Passenger trend over time
        #             html.Div([
        #                 html.H4('Passenger Trend Over Time', style={'textAlign': 'center', 'color': EVOLUTION_TEXT_COLOR}),
        #                 dcc.Graph(id='passenger-trend-chart')
        #             ], style={'width': '48%', 'display': 'inline-block', 'verticalAlign': 'top', 'marginLeft': '4%', 'backgroundColor': EVOLUTION_WHITE, 'padding': '15px', 'borderRadius': '10px', 'boxShadow': '0 2px 4px rgba(0, 0, 0, 0.05)'})
        #         ], style={'margin': '10px 20px'}),
        
        #         # Second row of charts
        #         html.Div([
        #             # Hourly patterns
        #             html.Div([
        #                 html.H4('Hourly Passenger Patterns', style={'textAlign': 'center', 'color': EVOLUTION_TEXT_COLOR}),
        #                 dcc.Graph(id='hourly-patterns-chart')
        #             ], style={'width': '48%', 'display': 'inline-block', 'verticalAlign': 'top', 'backgroundColor': EVOLUTION_WHITE, 'padding': '15px', 'borderRadius': '10px', 'boxShadow': '0 2px 4px rgba(0, 0, 0, 0.05)'}),
            
        #             # Weekly patterns
        #             html.Div([
        #                 html.H4('Weekly Passenger Patterns', style={'textAlign': 'center', 'color': EVOLUTION_TEXT_COLOR}),
        #                 dcc.Graph(id='weekly-patterns-chart')
        #             ], style={'width': '48%', 'display': 'inline-block', 'verticalAlign': 'top', 'marginLeft': '4%', 'backgroundColor': EVOLUTION_WHITE, 'padding': '15px', 'borderRadius': '10px', 'boxShadow': '0 2px 4px rgba(0, 0, 0, 0.05)'})
        #         ], style={'margin': '20px 20px'}),
        
        #         # Third row of charts
        #         html.Div([
        #             # Monthly patterns
        #             html.Div([
        #                 html.H4('Monthly Passenger Patterns', style={'textAlign': 'center', 'color': EVOLUTION_TEXT_COLOR}),
        #                 dcc.Graph(id='monthly-patterns-chart')
        #             ], style={'width': '48%', 'display': 'inline-block', 'verticalAlign': 'top', 'backgroundColor': EVOLUTION_WHITE, 'padding': '15px', 'borderRadius': '10px', 'boxShadow': '0 2px 4px rgba(0, 0, 0, 0.05)'}),
            
        #             # Yearly trends
        #             html.Div([
        #                 html.H4('Yearly Passenger Trends', style={'textAlign': 'center', 'color': EVOLUTION_TEXT_COLOR}),
        #                 dcc.Graph(id='yearly-trends-chart')
        #             ], style={'width': '48%', 'display': 'inline-block', 'verticalAlign': 'top', 'marginLeft': '4%', 'backgroundColor': EVOLUTION_WHITE, 'padding': '15px', 'borderRadius': '10px', 'boxShadow': '0 2px 4px rgba(0, 0, 0, 0.05)'})
        #         ], style={'margin': '20px 20px'}),
        
        #         # Key insights card
        #         html.Div([
        #             html.H3('Key Insights', style={'margin': '10px 0px', 'color': EVOLUTION_TEXT_COLOR}),
        #             html.Div(id='overview-insights', style={'fontSize': 16, 'lineHeight': '1.5'})
        #         ], style={'padding': '20px', 'backgroundColor': EVOLUTION_GREY, 'borderRadius': '10px', 'margin': '20px 20px', 'boxShadow': '0 2px 4px rgba(0, 0, 0, 0.05)'})
        #     ], style={'padding': '20px'})
        # ]),
        
        # Forecasting Tab
        dcc.Tab(label='Demand Forecasting', style={'backgroundColor': EVOLUTION_DARK_GREEN, 'color': EVOLUTION_WHITE},
                selected_style={'backgroundColor': EVOLUTION_LIGHT_GREEN, 'color': EVOLUTION_WHITE, 'fontWeight': 'bold'},
                children=[
            html.Div([
                # Filters and controls
                html.Div([
                    html.H3('Forecast Parameters', style={'margin': '10px 0px', 'color': EVOLUTION_TEXT_COLOR}),
                    html.Div([
                        html.Div([
                            html.Label('Select Route:', style={'fontWeight': 'bold'}),
                            dcc.Dropdown(
                                id='route-selector-forecast',
                                options=[{'label': route, 'value': route} for route in routes],
                                value=routes[0] if len(routes) > 0 else None
                            )
                        ], style={'width': '30%', 'display': 'inline-block', 'marginRight': '3%'}),
                        
                        html.Div([
                            html.Label('Forecast Method:', style={'fontWeight': 'bold'}),
                            dcc.Dropdown(
                                id='forecast-method',
                                options=[
                                    {'label': 'Prophet', 'value': 'prophet'},
                                    {'label': 'Exponential Smoothing', 'value': 'exponential_smoothing'}
                                ],
                                value='prophet'
                            )
                        ], style={'width': '30%', 'display': 'inline-block', 'marginRight': '3%'}),
                        
                        html.Div([
                            html.Label('Forecast Horizon (days):', style={'fontWeight': 'bold'}),
                            dcc.Slider(
                                id='forecast-horizon',
                                min=30,
                                max=365,
                                step=30,
                                value=180,
                                marks={i: str(i) for i in range(30, 366, 30)}
                            )
                        ], style={'width': '30%', 'display': 'inline-block'})
                    ]),
                    html.Button('Generate Forecast', 
                                id='generate-forecast-button', 
                                n_clicks=0,
                                style={'marginTop': '15px', 'padding': '10px 20px', 'fontSize': 16, 
                                       'backgroundColor': EVOLUTION_DARK_GREEN, 'color': EVOLUTION_WHITE, 'border': 'none', 
                                       'borderRadius': '5px', 'cursor': 'pointer', 'boxShadow': '0 2px 4px rgba(0, 0, 0, 0.1)'})
                ], style={'padding': '20px', 'backgroundColor': EVOLUTION_GREY, 'borderRadius': '10px', 'margin': '10px 20px', 'boxShadow': '0 2px 4px rgba(0, 0, 0, 0.05)'}),
                
                # Results section
                html.Div([
                    # Forecast chart
                    html.Div([
                        html.H4('Passenger Demand Forecast', style={'textAlign': 'center', 'color': EVOLUTION_TEXT_COLOR}),
                        dcc.Graph(id='forecast-chart')
                    ], style={'backgroundColor': EVOLUTION_WHITE, 'padding': '15px', 'borderRadius': '10px', 'boxShadow': '0 2px 4px rgba(0, 0, 0, 0.05)', 'margin': '10px 0'}),
                    
                    # Forecast components (if Prophet)
                    html.Div([
                        html.H4('Forecast Components', style={'textAlign': 'center', 'color': EVOLUTION_TEXT_COLOR}),
                        dcc.Graph(id='forecast-components-chart')
                    ], style={'backgroundColor': EVOLUTION_WHITE, 'padding': '15px', 'borderRadius': '10px', 'boxShadow': '0 2px 4px rgba(0, 0, 0, 0.05)', 'margin': '20px 0'}),
                    
                    # Peak demand insights
                    html.Div([
                        html.H3('Forecast Insights', style={'margin': '10px 0px', 'color': EVOLUTION_TEXT_COLOR}),
                        html.Div(id='forecast-insights', style={'fontSize': 16, 'lineHeight': '1.5'})
                    ], style={'padding': '20px', 'backgroundColor': EVOLUTION_GREY, 'borderRadius': '10px', 'margin': '20px 0', 'boxShadow': '0 2px 4px rgba(0, 0, 0, 0.05)'})
                ], style={'padding': '0 20px'})
            ], style={'padding': '20px'})
        ]),
        
        # Bus Allocation Tab
        dcc.Tab(label='Bus Allocation', style={'backgroundColor': EVOLUTION_DARK_GREEN, 'color': EVOLUTION_WHITE},
                selected_style={'backgroundColor': EVOLUTION_LIGHT_GREEN, 'color': EVOLUTION_WHITE, 'fontWeight': 'bold'},
                children=[
            html.Div([
                # Filters and controls
                html.Div([
                    html.H3('Bus Allocation Parameters', style={'margin': '10px 0px', 'color': EVOLUTION_TEXT_COLOR}),
                    html.Div([
                        html.Div([
                            html.Label('Select Route:', style={'fontWeight': 'bold'}),
                            dcc.Dropdown(
                                id='route-selector-allocation',
                                options=[{'label': route, 'value': route} for route in routes],
                                value=routes[0] if len(routes) > 0 else None
                            )
                        ], style={'width': '45%', 'display': 'inline-block', 'marginRight': '10%'}),
                        
                        html.Div([
                            html.Label('Optimization Target:', style={'fontWeight': 'bold'}),
                            dcc.Dropdown(
                                id='optimization-target',
                                options=[
                                    {'label': 'Maximize Profit', 'value': 'profit'},
                                    {'label': 'Maximize Capacity Utilization', 'value': 'capacity_util'},
                                    {'label': 'Minimize Unserved Demand', 'value': 'unserved_demand'}
                                ],
                                value='profit'
                            )
                        ], style={'width': '45%', 'display': 'inline-block'})
                    ]),
                    html.Button('Optimize Allocation', 
                                id='optimize-allocation-button', 
                                n_clicks=0,
                                style={'marginTop': '15px', 'padding': '10px 20px', 'fontSize': 16, 
                                       'backgroundColor': EVOLUTION_DARK_GREEN, 'color': EVOLUTION_WHITE, 'border': 'none', 
                                       'borderRadius': '5px', 'cursor': 'pointer', 'boxShadow': '0 2px 4px rgba(0, 0, 0, 0.1)'})
                ], style={'padding': '20px', 'backgroundColor': EVOLUTION_GREY, 'borderRadius': '10px', 'margin': '10px 20px', 'boxShadow': '0 2px 4px rgba(0, 0, 0, 0.05)'}),
                
                # Results section
                html.Div([
                    # Allocation charts
                    html.Div([
                        html.H4('Optimized Bus Allocation', style={'textAlign': 'center', 'color': EVOLUTION_TEXT_COLOR}),
                        dcc.Graph(id='bus-allocation-chart')
                    ], style={'backgroundColor': EVOLUTION_WHITE, 'padding': '15px', 'borderRadius': '10px', 'boxShadow': '0 2px 4px rgba(0, 0, 0, 0.05)', 'margin': '10px 0'}),
                    
                    # Financial impact
                    html.Div([
                        html.H4('Financial Impact', style={'textAlign': 'center', 'color': EVOLUTION_TEXT_COLOR}),
                        dcc.Graph(id='financial-impact-chart')
                    ], style={'backgroundColor': EVOLUTION_WHITE, 'padding': '15px', 'borderRadius': '10px', 'boxShadow': '0 2px 4px rgba(0, 0, 0, 0.05)', 'margin': '20px 0'}),
                    
                    # Allocation statistics and recommendations
                    html.Div([
                        html.H3('Allocation Recommendations', style={'margin': '10px 0px', 'color': EVOLUTION_TEXT_COLOR}),
                        html.Div(id='allocation-recommendations', style={'fontSize': 16, 'lineHeight': '1.5'})
                    ], style={'padding': '20px', 'backgroundColor': EVOLUTION_GREY, 'borderRadius': '10px', 'margin': '20px 0', 'boxShadow': '0 2px 4px rgba(0, 0, 0, 0.05)'})
                ], style={'padding': '0 20px'})
            ], style={'padding': '20px'})
        ]),
        
        # Financial Performance Tab
        dcc.Tab(label='Financial Performance', style={'backgroundColor': EVOLUTION_DARK_GREEN, 'color': EVOLUTION_WHITE},
                selected_style={'backgroundColor': EVOLUTION_LIGHT_GREEN, 'color': EVOLUTION_WHITE, 'fontWeight': 'bold'},
                children=[
            html.Div([
                # Filters and controls
                html.Div([
                    html.H3('Financial Analysis Filters', style={'margin': '10px 0px', 'color': EVOLUTION_TEXT_COLOR}),
                    html.Label('Select Routes:', style={'fontWeight': 'bold'}),
                    dcc.Dropdown(
                        id='route-selector-financial',
                        options=[{'label': route, 'value': route} for route in routes],
                        value=routes,
                        multi=True,
                        style={'marginBottom': '15px'}
                    ),
                    html.Label('Date Range:', style={'fontWeight': 'bold'}),
                    dcc.DatePickerRange(
                        id='date-range-financial',
                        start_date=df['datetime'].min() if df is not None else None,
                        end_date=df['datetime'].max() if df is not None else None,
                        display_format='YYYY-MM-DD'
                    ),
                ], style={'padding': '20px', 'backgroundColor': EVOLUTION_GREY, 'borderRadius': '10px', 'margin': '10px 20px', 'boxShadow': '0 2px 4px rgba(0, 0, 0, 0.05)'}),
                
                # First row of charts
                html.Div([
                    # Revenue by route
                    html.Div([
                        html.H4('Total Revenue by Route', style={'textAlign': 'center', 'color': EVOLUTION_TEXT_COLOR}),
                        dcc.Graph(id='revenue-by-route-chart')
                    ], style={'width': '48%', 'display': 'inline-block', 'verticalAlign': 'top', 'backgroundColor': EVOLUTION_WHITE, 'padding': '15px', 'borderRadius': '10px', 'boxShadow': '0 2px 4px rgba(0, 0, 0, 0.05)'}),
                    
                    # Profit margin by route
                    html.Div([
                        html.H4('Profit Margin by Route', style={'textAlign': 'center', 'color': EVOLUTION_TEXT_COLOR}),
                        dcc.Graph(id='profit-margin-chart')
                    ], style={'width': '48%', 'display': 'inline-block', 'verticalAlign': 'top', 'marginLeft': '4%', 'backgroundColor': EVOLUTION_WHITE, 'padding': '15px', 'borderRadius': '10px', 'boxShadow': '0 2px 4px rgba(0, 0, 0, 0.05)'})
                ], style={'margin': '20px 20px'}),
                
                # Second row of charts
                html.Div([
                    # Revenue vs Cost trend
                    html.Div([
                        html.H4('Revenue vs Cost Trend', style={'textAlign': 'center', 'color': EVOLUTION_TEXT_COLOR}),
                        dcc.Graph(id='revenue-cost-trend-chart')
                    ], style={'width': '48%', 'display': 'inline-block', 'verticalAlign': 'top', 'backgroundColor': EVOLUTION_WHITE, 'padding': '15px', 'borderRadius': '10px', 'boxShadow': '0 2px 4px rgba(0, 0, 0, 0.05)'}),
                    
                    # Capacity utilization vs profit
                    html.Div([
                        html.H4('Capacity Utilization vs Profit', style={'textAlign': 'center', 'color': EVOLUTION_TEXT_COLOR}),
                        dcc.Graph(id='capacity-util-profit-chart')
                    ], style={'width': '48%', 'display': 'inline-block', 'verticalAlign': 'top', 'marginLeft': '4%', 'backgroundColor': EVOLUTION_WHITE, 'padding': '15px', 'borderRadius': '10px', 'boxShadow': '0 2px 4px rgba(0, 0, 0, 0.05)'})
                ], style={'margin': '20px 20px'}),
                
                # Financial insights
                html.Div([
                    html.H3('Financial Insights', style={'margin': '10px 0px', 'color': EVOLUTION_TEXT_COLOR}),
                    html.Div(id='financial-insights', style={'fontSize': 16, 'lineHeight': '1.5'})
                ], style={'padding': '20px', 'backgroundColor': EVOLUTION_GREY, 'borderRadius': '10px', 'margin': '20px 20px', 'boxShadow': '0 2px 4px rgba(0, 0, 0, 0.05)'})
            ], style={'padding': '20px'})
        ]),
    ], style={'borderRadius': '10px', 'overflow': 'hidden'}),
    
    # Footer
    html.Div([
        html.Hr(style={'border': f'1px solid {EVOLUTION_DARK_GREEN}', 'margin': '30px 0 15px 0'}),
        html.Div([
            html.P('Evolution Inc. - Growing Together', 
                   style={'textAlign': 'center', 'color': EVOLUTION_DARK_GREEN, 'fontWeight': 'bold', 'fontSize': '16px'}),
            html.P('TripBook Analytics Dashboard © 2025', 
                   style={'textAlign': 'center', 'color': EVOLUTION_TEXT_COLOR, 'fontSize': '14px', 'margin': '5px 0'})
        ])
    ])
], style={
    'fontFamily': 'Arial, sans-serif', 
    'maxWidth': '1200px', 
    'margin': '0 auto', 
    'backgroundColor': EVOLUTION_WHITE,
    'padding': '15px',
    'borderRadius': '10px',
    'boxShadow': '0 4px 8px rgba(0, 0, 0, 0.1)'
})
        # Passenger Overview Tab
dcc.Tab(label='Passenger Overview', style={'backgroundColor': EVOLUTION_DARK_GREEN, 'color': EVOLUTION_WHITE},
        selected_style={'backgroundColor': EVOLUTION_LIGHT_GREEN, 'color': EVOLUTION_WHITE, 'fontWeight': 'bold'},
        children=[
    html.Div([
        # Filters and controls
        html.Div([
            html.H3('Filters', style={'margin': '10px 0px', 'color': EVOLUTION_TEXT_COLOR}),
            html.Label('Select Routes:', style={'fontWeight': 'bold'}),
            dcc.Dropdown(
                id='route-selector-overview',
                options=[{'label': route, 'value': route} for route in routes],
                value=routes,
                multi=True,
                style={'marginBottom': '15px'}
            ),
            html.Label('Date Range:', style={'fontWeight': 'bold'}),
            dcc.DatePickerRange(
                id='date-range-overview',
                start_date=df['datetime'].min() if df is not None else None,
                end_date=df['datetime'].max() if df is not None else None,
                display_format='YYYY-MM-DD'
            ),
        ], style={'padding': '20px', 'backgroundColor': EVOLUTION_GREY, 'borderRadius': '10px', 'margin': '10px 20px', 'boxShadow': '0 2px 4px rgba(0, 0, 0, 0.05)'}),
        
        # First row of charts
        html.Div([
            # Total passengers by route
            html.Div([
                html.H4('Total Passengers by Route', style={'textAlign': 'center', 'color': EVOLUTION_TEXT_COLOR}),
                dcc.Graph(id='total-passengers-chart')
            ], style={'width': '48%', 'display': 'inline-block', 'verticalAlign': 'top', 'backgroundColor': EVOLUTION_WHITE, 'padding': '15px', 'borderRadius': '10px', 'boxShadow': '0 2px 4px rgba(0, 0, 0, 0.05)'}),
            
            # Passenger trend over time
            html.Div([
                html.H4('Passenger Trend Over Time', style={'textAlign': 'center', 'color': EVOLUTION_TEXT_COLOR}),
                dcc.Graph(id='passenger-trend-chart')
            ], style={'width': '48%', 'display': 'inline-block', 'verticalAlign': 'top', 'marginLeft': '4%', 'backgroundColor': EVOLUTION_WHITE, 'padding': '15px', 'borderRadius': '10px', 'boxShadow': '0 2px 4px rgba(0, 0, 0, 0.05)'})
        ], style={'margin': '10px 20px'}),
        
        # Second row of charts
        html.Div([
            # Hourly patterns
            html.Div([
                html.H4('Hourly Passenger Patterns', style={'textAlign': 'center', 'color': EVOLUTION_TEXT_COLOR}),
                dcc.Graph(id='hourly-patterns-chart')
            ], style={'width': '48%', 'display': 'inline-block', 'verticalAlign': 'top', 'backgroundColor': EVOLUTION_WHITE, 'padding': '15px', 'borderRadius': '10px', 'boxShadow': '0 2px 4px rgba(0, 0, 0, 0.05)'}),
            
            # Weekly patterns
            html.Div([
                html.H4('Weekly Passenger Patterns', style={'textAlign': 'center', 'color': EVOLUTION_TEXT_COLOR}),
                dcc.Graph(id='weekly-patterns-chart')
            ], style={'width': '48%', 'display': 'inline-block', 'verticalAlign': 'top', 'marginLeft': '4%', 'backgroundColor': EVOLUTION_WHITE, 'padding': '15px', 'borderRadius': '10px', 'boxShadow': '0 2px 4px rgba(0, 0, 0, 0.05)'})
        ], style={'margin': '20px 20px'}),
        
        # Third row of charts
        html.Div([
            # Monthly patterns
            html.Div([
                html.H4('Monthly Passenger Patterns', style={'textAlign': 'center', 'color': EVOLUTION_TEXT_COLOR}),
                dcc.Graph(id='monthly-patterns-chart')
            ], style={'width': '48%', 'display': 'inline-block', 'verticalAlign': 'top', 'backgroundColor': EVOLUTION_WHITE, 'padding': '15px', 'borderRadius': '10px', 'boxShadow': '0 2px 4px rgba(0, 0, 0, 0.05)'}),
            
            # Yearly trends
            html.Div([
                html.H4('Yearly Passenger Trends', style={'textAlign': 'center', 'color': EVOLUTION_TEXT_COLOR}),
                dcc.Graph(id='yearly-trends-chart')
            ], style={'width': '48%', 'display': 'inline-block', 'verticalAlign': 'top', 'marginLeft': '4%', 'backgroundColor': EVOLUTION_WHITE, 'padding': '15px', 'borderRadius': '10px', 'boxShadow': '0 2px 4px rgba(0, 0, 0, 0.05)'})
        ], style={'margin': '20px 20px'}),
        
        # Key insights card
        html.Div([
            html.H3('Key Insights', style={'margin': '10px 0px', 'color': EVOLUTION_TEXT_COLOR}),
            html.Div(id='overview-insights', style={'fontSize': 16, 'lineHeight': '1.5'})
        ], style={'padding': '20px', 'backgroundColor': EVOLUTION_GREY, 'borderRadius': '10px', 'margin': '20px 20px', 'boxShadow': '0 2px 4px rgba(0, 0, 0, 0.05)'})
    ], style={'padding': '20px'})
]),
        
if __name__ == '__main__':
    
    app.run_server(debug=True, port=8050)