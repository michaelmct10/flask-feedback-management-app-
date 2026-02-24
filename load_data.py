import json
from extensions import db
from feedback.models import Feedback  # Import Feedback model
from app import app  # Import Flask app
from datetime import datetime, timezone

# Load data from feedback JSON file
with open('feedback_data.json', mode='r') as json_file:
    feedback_data = json.load(json_file)

# Load data into feedback table in the database
with app.app_context():
    for item in feedback_data:
        # Convert date from string to datetime object
        created_date = datetime.strptime(item['Created Date'], "%d/%m/%Y")
        last_updated_date = datetime.strptime(item['Last Updated Date'], "%d/%m/%Y")

        # Create a new instance of the Feedback model for each item
        new_feedback = Feedback(
            id=int(item['Id']), 
            category=item['Category'],
            description=item['Description'],
            resolved_status=item['Resolved Status'],
            priority_level=item['Priority Level'],
            related_section=item['Related Section'],
            created_date=created_date,  
            last_updated_date=last_updated_date,  
            assigned_to=item['Assigned To']
        )
        
        # Add the new instance to the session
        db.session.add(new_feedback)

    # Commit all the changes to the database
    db.session.commit()

print("Feedback data successfully loaded into the database!")
