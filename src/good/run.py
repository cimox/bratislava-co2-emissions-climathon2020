import dash as dash

from good.dashboard_builder import *


if __name__ == '__main__':
    app: dash.Dash = dash.Dash(
        __name__, external_stylesheets=[
            'https://codepen.io/chriddyp/pen/bWLwgP.css', './assets/stylesheets.css'
        ],
        suppress_callback_exceptions=True,
        meta_tags=[
            {"name": "viewport", "content": "width=device-width, initial-scale=1"}
        ]
    )

    dashboard_builder = DashboardBuilder(app)
    dashboard_builder.build()

