import pandas as pd
import folium
from folium import plugins
import numpy as np
from collections import Counter
import math
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

def load_and_process_data():
    """Load and merge the frog data files with enhanced processing"""
    try:
        # Load the CSV files
        frog_id_data = pd.read_csv('https://raw.githubusercontent.com/rfordatascience/tidytuesday/main/data/2025/2025-09-02/frogID_data.csv')
        frog_names = pd.read_csv('https://raw.githubusercontent.com/rfordatascience/tidytuesday/main/data/2025/2025-09-02/frog_names.csv')
        
        print(f"Loaded {len(frog_id_data)} occurrence records")
        print(f"Loaded {len(frog_names)} species names")
        
        # Merge the datasets on scientificName
        merged_data = pd.merge(frog_id_data, frog_names, on='scientificName', how='left')
        
        # Remove records with missing coordinates
        merged_data = merged_data.dropna(subset=['decimalLatitude', 'decimalLongitude'])
        
        # Process dates
        merged_data['eventDate'] = pd.to_datetime(merged_data['eventDate'], errors='coerce')
        merged_data['month'] = merged_data['eventDate'].dt.month
        merged_data['season'] = merged_data['month'].apply(get_season)
        
        print(f"Processed dataset contains {len(merged_data)} records")
        
        return merged_data
        
    except FileNotFoundError as e:
        print(f"Error: Could not find CSV file - {e}")
        return None
    except Exception as e:
        print(f"Error loading data: {e}")
        return None

def get_season(month):
    """Convert month to season (Southern Hemisphere)"""
    if pd.isna(month):
        return 'Unknown'
    elif month in [12, 1, 2]:
        return 'Summer'
    elif month in [3, 4, 5]:
        return 'Autumn'
    elif month in [6, 7, 8]:
        return 'Winter'
    else:
        return 'Spring'

def calculate_geographic_range(species_data):
    """Calculate geographic range metrics for a species"""
    if len(species_data) == 0:
        return {'range_area': 0, 'lat_range': 0, 'lon_range': 0, 'num_locations': 0}
    
    lats = species_data['decimalLatitude']
    lons = species_data['decimalLongitude']
    
    # Calculate bounding box
    lat_range = lats.max() - lats.min()
    lon_range = lons.max() - lons.min()
    
    # Approximate area (very rough estimate)
    range_area = lat_range * lon_range * 111 * 111  # Convert degrees to km²
    
    return {
        'range_area': range_area,
        'lat_range': lat_range,
        'lon_range': lon_range,
        'num_locations': len(species_data),
        'num_states': species_data['stateProvince'].nunique() if 'stateProvince' in species_data else 0
    }

def analyze_endemism(data):
    """Analyze species endemism by state/province"""
    print("\n" + "="*60)
    print("ENDEMISM ANALYSIS")
    print("="*60)
    
    # Group by species and analyze their geographic distribution
    species_distribution = {}
    endemic_species = {}
    
    for species in data['scientificName'].unique():
        species_data = data[data['scientificName'] == species]
        states = species_data['stateProvince'].unique()
        states = [s for s in states if pd.notna(s)]
        
        species_distribution[species] = {
            'states': states,
            'num_states': len(states),
            'num_records': len(species_data),
            'common_name': species_data['commonName'].iloc[0] if pd.notna(species_data['commonName'].iloc[0]) else 'Unknown'
        }
        
        # Consider endemic if found in only one state and has multiple records
        if len(states) == 1 and len(species_data) >= 3:
            state = states[0]
            if state not in endemic_species:
                endemic_species[state] = []
            endemic_species[state].append({
                'species': species,
                'common_name': species_distribution[species]['common_name'],
                'records': len(species_data)
            })
    
    # Print endemic species by state
    print("Potentially Endemic Species (found in only one state with ≥3 records):")
    for state, species_list in endemic_species.items():
        print(f"\n{state} ({len(species_list)} potentially endemic species):")
        for sp in sorted(species_list, key=lambda x: x['records'], reverse=True):
            print(f"  • {sp['species']} ({sp['common_name']}) - {sp['records']} records")
    
    return endemic_species, species_distribution

