import warnings
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns
from statsmodels.tsa.seasonal import seasonal_decompose
from statsmodels.tsa.holtwinters import ExponentialSmoothing
from statsmodels.tsa.statespace.sarimax import SARIMAX
from prophet import Prophet
from sklearn.metrics import mean_absolute_error, mean_squared_error
import os

# Import our new metrics calculation module
from metrics_calculation import calculate_transport_metrics, summarize_metrics_by_route, generate_metrics_insights, get_optimization_recommendations

# Suppress warnings
warnings.simplefilter(action="ignore", category=FutureWarning)
warnings.filterwarnings('ignore')

# Set styles
plt.style.use('fivethirtyeight')
sns.set_palette('Set2')

def load_and_prepare_data(file_path='tripbook_passenger_data.csv'):
    """
    Load and prepare the passenger data for analysis
    """
    print("Loading passenger data...")
    df = pd.read_csv(file_path)
    df['datetime'] = pd.to_datetime(df['datetime'])
    
    # Set datetime as index for time series analysis
    df.set_index('datetime', inplace=True)
    
    # Calculate transport metrics
    print("Calculating transport metrics...")
    df_with_metrics = calculate_transport_metrics(df.reset_index())
    
    # Create a summary by route
    metrics_summary = summarize_metrics_by_route(df_with_metrics)
    
    # Generate insights
    metrics_insights = generate_metrics_insights(df_with_metrics, metrics_summary)
    
    # Get optimization recommendations
    recommendations = get_optimization_recommendations(metrics_insights)
    
    # Save metrics results
    os.makedirs('analysis_results', exist_ok=True)
    df_with_metrics.to_csv('analysis_results/transport_metrics_detailed.csv', index=False)
    metrics_summary.to_csv('analysis_results/transport_metrics_summary.csv', index=False)
    
    # Print insights and recommendations
    print("\nTransport Metrics Insights:")
    print("--------------------------")
    for category, insight in metrics_insights.items():
        print(f"{category.replace('_', ' ').title()}: {insight['message']}")
    
    print("\nOptimization Recommendations:")
    print("----------------------------")
    for i, rec in enumerate(recommendations, 1):
        print(f"{i}. {rec}")
    
    return df, df_with_metrics, metrics_summary, metrics_insights, recommendations

