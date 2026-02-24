import csv
import json

csv_file_path = 'feedback_data.csv' 
json_file_path = 'feedback_data.json'

# Read CSV and convert to JSON
with open(csv_file_path, mode='r') as csv_file:
    csv_reader = csv.DictReader(csv_file)
    data = [row for row in csv_reader]

# Write JSON data to a file
with open(json_file_path, mode='w') as json_file:
    json.dump(data, json_file, indent=4)

print("CSV successfully converted to JSON!")
