# Goal
- The goal is to make a script that makes a ship log entry in the style of old ship logs from year 1500 - 1800. The ship log should be invented and creative - but grounded using weather data and location data. 
- The log should be written in Norwegian
- Make sure to put effort into the prompt being creative
- Make a python script that uses ollama api. Make the code and architecture simple. 
- The output should be in markdown
- The python script is intended to be run autonomously and output to different options:
    - Call a webhook with the ship log entry
    - Make a log entry as a markdown file with the datetime in the filename. Add the filename to a registry.json
    - Echo to shell

# Location data
- Use one random sample from the fyrlykter_sorlandet.geojson as the coordinate and the data fields for the sample as data into the prompt

# Weather data
Use the first entry in timeseries for getting weather data for a position: https://api.met.no/weatherapi/nowcast/2.0/complete?lat=58.62151&lon=9.06186

# Examples for inspiration.
Make examples from these real log entries to use in the system prompt

The examples are in logsample.md