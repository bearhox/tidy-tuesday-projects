import pandas as pd
import folium
from folium import plugins
import numpy as np
import os

def load_and_process_data():
    """Load and merge the frog data files"""
    try:
        # Load the CSV files
        frog_id_data = pd.read_csv('https://raw.githubusercontent.com/rfordatascience/tidytuesday/main/data/2025/2025-09-02/frogID_data.csv')
        frog_names = pd.read_csv('https://raw.githubusercontent.com/rfordatascience/tidytuesday/main/data/2025/2025-09-02/frog_names.csv')
        
        print(f"Loaded {len(frog_id_data)} occurrence records")
        print(f"Loaded {len(frog_names)} species names")
        
        # Merge the datasets on scientificName
        merged_data = pd.merge(frog_id_data, frog_names, on='scientificName', how='left')
        
        print(f"Merged dataset contains {len(merged_data)} records")
        
        # Remove records with missing coordinates
        merged_data = merged_data.dropna(subset=['decimalLatitude', 'decimalLongitude'])
        
        print(f"After removing records with missing coordinates: {len(merged_data)} records")
        
        return merged_data
        
    except FileNotFoundError as e:
        print(f"Error: Could not find CSV file - {e}")
        print("Please ensure both 'frogID_data.csv' and 'frog_names.csv' are in the current directory")
        return None
    except Exception as e:
        print(f"Error loading data: {e}")
        return None



def create_frog_map(data):
    """Create an interactive map with frog species locations"""
    
    # Calculate map center based on data bounds
    center_lat = data['decimalLatitude'].mean()
    center_lon = data['decimalLongitude'].mean()
    
    # Create base map
    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=6,
        tiles='OpenStreetMap'
    )
    
    # Add different tile layers with proper attributions
    folium.TileLayer(
        tiles='https://stamen-tiles-{s}.a.ssl.fastly.net/terrain/{z}/{x}/{y}{r}.png',
        attr='Map tiles by <a href="http://stamen.com">Stamen Design</a>, <a href="http://creativecommons.org/licenses/by/3.0">CC BY 3.0</a> &mdash; Map data &copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
        name='Stamen Terrain',
        overlay=False,
        control=True
    ).add_to(m)
    
    folium.TileLayer(
        tiles='CartoDB positron',
        name='CartoDB Positron',
        overlay=False,
        control=True
    ).add_to(m)

    
    # Create color palette for different species
    unique_species = data['scientificName'].unique()
    colors = ['red', 'blue', 'green', 'purple', 'orange', 'darkred', 
              'lightred', 'beige', 'darkblue', 'darkgreen', 'cadetblue', 
              'darkpurple', 'white', 'pink', 'lightblue', 'lightgreen', 
              'gray', 'black', 'lightgray']
    
    # Create a color mapping for species
    species_colors = {}
    for i, species in enumerate(unique_species):
        species_colors[species] = colors[i % len(colors)]
    
    # Add markers for each frog occurrence
    marker_cluster = plugins.MarkerCluster().add_to(m)
    
    for idx, row in data.iterrows():
        # Create popup text with frog information
        popup_text = f"""
        <b>Scientific Name:</b> {row['scientificName']}<br>
        <b>Common Name:</b> {row.get('commonName', 'Unknown')}<br>
        <b>Subfamily:</b> {row.get('subfamily', 'Unknown')}<br>
        <b>Date:</b> {row.get('eventDate', 'Unknown')}<br>
        <b>Time:</b> {row.get('eventTime', 'Unknown')}<br>
        <b>State/Province:</b> {row.get('stateProvince', 'Unknown')}<br>
        <b>Coordinates:</b> {row['decimalLatitude']:.4f}, {row['decimalLongitude']:.4f}
        """
        
        folium.Marker(
            location=[row['decimalLatitude'], row['decimalLongitude']],
            popup=folium.Popup(popup_text, max_width=300),
            tooltip=f"{row['scientificName']} ({row.get('commonName', 'Unknown')})",
            icon=folium.Icon(
                color=species_colors[row['scientificName']],
                icon='info-sign'
            )
        ).add_to(marker_cluster)
    
    # Add layer control
    folium.LayerControl().add_to(m)
    
    # Add a legend for species colors (simplified version)
    legend_html = '''
    <div style="position: fixed; 
                bottom: 50px; left: 50px; width: 200px; height: 90px; 
                background-color: white; border:2px solid grey; z-index:9999; 
                font-size:14px; padding: 10px">
    <p><b>Frog Species Map</b></p>
    <p>Click on markers for details</p>
    <p>Total species: {}</p>
    <p>Total records: {}</p>
    </div>
    '''.format(len(unique_species), len(data))
    
    m.get_root().html.add_child(folium.Element(legend_html))
    
    return m

def generate_species_summary(data):
    """Generate a summary of species data"""
    print("\n" + "="*50)
    print("FROG SPECIES SUMMARY")
    print("="*50)
    
    print(f"Total number of records: {len(data)}")
    print(f"Total number of unique species: {data['scientificName'].nunique()}")
    print(f"Total number of subfamilies: {data['subfamily'].nunique()}")
    
    # Most common species
    species_counts = data['scientificName'].value_counts().head(10)
    print(f"\nTop 10 most recorded species:")
    for species, count in species_counts.items():
        common_name = data[data['scientificName'] == species]['commonName'].iloc[0]
        print(f"  {species} ({common_name}): {count} records")
    
    # Geographic distribution
    if 'stateProvince' in data.columns:
        state_counts = data['stateProvince'].value_counts().head(10)
        print(f"\nTop 10 states/provinces by number of records:")
        for state, count in state_counts.items():
            print(f"  {state}: {count} records")
    
    # Date range
    if 'eventDate' in data.columns:
        data['eventDate'] = pd.to_datetime(data['eventDate'], errors='coerce')
        date_range = f"{data['eventDate'].min().strftime('%Y-%m-%d')} to {data['eventDate'].max().strftime('%Y-%m-%d')}"
        print(f"\nDate range: {date_range}")

def main():
    """Main function to run the frog mapping script"""
    print("Frog Species Location Mapper")
    print("="*30)
    
    # Load and process data
    data = load_and_process_data()
    
    if data is None:
        return
    
    # Generate summary
    generate_species_summary(data)
    
    # Create map
    print(f"\nCreating interactive map...")
    frog_map = create_frog_map(data)
    
    # Save map
    map_filename = 'frog_species_map.html'
    frog_map.save(map_filename)
    
    print(f"\nMap saved as '{map_filename}'")
    print(f"Open this file in your web browser to view the interactive map!")
    
    # Optional: Create a heatmap version
    create_heatmap = input("\nWould you like to create a density heatmap as well? (y/n): ")
    
    if create_heatmap.lower() == 'y':
        print("Creating density heatmap...")
        
        # Create heatmap
        heatmap = folium.Map(
            location=[data['decimalLatitude'].mean(), data['decimalLongitude'].mean()],
            zoom_start=6
        )
        
        # Prepare data for heatmap
        heat_data = [[row['decimalLatitude'], row['decimalLongitude']] 
                    for idx, row in data.iterrows()]
        
        # Add heatmap layer
        plugins.HeatMap(heat_data).add_to(heatmap)
        
        # Save heatmap
        heatmap_filename = 'frog_species_heatmap.html'
        heatmap.save(heatmap_filename)
        print(f"Heatmap saved as '{heatmap_filename}'")

if __name__ == "__main__":
    main()
