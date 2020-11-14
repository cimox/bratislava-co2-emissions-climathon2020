import glob
import json
import random
from typing import List

import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objects as go
import pandas as pd
import numpy as np

SHP_INPUT_PATH = './data/treesAsPoints/stromy.shp'
JSON_OUTPUT_PATH = './data/treesAsPoints/stromy.geojson'
RADIUS = 2.5

with open(JSON_OUTPUT_PATH, 'r') as f:
    trees_geojson = json.load(f)

trees_geojson_sample = trees_geojson.copy()
trees_geojson_sample["features"] = random.sample(trees_geojson["features"], 10000)


step = 0.00001
co2_multiplier = 1.3
to_bin = lambda x: np.floor(x / step) * step

path = './data/bus/' # use your path
all_files = glob.glob(path + "/*.csv")

li = []

for filename in all_files:
    df = pd.read_csv(filename, index_col=None, header=0)
    li.append(df)

bus = pd.concat(li, axis=0, ignore_index=True)

# bus = pd.read_csv('./data/bus/CLIMATHON_BUSES_01_2019_BRATISLAVA_BUSES.csv')

# Convert data types to float
bus["LAT"] = bus["LAT"].str.replace(',', '.').astype(float)
bus["LON"] = bus["LON"].str.replace(',', '.').astype(float)

# Create lat/lon bins to group close points
bus["latbin"] = bus.LAT.map(to_bin)
bus["lonbin"] = bus.LON.map(to_bin)

# Groupby close lat/lon points
groups = bus.groupby(by=["latbin", "lonbin"])
result = groups.count()

# Calculate "co2" for a given map point and reset index
result["co2"] = result['DATE'] * co2_multiplier
result.reset_index(inplace=True)


class DashboardBuilder:
    def __init__(self, app):
        self.app = app

    def build(self):
        self._build_base_layout()

        self.app.run_server(debug=True)

    def _build_base_layout(self, build_time=None):
        self.app.layout = html.Div(
            className="masthead",
            children=self._init_base_elements(build_time)
        )

    def _init_base_elements(self, build_time=None) -> List[html.Div]:
        return [
            html.Div(id='blank-output'),
            self._build_navbar(),
            # self._build_trees_map(),
            self._build_combined_map(),
        ]

    @staticmethod
    def _build_navbar() -> html.Div:
        return html.Div(
            className="navbar",
            children=[
                html.H1("GOOD. Climathon 2020")
            ])

    @staticmethod
    def _build_trees_map() -> html.Div:
        fig = go.Figure(go.Scattermapbox())

        fig.update_layout(
            mapbox={
                'style': "carto-positron",
                'center': {
                    'lon': 17.1077,
                    'lat': 48.1486
                },
                'zoom': 12,
                'layers': [{
                    'sourcetype': 'geojson',
                    'source': trees_geojson_sample,
                    'type': 'circle',
                    'color': 'rgba(50,205,50, 0.75)',
                    'circle': {
                        'radius': RADIUS
                    }
                }]
            },
            margin={'l': 0, 'r': 0, 'b': 0, 't': 0}
        )

        return html.Div(
            children=[
                dcc.Graph(figure=fig, style={"height": "45vh"})
            ]
        )

    @staticmethod
    def _build_combined_map() -> html.Div:
        fig = go.Figure(
            go.Densitymapbox(
                lat=result.latbin, lon=result.lonbin, z=result.co2, radius=10
            )
        )
        fig.update_layout(
            mapbox={
                'style': 'carto-positron',
                'zoom': 11,
                'center': {
                    'lon': 17.1077,
                    'lat': 48.1486
                },
                'layers': [
                    {
                        'sourcetype': 'geojson',
                        'source': trees_geojson_sample,
                        'type': 'circle',
                        'color': 'rgba(50,205,50, 0.75)',
                        'circle': {
                            'radius': RADIUS
                        },
                    },
                ]
            }
        )
        fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})

        return html.Div(
            children=[
                dcc.Graph(figure=fig, style={"height": "90vh"})
            ]
        )
