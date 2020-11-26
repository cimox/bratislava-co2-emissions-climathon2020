# Bratislava CO2 Emissions and Trees Sequestration Modelling (_Team GOOD._)
Bratislava Climate (online) Hackathon 2020 website:
- https://climathon.climate-kic.org/bratislava

Media mentions:
- https://www.linkedin.com/feed/update/urn:li:activity:6733815166514851840
- https://www.facebook.com/Bratislava.sk/posts/3739488752780801
- https://bratislava.sk/sk/sprava/bratislavsky-climathon-priniesol-napad-ako-zmiernit-prehrievanie-mesta

Final presentations recording:
- Starting at 42:00 https://www.youtube.com/watch?v=HDvq4hWsstc

**Online application DEMO:**
- https://good-climathon2020.herokuapp.com/

## Application screenshot
![Application screenshot GIF](./app.gif)

## About the application
- Python map web GIS application for modelling trees sequestration impact in the Bratislava (Slovakia).
- Technologies used: 
  - Python + Numpy and Pandas stack for data processing
  - Plotly Dash for visualization
  - QGis for manual data exploration and exports
- Data sources:g
  - Open street maps data public transport lines (geojson)
  - Bratislava public datasets with planted treees

## Installation instructions
1. Create and activate python virtualenv
1. Install requirements `pip install -r requirements.txt`
1. Run the app `python run.py`

## Next-steps
- Improve CO2 emissions model calculated from the public transport.
- Improve precision of CO2 emissions models.
- Model the best locations to plant the trees.
- Display heat islands by adding spectral GIS data.
- Model trees impact on heat islands.

## Contributing
Open an MR and contribute.

## License
See LICENSE file.

## Authors
- Matus Cimerman <matus.cimerman [at] gmail [dot] com>
- Daniel Kozak <kozakdaniel12 [at] gmail [dot] com>
- Tomas Kozak <kozaktx [at] gmail [dot] com>