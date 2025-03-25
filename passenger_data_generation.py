import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import random

def generate_passenger_data(years=15, seed=42):
    """
    Generate synthetic passenger data for routes between Kigali, Musanze, and Gisenyi
    for the specified number of years.
    
    Parameters:
    -----------
    years : int
        Number of years of data to generate
    seed : int
        Random seed for reproducibility
    
    Returns:
    --------
    pandas.DataFrame
        DataFrame containing synthetic passenger data
    """
    np.random.seed(seed)
    random.seed(seed)
    
    # Define routes - removed local Kigali routes as requested
    routes = [
        "Kigali-Musanze", "Musanze-Kigali",
        "Kigali-Gisenyi", "Gisenyi-Kigali",
        "Musanze-Gisenyi", "Gisenyi-Musanze"
    ]
    
    # Define base demand for each route
    base_demand = {
        "Kigali-Musanze": 120, "Musanze-Kigali": 110,
        "Kigali-Gisenyi": 90, "Gisenyi-Kigali": 85,
        "Musanze-Gisenyi": 60, "Gisenyi-Musanze": 55
    }
    
    # Define seasonal patterns
    # Monthly seasonality (1.0 = average demand, higher = more demand)
    monthly_seasonality = {
        1: 0.8,   # January
        2: 0.85,  # February
        3: 0.9,   # March
        4: 1.1,   # April (Easter)
        5: 1.0,   # May
        6: 1.2,   # June (school holidays)
        7: 1.3,   # July (school holidays)
        8: 1.2,   # August (school holidays end)
        9: 1.0,   # September
        10: 0.95, # October
        11: 1.0,  # November
        12: 1.4   # December (holidays)
    }
    
    # Day of week patterns (weekday effect)
    dow_effect = {
        0: 1.2,  # Monday
        1: 0.9,  # Tuesday
        2: 0.85, # Wednesday
        3: 0.9,  # Thursday
        4: 1.3,  # Friday
        5: 1.5,  # Saturday
        6: 1.4   # Sunday
    }
    
    # Hour of day patterns
    hourly_patterns = {
        # Morning peak for outbound from Kigali, afternoon peak for inbound to Kigali
        "Kigali-Musanze": {h: 1.8 if 5 <= h <= 9 else (1.5 if 14 <= h <= 18 else 0.5) for h in range(24)},
        "Musanze-Kigali": {h: 1.8 if 5 <= h <= 9 else (1.5 if 14 <= h <= 18 else 0.5) for h in range(24)},
        "Kigali-Gisenyi": {h: 1.8 if 6 <= h <= 10 else (1.5 if 13 <= h <= 17 else 0.5) for h in range(24)},
        "Gisenyi-Kigali": {h: 1.8 if 6 <= h <= 10 else (1.5 if 13 <= h <= 17 else 0.5) for h in range(24)},
        "Musanze-Gisenyi": {h: 1.5 if 7 <= h <= 11 else (1.2 if 15 <= h <= 19 else 0.6) for h in range(24)},
        "Gisenyi-Musanze": {h: 1.5 if 7 <= h <= 11 else (1.2 if 15 <= h <= 19 else 0.6) for h in range(24)}
    }
    
    # Define yearly growth rates for each route
    yearly_growth = {
        "Kigali-Musanze": 0.05, "Musanze-Kigali": 0.05,
        "Kigali-Gisenyi": 0.06, "Gisenyi-Kigali": 0.06,
        "Musanze-Gisenyi": 0.04, "Gisenyi-Musanze": 0.04
    }
    
    # Start date (15 years ago from today)
    start_date = datetime.now() - timedelta(days=365 * years)
    start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
    
    # Generate data
    data = []
    
    # Special events that affect passenger numbers
    special_events = generate_special_events(start_date, years)
    
    # Create each day's data
    current_date = start_date
    end_date = start_date + timedelta(days=365 * years)
    
    while current_date < end_date:
        year = current_date.year
        month = current_date.month
        day = current_date.day
        dow = current_date.weekday()  # 0 = Monday, 6 = Sunday
        
        # Check for special events
        event_multiplier = 1.0
        event_name = None
        for event_date, (event_mult, event_nm) in special_events.items():
            if (current_date.month == event_date[0] and 
                current_date.day == event_date[1] and 
                (event_date[2] == -1 or current_date.year == event_date[2])):
                event_multiplier = event_mult
                event_name = event_nm
                break
        
        # Generate hourly data for each route
        for hour in range(24):
            for route in routes:
                # Calculate years since start for growth calculation
                years_since_start = (current_date - start_date).days / 365
                
                # Apply growth factor
                growth_factor = (1 + yearly_growth[route]) ** years_since_start
                
                # Calculate base passengers for this timestamp and route
                base_passengers = base_demand[route] * growth_factor
                
                # Apply seasonal factors
                month_factor = monthly_seasonality[month]
                dow_factor = dow_effect[dow]
                hour_factor = hourly_patterns[route][hour]
                
                # Apply random noise (normal distribution around 1.0)
                noise = np.random.normal(1.0, 0.15)
                
                # Calculate final passenger count
                passengers = int(base_passengers * month_factor * dow_factor * 
                                hour_factor * noise * event_multiplier)
                
                # Ensure at least 0 passengers
                passengers = max(0, passengers)
                
                # Create data entry
                entry = {
                    'datetime': current_date + timedelta(hours=hour),
                    'route': route,
                    'passengers': passengers,
                    'special_event': event_name
                }
                
                data.append(entry)
        
        # Move to next day
        current_date += timedelta(days=1)
    
    # Convert to DataFrame
    df = pd.DataFrame(data)
    
    # Extract time components
    df['year'] = df['datetime'].dt.year
    df['month'] = df['datetime'].dt.month
    df['day'] = df['datetime'].dt.day
    df['hour'] = df['datetime'].dt.hour
    df['day_of_week'] = df['datetime'].dt.dayofweek
    df['is_weekend'] = df['day_of_week'].apply(lambda x: 1 if x >= 5 else 0)
    df['month_name'] = df['datetime'].dt.strftime('%B')
    df['day_name'] = df['datetime'].dt.strftime('%A')
    
    # Extract route components
    df[['origin', 'destination']] = df['route'].str.split('-', expand=True)
    
    return df

