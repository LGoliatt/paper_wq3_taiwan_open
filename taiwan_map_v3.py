import pandas as pd
import requests
from io import BytesIO
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from pyproj import Transformer
import numpy as np
import warnings

# Suppress warnings to reduce clutter, but log critical errors
warnings.filterwarnings("ignore", category=UserWarning)

# === 1. Load and inspect data ===
key = '1a5DReajqstsnUSUdTcRm8pZqeIP9ZmOct834UcOLmjg'
link = 'https://docs.google.com/spreadsheet/ccc?key=' + key + '&output=csv'
print("📥 Downloading data...")
try:
    r = requests.get(link)
    r.raise_for_status()
except requests.RequestException as e:
    raise Exception("Failed to download data: {}".format(e))

df = pd.read_csv(BytesIO(r.content), header=0)
print("\n📋 DataFrame Info:")
print(df.head())
print("\nColumn names: {}".format(df.columns.tolist()))
print("\nTWD97 coordinate samples:")
print(df[['twd97lon', 'twd97lat']].head())

# === 2. Clean and validate coordinates ===
# Keep only unique coordinates
df = df[['twd97lon', 'twd97lat']].drop_duplicates().copy()

# Ensure columns exist
if 'twd97lon' not in df.columns or 'twd97lat' not in df.columns:
    raise KeyError("Columns 'twd97lon' and 'twd97lat' not found! Check your sheet.")

# Drop rows with missing or non-numeric coordinates
df = df.dropna(subset=['twd97lon', 'twd97lat']).copy()
df['twd97lon'] = pd.to_numeric(df['twd97lon'], errors='coerce')
df['twd97lat'] = pd.to_numeric(df['twd97lat'], errors='coerce')
df = df.dropna(subset=['twd97lon', 'twd97lat'])

print("\n✅ Valid stations after cleaning: {}".format(len(df)))
if len(df) == 0:
    raise ValueError("No valid coordinates found!")

# === 3. Transform TWD97 (EPSG:3826) → WGS84 (EPSG:4326) ===
try:
    transformer = Transformer.from_crs("EPSG:3826", "EPSG:4326", always_xy=True)
    lon_wgs84, lat_wgs84 = transformer.transform(df['twd97lon'].values, df['twd97lat'].values)
    print("\n🔄 Coordinates transformed from TWD97 to WGS84.")
except Exception as e:
    print("⚠️ Transformation failed: {}. Assuming coordinates are already in WGS84.".format(e))
    lon_wgs84 = df['twd97lon'].values
    lat_wgs84 = df['twd97lat'].values

# Replace any invalid coordinates (e.g., inf or NaN)
valid_coords = np.isfinite(lon_wgs84) & np.isfinite(lat_wgs84)
lon_wgs84 = lon_wgs84[valid_coords]
lat_wgs84 = lat_wgs84[valid_coords]
df = df[valid_coords].copy()

print("\n📍 First 5 coordinates (WGS84):")
for i in range(min(5, len(lon_wgs84))):
    print("  ({:.4f}, {:.4f})".format(lon_wgs84[i], lat_wgs84[i]))

# === 4. Validate coordinates are near Taiwan ===
taiwan_bounds = {
    'lon_min': 120.0, 'lon_max': 122.1,
    'lat_min': 21.8, 'lat_max': 25.4
}

print("\n🌍 Taiwan bounding box:")
print("  Longitude: {} to {}".format(taiwan_bounds['lon_min'], taiwan_bounds['lon_max']))
print("  Latitude: {} to {}".format(taiwan_bounds['lat_min'], taiwan_bounds['lat_max']))

valid_mask = (
    (lon_wgs84 >= taiwan_bounds['lon_min']) &
    (lon_wgs84 <= taiwan_bounds['lon_max']) &
    (lat_wgs84 >= taiwan_bounds['lat_min']) &
    (lat_wgs84 <= taiwan_bounds['lat_max'])
)

print("\n🎯 Stations within Taiwan bounding box: {} / {}".format(valid_mask.sum(), len(lon_wgs84)))
if valid_mask.sum() == 0:
    print("⚠️ Warning: No stations fall within expected Taiwan bounds! Plotting all points for inspection...")

# === 5. Plot ===
fig = plt.figure(figsize=(10, 10))
ax = plt.axes(projection=ccrs.PlateCarree())

