import dash as dash

from src.good.dashboard_builder import *


app: dash.Dash = dash.Dash(
    __name__, external_stylesheets=[
        'https://codepen.io/chriddyp/pen/bWLwgP.css', 
        'http://0.0.0.0:5000/src/good/assets/stylesheets.css'
    ],
    suppress_callback_exceptions=True,
    meta_tags=[
        {"name": "viewport", "content": "width=device-width, initial-scale=1"}
    ]
)

server = app.server
    
dashboard_builder = DashboardBuilder(app)
dashboard_builder.build()


if __name__ == '__main__':
    self.app.run_server(debug=True)