def generate_special_events(start_date, years):
    """
    Generate special events that affect passenger demand
    
    Returns a dictionary of tuples (month, day, year) -> (multiplier, event_name)
    If year is -1, the event occurs every year on that date
    """
    events = {}
    
    # Recurring annual events
    events[(1, 1, -1)] = (0.7, "New Year's Day")
    events[(2, 14, -1)] = (1.2, "Valentine's Day")
    events[(5, 1, -1)] = (1.3, "Labor Day")
    events[(7, 4, -1)] = (1.4, "Rwanda Independence Day")
    events[(7, 1, -1)] = (1.4, "Rwanda Day")
    events[(12, 25, -1)] = (0.6, "Christmas Day")
    events[(12, 31, -1)] = (1.5, "New Year's Eve")
    
    # Generate some random one-time events
    random.seed(42)  # For reproducibility
    current_year = start_date.year
    
    for _ in range(years * 3):  # Create about 3 events per year
        event_year = random.randint(current_year, current_year + years - 1)
        event_month = random.randint(1, 12)
        event_day = random.randint(1, 28)  # Avoid month boundary issues
        
        # Random multiplier between 0.5 and 2.0
        multiplier = random.uniform(0.5, 2.0)
        
        event_types = [
            "Festival", "Conference", "Sports Event", 
            "Political Rally", "Concert", "Strike", 
            "Weather Disruption", "Road Construction"
        ]
        event_name = f"{random.choice(event_types)} {event_year}"
        
        events[(event_month, event_day, event_year)] = (multiplier, event_name)
    
    return events

def add_bus_capacity_and_financial_data(df):
    """
    Add bus capacity, revenue, and cost data to the passenger dataframe
    """
    # Define bus types and their capacities
    bus_types = {
        "Mini": 16,
        "Medium": 30,
        "Large": 50
    }
    
    # Define ticket prices for each route (in Rwandan Francs)
    ticket_prices = {
        "Kigali-Musanze": 2500, "Musanze-Kigali": 2500,
        "Kigali-Gisenyi": 3500, "Gisenyi-Kigali": 3500,
        "Musanze-Gisenyi": 1800, "Gisenyi-Musanze": 1800
    }
    
    # Define operating costs per kilometer
    operating_costs_per_km = {
        "Mini": 150,
        "Medium": 250,
        "Large": 400
    }
    
    # Define route distances (in kilometers)
    route_distances = {
        "Kigali-Musanze": 80, "Musanze-Kigali": 80,
        "Kigali-Gisenyi": 155, "Gisenyi-Kigali": 155,
        "Musanze-Gisenyi": 75, "Gisenyi-Musanze": 75
    }
    
    # Add bus allocation data
    df['allocated_bus_type'] = ''
    df['bus_capacity'] = 0
    df['num_buses_allocated'] = 0
    df['ticket_price'] = df['route'].map(ticket_prices)
    df['route_distance_km'] = df['route'].map(route_distances)
    
    # Calculate revenue
    df['revenue'] = df['passengers'] * df['ticket_price']
    
    # Allocate buses (simple allocation based on passenger count)
    for idx, row in df.iterrows():
        if row['passengers'] <= 16:
            bus_type = "Mini"
            num_buses = max(1, int(np.ceil(row['passengers'] / 16)))
        elif row['passengers'] <= 60:
            bus_type = "Medium"
            num_buses = max(1, int(np.ceil(row['passengers'] / 30)))
        else:
            bus_type = "Large"
            num_buses = max(1, int(np.ceil(row['passengers'] / 50)))
        
        df.at[idx, 'allocated_bus_type'] = bus_type
        df.at[idx, 'bus_capacity'] = bus_types[bus_type]
        df.at[idx, 'num_buses_allocated'] = num_buses
    
    # Calculate operating costs
    df['operating_cost'] = df.apply(
        lambda row: row['num_buses_allocated'] * 
                   operating_costs_per_km[row['allocated_bus_type']] * 
                   row['route_distance_km'],
        axis=1
    )
    
    # Calculate profit
    df['profit'] = df['revenue'] - df['operating_cost']
    
    # Calculate capacity utilization
    df['capacity_utilization'] = df.apply(
        lambda row: min(100, (row['passengers'] / 
                            (row['num_buses_allocated'] * row['bus_capacity'])) * 100),
        axis=1
    )
    
    return df

# Generate the data
df = generate_passenger_data(years=15)
df = add_bus_capacity_and_financial_data(df)

# Save to CSV
df.to_csv('tripbook_passenger_data.csv', index=False)

print(f"Generated {len(df)} passenger data records spanning {df['year'].min()} to {df['year'].max()}")
print(f"Data saved to 'tripbook_passenger_data.csv'")

# Display a sample
print("\nSample of generated data:")
print(df.sample(5))