# Add base features with lower-resolution (50m) for stability
ax.add_feature(cfeature.LAND.with_scale('50m'), facecolor='#f0f0f0', edgecolor='gray')
ax.add_feature(cfeature.OCEAN.with_scale('50m'), facecolor='#d0e7ff')
ax.add_feature(cfeature.COASTLINE.with_scale('50m'), linewidth=0.8)
ax.add_feature(cfeature.BORDERS.with_scale('50m'), linewidth=0.5, linestyle='--')
# Comment out rivers to test stability; uncomment to re-enable
ax.add_feature(cfeature.RIVERS.with_scale('50m'), linewidth=0.5, color='blue', alpha=0.6)


## Try set_extent, fallback to set_xlim/set_ylim
try:
    ax.set_extent([119.8, 122.3, 21.5, 25.6], crs=ccrs.PlateCarree())
except Exception as e:
    print("⚠️ Error setting extent: {}. Using set_xlim/set_ylim as fallback.".format(e))
    ax.set_xlim(119.8, 122.3)
    ax.set_ylim(21.5, 25.6)

# Plot monitoring stations
ax.scatter(
    lon_wgs84, lat_wgs84,
    color='red',
    s=100,
    edgecolor='black',
    linewidth=0.8,
    transform=ccrs.PlateCarree(),
    label='Monitoring Stations (n={})'.format(len(lon_wgs84)),
    zorder=10
)

# Add gridlines with customized appearance
gl = ax.gridlines(draw_labels=True, linestyle='--', alpha=0.5, color='gray')
gl.top_labels = False
gl.right_labels = False
gl.xlabel_style = {'size': 10, 'color': 'black'}
gl.ylabel_style = {'size': 10, 'color': 'black'}

# Add legend to main map
ax.legend(loc='upper right', fontsize=12, frameon=True, edgecolor='black')

# === 6. Add Inset Map ===
inset_ax = fig.add_axes([0.50, 0.05, 0.25, 0.25], projection=ccrs.PlateCarree())
try:
    inset_ax.set_extent([100, 145, 15, 45], crs=ccrs.PlateCarree())
except Exception as e:
    print("⚠️ Error setting inset extent: {}. Using default inset extent.".format(e))
    inset_ax.set_extent([95, 150, 10, 50], crs=ccrs.PlateCarree())

inset_ax.add_feature(cfeature.LAND.with_scale('50m'), facecolor='#f0f0f0')
inset_ax.add_feature(cfeature.OCEAN.with_scale('50m'), facecolor='#d0e7ff')
inset_ax.add_feature(cfeature.COASTLINE.with_scale('50m'), linewidth=0.3)
inset_ax.add_feature(cfeature.BORDERS.with_scale('50m'), linewidth=0.2, linestyle='--')

# Add a marker for Taiwan on the inset map
inset_ax.scatter(
    [121], [23.5],  # Approximate center of Taiwan
    color='red',
    s=50,
    edgecolor='black',
    linewidth=0.5,
    transform=ccrs.PlateCarree(),
    zorder=11
)

# Indicate the location of the main map on the inset
from matplotlib.patches import Rectangle
main_extent = ax.get_extent(crs=ccrs.PlateCarree())
lon_min, lon_max, lat_min, lat_max = main_extent
rect = Rectangle(
    (lon_min, lat_min),
    lon_max - lon_min,
    lat_max - lat_min,
    facecolor='none',
    edgecolor='red',
    linewidth=2,
    transform=ccrs.PlateCarree(),
    zorder=12
)
inset_ax.add_patch(rect)

# Add title to the main map
ax.set_title('Monitoring Stations in Taiwan', fontsize=16, fontweight='bold', pad=15)

# Ensure high-quality layout
plt.tight_layout()

# Save the plot before displaying to avoid display-related crashes
try:
    plt.savefig('taiwan_monitoring_stations.pdf', dpi=300, bbox_inches='tight')
    print("\n💾 Plot saved as 'taiwan_monitoring_stations.pdf'")
except Exception as e:
    print("⚠️ Error saving plot: {}".format(e))

# Display the plot
try:
    plt.show()
except Exception as e:
    print("⚠️ Error displaying plot: {}. Check saved PDF.".format(e))