def analyze_transport_metrics(df_with_metrics, metrics_summary):
    """
    Analyze and visualize transport metrics
    """
    print("\nAnalyzing transport metrics...")
    
    # Create results directory if it doesn't exist
    os.makedirs('analysis_results', exist_ok=True)
    
    # 1. ASK vs RPK analysis
    plt.figure(figsize=(14, 8))
    x = np.arange(len(metrics_summary))
    width = 0.35
    
    plt.bar(x - width/2, metrics_summary['ask'] / 1000, width, label='ASK (in thousands)')
    plt.bar(x + width/2, metrics_summary['rpk'] / 1000, width, label='RPK (in thousands)')
    
    plt.xlabel('Route')
    plt.ylabel('Seat Kilometers (thousands)')
    plt.title('Available Seat Kilometers (ASK) vs Revenue Passenger Kilometers (RPK) by Route')
    plt.xticks(x, metrics_summary['route'], rotation=45)
    plt.legend()
    plt.tight_layout()
    plt.savefig('analysis_results/ask_vs_rpk.png', dpi=300)
    
    # 2. Load Factor analysis
    plt.figure(figsize=(14, 8))
    sns.barplot(x='route', y='load_factor', data=metrics_summary)
    plt.axhline(y=50, color='r', linestyle='--', label='50% Threshold')
    plt.axhline(y=85, color='g', linestyle='--', label='85% Optimal')
    
    plt.xlabel('Route')
    plt.ylabel('Load Factor (%)')
    plt.title('Average Load Factor by Route')
    plt.xticks(rotation=45)
    plt.legend()
    plt.tight_layout()
    plt.savefig('analysis_results/load_factor.png', dpi=300)
    
    # 3. RPKM vs CPKM analysis
    plt.figure(figsize=(14, 8))
    x = np.arange(len(metrics_summary))
    width = 0.35
    
    plt.bar(x - width/2, metrics_summary['rpkm'], width, label='RPKM')
    plt.bar(x + width/2, metrics_summary['cpkm'], width, label='CPKM')
    
    plt.xlabel('Route')
    plt.ylabel('Amount per Kilometer (RWF)')
    plt.title('Revenue per Kilometer (RPKM) vs Cost per Kilometer (CPKM) by Route')
    plt.xticks(x, metrics_summary['route'], rotation=45)
    plt.legend()
    plt.tight_layout()
    plt.savefig('analysis_results/rpkm_vs_cpkm.png', dpi=300)
    
    # 4. Profitability Index
    plt.figure(figsize=(14, 8))
    sns.barplot(x='route', y='profitability_index', data=metrics_summary)
    plt.axhline(y=1, color='r', linestyle='--', label='Breakeven (PI=1)')
    
    plt.xlabel('Route')
    plt.ylabel('Profitability Index (RPKM/CPKM)')
    plt.title('Profitability Index by Route')
    plt.xticks(rotation=45)
    plt.legend()
    plt.tight_layout()
    plt.savefig('analysis_results/profitability_index.png', dpi=300)
    
    # 5. Hourly Load Factor Patterns
    hourly_load_factors = df_with_metrics.groupby(['hour', 'route'])['load_factor'].mean().reset_index()
    
    plt.figure(figsize=(14, 8))
    for route in df_with_metrics['route'].unique():
        route_data = hourly_load_factors[hourly_load_factors['route'] == route]
        plt.plot(route_data['hour'], route_data['load_factor'], marker='o', label=route)
    
    plt.xlabel('Hour of Day')
    plt.ylabel('Average Load Factor (%)')
    plt.title('Hourly Load Factor Patterns by Route')
    plt.xticks(range(0, 24, 2))
    plt.grid(True, alpha=0.3)
    plt.legend(title='Routes', bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.tight_layout()
    plt.savefig('analysis_results/hourly_load_factors.png', dpi=300)
    
    # 6. Daily Load Factor Patterns
    daily_load_factors = df_with_metrics.groupby(['day_of_week', 'route'])['load_factor'].mean().reset_index()
    day_names = {0: 'Monday', 1: 'Tuesday', 2: 'Wednesday', 3: 'Thursday', 
                4: 'Friday', 5: 'Saturday', 6: 'Sunday'}
    daily_load_factors['day_name'] = daily_load_factors['day_of_week'].map(day_names)
    
    plt.figure(figsize=(14, 8))
    for route in df_with_metrics['route'].unique():
        route_data = daily_load_factors[daily_load_factors['route'] == route]
        plt.plot(route_data['day_of_week'], route_data['load_factor'], marker='o', label=route)
    
    plt.xlabel('Day of Week')
    plt.ylabel('Average Load Factor (%)')
    plt.title('Daily Load Factor Patterns by Route')
    plt.xticks(range(7), [day_names[i] for i in range(7)])
    plt.grid(True, alpha=0.3)
    plt.legend(title='Routes', bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.tight_layout()
    plt.savefig('analysis_results/daily_load_factors.png', dpi=300)
    
    # 7. Revenue per Trip Analysis
    plt.figure(figsize=(14, 8))
    sns.barplot(x='route', y='revenue_per_trip', data=metrics_summary)
    
    plt.xlabel('Route')
    plt.ylabel('Average Revenue per Trip (RWF)')
    plt.title('Average Revenue per Trip by Route')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig('analysis_results/revenue_per_trip.png', dpi=300)
    
    # 8. Profit per Kilometer Analysis
    plt.figure(figsize=(14, 8))
    sns.barplot(x='route', y='profit_per_km', data=metrics_summary)
    
    plt.xlabel('Route')
    plt.ylabel('Profit per Kilometer (RWF)')
    plt.title('Average Profit per Kilometer by Route')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig('analysis_results/profit_per_km.png', dpi=300)
    
    print("Transport metrics analysis complete. All visualizations have been saved.")
    
    return hourly_load_factors, daily_load_factors

# ==== Include other functions from the original passenger_analysis_forecast.py file here ====

def run_full_analysis(file_path='tripbook_passenger_data.csv'):
    """
    Run the full passenger data analysis pipeline including transport metrics
    """
    try:
        # Create results directory
        os.makedirs('analysis_results', exist_ok=True)
            
        # Load data and calculate transport metrics
        df, df_with_metrics, metrics_summary, metrics_insights, recommendations = load_and_prepare_data(file_path)
            
        # Analyze transport metrics
        hourly_load_factors, daily_load_factors = analyze_transport_metrics(df_with_metrics, metrics_summary)
            
        # Basic exploration
        basic_data_exploration(df)
            
        # Time-based pattern analysis
        hourly_patterns, peak_hours = analyze_hourly_patterns(df)
        daily_patterns = analyze_daily_patterns(df)
        monthly_patterns = analyze_monthly_patterns(df)
        yearly_patterns, growth_rates = analyze_yearly_trends(df)
            
        # Performance analysis
        capacity_util = analyze_capacity_utilization(df)
        financial_metrics = analyze_financial_performance(df)
            
        # Time series analysis and forecasting for all routes
        routes = df['route'].unique()
        results_by_route = {}
        
        for route in routes:
            print(f"\n{'='*50}")
            print(f"ANALYZING ROUTE: {route}")
            print(f"{'='*50}")
            
            # Perform decomposition
            try:
                decomposition = time_series_decomposition(df, route=route)
            except Exception as e:
                print(f"Error in time series decomposition: {e}")
                print("Continuing with other analyses...")
                decomposition = None
                
            # Forecast with Prophet
            try:
                prophet_forecast = forecast_with_prophet(df, route=route, forecast_periods=365)
            except Exception as e:
                print(f"Error in Prophet forecasting: {e}")
                print("Continuing with other analyses...")
                prophet_forecast = None
                
            # Forecast with SARIMA
            try:
                sarima_forecast, sarima_ci = forecast_route_with_sarima(df, route=route, forecast_periods=365)
            except Exception as e:
                print(f"Error in SARIMA forecasting: {e}")
                print("Continuing with other analyses...")
                sarima_forecast, sarima_ci = None, None
                
            # Use the forecast that worked for optimization
            forecast_for_optimization = prophet_forecast if prophet_forecast is not None else sarima_forecast
                
            # Optimize bus allocation
            if forecast_for_optimization is not None:
                try:
                    allocation = optimize_bus_allocation(df, forecast_for_optimization, route=route)
                except Exception as e:
                    print(f"Error in bus allocation optimization: {e}")
                    print("Skipping bus allocation optimization.")
                    allocation = None
            else:
                print("No forecast available for bus allocation optimization.")
                allocation = None
            
            # Store results for this route
            results_by_route[route] = {
                'decomposition': decomposition,
                'prophet_forecast': prophet_forecast,
                'sarima_forecast': sarima_forecast,
                'allocation': allocation
            }
            
        print("\nAnalysis complete. All visualizations have been saved.")
            
        return {
            'hourly_patterns': hourly_patterns,
            'peak_hours': peak_hours,
            'daily_patterns': daily_patterns,
            'monthly_patterns': monthly_patterns,
            'yearly_patterns': yearly_patterns,
            'growth_rates': growth_rates,
            'capacity_util': capacity_util,
            'financial_metrics': financial_metrics,
            'route_results': results_by_route,
            'transport_metrics': {
                'detailed': df_with_metrics,
                'summary': metrics_summary,
                'insights': metrics_insights,
                'recommendations': recommendations,
                'hourly_load_factors': hourly_load_factors,
                'daily_load_factors': daily_load_factors
            }
        }
    except Exception as e:
        print(f"Error in analysis: {e}")
        import traceback
        traceback.print_exc()
        print("Analysis terminated due to errors.")
        return None
def basic_data_exploration(df):
    """
    Perform basic data exploration
    """
    print("\nBasic Data Exploration:")
    print("-----------------------")
        
    print(f"Data spans from {df.index.min()} to {df.index.max()}")
    print(f"Total number of records: {len(df)}")
    print("\nUnique routes:")
    for route in df['route'].unique():
        print(f"  - {route}")
        
    print("\nPassenger statistics by route:")
    route_stats = df.groupby('route')['passengers'].agg(['count', 'mean', 'std', 'min', 'max'])
    print(route_stats)
        
    return route_stats

def analyze_hourly_patterns(df):
    """
    Analyze hourly patterns in passenger traffic
    """
    print("\nAnalyzing hourly patterns...")
        
    # Create pivot table for hourly passenger averages by route
    hourly_passengers = df.pivot_table(
        index='hour', 
        columns='route', 
        values='passengers', 
        aggfunc='mean'
    )
        
    # Plot hourly patterns
    plt.figure(figsize=(14, 8))
    for route in hourly_passengers.columns:
        plt.plot(hourly_passengers.index, hourly_passengers[route], label=route, marker='o', linestyle='-')
        
    plt.title('Average Hourly Passenger Volume by Route', fontsize=16)
    plt.xlabel('Hour of Day', fontsize=14)
    plt.ylabel('Average Number of Passengers', fontsize=14)
    plt.xticks(range(0, 24))
    plt.grid(True, alpha=0.3)
    plt.legend(title='Routes', bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.tight_layout()
    plt.savefig('analysis_results/hourly_passenger_patterns.png', dpi=300)
        
    # Identify peak hours for each route
    peak_hours = {}
    for route in hourly_passengers.columns:
        peak_hour = hourly_passengers[route].idxmax()
        peak_value = hourly_passengers[route].max()
        peak_hours[route] = (peak_hour, peak_value)
        
    print("\nPeak hours by route:")
    for route, (hour, value) in peak_hours.items():
        print(f"  - {route}: {hour}:00 with {value:.1f} average passengers")
        
    return hourly_passengers, peak_hours


def analyze_daily_patterns(df):
    """
    Analyze daily patterns in passenger traffic
    """
    print("\nAnalyzing daily patterns...")
        
    # Create pivot table for daily passenger averages by route
    daily_passengers = df.pivot_table(
        index='day_of_week', 
        columns='route', 
        values='passengers', 
        aggfunc='mean'
    )
        
    # Map day numbers to names for better readability
    day_names = {
        0: 'Monday', 
        1: 'Tuesday', 
        2: 'Wednesday', 
        3: 'Thursday', 
        4: 'Friday', 
        5: 'Saturday', 
        6: 'Sunday'
    }
    daily_passengers.index = [day_names[day] for day in daily_passengers.index]
        
    # Plot daily patterns
    plt.figure(figsize=(14, 8))
    for route in daily_passengers.columns:
        plt.plot(daily_passengers.index, daily_passengers[route], label=route, marker='o', linestyle='-')
        
    plt.title('Average Daily Passenger Volume by Route', fontsize=16)
    plt.xlabel('Day of Week', fontsize=14)
    plt.ylabel('Average Number of Passengers', fontsize=14)
    plt.grid(True, alpha=0.3)
    plt.legend(title='Routes', bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.tight_layout()
    plt.savefig('analysis_results/daily_passenger_patterns.png', dpi=300)
        
    return daily_passengers


def analyze_monthly_patterns(df):
    """
    Analyze monthly patterns in passenger traffic
    """
    print("\nAnalyzing monthly patterns...")
        
    # Create pivot table for monthly passenger averages by route
    monthly_passengers = df.pivot_table(
        index='month', 
        columns='route', 
        values='passengers', 
        aggfunc='mean'
    )
        
    # Map month numbers to names for better readability
    month_names = {
        1: 'Jan', 2: 'Feb', 3: 'Mar', 4: 'Apr', 5: 'May', 6: 'Jun',
        7: 'Jul', 8: 'Aug', 9: 'Sep', 10: 'Oct', 11: 'Nov', 12: 'Dec'
    }
    monthly_passengers.index = [month_names[month] for month in monthly_passengers.index]
        
    # Plot monthly patterns
    plt.figure(figsize=(14, 8))
    for route in monthly_passengers.columns:
        plt.plot(monthly_passengers.index, monthly_passengers[route], label=route, marker='o', linestyle='-')
        
    plt.title('Average Monthly Passenger Volume by Route', fontsize=16)
    plt.xlabel('Month', fontsize=14)
    plt.ylabel('Average Number of Passengers', fontsize=14)
    plt.grid(True, alpha=0.3)
    plt.legend(title='Routes', bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.tight_layout()
    plt.savefig('analysis_results/monthly_passenger_patterns.png', dpi=300)
        
    return monthly_passengers

def analyze_yearly_trends(df):
    """
    Analyze yearly trends in passenger traffic
    """
    print("\nAnalyzing yearly trends...")
        
    # Create pivot table for yearly passenger averages by route
    yearly_passengers = df.pivot_table(
        index='year', 
        columns='route', 
        values='passengers', 
        aggfunc='mean'
    )
        
    # Plot yearly trends
    plt.figure(figsize=(14, 8))
    for route in yearly_passengers.columns:
        plt.plot(yearly_passengers.index, yearly_passengers[route], label=route, marker='o', linestyle='-')
        
    plt.title('Average Yearly Passenger Volume by Route', fontsize=16)
    plt.xlabel('Year', fontsize=14)
    plt.ylabel('Average Number of Passengers', fontsize=14)
    plt.grid(True, alpha=0.3)
    plt.legend(title='Routes', bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.tight_layout()
    plt.savefig('analysis_results/yearly_passenger_trends.png', dpi=300)
        
    # Calculate growth rates
    growth_rates = {}
    for route in yearly_passengers.columns:
        first_year = yearly_passengers.index.min()
        last_year = yearly_passengers.index.max()
        first_value = yearly_passengers.loc[first_year, route]
        last_value = yearly_passengers.loc[last_year, route]
        years_diff = last_year - first_year
            
        # Calculate compound annual growth rate (CAGR)
        cagr = (last_value / first_value) ** (1 / years_diff) - 1
        growth_rates[route] = cagr * 100  # Convert to percentage
        
    print("\nCompound Annual Growth Rate (CAGR) by route:")
    for route, rate in growth_rates.items():
        print(f"  - {route}: {rate:.2f}%")
        
    return yearly_passengers, growth_rates


def analyze_capacity_utilization(df):
    """
    Analyze capacity utilization and efficiency
    """
    print("\nAnalyzing capacity utilization...")
        
    # Create pivot table for capacity utilization by route
    capacity_util = df.pivot_table(
        index='route', 
        values=['capacity_utilization', 'passengers', 'num_buses_allocated'],
        aggfunc={'capacity_utilization': 'mean', 'passengers': 'sum', 'num_buses_allocated': 'sum'}
    )
        
    # Plot capacity utilization
    plt.figure(figsize=(14, 8))
    sns.barplot(x=capacity_util.index, y=capacity_util['capacity_utilization'])
        
    plt.title('Average Capacity Utilization by Route', fontsize=16)
    plt.xlabel('Route', fontsize=14)
    plt.ylabel('Average Capacity Utilization (%)', fontsize=14)
    plt.xticks(rotation=45)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig('analysis_results/capacity_utilization.png', dpi=300)
        
    print("\nAverage capacity utilization by route:")
    for route in capacity_util.index:
        print(f"  - {route}: {capacity_util.loc[route, 'capacity_utilization']:.2f}%")
        
    return capacity_util


def analyze_financial_performance(df):
    """
    Analyze financial performance metrics
    """
    print("\nAnalyzing financial performance...")
    
    # Create pivot table for financial metrics by route
    financial_metrics = df.pivot_table(
        index='route', 
        values=['revenue', 'operating_cost', 'profit'],
        aggfunc='sum'
    )
    
    # Add profit margin column
    financial_metrics['profit_margin'] = financial_metrics['profit'] / financial_metrics['revenue'] * 100
    
    # Plot revenue, cost, and profit
    plt.figure(figsize=(14, 8))
    financial_metrics[['revenue', 'operating_cost', 'profit']].plot(kind='bar', ax=plt.gca())
    
    plt.title('Financial Performance by Route (Total)', fontsize=16)
    plt.xlabel('Route', fontsize=14)
    plt.ylabel('Amount (RWF)', fontsize=14)
    plt.xticks(rotation=45)
    plt.grid(True, alpha=0.3)
    plt.legend(title='Metric')
    plt.tight_layout()
    plt.savefig('analysis_results/financial_performance.png', dpi=300)
    
    # Plot profit margin
    plt.figure(figsize=(14, 8))
    financial_metrics['profit_margin'].plot(kind='bar', color='green', ax=plt.gca())
    
    plt.title('Profit Margin by Route', fontsize=16)
    plt.xlabel('Route', fontsize=14)
    plt.ylabel('Profit Margin (%)', fontsize=14)
    plt.xticks(rotation=45)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig('analysis_results/profit_margin.png', dpi=300)
    
    print("\nFinancial metrics by route (in millions RWF):")
    for route in financial_metrics.index:
        revenue = financial_metrics.loc[route, 'revenue'] / 1e6
        cost = financial_metrics.loc[route, 'operating_cost'] / 1e6
        profit = financial_metrics.loc[route, 'profit'] / 1e6
        margin = financial_metrics.loc[route, 'profit_margin']
        print(f"  - {route}: Revenue: {revenue:.2f}M, Cost: {cost:.2f}M, Profit: {profit:.2f}M, Margin: {margin:.2f}%")
    
    return financial_metrics


def time_series_decomposition(df, route="Kigali-Musanze"):
    """
    Perform time series decomposition for a specific route
    """
    print(f"\nPerforming time series decomposition for {route}...")
    
    # Prepare data for the specific route
    route_data = df[df['route'] == route].copy()
    
    # Resample to daily frequency
    daily_data = route_data['passengers'].resample('D').mean()
    daily_data = daily_data.fillna(daily_data.bfill())
    
    # Perform decomposition
    decomposition = seasonal_decompose(daily_data, model='multiplicative', period=7)
    
    # Plot decomposition
    plt.figure(figsize=(14, 12))
    
    plt.subplot(411)
    plt.plot(daily_data, label='Observed')
    plt.legend(loc='upper left')
    plt.title(f'Time Series Decomposition: {route}', fontsize=16)
    
    plt.subplot(412)
    plt.plot(decomposition.trend, label='Trend')
    plt.legend(loc='upper left')
    
    plt.subplot(413)
    plt.plot(decomposition.seasonal, label='Seasonality')
    plt.legend(loc='upper left')
    
    plt.subplot(414)
    plt.plot(decomposition.resid, label='Residuals')
    plt.legend(loc='upper left')
    
    plt.tight_layout()
    plt.savefig(f'analysis_results/time_series_decomposition_{route.replace("-", "_")}.png', dpi=300)
    
    return decomposition

def forecast_with_prophet(df, route="Kigali-Musanze", forecast_periods=365):
    """
    Forecast passenger demand using Prophet
    """
    print(f"\nForecasting passenger demand for {route} using Prophet...")
        
    # Prepare data for the specific route
    route_data = df[df['route'] == route].copy()
        
    # Resample to daily frequency
    daily_data = route_data['passengers'].resample('D').mean()
    daily_data = daily_data.fillna(daily_data.bfill())
        
    # Prepare data for Prophet
    prophet_data = pd.DataFrame({
        'ds': daily_data.index,
        'y': daily_data.values
    })
        
    # Create and fit Prophet model
    model = Prophet(
        yearly_seasonality=True,
        weekly_seasonality=True,
        daily_seasonality=False,
        changepoint_prior_scale=0.05
    )
        
    # Add custom Rwanda holidays
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
                
        print("  Added custom Rwanda holidays to the forecast model.")
    except Exception as e:
        print(f"  Warning: Could not add custom holidays: {e}")
        
    model.fit(prophet_data)
    
    # Create future dataframe for forecasting
    future = model.make_future_dataframe(periods=forecast_periods)
    
    # Make forecast
    forecast = model.predict(future)
    
    # Plot forecast
    plt.figure(figsize=(14, 8))
    
    # Plot actual values
    plt.plot(prophet_data['ds'], prophet_data['y'], label='Historical Data', color='blue')
    
    # Plot forecast
    plt.plot(forecast['ds'], forecast['yhat'], label='Forecast', color='red')
    
    # Plot confidence intervals
    plt.fill_between(
        forecast['ds'], 
        forecast['yhat_lower'], 
        forecast['yhat_upper'], 
        color='red', 
        alpha=0.2, 
        label='95% Confidence Interval'
    )
    
    plt.title(f'Passenger Demand Forecast for {route}', fontsize=16)
    plt.xlabel('Date', fontsize=14)
    plt.ylabel('Number of Passengers', fontsize=14)
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.tight_layout()
    plt.savefig(f'analysis_results/prophet_forecast_{route.replace("-", "_")}.png', dpi=300)
    
    # Find peak demand in the future period only
    future_forecast = forecast.iloc[-forecast_periods:]
    peak_day = future_forecast.loc[future_forecast['yhat'].idxmax()]
    
    print(f"\nPeak demand for {route} is forecast on {peak_day['ds'].date()} with {peak_day['yhat']:.0f} passengers")
    
    return forecast

def forecast_route_with_sarima(df, route="Kigali-Musanze", forecast_periods=365):
    """
    Forecast passenger demand using SARIMA
    """
    print(f"\nForecasting passenger demand for {route} using SARIMA...")
    
    # Prepare data for the specific route
    route_data = df[df['route'] == route].copy()
    
    # Resample to daily frequency
    daily_data = route_data['passengers'].resample('D').mean()
    daily_data = daily_data.fillna(daily_data.bfill())
    
    # Define SARIMA parameters - these should be optimized based on ACF/PACF analysis
    order = (1, 1, 1)
    seasonal_order = (1, 1, 1, 7)  # Weekly seasonality
    
    # Fit SARIMA model
    model = SARIMAX(
        daily_data,
        order=order,
        seasonal_order=seasonal_order,
        enforce_stationarity=False,
        enforce_invertibility=False
    )
    
    results = model.fit(disp=False)
    
    # Forecast
    forecast_index = pd.date_range(
        start=daily_data.index[-1] + pd.Timedelta(days=1),
        periods=forecast_periods,
        freq='D'
    )
    
    forecast = results.get_forecast(steps=forecast_periods)
    forecast_mean = forecast.predicted_mean
    forecast_ci = forecast.conf_int()
    
    # Plot forecast
    plt.figure(figsize=(14, 8))
    
    # Plot historical data
    plt.plot(daily_data.index, daily_data, label='Historical Data', color='blue')
    
    # Plot forecast
    plt.plot(forecast_index, forecast_mean, label='Forecast', color='red')
    
    # Plot confidence intervals
    plt.fill_between(
        forecast_index,
        forecast_ci.iloc[:, 0],
        forecast_ci.iloc[:, 1],
        color='red',
        alpha=0.2,
        label='95% Confidence Interval'
    )
    
    plt.title(f'SARIMA Forecast for {route}', fontsize=16)
    plt.xlabel('Date', fontsize=14)
    plt.ylabel('Number of Passengers', fontsize=14)
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.tight_layout()
    plt.savefig(f'analysis_results/sarima_forecast_{route.replace("-", "_")}.png', dpi=300)
    
    return forecast_mean, forecast_ci


def optimize_bus_allocation(df, forecast, route="Kigali-Musanze"):
    """
    Optimize bus allocation based on forecasted demand
    """
    print(f"\nOptimizing bus allocation for {route}...")
        
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
    route_distance = df[df['route'] == route]['route_distance_km'].iloc[0]
        
    # Get ticket price
    ticket_price = df[df['route'] == route]['ticket_price'].iloc[0]
        
    # For Prophet forecast
    if isinstance(forecast, pd.DataFrame) and 'yhat' in forecast.columns:
        # Use only the future forecasted values
        forecast_values = forecast['yhat'].tail(365).values
    else:
        # For SARIMA forecast
        forecast_values = forecast.values
        
    # Create optimal allocation dataframe
    allocation_results = []
        
    for demand in forecast_values:
        best_profit = float('-inf')
        best_allocation = None
            
        # Try different bus combinations
        for bus_type, capacity in bus_types.items():
            # Calculate minimum number of buses needed
            min_buses = max(1, int(np.ceil(demand / capacity)))
                
            # Try a range around this minimum
            for num_buses in range(max(1, min_buses-1), min_buses+3):
                # Calculate potential revenue (assuming all forecasted passengers can be served)
                potential_revenue = min(demand, num_buses * capacity) * ticket_price
                    
                # Calculate operating cost
                operating_cost = num_buses * cost_per_km[bus_type] * route_distance
                    
                # Calculate profit
                profit = potential_revenue - operating_cost
                    
                # Calculate capacity utilization
                capacity_util = min(100, (min(demand, num_buses * capacity) / (num_buses * capacity)) * 100)
                    
                # Update best allocation if profit is higher
                if profit > best_profit:
                    best_profit = profit
                    best_allocation = {
                        'bus_type': bus_type,
                        'num_buses': num_buses,
                        'potential_demand': demand,
                        'capacity': num_buses * capacity,
                        'potential_revenue': potential_revenue,
                        'operating_cost': operating_cost,
                        'profit': profit,
                        'capacity_utilization': capacity_util,
                        'passengers_served': min(demand, num_buses * capacity),
                        'unserved_demand': max(0, demand - num_buses * capacity)
                    }
            
        allocation_results.append(best_allocation)
        
    # Convert to dataframe
    allocation_df = pd.DataFrame(allocation_results)
        
    # Plot results
    plt.figure(figsize=(14, 8))
        
    plt.subplot(311)
    plt.title(f'Optimized Bus Allocation for {route}', fontsize=16)
    plt.plot(allocation_df['potential_demand'], label='Forecasted Demand', color='blue')
    plt.plot(allocation_df['capacity'], label='Allocated Capacity', color='green')
    plt.ylabel('Passengers / Capacity', fontsize=14)
    plt.legend()
    plt.grid(True, alpha=0.3)
        
    plt.subplot(312)
    plt.bar(range(len(allocation_df)), allocation_df['num_buses'], label='Number of Buses')
    colors = {'Mini': 'green', 'Medium': 'blue', 'Large': 'red'}
    for i, bus_type in enumerate(allocation_df['bus_type']):
        plt.bar(i, allocation_df.iloc[i]['num_buses'], color=colors[bus_type])
    plt.ylabel('Number of Buses', fontsize=14)
    plt.grid(True, alpha=0.3)
        
    plt.subplot(313)
    plt.plot(allocation_df['profit'], label='Profit', color='green')
    plt.plot(allocation_df['potential_revenue'], label='Revenue', color='blue')
    plt.plot(allocation_df['operating_cost'], label='Operating Cost', color='red')
    plt.ylabel('Amount (RWF)', fontsize=14)
    plt.xlabel('Day', fontsize=14)
    plt.legend()
    plt.grid(True, alpha=0.3)
        
    plt.tight_layout()
    plt.savefig(f'analysis_results/optimized_allocation_{route.replace("-", "_")}.png', dpi=300)
        
    # Calculate statistics
    print(f"\nOptimized allocation statistics for {route}:")
    print(f"  - Average daily profit: {allocation_df['profit'].mean():.2f} RWF")
    print(f"  - Average capacity utilization: {allocation_df['capacity_utilization'].mean():.2f}%")
    print(f"  - Average number of buses needed: {allocation_df['num_buses'].mean():.2f}")
        
    # Bus type distribution
    bus_type_counts = allocation_df['bus_type'].value_counts(normalize=True) * 100
    print("\nOptimal bus type distribution:")
    for bus_type, percentage in bus_type_counts.items():
        print(f"  - {bus_type}: {percentage:.2f}%")
        
    return allocation_df



if __name__ == "__main__":
    # Run the full analysis
    results = run_full_analysis()