def analyze_calling_seasons(data):
    """Analyze calling seasons for different species"""
    print("\n" + "="*60)
    print("CALLING SEASON ANALYSIS")
    print("="*60)
    
    # Filter out records without date information
    seasonal_data = data.dropna(subset=['month'])
    
    if len(seasonal_data) == 0:
        print("No seasonal data available")
        return None
    
    # Count recordings by species and season
    season_analysis = seasonal_data.groupby(['scientificName', 'season']).size().unstack(fill_value=0)
    
    # Calculate seasonal preferences
    seasonal_preferences = {}
    for species in season_analysis.index:
        species_data = season_analysis.loc[species]
        total_records = species_data.sum()
        
        if total_records >= 5:  # Only analyze species with enough data
            seasonal_preferences[species] = {
                'total_records': total_records,
                'peak_season': species_data.idxmax(),
                'season_percentages': (species_data / total_records * 100).round(1).to_dict(),
                'common_name': data[data['scientificName'] == species]['commonName'].iloc[0]
            }
    
    # Print seasonal patterns
    print("Species with Distinct Calling Seasons (≥5 records):")
    for species, info in sorted(seasonal_preferences.items(), key=lambda x: x[1]['total_records'], reverse=True)[:15]:
        common_name = info['common_name'] if pd.notna(info['common_name']) else 'Unknown'
        print(f"\n{species} ({common_name}) - {info['total_records']} records")
        print(f"  Peak season: {info['peak_season']}")
        for season, pct in info['season_percentages'].items():
            if pct > 0:
                print(f"  {season}: {pct}%")
    
    return seasonal_preferences

def analyze_geographic_ranges(data):
    """Analyze geographic ranges to find widest and rarest species"""
    print("\n" + "="*60)
    print("GEOGRAPHIC RANGE ANALYSIS")
    print("="*60)
    
    range_analysis = {}
    
    for species in data['scientificName'].unique():
        species_data = data[data['scientificName'] == species]
        range_metrics = calculate_geographic_range(species_data)
        
        range_analysis[species] = {
            **range_metrics,
            'common_name': species_data['commonName'].iloc[0] if pd.notna(species_data['commonName'].iloc[0]) else 'Unknown'
        }
    
    # Sort by range area (widest distribution)
    widest_ranges = sorted(range_analysis.items(), key=lambda x: x[1]['range_area'], reverse=True)[:10]
    
    # Sort by number of records (rarest - fewest records)
    rarest_species = sorted(range_analysis.items(), key=lambda x: x[1]['num_locations'])[:10]
    
    print("Species with WIDEST Geographic Ranges:")
    for i, (species, metrics) in enumerate(widest_ranges, 1):
        common_name = metrics['common_name']
        print(f"{i:2d}. {species} ({common_name})")
        print(f"     Range: {metrics['range_area']:,.0f} km² | States: {metrics['num_states']} | Records: {metrics['num_locations']}")
    
    print("\nRAREST Species (fewest records):")
    for i, (species, metrics) in enumerate(rarest_species, 1):
        common_name = metrics['common_name']
        if metrics['num_locations'] <= 5:  # Only show truly rare ones
            print(f"{i:2d}. {species} ({common_name})")
            print(f"     Records: {metrics['num_locations']} | States: {metrics['num_states']}")
    
    return range_analysis

