import numpy as np

from datetime import datetime
from datetime import timedelta

import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func

from flask import Flask, jsonify
from sqlalchemy.sql.operators import endswith_op

#################################################
# Database Setup
#################################################
engine = create_engine("sqlite:///Resources/hawaii.sqlite", pool_pre_ping=True)

# reflect an existing database into a new model
Base = automap_base()
# reflect the tables
Base.prepare(engine, reflect=True)

# Save references to the tables
Measurement, Station = Base.classes.measurement, Base.classes.station
 
#################################################
# Flask Setup
#################################################

# 1. Create an app
app = Flask(__name__)


# 2. Define static routes

# Home: list all routes that are available.
@app.route("/")
def home():
    return (
        "Welcome to the API!<br/><br/>"
        "Available routes:<br/><br/>"
        "All precipitation data with dates:<br/>"
        "/api/v1.0/precipitation<br/><br/>"
        "List of stations:<br/>"
        "/api/v1.0/stations<br/><br/>"
        "365 days of data from the most active station:<br/>"
        "/api/v1.0/tobs<br/><br/>"
        "All data after requested start date:<br/>"
        "/api/v1.0/YYYY-MM-DD<br/><br/>"
        "All data within requested date range (/start/end):<br/>"
        "/api/v1.0/YYYY-MM-DD/YYYY-MM-DD<br/><br/>"
    )

# Precipitation: convert the query results to a dictionary using `date` as the key and `prcp` as the value.
# Return the JSON representation of your dictionary.
@app.route("/api/v1.0/precipitation")
def precipitation():

    # Create our session (link) from Python to the DB
    session = Session(engine)

    """Return a list of all precipitation measurements with dates as the key values."""
    # Query all measurements
    results = session.query(Measurement.date, Measurement.prcp).all()
    session.close()

    # Create a dictionary from the row data and append to a list 
    all_dates = []
    for date, prcp in results:
        date_dict = {date: prcp}
        all_dates.append(date_dict)
    return jsonify(all_dates)

# Stations: return a JSON list of stations from the dataset.
@app.route("/api/v1.0/stations")
def stations():
     
    # Create our session (link) from Python to the DB
    session = Session(engine)

    """Return a JSON list of stations from the dataset."""
    # Query all stations
    results = session.query(Station.station).all()
    session.close()

    # Convert list of tuples into normal list
    all_stations = list(np.ravel(results))
    return jsonify(all_stations)

# Tobs: query the dates and temperature observations of the most active station for the last year of data.
# Return a JSON list of temperature observations (TOBS) for the previous year.
@app.route("/api/v1.0/tobs")
def tobs():
    
    # Create our session (link) from Python to the DB
    session = Session(engine)

    """Return a JSON list of temperature observations (TOBS) for the previous year from the most active station."""
    # Query all measurements to find the most active station
    results = session.query(Measurement.station, func.count('*')).\
    group_by(Measurement.station).\
    order_by(func.count('*').desc()).all()
    session.close()  

    # Pull most active station from results
    most_active_station = results[0][0]

    # Create our session (link) from Python to the DB
    session = Session(engine)

    # Find the most recent date in the data set.
    station_date = session.query(Measurement.date).filter(Measurement.station == most_active_station).order_by(Measurement.date.desc()).first()
    session.close()  

    # Calculate the date one year from the last date in station's data set.
    station_date = datetime.strptime(station_date[0], '%Y-%m-%d')
    station_year = station_date - timedelta(days=365)
    station_year = station_year.strftime("%Y-%m-%d")

    # Create our session (link) from Python to the DB
    session = Session(engine)

    # Perform a query to retrieve the tobs 
    temperature_query = session.query(Measurement.date, Measurement.tobs).\
    filter(Measurement.date >= station_year).\
    filter(Measurement.station == most_active_station).\
    order_by(Measurement.date.desc()).all()
    session.close()  

    # Create a dictionary from the row data and append to a list    
    active_station_tobs = []
    for date, tobs in temperature_query:
        tobs_dict = {date: tobs}
        active_station_tobs.append(tobs_dict)
    return jsonify(active_station_tobs)

