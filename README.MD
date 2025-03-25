# TripBook Fleet Management System - Getting Started Guide

## Overview

TripBook is an advanced fleet management system that provides comprehensive analytics, demand forecasting, and bus allocation optimization for transport routes in Rwanda, focusing on routes between Kigali, Musanze, and Gisenyi.

## Quick Start Guide

Follow these steps to set up and run the TripBook Fleet Management system:

### Step 1: Clone or Download the Repository

```bash
git clone git@github.com:kevinbivegete/trip-book.git
cd tripbook

```
If you want to clone only current version
```bash
git clone --branch Version3 --single-branch git@github.com:kevinbivegete/trip-book.git
cd tripbook
```
### Step 2: Create and Activate Virtual Environment

```bash
# Create a virtual environment
python -m venv trip-env

# Activate the virtual environment
# On Windows:
source trip-env/Scripts/activate
# On macOS/Linux:
source trip-env/bin/activate
```

You should see `(trip-env)` appear at the beginning of your command prompt, indicating the virtual environment is active.

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

This may take a few minutes as it installs all required packages including dash, plotly, pandas, numpy, prophet, and statsmodels.

### Step 4: Run the Complete System

Execute the following commands in order:

```bash
# Generate synthetic data
python passenger_data_generation.py

# Run analysis and calculate metrics
python passenger_analysis_forecast.py

# Launch the dashboard
python tripbook_dashboard.py
```

Access the dashboard at http://localhost:8050 in your web browser.

### Step 5: Deactivate Virtual Environment When Finished

When you're done using TripBook, you can deactivate the virtual environment:

```bash
deactivate
```

## Features

- **Transport Metrics:** Analysis using industry-standard KPIs like ASK, RPK, Load Factor, RPKM, and CPKM
- **Passenger Analytics:** Visualization of passenger trends by hour, day, month, and year
- **Demand Forecasting:** Advanced prediction of passenger demand using Prophet and Exponential Smoothing
- **Bus Allocation Optimization:** AI-powered allocation strategies to maximize profits or capacity utilization
- **Financial Performance:** Comprehensive financial analysis and profitability tracking

## Dashboard Tabs

### 1. Transport Metrics Tab

This tab provides visualizations and insights for key transport industry metrics:

- **Available Seat Kilometers (ASK):** Measures total transport capacity
- **Revenue Passenger Kilometers (RPK):** Tracks actual passenger usage
- **Load Factor (%):** Shows capacity utilization (RPK/ASK × 100%)
- **Revenue per Kilometer (RPKM):** Financial efficiency metric
- **Cost per Kilometer (CPKM):** Operational cost efficiency

### 2. Passenger Overview Tab

Analyze passenger trends and patterns across different time scales:
- View total passengers by route
- Explore hourly, weekly, monthly, and yearly patterns
- Review insights about peak times and growth trends

### 3. Demand Forecasting Tab

Generate passenger demand forecasts using time series analysis:
- Select a specific route
- Choose a forecasting method (Prophet or Exponential Smoothing)
- Set the forecast horizon in days (30-365 days)
- View the forecast chart, components, and insights

### 4. Bus Allocation Tab

Optimize bus allocation based on forecasted demand:
- Select a route for optimization
- Choose optimization target (profit, capacity utilization, or unserved demand)
- View optimized allocation, financial impact, and recommendations

### 5. Financial Performance Tab

Analyze financial metrics and profitability by route:
- View revenue, profit margins, and financial trends
- Analyze the relationship between capacity utilization and profit
- Review financial insights and optimization opportunities

## Troubleshooting

- **Virtual environment issues:** Make sure you've activated the environment properly before installing dependencies
- **Prophet installation errors:** If Prophet fails to install, try installing pystan first: `pip install pystan==2.19.1.1`
- **Dashboard not loading:** Ensure all dependencies are installed and the data file exists
- **Analysis error:** Ensure the passenger_data_generation.py script ran successfully
- **Missing visualizations:** Check that the analysis_results folder was created by the analysis script

## Project Structure

```
tripbook/
│
├── passenger_data_generation.py   # Data generation script
├── metrics_calculation.py         # Transport metrics calculator
├── passenger_analysis_forecast.py # Analysis and forecasting script
├── tripbook_dashboard.py          # Interactive dashboard
├── requirements.txt               # Python dependencies
├── assets/                        # Dashboard assets
│   └── evolution_logo.png         # Evolution Inc. logo
```

## Credits

Developed by Evolution Inc. © 2025

Credits goes to Kevin Rodrigue Bivegete, Ngoga Alexis, Karera Chryssie, Shami Sion, Rugero Olsen