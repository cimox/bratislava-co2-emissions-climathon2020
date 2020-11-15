import glob
import json
import random
from typing import List

import dash
import dash_daq as daq
import dash_core_components as dcc
import dash_html_components as html
import geojson
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from geojson_length import calculate_distance, Unit

BUS_LINES_PATH = './data/bus/bus_lines.geojson'
JSON_OUTPUT_PATH = './data/treesAsPoints/stromy.geojson'
TREES_BASE_COUNT = 86000
TREE_RADIUS = 1.5
TREE_OPACITY = 0.25
TREE_COLOR = f'rgba(50,205,50, {TREE_OPACITY})'
SPATIAL_GROUP_STEP = 0.00001
CO2_MULTIPLIER = 10 * 365  # 10x per day * 165 days a year
CO2_SEQUESTRATION_YEAR_KG = 22
HEATMAP_RADIUS = 23
MIN_HEATMAP_RADIUS = 7

DEBUG = True


class DashboardBuilder:
    def __init__(self, app):
        self.app = app

        self.trees_geojson = None
        self.bus_geojson = None
        self.bus_df = None
        self.bus_df_co2 = None

        self._prepare_data()

    def _prepare_data(self):
        with open(JSON_OUTPUT_PATH, 'r') as f:
            self.trees_geojson = json.load(f)

        with open(BUS_LINES_PATH, 'r') as f:
            self.bus_geojson = geojson.load(f)

        if DEBUG:
            self.bus_df_co2 = pd.read_csv('./data/calculated_co2.csv')
        else:
            self._prepare_bus_df()
            self._calc_carbon_emissions()

    def _prepare_bus_df(self):
        # Keep only bus lines
        bus_lines_only = [x for x in self.bus_geojson.features if 'bus' in str(x.properties['name']).lower()]

        self.bus_df = pd.DataFrame()
        columns = ['name', 'LON', 'LAT', 'distance_total_meters']
        for feature in bus_lines_only:
            distance_meters = calculate_distance(feature, Unit.meters)

            cnt = 0
            array = []
            for line_string in feature.geometry.coordinates:
                for lon_lat in line_string:
                    array.append([
                        feature.properties['name'], lon_lat[0], lon_lat[1], distance_meters
                    ])
                    cnt = cnt + 1

            partial_df = pd.DataFrame(array, columns=columns)
            partial_df['co2'] = (distance_meters * 0.0013) / cnt
            self.bus_df = pd.concat([self.bus_df, partial_df])

    def _calc_carbon_emissions(self):
        to_bin = lambda x: np.floor(x / SPATIAL_GROUP_STEP) * SPATIAL_GROUP_STEP

        # Create lat/lon bins to group close points
        self.bus_df["latbin"] = self.bus_df.LAT.map(to_bin)
        self.bus_df["lonbin"] = self.bus_df.LON.map(to_bin)

        # Groupby close lat/lon points
        groups = self.bus_df.groupby(by=["latbin", "lonbin"])
        self.bus_df_co2 = groups.sum()
        self.bus_df_co2.reset_index(inplace=True)

        self.bus_df_co2["co2_per_year"] = self.bus_df_co2["co2"] * CO2_MULTIPLIER

        cnt_trees = len(self.trees_geojson['features'])
        trees_co2_sequestration = cnt_trees * CO2_SEQUESTRATION_YEAR_KG
        trees_co2_sequestration_per_point = trees_co2_sequestration / len(self.bus_df_co2)

        self.bus_df_co2["co2_per_year_with_trees"] = self.bus_df_co2["co2_per_year"] - trees_co2_sequestration_per_point
        self.bus_df_co2["co2_per_year_with_trees"][self.bus_df_co2["co2_per_year_with_trees"] < 0] = 0

    def build(self):
        self._build_base_layout()
        self._slider_callback_value()
        self._slider_callback_sequestered_co2()
        self._slider_callback_produced_co2()
        self._callback_map()

    def _build_base_layout(self, build_time=None):
        self.app.layout = html.Div(
            className="masthead",
            children=self._init_base_elements(build_time)
        )

    def _slider_callback_value(self):
        @self.app.callback(
            dash.dependencies.Output('slider-output-container', 'children'),
            [dash.dependencies.Input('my-slider', 'value')])
        def update_output(value):
            return html.Span(
                children=[
                    'Planted ', html.B(children=[value]), ' trees'
                ]
            )

    def _slider_callback_sequestered_co2(self):
        @self.app.callback(
            dash.dependencies.Output('co2-sequestered', 'children'),
            [dash.dependencies.Input('my-slider', 'value')])
        def update_output(cnt_trees):
            return html.B('{:,}'.format(int(cnt_trees * CO2_SEQUESTRATION_YEAR_KG)), id='co2-sequestered')

    def _slider_callback_produced_co2(self):
        @self.app.callback(
            dash.dependencies.Output('co2-produced', 'children'),
            [dash.dependencies.Input('my-slider', 'value')])
        def update_output(cnt_trees):
            return html.B('{:,}'.format(int(self.bus_df_co2['co2_per_year'].sum())), id='co2-produced')

    def _callback_map(self):
        @self.app.callback(
            dash.dependencies.Output('map-output', 'children'),
            [
                dash.dependencies.Input('my-slider', 'value'),
                dash.dependencies.Input('trees-boolean-switch', 'on')
            ]
        )
        def update_output(cnt_trees, show_trees):
            trees_co2_sequestration = cnt_trees * CO2_SEQUESTRATION_YEAR_KG
            trees_co2_sequestration_per_point = trees_co2_sequestration / len(self.bus_df_co2)

            self.bus_df_co2["co2_per_year_with_trees"] = \
                self.bus_df_co2["co2_per_year"] - trees_co2_sequestration_per_point
            self.bus_df_co2.loc[self.bus_df_co2.co2_per_year_with_trees < 0, 'co2_per_year_with_trees'] = 0

            if cnt_trees <= TREES_BASE_COUNT:
                heatmap_radius = min(HEATMAP_RADIUS + TREES_BASE_COUNT / max(cnt_trees, 1), 35)
            else:
                heatmap_radius = HEATMAP_RADIUS - ((cnt_trees / TREES_BASE_COUNT) * 2)

            return self._build_combined_map(show_trees, heatmap_radius)

    def _init_base_elements(self, build_time=None) -> List[html.Div]:
        return [
            html.Div(id='blank-output'),
            self._build_navbar(),
            self._build_combined_map(),
        ]

    @staticmethod
    def _build_navbar() -> html.Div:
        return html.Div(
            className="navbar",
            children=[
                html.Center(html.H1("GOOD. Climathon 2020")),
                html.Div(
                    className="row",
                    children=[
                        html.Div(
                            className="column",
                            children=[
                                daq.BooleanSwitch(
                                    id='trees-boolean-switch',
                                    on=False,
                                    label='Show existing trees on the map',
                                    labelPosition='top'
                                ),
                            ]
                        ),
                        html.Div(
                            className="column",
                            children=[
                                dcc.Slider(
                                    id='my-slider',
                                    min=0,
                                    max=1000000,
                                    step=10000,
                                    value=86000,
                                ),
                                html.Div(id='slider-output-container')
                            ]
                        ),
                        html.Div(
                            className="column",
                            children=[
                                html.Span(children=[
                                    'CO2 per year PRODUCED: ',
                                    html.B(0, id='co2-produced'), ' kg'
                                ]),
                                html.Br(),
                                html.Span(children=[
                                    'CO2 per year SEQUESTERED: ',
                                    html.B(0, id='co2-sequestered'), ' kg'
                                ]),
                            ]
                        )
                    ]
                )
            ])

    def _build_combined_map(self, show_trees: bool = False, heatmap_radius: float = HEATMAP_RADIUS) -> html.Div:
        if show_trees is True:
            layers = [{
                'sourcetype': 'geojson',
                'source': self.trees_geojson,
                'type': 'circle',
                'color': TREE_COLOR,
                'circle': {
                    'radius': TREE_RADIUS
                },
            }]
        else:
            layers = []

        fig = go.Figure(
            go.Densitymapbox(
                lat=self.bus_df_co2.latbin, lon=self.bus_df_co2.lonbin,
                z=self.bus_df_co2.co2_per_year_with_trees, radius=max(1, heatmap_radius)
            )
        )
        fig.update_layout(
            mapbox={
                'style': 'carto-positron',
                'zoom': 12,
                'center': {
                    'lon': 17.1077,
                    'lat': 48.1486
                },
                'layers': layers
            }
        )
        fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})

        return html.Div(
            children=[
                dcc.Graph(figure=fig, style={"height": "75vh"})
            ],
            id='map-output'
        )
