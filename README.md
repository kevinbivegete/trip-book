# TripBook - Fleet Management and Passenger Analytics System

## Overview

TripBook is a comprehensive solution developed by **Evolution Inc.** to optimize bus allocation, forecast passenger demand, and visualize transportation analytics. The system is designed to address key challenges in the transportation industry through data-driven decision-making.

### Key Features

1. **Passenger Data Analytics**

   - Historical trend analysis
   - Identification of peak travel times and periods
   - Passenger volume tracking across routes

2. **Demand Forecasting**

   - Advanced time series forecasting
   - Seasonal pattern detection
   - Special event impact analysis

3. **Resource Allocation**

   - Optimized bus fleet allocation
   - Route-specific bus type recommendations
   - Maximization of profit or capacity utilization

4. **Financial Performance Tracking**

   - Revenue and cost analysis
   - Profit margin calculation
   - Route profitability comparison

### Routes Covered

The system currently analyzes data for the following routes:

- Kigali-Musanze
- Musanze-Kigali
- Kigali-Gisenyi
- Gisenyi-Kigali
- Musanze-Gisenyi
- Gisenyi-Musanze

## Project Components

1. **Data Generation**

   - Synthetic passenger data generation (15 years of data)
   - Incorporates seasonal patterns, weekly trends, and special events

2. **Data Analysis & Forecasting**

   - Time series decomposition
   - Multiple forecasting models (Prophet, SARIMA)
   - Pattern identification and anomaly detection

3. **Dashboard**

   - Interactive Dash-based web application
   - Comprehensive visualizations
   - Real-time optimization tools

4. **Bus Allocation Algorithm**

   - Optimized resource allocation
   - Multiple optimization targets (profit, capacity, service level)
   - Detailed operational recommendations

## Installation & Setup

### Prerequisites

- Python 3.8 or higher
- pip package manager

### Required Packages

```bash
pip install -r requirements.txt
```

### Running the Application

1. Clone the repository:

```bash
git clone https://github.com/kevinbivegete/trip-book.git
cd tripbook
```

2. Run the following scripts:

```bash
python passenger_data_generation.py
python passenger_analysis_forecast.py
```

This will:

- Generate synthetic passenger data (if not already present)
- Analyze the data and create forecasts
- Launch the interactive dashboard in your default web browser

## Using the Dashboard

The dashboard consists of four main tabs:

1. **Passenger Overview**

   - Filter by routes and date range
   - View passenger trends by hour, day, month, and year
   - Identify key insights and patterns

2. **Demand Forecasting**

   - Select a route and forecasting method
   - Choose the forecast horizon
   - View detailed forecast components and insights

3. **Bus Allocation**

   - Optimize bus allocation based on forecasted demand
   - Choose optimization target (profit, capacity utilization, service level)
   - Get specific bus fleet recommendations

4. **Financial Performance**

   - Analyze revenue, costs, and profits by route
   - Identify the most profitable routes
   - Understand the relationship between capacity utilization and profit

## Future Development

- Integration with a ticket booking mobile app
- Real-time data processing capability
- Machine learning for more accurate demand prediction
- Multi-city expansion

## License

This project is developed by **Evolution Inc.** and is proprietary. Unauthorized copying or distribution of this project, via any medium, is strictly prohibited.

## Contact

For more information, please contact the project team at evolutioninc2025\@gmail.com.

