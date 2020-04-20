from flask import Flask, jsonify

import numpy as np

import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func


import datetime as dt
from datetime import timedelta
# Database Setup
engine = create_engine("sqlite:///Resources/hawaii.sqlite")

# reflect an existing database into a new model
Base = automap_base()
# reflect the tables
Base.prepare(engine, reflect=True)

# Save references to each table
Measurement = Base.classes.measurement
Station = Base.classes.station

# Create our session (link) from Python to the DB
session = Session(engine)

# Flask Setup
app = Flask(__name__)

@app.route("/")
def welcome():
    """Available API Routes:"""
    return (
        f"Available Routes:<br/>"
        f"/api/v1.0/precipitation<br/>"
        f"/api/v1.0/stations<br/>"
        f"/api/v1.0/tobs<br/>"
        f"<br/>"
        f"/api/v1.0/<start>/<end><br/>"
        f"Enter the start date, and an optional end date, in the form 'yyy-mm-dd' into <start> and <end><br>"
        f"example: /api/v1.0/temp/2017-03-04 or /api/v1.0/temp/2012-03-04/2017-03-25"
    )

@app.route("/api/v1.0/precipitation")
def precipitation():
    """Last Year of Percipitation Data"""
    session = Session(engine)
    # Measurements last date 
    last_date = session.query(Measurement.date).order_by(Measurement.date.desc()).first().date

    # Convert last date string to date
    last_date = dt.datetime.strptime(last_date, "%Y-%m-%d")

    # Calculate date one year before last date
    first_date = last_date - timedelta(days=365)

    # Query the data and precipitation scores
    last_year_data = session.query(Measurement.date, Measurement.prcp).filter(Measurement.date >= first_date).all()
    return jsonify(last_year_data)


@app.route("/api/v1.0/stations")
def stations():
    """List of Weather Stations"""
    session = Session(engine)

    stations = session.query(Station.station).all()

    # Return JSON of Stations
    return jsonify(stations)

@app.route("/api/v1.0/tobs")
def temp_monthly():
    """Temperature Observations for Top Station for Last Year"""
    
    session = Session(engine)
    
    last_date = session.query(Measurement.date).order_by(Measurement.date.desc()).first().date

    last_date = dt.datetime.strptime(last_date, "%Y-%m-%d")

    first_date = last_date - timedelta(days=365)

    station_counts = session.query(Measurement.station, func.count(Measurement.station)).group_by(Measurement.station).order_by(func.count(Measurement.station).desc()).all()
    
    # Create top station variable
    top_station = (station_counts[0][0])

    # Using the station id from the previous query, calculate the lowest temperature recorded, 
    # highest temperature recorded, and average temperature of the most active station?
    session.query(func.min(Measurement.tobs), func.max(Measurement.tobs), func.avg(Measurement.tobs)).\
    filter(Measurement.station == top_station).all()
    
    # Choose the station with the highest number of temperature observations.
    # Query the last 12 months of temperature observation data for this station and plot the results as a histogram
    top_station_ly = session.query(Measurement.date, Measurement.tobs).\
    filter(Measurement.station == top_station).filter(Measurement.date >= first_date).all()
    return jsonify(top_station_ly)

@app.route("/api/v1.0/temp/<start>")
@app.route("/api/v1.0/temp/<start>/<end>")
def stats(start=None, end=None):
    session = Session(engine)

    """TMIN, TAVG, TMAX."""

    # Select statement
    sel = [func.min(Measurement.tobs), func.avg(Measurement.tobs), func.max(Measurement.tobs)]

    if not end:
        # calculate TMIN, TAVG, TMAX for dates greater than start
        results = session.query(*sel).\
            filter(Measurement.date >= start).all()
        # Unravel results into a 1D array and convert to a list
        temps = list(np.ravel(results))
        return jsonify(temps)

    # calculate TMIN, TAVG, TMAX with start and stop
    results = session.query(*sel).\
        filter(Measurement.date >= start).\
        filter(Measurement.date <= end).all()
  
    return jsonify(results)

if __name__ == '__main__':
    app.run()