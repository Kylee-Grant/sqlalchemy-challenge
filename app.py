# 1. Import Flask
from flask import Flask


# 2. Create an app
app = Flask(__name__)


# 3. Define static routes

# Home: list all routes that are available.
@app.route("/")
def home():
    return "Hello, world!"

# Precipitation: convert the query results to a dictionary using `date` as the key and `prcp` as the value.
# Return the JSON representation of your dictionary.
@app.route("/api/v1.0/precipitation")
def index():
    return 

# Stations: return a JSON list of stations from the dataset.
@app.route("/api/v1.0/stations")
def about():
    return 

# Tobs: query the dates and temperature observations of the most active station for the last year of data.
# Return a JSON list of temperature observations (TOBS) for the previous year.
@app.route("/api/v1.0/tobs")
def contact():
    return 

# Return a JSON list of the min, avg, and the max temp for a given start or start-end range.
# When given the start only, calculate `TMIN`, `TAVG`, and `TMAX` for all dates greater than and equal to the start date.
# When given the start and the end date, calculate the `TMIN`, `TAVG`, and `TMAX` for dates between the start and end date inclusive.
@app.route("/api/v1.0/<start>")
def index():
    return 

@app.route("/api/v1.0/<start>/<end>")
def about():
    return 


# 4. Define main behavior
if __name__ == "__main__":
    app.run(debug=True)
