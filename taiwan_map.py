import geopandas as gpd
import matplotlib.pyplot as plt
import requests, zipfile, io, os
import pandas as pd
from io import BytesIO
from matplotlib.patches import FancyArrowPatch, Circle

# Configurar estilo profissional
plt.style.use('seaborn-v0_8-whitegrid')

# --- Função para adicionar rosa dos ventos ---
def add_compass(ax, x, y, size=0.1):
    """
    Desenha uma rosa dos ventos simples no canto do mapa.
    """
    ax_lims = ax.get_xlim() + ax.get_ylim()
    scale = (ax_lims[1] - ax_lims[0]) * size
    circle = Circle((x, y), scale * 0.5, color='white', alpha=0.8, edgecolor='black')
    ax.add_patch(circle)
    north_arrow = FancyArrowPatch(
        (x, y - scale * 0.4), (x, y + scale * 0.4),
        arrowstyle='->', mutation_scale=15, color='black', linewidth=1.5
    )
    ax.add_patch(north_arrow)
    ax.text(x, y + scale * 0.5, 'N', fontsize=10, ha='center', va='bottom', weight='bold')
    east_arrow = FancyArrowPatch(
        (x - scale * 0.4, y), (x + scale * 0.4, y),
        arrowstyle='->', mutation_scale=15, color='black', linewidth=1.5
    )
    ax.add_patch(east_arrow)
    ax.text(x + scale * 0.5, y, 'E', fontsize=10, ha='left', va='center', weight='bold')

# --- 1. Ler estações do Google Sheets ---
key = '1a5DReajqstsnUSUdTcRm8pZqeIP9ZmOct834UcOLmjg'
link = f'https://docs.google.com/spreadsheet/ccc?key={key}&output=csv'
r = requests.get(link)
df = pd.read_csv(BytesIO(r.content), header=0, low_memory=False)
# Seleciona e remove duplicatas
stations = df[['siteengname', 'twd97lon', 'twd97lat']].drop_duplicates(
    subset='siteengname', keep='first'
)

# --- 2. Baixar shapefile de Taiwan (nível 2 = municípios) ---
url = "https://geodata.ucdavis.edu/gadm/gadm4.1/shp/gadm41_TWN_shp.zip"
data_dir = "./data"
os.makedirs(data_dir, exist_ok=True)
r = requests.get(url)
z = zipfile.ZipFile(io.BytesIO(r.content))
z.extractall(data_dir)
shp_path = os.path.join(data_dir, "gadm41_TWN_2.shp")
taiwan = gpd.read_file(shp_path)

# --- 3. Reprojetar para WGS84 ---
taiwan = taiwan.to_crs(epsg=4326)

# --- 4. Criar figura (manter escala original) ---
fig, ax = plt.subplots(figsize=(8, 8))  # Escala original

# Plotar Taiwan inteiro (inclui ilhas, como no original)
taiwan.plot(ax=ax, color='#e6f3e6', edgecolor='gray', linewidth=0.8, alpha=0.9)

# Plotar estações em azul moderno
valid_stations = stations.dropna(subset=['twd97lon', 'twd97lat'])
if not valid_stations.empty:
    ax.scatter(
        valid_stations['twd97lon'], valid_stations['twd97lat'],
        color='#1f78b4', s=35, alpha=0.8, label="Weather Stations",
        edgecolor='white', linewidth=0.5
    )
else:
    print("Nenhuma estação válida para plotar!")

# Ajustar limites do mapa (manter escala original)
minx, miny, maxx, maxy = taiwan.total_bounds
margin = 0.2
ax.set_xlim(118 - margin, maxx + margin)  # Limite x fixo em 118, como no original
ax.set_ylim(22 - margin, maxy + margin)   # Limite y fixo em 22, como no original

# Título e eixos em inglês
# ax.set_title("Taiwan Weather Stations Map", fontsize=16, weight='bold', pad=15)
ax.set_xlabel("Longitude (°E)", fontsize=14)
ax.set_ylabel("Latitude (°N)", fontsize=14)

# Grade sutil
ax.grid(True, linestyle='--', alpha=0.7)

# Legenda maior e refinada
legend = ax.legend(fontsize=14, loc='upper right', frameon=True)
legend.get_frame().set_edgecolor('black')
legend.get_frame().set_linewidth(0.8)
legend.get_frame().set_facecolor('white')

# Adicionar rosa dos ventos no canto inferior esquerdo
add_compass(ax, 118 - margin + 0.3, 22 - margin + 0.3, size=0.15)
add_scale_bar(ax, lon=120.0, lat=21.9, length_km=50)
ax.set_aspect('equal')
plt.tight_layout()

# Salvar em alta qualidade
plt.savefig('plots/taiwan_map.png', dpi=300, bbox_inches='tight', facecolor='white')
plt.show()

# --- 5. Info no console ---
print(f"Total unique stations: {len(stations)}")
print(f"With valid coordinates: {len(valid_stations)}")
#%%

