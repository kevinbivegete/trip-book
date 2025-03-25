import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def calculate_transport_metrics(df):
    """
    Calculate key transport metrics for the TripBook fleet management system.
    
    Parameters:
    -----------
    df : pandas.DataFrame
        Input DataFrame containing passenger data
        
    Returns:
    --------
    pandas.DataFrame
        DataFrame with calculated metrics
    """
    # Create a copy to avoid modifying the original DataFrame
    metrics_df = df.copy()
    
    # 1. Calculate Available Seat Kilometers (ASK)
    # ASK = Total Seats × Distance Traveled
    metrics_df['ask'] = metrics_df['num_buses_allocated'] * metrics_df['bus_capacity'] * metrics_df['route_distance_km']
    
    # 2. Calculate Revenue Passenger Kilometers (RPK)
    # RPK = Revenue Paying Passengers × Distance
    metrics_df['rpk'] = metrics_df['passengers'] * metrics_df['route_distance_km']
    
    # 3. Calculate Load Factor (%)
    # Load Factor = (RPK / ASK) × 100
    metrics_df['load_factor'] = (metrics_df['rpk'] / metrics_df['ask']) * 100
    
    # 4. Calculate Revenue per Kilometer (RPKM)
    # RPKM = Total Revenue / Total Distance Traveled
    metrics_df['rpkm'] = metrics_df['revenue'] / (metrics_df['num_buses_allocated'] * metrics_df['route_distance_km'])
    
    # 5. Calculate Cost per Kilometer (CPKM)
    # CPKM = Total Operational Costs / Total Distance Traveled
    metrics_df['cpkm'] = metrics_df['operating_cost'] / (metrics_df['num_buses_allocated'] * metrics_df['route_distance_km'])
    
    # 6. Calculate Bus Utilization Rate (%)
    # For this, we need to calculate the hourly utilization
    # We'll consider a bus as utilized if it has passengers during that hour
    metrics_df['bus_utilization_rate'] = (metrics_df['passengers'] > 0).astype(int) * 100
    
    # 7. Passenger Revenue per Trip
    # Revenue per Trip = Total Revenue / Total Trips
    # Since each row represents an hour of operation, we'll consider each row as a "trip"
    metrics_df['revenue_per_trip'] = metrics_df['revenue']
    
    # 8. Additional derived metrics
    # Profit per Kilometer
    metrics_df['profit_per_km'] = metrics_df['profit'] / (metrics_df['num_buses_allocated'] * metrics_df['route_distance_km'])
    
    # Profitability Index (PI): Ratio of RPKM to CPKM
    metrics_df['profitability_index'] = metrics_df['rpkm'] / metrics_df['cpkm']
    
    # Clean up any potential NaN or infinite values
    for col in ['load_factor', 'rpkm', 'cpkm', 'profitability_index']:
        metrics_df[col] = metrics_df[col].replace([np.inf, -np.inf], np.nan)
        metrics_df[col] = metrics_df[col].fillna(0)
    
    return metrics_df

def summarize_metrics_by_route(df):
    """
    Summarize key transport metrics by route.
    
    Parameters:
    -----------
    df : pandas.DataFrame
        DataFrame with calculated metrics
        
    Returns:
    --------
    pandas.DataFrame
        Summary DataFrame with average metrics by route
    """
    # Group by route and calculate average metrics
    summary = df.groupby('route').agg({
        'ask': 'sum',
        'rpk': 'sum',
        'load_factor': 'mean',
        'rpkm': 'mean',
        'cpkm': 'mean',
        'bus_utilization_rate': 'mean',
        'revenue_per_trip': 'mean',
        'profit_per_km': 'mean',
        'profitability_index': 'mean',
        'passengers': 'sum',
        'revenue': 'sum',
        'operating_cost': 'sum',
        'profit': 'sum'
    }).reset_index()
    
    # Recalculate some metrics at the route level
    summary['load_factor'] = (summary['rpk'] / summary['ask']) * 100
    
    return summary