def create_endemism_map(data, endemic_species):
    """Create a map showing potentially endemic species"""
    center_lat = data['decimalLatitude'].mean()
    center_lon = data['decimalLongitude'].mean()
    
    m = folium.Map(location=[center_lat, center_lon], zoom_start=6)
    
    # Color palette for different states
    state_colors = ['red', 'blue', 'green', 'purple', 'orange', 'darkred', 'lightred']
    state_color_map = {}
    
    color_idx = 0
    for state, species_list in endemic_species.items():
        state_color_map[state] = state_colors[color_idx % len(state_colors)]
        color_idx += 1
        
        # Add markers for endemic species in this state
        for species_info in species_list:
            species_data = data[data['scientificName'] == species_info['species']]
            
            for idx, row in species_data.iterrows():
                popup_text = f"""
                <b>POTENTIALLY ENDEMIC SPECIES</b><br>
                <b>State:</b> {state}<br>
                <b>Scientific Name:</b> {species_info['species']}<br>
                <b>Common Name:</b> {species_info['common_name']}<br>
                <b>Total Records in State:</b> {species_info['records']}<br>
                <b>Date:</b> {row.get('eventDate', 'Unknown')}<br>
                """
                
                folium.Marker(
                    location=[row['decimalLatitude'], row['decimalLongitude']],
                    popup=folium.Popup(popup_text, max_width=300),
                    tooltip=f"Endemic: {species_info['species']}",
                    icon=folium.Icon(color=state_color_map[state], icon='star')
                ).add_to(m)
    
    # Add legend
    legend_html = f'''
    <div style="position: fixed; bottom: 50px; left: 50px; width: 300px; height: auto; 
                background-color: white; border:2px solid grey; z-index:9999; 
                font-size:12px; padding: 10px">
    <p><b>Potentially Endemic Frog Species</b></p>
    <p>Species found in only one state (≥3 records)</p>
    '''
    
    for state, color in state_color_map.items():
        species_count = len(endemic_species[state])
        legend_html += f'<p><span style="color:{color}">●</span> {state}: {species_count} species</p>'
    
    legend_html += '</div>'
    m.get_root().html.add_child(folium.Element(legend_html))
    
    return m

def create_seasonal_map(data, seasonal_preferences):
    """Create a map showing seasonal calling patterns"""
    center_lat = data['decimalLatitude'].mean()
    center_lon = data['decimalLongitude'].mean()
    
    m = folium.Map(location=[center_lat, center_lon], zoom_start=6)
    
    # Season colors
    season_colors = {'Summer': 'red', 'Autumn': 'orange', 'Winter': 'blue', 'Spring': 'green'}
    
    # Add markers for species with distinct seasonal patterns
    for species, info in seasonal_preferences.items():
        species_data = data[data['scientificName'] == species]
        peak_season = info['peak_season']
        
        for idx, row in species_data.iterrows():
            if pd.notna(row.get('season')):
                popup_text = f"""
                <b>Scientific Name:</b> {species}<br>
                <b>Common Name:</b> {info['common_name']}<br>
                <b>Peak Calling Season:</b> {peak_season}<br>
                <b>This Record:</b> {row['season']}<br>
                <b>Date:</b> {row.get('eventDate', 'Unknown')}<br>
                <b>Seasonal Distribution:</b><br>
                """
                
                for season, pct in info['season_percentages'].items():
                    if pct > 0:
                        popup_text += f"  {season}: {pct}%<br>"
                
                folium.CircleMarker(
                    location=[row['decimalLatitude'], row['decimalLongitude']],
                    radius=5,
                    popup=folium.Popup(popup_text, max_width=300),
                    tooltip=f"{species} - Peak: {peak_season}",
                    color=season_colors.get(peak_season, 'gray'),
                    fillColor=season_colors.get(peak_season, 'gray'),
                    fillOpacity=0.7
                ).add_to(m)
    
    # Add legend
    legend_html = '''
    <div style="position: fixed; bottom: 50px; left: 50px; width: 250px; height: auto; 
                background-color: white; border:2px solid grey; z-index:9999; 
                font-size:12px; padding: 10px">
    <p><b>Frog Calling Seasons</b></p>
    <p>Markers colored by peak calling season:</p>
    <p><span style="color:red">●</span> Summer (Dec-Feb)</p>
    <p><span style="color:orange">●</span> Autumn (Mar-May)</p>
    <p><span style="color:blue">●</span> Winter (Jun-Aug)</p>
    <p><span style="color:green">●</span> Spring (Sep-Nov)</p>
    </div>
    '''
    m.get_root().html.add_child(folium.Element(legend_html))
    
    return m

