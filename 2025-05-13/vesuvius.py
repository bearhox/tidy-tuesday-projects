
# Using Python
# Option 1: pydytuesday python library
## pip install pydytuesday
import pandas
import pydytuesday

# Download files from the week, which you can then read in locally
pydytuesday.get_date('2025-05-13')

# Option 2: Read directly from GitHub and assign to an object
vesuvius = pandas.read_csv('https://raw.githubusercontent.com/rfordatascience/tidytuesday/main/data/2025/2025-05-13/vesuvius.csv')

vesuvius['time'] = pandas.to_datetime(vesuvius['time'])
vesuvius['year'] = vesuvius['time'].dt.year
vesuvius['month'] = vesuvius['time'].dt.month
vesuvius['day'] = vesuvius['time'].dt.day
vesuvius['hour'] = vesuvius['time'].dt.hour
vesuvius['weekday'] = vesuvius['time'].dt.day_name()


import seaborn as sns
import matplotlib.pyplot as plt



plt.figure(figsize=(10, 5))
sns.countplot(data=vesuvius, x="hour")
plt.title("Earthquakes near Vesuvius by Hour of Day")
plt.xlabel("Hour")
plt.ylabel("Count")
plt.show()


""" plt.figure(figsize=(8, 6))
sns.scatterplot(data=vesuvius, x="depth_km", y="duration_magnitude_md", alpha=0.6)
plt.title("Earthquake Depth vs. Magnitude")
plt.xlabel("Depth (km)")
plt.ylabel("Duration Magnitude (Md)")
plt.show() """