def generate_metrics_insights(df, summary_df):
    """
    Generate insights based on calculated metrics.
    
    Parameters:
    -----------
    df : pandas.DataFrame
        DataFrame with calculated metrics
    summary_df : pandas.DataFrame
        Summary DataFrame with average metrics by route
        
    Returns:
    --------
    dict
        Dictionary containing insights for each metric
    """
    insights = {}
    
    # ASK vs RPK insights
    total_ask = summary_df['ask'].sum()
    total_rpk = summary_df['rpk'].sum()
    overall_load_factor = (total_rpk / total_ask) * 100
    
    insights['capacity_utilization'] = {
        'total_ask': total_ask,
        'total_rpk': total_rpk,
        'overall_load_factor': overall_load_factor,
        'message': f"Overall fleet load factor is {overall_load_factor:.2f}%."
    }
    
    # Route efficiency insights
    best_load_factor_route = summary_df.loc[summary_df['load_factor'].idxmax()]
    worst_load_factor_route = summary_df.loc[summary_df['load_factor'].idxmin()]
    
    insights['route_efficiency'] = {
        'best_route': best_load_factor_route['route'],
        'best_load_factor': best_load_factor_route['load_factor'],
        'worst_route': worst_load_factor_route['route'],
        'worst_load_factor': worst_load_factor_route['load_factor'],
        'message': f"The most efficient route is {best_load_factor_route['route']} with a load factor of {best_load_factor_route['load_factor']:.2f}%. The least efficient route is {worst_load_factor_route['route']} with a load factor of {worst_load_factor_route['load_factor']:.2f}%."
    }
    
    # Financial performance insights
    best_profit_route = summary_df.loc[summary_df['profit_per_km'].idxmax()]
    
    insights['financial_performance'] = {
        'best_profit_route': best_profit_route['route'],
        'best_profit_per_km': best_profit_route['profit_per_km'],
        'message': f"The most profitable route per kilometer is {best_profit_route['route']} with {best_profit_route['profit_per_km']:.2f} RWF/km."
    }
    
    # RPKM vs CPKM insights
    profitable_routes = summary_df[summary_df['rpkm'] > summary_df['cpkm']]
    unprofitable_routes = summary_df[summary_df['rpkm'] <= summary_df['cpkm']]
    
    insights['rpkm_cpkm'] = {
        'profitable_routes': profitable_routes['route'].tolist(),
        'unprofitable_routes': unprofitable_routes['route'].tolist(),
        'profitable_count': len(profitable_routes),
        'unprofitable_count': len(unprofitable_routes),
        'message': f"{len(profitable_routes)} routes are profitable (RPKM > CPKM) and {len(unprofitable_routes)} routes are unprofitable."
    }
    
    # Bus utilization insights
    avg_bus_utilization = summary_df['bus_utilization_rate'].mean()
    
    insights['bus_utilization'] = {
        'avg_utilization': avg_bus_utilization,
        'message': f"Average bus utilization rate is {avg_bus_utilization:.2f}%."
    }
    
    # Time-based insights - for hourly patterns
    hourly_load_factors = df.groupby('hour')['load_factor'].mean()
    peak_hour = hourly_load_factors.idxmax()
    off_peak_hour = hourly_load_factors.idxmin()
    
    insights['time_patterns'] = {
        'peak_hour': peak_hour,
        'peak_load_factor': hourly_load_factors[peak_hour],
        'off_peak_hour': off_peak_hour,
        'off_peak_load_factor': hourly_load_factors[off_peak_hour],
        'message': f"Peak hour is {peak_hour}:00 with an average load factor of {hourly_load_factors[peak_hour]:.2f}%. Off-peak hour is {off_peak_hour}:00 with an average load factor of {hourly_load_factors[off_peak_hour]:.2f}%."
    }
    
    return insights

def get_optimization_recommendations(insights):
    """
    Generate optimization recommendations based on insights.
    
    Parameters:
    -----------
    insights : dict
        Dictionary containing insights for each metric
        
    Returns:
    --------
    list
        List of recommendation strings
    """
    recommendations = []
    
    # Capacity optimization recommendations
    if insights['capacity_utilization']['overall_load_factor'] < 50:
        recommendations.append("Overall load factor is below 50%. Consider reducing fleet size or optimizing schedules.")
    elif insights['capacity_utilization']['overall_load_factor'] > 85:
        recommendations.append("Overall load factor is above 85%. Consider increasing capacity on high-demand routes.")
    
    # Route optimization
    if len(insights['rpkm_cpkm']['unprofitable_routes']) > 0:
        unprofitable_routes = ", ".join(insights['rpkm_cpkm']['unprofitable_routes'])
        recommendations.append(f"Routes with negative profit margins ({unprofitable_routes}) should be evaluated for pricing adjustments or service reduction.")
    
    # Time-based optimization
    peak_hour = insights['time_patterns']['peak_hour']
    off_peak_hour = insights['time_patterns']['off_peak_hour']
    recommendations.append(f"Consider increasing capacity at peak hour ({peak_hour}:00) and reducing service during off-peak hours (e.g., {off_peak_hour}:00) to optimize resource allocation.")
    
    # Bus utilization recommendation
    if insights['bus_utilization']['avg_utilization'] < 70:
        recommendations.append("Bus utilization is below optimal. Consider reducing fleet size or implementing better scheduling algorithms.")
    
    return recommendations