# Return a JSON list of the min, avg, and the max temp for a given start or start-end range.
# When given the start only, calculate `TMIN`, `TAVG`, and `TMAX` for all dates greater than and equal to the start date.
# When given the start and the end date, calculate the `TMIN`, `TAVG`, and `TMAX` for dates between the start and end date inclusive.
@app.route("/api/v1.0/<start>")
def start(start):
    
    try:
        convert_date = datetime.strptime(start, '%Y-%m-%d')
    except ValueError:
        return jsonify(f"Error: {start} is not a valid date. Use YYYY-MM-DD.")
    
    # A bit redundant, but I'm adding in additional checks in case the ValueError check does not work as intended
    if len(start)>10:
        return jsonify(f"Error: Please confirm dates. More characters than expected were entered.")
    elif len(start)<10:
        return jsonify(f"Error: Please confirm dates. Fewer characters than expected were entered.")

    """Return a JSON list of the min, avg, and the max temp for a given start or start-end range. 
    #When given the start only, calculate `TMIN`, `TAVG`, and `TMAX` for all dates greater than and equal to the start date."""
    # Create our session (link) from Python to the DB
    session = Session(engine)

    # Perform a query to retrieve the tobs 
    results = session.query(Measurement.date, Measurement.tobs).\
    filter(Measurement.date >= start).\
    order_by(Measurement.date.desc()).all()
    session.close()  

    if results == []:
        # Create our session (link) from Python to the DB
        session = Session(engine)

        # Perform a query to retrieve the dates 
        first_date = session.query(Measurement.date).\
        order_by(Measurement.date.asc()).first()
        last_date = session.query(Measurement.date).\
        order_by(Measurement.date.desc()).first()
        session.close()
        return jsonify(f"Error: Date is out of range. Please use a date between {first_date[0]} and {last_date[0]}.")  
   
    # Query and add data to dict  
    session = Session(engine)
    min_tobs = session.query(func.min(Measurement.tobs)).filter(Measurement.date >= start).first()
    max_tobs = session.query(func.max(Measurement.tobs)).filter(Measurement.date >= start).first()
    avg_tobs = session.query(func.avg(Measurement.tobs)).filter(Measurement.date >= start).first()
    session.close()
    stats_tobs = {"min": min_tobs[0], "max": max_tobs[0], "average" : round(avg_tobs[0],2)}
    return jsonify(stats_tobs)  

@app.route("/api/v1.0/<start>/<end>")
def start_end(start, end):

    try:
        convert_date = datetime.strptime(start, '%Y-%m-%d')
    except ValueError:
        return jsonify(f"Error: {start} is not a valid date. Use YYYY-MM-DD.")
    try:
        convert_date = datetime.strptime(end, '%Y-%m-%d')
    except ValueError:
        return jsonify(f"Error: {end} is not a valid date. Use YYYY-MM-DD.")
    
    # A bit redundant, but I'm adding in additional checks in case the ValueError check does not work as intended
    if (len(start)>10) or (len(end)>10):
        return jsonify(f"Error: Please confirm dates. More characters than expected were entered.")
    elif (len(start)<10) or (len(end)<10):
        return jsonify(f"Error: Please confirm dates. Fewer characters than expected were entered.")
    elif start>end:
        return jsonify(f"Error: Please confirm dates. {start} is later than {end}.")

    # Create our session (link) from Python to the DB
    session = Session(engine)

    """Return a JSON list of the min, avg, and the max temp for a given start or start-end range. 
    When given the start and the end date, calculate the `TMIN`, `TAVG`, and `TMAX` for dates between the start and end date inclusive."""
    # Query all measurements to find the most active station
    results = session.query(Measurement.date, Measurement.tobs).\
    filter(Measurement.date >= start).\
    filter(Measurement.date <= end).\
    order_by(Measurement.date.desc()).all()
    session.close()  

    if results == []:
        # Create our session (link) from Python to the DB
        session = Session(engine)

        # Perform a query to retrieve the dates 
        first_date = session.query(Measurement.date).\
        order_by(Measurement.date.asc()).first()
        last_date = session.query(Measurement.date).\
        order_by(Measurement.date.desc()).first()
        session.close()
        return jsonify(f"Error: Date is out of range. Please use a date between {first_date[0]} and {last_date[0]}.")  
    # Query and add data to dict  
    session = Session(engine)
    min_tobs = session.query(func.min(Measurement.tobs)).filter(Measurement.date >= start).filter(Measurement.date <= end).first()
    max_tobs = session.query(func.max(Measurement.tobs)).filter(Measurement.date >= start).filter(Measurement.date <= end).first()
    avg_tobs = session.query(func.avg(Measurement.tobs)).filter(Measurement.date >= start).filter(Measurement.date <= end).first()
    session.close()
    stats_tobs = {"min": min_tobs[0], "max": max_tobs[0], "average" : round(avg_tobs[0],2)}
    return jsonify(stats_tobs)  

# 3. Define main behavior
if __name__ == "__main__":
    app.run(debug=True)
