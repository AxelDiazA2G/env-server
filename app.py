"""
Flask application for handling environmental data with various endpoints.

This application provides RESTful APIs to interact with environmental data
stored in an SQLite Cloud database. It includes endpoints for summarizing data,
retrieving temperature and motion data, calculating averages, and fetching data
within specific ranges.

Dependencies:
- Flask: Web framework for creating the API endpoints.
- Flask-CORS: Middleware for handling Cross-Origin Resource Sharing.
- SQLiteCloud: Library for connecting to SQLite Cloud.
- OpenAI: API for generating summaries from environmental data.
- json: Standard library for JSON operations.
- os: Standard library for environment variables and OS operations.
- datetime: Standard library for date and time operations.

Environment Variables:
- API_KEY: SQLite Cloud API key.
- DATABASE_URL: URL for SQLite Cloud database.
- OPENAI_API_KEY: API key for OpenAI service.
- PORT: Port on which to run the Flask application (default: 5000).

Routes:
- POST /summarize: Summarizes provided environmental data using OpenAI.
- GET /data/temperature: Retrieves the latest 100 temperature records.
- GET /data/motion: Retrieves the latest 100 motion records.
- GET /data/temperature/average/day: Retrieves daily average temperature.
- GET /data/temperature/average/week: Retrieves weekly average temperature.
- GET /data/temperature/average/month: Retrieves monthly average temperature.
- GET /data/motion/by-day: Retrieves the count of motion events per day.
- GET /data/temperature/by-day: Retrieves daily average temperature.
- GET /data/motion/by-hour: Retrieves motion count per hour.
- GET /data/motion/by-week: Retrieves motion count per week.
- GET /data/temperature/range: Retrieves temperature records within a date range.
- GET /data/motion/range: Retrieves motion records within a date range.
- GET /data/temperature/peak: Retrieves the record with the highest temperature.
- GET /data/motion/peak: Retrieves the day with the highest count of motion events.
- GET /data/temperature/summary: Retrieves summary statistics for temperature.
- GET /data/motion/summary: Retrieves summary statistics for motion events.
- GET /data/temperature/interval: Retrieves average temperature for custom time intervals.
- GET /data/motion/interval: Retrieves motion count for custom time intervals.

Functions:
- get_summary: Summarizes the provided environmental data using OpenAI.
- get_temperature_data: Fetches the latest 100 temperature records.
- get_motion_data: Fetches the latest 100 motion records.
- get_daily_temperature_average: Retrieves the average temperature for each day.
- get_weekly_temperature_average: Retrieves the average temperature for each week.
- get_monthly_temperature_average: Retrieves the average temperature for each month.
- get_motion_by_day: Retrieves the count of motion events for each day.
- get_temperature_by_day: Retrieves the average temperature for each day.
- get_motion_by_hour: Retrieves the count of motion events for each hour.
- get_motion_by_week: Retrieves the count of motion events for each week.
- get_temperature_in_range: Retrieves temperature records within a specified date range.
- get_motion_in_range: Retrieves motion records within a specified date range.
- get_peak_temperature: Retrieves the highest recorded temperature.
- get_peak_motion: Retrieves the day with the highest count of motion events.
- get_temperature_summary: Retrieves summary statistics (min, max, avg) for temperature.
- get_motion_summary: Retrieves summary statistics (total events, average per day) for motion events.
- get_temperature_custom_interval: Retrieves average temperature for custom intervals.
- get_motion_custom_interval: Retrieves motion count for custom intervals.

Error Handling:
- Each endpoint has error handling to return a JSON response with an error message
  and appropriate HTTP status code in case of failures or exceptions.
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import sqlitecloud
import os
from datetime import datetime, timedelta
from openai import OpenAI
import json

# SQLiteCloud connection details
API_KEY = os.getenv('API_KEY')
DATABASE_URL = os.getenv('DATABASE_URL')
DB_NAME = 'finalProject'
OPENAI_API_KEY= os.getenv('OPENAI_KEY')
client = OpenAI(api_key=OPENAI_API_KEY)
app = Flask(__name__)
CORS(app)  # This will enable CORS for all routes

# Open the connection to SQLite Cloud
try:
    # Constructing the connection string
    conn = sqlitecloud.connect(f"{DATABASE_URL}/{DB_NAME}?apikey={API_KEY}")
    print("Connected to SQLite Cloud")
except Exception as e:
    print(f"Failed to connect to SQLite Cloud: {e}")

@app.route('/summarize', methods=['POST'])
def get_summary():
    """
    Summarizes the provided environmental data using OpenAI.
    
    Request JSON format:
    {
        "data": <environmental_data>
    }

    Response JSON format:
    {
        "summary": <summary_text>
    }

    Returns:
    - 200 OK: On successful summary generation.
    - 400 Bad Request: If no data is provided.
    - 500 Internal Server Error: If an error occurs during processing.
    """
    try:
        data = request.json
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        # Convert data to a string format
        data_str = json.dumps(data, indent=2)

        # Prepare the messages for OpenAI
        messages = [
        {"role": "system", "content": """You are an AI assistant specialized in summarizing environmental data. Your task is to provide a concise, well-structured summary of the given environmental data. Please follow these guidelines:

1. Start with a brief overview of the data period and types of measurements included.
2. Provide key statistics:
   - Average temperature (if available)
   - Total number of motion events (if available)
   - Any other relevant aggregate data
3. Identify and mention any notable patterns or anomalies in the data.
4. Format the summary in easy-to-read paragraphs with appropriate line breaks.
5. Use bullet points for listing key points or statistics when appropriate.
6. End with a brief conclusion or recommendation based on the data.

Ensure that your response is well-formatted and easily readable when returned through an API."""},
        {"role": "user", "content": f"Please provide a brief, well-structured summary of the following environmental data:\n\n{data_str}"}
    ]

        # Make a request to the OpenAI API
        completion = client.chat.completions.create(
            model="gpt-4o-mini-2024-07-18",  # or another appropriate model
            messages=messages,
            max_tokens=650,
            n=1,
            temperature=0.7,
        )

        # Extract the summary from the response
        summary = completion.choices[0].message.content.strip()

        return jsonify({'summary': summary})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/data/temperature', methods=['GET'])
def get_temperature_data():
    """
    Retrieves the latest 100 temperature records.

    Response JSON format:
    [
        {
            "id": <record_id>,
            "timestamp": <timestamp>,
            "temperature": <temperature_value>
        },
        ...
    ]

    Returns:
    - 200 OK: On successful data retrieval.
    - 500 Internal Server Error: If an error occurs during data retrieval.
    """
    try:
        cursor = conn.cursor()
        query = 'SELECT * FROM temperature ORDER BY timestamp DESC LIMIT 100'
        cursor.execute(query)
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        results = [dict(zip(columns, row)) for row in rows]
        return jsonify(results)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/data/motion', methods=['GET'])
def get_motion_data():
    """
    Retrieves the latest 100 motion records.

    Response JSON format:
    [
        {
            "id": <record_id>,
            "timestamp": <timestamp>,
            "motion_detected": <motion_detected_value>
        },
        ...
    ]

    Returns:
    - 200 OK: On successful data retrieval.
    - 500 Internal Server Error: If an error occurs during data retrieval.
    """
    try:
        cursor = conn.cursor()
        query = 'SELECT * FROM motion ORDER BY timestamp DESC LIMIT 100'
        cursor.execute(query)
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        results = [dict(zip(columns, row)) for row in rows]
        return jsonify(results)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/data/temperature/average/day', methods=['GET'])
def get_daily_temperature_average():
    """
    Retrieves daily average temperature.

    Response JSON format:
    [
        {
            "date": <date>,
            "average_temp": <average_temperature>
        },
        ...
    ]

    Returns:
    - 200 OK: On successful data retrieval.
    - 500 Internal Server Error: If an error occurs during data retrieval.
    """
    try:
        cursor = conn.cursor()
        query = """
            SELECT DATE(timestamp) as date, AVG(temperature) as average_temp
            FROM temperature
            GROUP BY DATE(timestamp)
            ORDER BY DATE(timestamp) DESC
        """
        cursor.execute(query)
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        results = [dict(zip(columns, row)) for row in rows]
        return jsonify(results)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/data/temperature/average/week', methods=['GET'])
def get_weekly_temperature_average():
    """
    Retrieves weekly average temperature.

    Response JSON format:
    [
        {
            "week": <week>,
            "average_temp": <average_temperature>
        },
        ...
    ]

    Returns:
    - 200 OK: On successful data retrieval.
    - 500 Internal Server Error: If an error occurs during data retrieval.
    """
    try:
        cursor = conn.cursor()
        query = """
            SELECT STRFTIME('%Y-%W', timestamp) as week, AVG(temperature) as average_temp
            FROM temperature
            GROUP BY STRFTIME('%Y-%W', timestamp)
            ORDER BY STRFTIME('%Y-%W', timestamp) DESC
        """
        cursor.execute(query)
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        results = [dict(zip(columns, row)) for row in rows]
        return jsonify(results)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/data/temperature/average/month', methods=['GET'])
def get_monthly_temperature_average():
    """
    Retrieves monthly average temperature.

    Response JSON format:
    [
        {
            "month": <month>,
            "average_temp": <average_temperature>
        },
        ...
    ]

    Returns:
    - 200 OK: On successful data retrieval.
    - 500 Internal Server Error: If an error occurs during data retrieval.
    """
    try:
        cursor = conn.cursor()
        query = """
            SELECT STRFTIME('%Y-%m', timestamp) as month, AVG(temperature) as average_temp
            FROM temperature
            GROUP BY STRFTIME('%Y-%m', timestamp)
            ORDER BY STRFTIME('%Y-%m', timestamp) DESC
        """
        cursor.execute(query)
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        results = [dict(zip(columns, row)) for row in rows]
        return jsonify(results)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/data/motion/by-day', methods=['GET'])
def get_motion_by_day():
    """
    Retrieves the count of motion events per day.

    Response JSON format:
    [
        {
            "date": <date>,
            "motion_count": <count_of_motion_events>
        },
        ...
    ]

    Returns:
    - 200 OK: On successful data retrieval.
    - 500 Internal Server Error: If an error occurs during data retrieval.
    """
    try:
        cursor = conn.cursor()
        query = """
            SELECT DATE(timestamp) as date, COUNT(*) as motion_count
            FROM motion
            GROUP BY DATE(timestamp)
            ORDER BY DATE(timestamp) DESC
        """
        cursor.execute(query)
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        results = [dict(zip(columns, row)) for row in rows]
        return jsonify(results)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/data/temperature/by-day', methods=['GET'])
def get_temperature_by_day():
    """
    Retrieves the average temperature for each day.

    Response JSON format:
    [
        {
            "date": <date>,
            "average_temp": <average_temperature>
        },
        ...
    ]

    Returns:
    - 200 OK: On successful data retrieval.
    - 500 Internal Server Error: If an error occurs during data retrieval.
    """
    try:
        cursor = conn.cursor()
        query = """
            SELECT DATE(timestamp) as date, AVG(temperature) as average_temp
            FROM temperature
            GROUP BY DATE(timestamp)
            ORDER BY DATE(timestamp) DESC
        """
        cursor.execute(query)
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        results = [dict(zip(columns, row)) for row in rows]
        return jsonify(results)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/data/motion/by-hour', methods=['GET'])
def get_motion_by_hour():
    """
    Retrieves motion count per hour.

    Response JSON format:
    [
        {
            "hour": <hour>,
            "motion_count": <count_of_motion_events>
        },
        ...
    ]

    Returns:
    - 200 OK: On successful data retrieval.
    - 500 Internal Server Error: If an error occurs during data retrieval.
    """
    try:
        cursor = conn.cursor()
        query = """
            SELECT STRFTIME('%H', timestamp) as hour, COUNT(*) as motion_count
            FROM motion
            GROUP BY STRFTIME('%H', timestamp)
            ORDER BY STRFTIME('%H', timestamp) ASC
        """
        cursor.execute(query)
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        results = [dict(zip(columns, row)) for row in rows]
        return jsonify(results)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/data/motion/by-week', methods=['GET'])
def get_motion_by_week():
    """
    Retrieves the count of motion events per week.

    Response JSON format:
    [
        {
            "week": <week>,
            "motion_count": <count_of_motion_events>
        },
        ...
    ]

    Returns:
    - 200 OK: On successful data retrieval.
    - 500 Internal Server Error: If an error occurs during data retrieval.
    """
    try:
        cursor = conn.cursor()
        query = """
            SELECT STRFTIME('%Y-%W', timestamp) as week, COUNT(*) as motion_count
            FROM motion
            GROUP BY STRFTIME('%Y-%W', timestamp)
            ORDER BY STRFTIME('%Y-%W', timestamp) DESC
        """
        cursor.execute(query)
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        results = [dict(zip(columns, row)) for row in rows]
        return jsonify(results)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/data/temperature/range', methods=['GET'])
def get_temperature_in_range():
    """
    Retrieves temperature records within a specified date range.

    Query Parameters:
    - start_date (required): Start of the date range in YYYY-MM-DD format.
    - end_date (required): End of the date range in YYYY-MM-DD format.

    Response JSON format:
    [
        {
            "id": <record_id>,
            "timestamp": <timestamp>,
            "temperature": <temperature_value>
        },
        ...
    ]

    Returns:
    - 200 OK: On successful data retrieval.
    - 400 Bad Request: If required query parameters are missing or invalid.
    - 500 Internal Server Error: If an error occurs during data retrieval.
    """
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        if not start_date or not end_date:
            return jsonify({'error': 'Start date and end date are required'}), 400

        cursor = conn.cursor()
        query = """
            SELECT * FROM temperature
            WHERE timestamp BETWEEN ? AND ?
            ORDER BY timestamp DESC
        """
        cursor.execute(query, (start_date, end_date))
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        results = [dict(zip(columns, row)) for row in rows]
        return jsonify(results)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/data/motion/range', methods=['GET'])
def get_motion_in_range():
    """
    Retrieves motion records within a specified date range.

    Query Parameters:
    - start_date (required): Start of the date range in YYYY-MM-DD format.
    - end_date (required): End of the date range in YYYY-MM-DD format.

    Response JSON format:
    [
        {
            "id": <record_id>,
            "timestamp": <timestamp>,
            "motion_detected": <motion_detected_value>
        },
        ...
    ]

    Returns:
    - 200 OK: On successful data retrieval.
    - 400 Bad Request: If required query parameters are missing or invalid.
    - 500 Internal Server Error: If an error occurs during data retrieval.
    """
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        if not start_date or not end_date:
            return jsonify({'error': 'Start date and end date are required'}), 400

        cursor = conn.cursor()
        query = """
            SELECT * FROM motion
            WHERE timestamp BETWEEN ? AND ?
            ORDER BY timestamp DESC
        """
        cursor.execute(query, (start_date, end_date))
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        results = [dict(zip(columns, row)) for row in rows]
        return jsonify(results)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/data/temperature/peak', methods=['GET'])
def get_peak_temperature():
    """
    Retrieves the record with the highest temperature.

    Response JSON format:
    {
        "id": <record_id>,
        "timestamp": <timestamp>,
        "temperature": <temperature_value>
    }

    Returns:
    - 200 OK: On successful data retrieval.
    - 500 Internal Server Error: If an error occurs during data retrieval.
    """
    try:
        cursor = conn.cursor()
        query = 'SELECT * FROM temperature ORDER BY temperature DESC LIMIT 1'
        cursor.execute(query)
        row = cursor.fetchone()
        columns = [desc[0] for desc in cursor.description]
        result = dict(zip(columns, row))
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/data/motion/peak', methods=['GET'])
def get_peak_motion():
    """
    Retrieves the day with the highest count of motion events.

    Response JSON format:
    {
        "date": <date>,
        "motion_count": <count_of_motion_events>
    }

    Returns:
    - 200 OK: On successful data retrieval.
    - 500 Internal Server Error: If an error occurs during data retrieval.
    """
    try:
        cursor = conn.cursor()
        query = """
            SELECT DATE(timestamp) as date, COUNT(*) as motion_count
            FROM motion
            GROUP BY DATE(timestamp)
            ORDER BY COUNT(*) DESC LIMIT 1
        """
        cursor.execute(query)
        row = cursor.fetchone()
        columns = [desc[0] for desc in cursor.description]
        result = dict(zip(columns, row))
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