def create_range_comparison_map(data, range_analysis):
    """Create a map comparing widest vs rarest species"""
    center_lat = data['decimalLatitude'].mean()
    center_lon = data['decimalLongitude'].mean()
    
    m = folium.Map(location=[center_lat, center_lon], zoom_start=6)
    
    # Get top 5 widest and rarest species
    widest_species = sorted(range_analysis.items(), key=lambda x: x[1]['range_area'], reverse=True)[:5]
    rarest_species = [s for s in sorted(range_analysis.items(), key=lambda x: x[1]['num_locations'])[:5] 
                     if s[1]['num_locations'] <= 5]
    
    # Add markers for widest range species
    for species, metrics in widest_species:
        species_data = data[data['scientificName'] == species]
        
        for idx, row in species_data.iterrows():
            popup_text = f"""
            <b>WIDE RANGE SPECIES</b><br>
            <b>Scientific Name:</b> {species}<br>
            <b>Common Name:</b> {metrics['common_name']}<br>
            <b>Range Area:</b> {metrics['range_area']:,.0f} km²<br>
            <b>States:</b> {metrics['num_states']}<br>
            <b>Total Records:</b> {metrics['num_locations']}<br>
            """
            
            folium.Marker(
                location=[row['decimalLatitude'], row['decimalLongitude']],
                popup=folium.Popup(popup_text, max_width=300),
                tooltip=f"Wide Range: {species}",
                icon=folium.Icon(color='green', icon='globe')
            ).add_to(m)
    
    # Add markers for rarest species
    for species, metrics in rarest_species:
        species_data = data[data['scientificName'] == species]
        
        for idx, row in species_data.iterrows():
            popup_text = f"""
            <b>RARE SPECIES</b><br>
            <b>Scientific Name:</b> {species}<br>
            <b>Common Name:</b> {metrics['common_name']}<br>
            <b>Total Records:</b> {metrics['num_locations']}<br>
            <b>States:</b> {metrics['num_states']}<br>
            """
            
            folium.Marker(
                location=[row['decimalLatitude'], row['decimalLongitude']],
                popup=folium.Popup(popup_text, max_width=300),
                tooltip=f"Rare: {species}",
                icon=folium.Icon(color='red', icon='warning-sign')
            ).add_to(m)
    
    # Add legend
    legend_html = '''
    <div style="position: fixed; bottom: 50px; left: 50px; width: 250px; height: auto; 
                background-color: white; border:2px solid grey; z-index:9999; 
                font-size:12px; padding: 10px">
    <p><b>Geographic Range Comparison</b></p>
    <p><span style="color:green">🌍</span> Widest Range Species (Top 5)</p>
    <p><span style="color:red">⚠️</span> Rarest Species (≤5 records)</p>
    </div>
    '''
    m.get_root().html.add_child(folium.Element(legend_html))
    
    return m

def main():
    """Main function with enhanced analysis"""
    print("ENHANCED FROG SPECIES RESEARCH ANALYSIS")
    print("="*50)
    
    # Load data
    data = load_and_process_data()
    if data is None:
        return
    
    # Perform analyses
    endemic_species, species_distribution = analyze_endemism(data)
    seasonal_preferences = analyze_calling_seasons(data)
    range_analysis = analyze_geographic_ranges(data)
    
    # Create specialized maps
    print(f"\nCreating research maps...")
    
    # 1. Endemism map
    if endemic_species:
        endemism_map = create_endemism_map(data, endemic_species)
        endemism_map.save('frog_endemism_map.html')
        print("✓ Endemic species map saved as 'frog_endemism_map.html'")
    
    # 2. Seasonal calling map  
    if seasonal_preferences:
        seasonal_map = create_seasonal_map(data, seasonal_preferences)
        seasonal_map.save('frog_seasonal_map.html')
        print("✓ Seasonal calling map saved as 'frog_seasonal_map.html'")
    
    # 3. Range comparison map
    range_map = create_range_comparison_map(data, range_analysis)
    range_map.save('frog_range_comparison_map.html')
    print("✓ Range comparison map saved as 'frog_range_comparison_map.html'")
    
    # Summary
    print(f"\n" + "="*60)
    print("RESEARCH SUMMARY")
    print("="*60)
    print(f"📊 Total species analyzed: {data['scientificName'].nunique()}")
    print(f"🗺️  Potentially endemic species found: {sum(len(species_list) for species_list in endemic_species.values())}")
    print(f"📅 Species with seasonal data: {len(seasonal_preferences) if seasonal_preferences else 0}")
    print(f"📍 Geographic range analysis completed for all species")
    
    print(f"\n🔍 Open the HTML files in your browser to explore:")
    print(f"   • frog_endemism_map.html - Shows potentially endemic species by state")
    print(f"   • frog_seasonal_map.html - Shows seasonal calling patterns") 
    print(f"   • frog_range_comparison_map.html - Compares widest vs rarest species")

if __name__ == "__main__":
    main()
