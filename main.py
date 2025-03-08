import subprocess
import os
import time
import webbrowser
import sys
import signal
import threading
import atexit

def print_header(message):
    """Print a formatted header message"""
    width = 70
    print("\n" + "=" * width)
    print(message.center(width))
    print("=" * width + "\n")

def run_data_generation():
    """Run the data generation script"""
    print_header("STEP 1: GENERATING PASSENGER DATA")
    try:
        if os.path.exists('tripbook_passenger_data.csv'):
            choice = input("Passenger data file already exists. Regenerate? (y/n): ").lower()
            if choice != 'y':
                print("Skipping data generation.")
                return
            
        subprocess.run(['python', 'passenger_data_generation.py'], check=True)
        print("Data generation completed successfully.")
    except subprocess.CalledProcessError:
        print("Error during data generation. Please check the error message above.")
        sys.exit(1)

def run_data_analysis():
    """Run the data analysis and forecasting script"""
    print_header("STEP 2: ANALYZING PASSENGER DATA AND GENERATING FORECASTS")
    try:
        # Create analysis_results directory if it doesn't exist
        os.makedirs('analysis_results', exist_ok=True)
        
        subprocess.run(['python', 'passenger_analysis_forecast.py'], check=True)
        print("Data analysis and forecasting completed successfully.")
    except subprocess.CalledProcessError:
        print("Error during data analysis. Please check the error message above.")
        sys.exit(1)

def run_dashboard():
    """Run the Dash dashboard application"""
    print_header("STEP 3: LAUNCHING INTERACTIVE DASHBOARD")
    dashboard_process = None
    
    try:
        # Start dashboard in a subprocess
        dashboard_process = subprocess.Popen(['python', 'tripbook_dashboard.py'])
        
        # Wait a moment for the server to start
        time.sleep(3)
        
        # Open web browser
        dashboard_url = "http://127.0.0.1:8050/"
        print(f"Opening dashboard in your web browser at {dashboard_url}")
        webbrowser.open(dashboard_url)
        
        # Keep the dashboard running until Ctrl+C
        print("\nDashboard is running. Press Ctrl+C to stop the application...\n")
        
        # Register clean-up function
        def cleanup():
            if dashboard_process:
                dashboard_process.terminate()
                print("\nDashboard stopped.")
        
        atexit.register(cleanup)
        
        # Wait for the dashboard process to end
        dashboard_process.wait()
    
    except KeyboardInterrupt:
        print("\nShutting down the dashboard...")
        if dashboard_process:
            dashboard_process.terminate()
    except Exception as e:
        print(f"Error running dashboard: {e}")
        if dashboard_process:
            dashboard_process.terminate()
        sys.exit(1)

def main():
    """Main function to run the entire workflow"""
    print_header("TRIPBOOK ANALYTICS AND FLEET MANAGEMENT SYSTEM")
    print("This script will perform the following steps:")
    print("1. Generate synthetic passenger data for intercity routes between Kigali, Musanze, and Gisenyi")
    print("2. Analyze the data and generate demand forecasts")
    print("3. Launch an interactive dashboard for visualization and optimization")
    
    try:
        run_data_generation()
        run_data_analysis()
        run_dashboard()
    except KeyboardInterrupt:
        print("\nProcess interrupted by user. Exiting...")

if __name__ == "__main__":
    main()