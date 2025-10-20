import pandas as pd

# Read CSV file 
csv_file = "/Users/erinhoxie/Library/Mobile Documents/com~apple~CloudDocs/Documents/Data Projects/sydney-water/weather.csv"
weather = pd.read_csv(csv_file)

# Print basic info about the DataFrame
print(f"Dataset shape: {weather.shape}")
print(f"Columns: {list(weather.columns)}")
print("\n" + "="*50)

# Print data types for each column
print("Data types for each column:")
print("-" * 30)
for column in weather.columns:
    dtype = weather[column].dtype
    print(f"{column}: {dtype}")

# Alternative: Print all data types at once
print("\n" + "="*50)
print("All data types (alternative view):")
print(weather.dtypes)

print(weather.head())
