import pytest
from app import app
from extensions import db
from feedback.models import Feedback
from datetime import datetime, timezone
import json

@pytest.fixture
def test_app():
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test_feedback.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(test_app):
    return test_app.test_client()

def test_add_feedback(client):
    """Test the add_feedback route to ensure feedback is added correctly."""
    
    # Define the input data for the POST request
    feedback_data = {
        "category": "Completeness",
        "description": "This is a test feedback.",
        "resolved_status": "Yes",
        "priority_level": "High",
        "related_section": "Abstract",
        "assigned_to": "Test User"
    }

    # Send a POST request to the /add route
    response = client.post("/feedback/add", data=feedback_data, follow_redirects=True)

    # Assert that the POST request was successful
    assert response.status_code == 200
    assert b"Comment added successfully!" in response.data  # Check for the flash message

    # Check if the feedback was added to the database
    added_feedback = Feedback.query.filter_by(description="This is a test feedback.").first()
    assert added_feedback is not None  # Ensure the feedback exists in the database
    assert added_feedback.category == "Completeness"
    assert added_feedback.resolved_status == "Yes"
    assert added_feedback.priority_level == "High"
    assert added_feedback.related_section == "Abstract"
    assert added_feedback.assigned_to == "Test User"

    # Cleanup: Remove the feedback after the test
    db.session.delete(added_feedback)
    db.session.commit()

def test_view_feedback(client):
    """Test the view_feedback route to ensure it displays feedback correctly."""
    
    # Prepopulate test database with sample feedback
    feedback1 = Feedback(
        category="Structure",
        description="Feedback 1 for Structure.",
        resolved_status="Yes",
        priority_level="High",
        related_section="Appendix",
        assigned_to="User1",
        created_date=datetime(2022, 1, 1, tzinfo=timezone.utc)
    )
    feedback2 = Feedback(
        category="Completeness",
        description="Feedback 2 for Completeness.",
        resolved_status="No",
        priority_level="Medium",
        related_section="Abstract",
        assigned_to="User2",
        created_date=datetime(2022, 2, 1, tzinfo=timezone.utc)
    )
    feedback3 = Feedback(
        category="Detail",
        description="Feedback 3 for Executive Summary.",
        resolved_status="Yes",
        priority_level="Low",
        related_section="Executive Summary",
        assigned_to="User3",
        created_date=datetime(2022, 3, 1, tzinfo=timezone.utc)
    )
    db.session.add_all([feedback1, feedback2, feedback3])
    db.session.commit()

    # Test viewing all feedback (default view)
    response = client.get("/feedback/")
    assert response.status_code == 200
    assert b"Feedback 1 for Structure." in response.data
    assert b"Feedback 2 for Completeness." in response.data
    assert b"Feedback 3 for Executive Summary." in response.data

    # Test filtering by related_section
    response = client.get("/feedback/", query_string={"related_section": "Appendix"})
    assert response.status_code == 200
    assert b"Feedback 1 for Structure." in response.data
    assert b"Feedback 2 for Completeness." not in response.data
    assert b"Feedback 3 for Executive Summary." not in response.data

    # Test sorting in ascending order (default)
    response = client.get("/feedback/", query_string={"sort": "asc"})
    assert response.status_code == 200
    assert response.data.index(b"Feedback 1 for Structure.") < response.data.index(b"Feedback 2 for Completeness.")
    assert response.data.index(b"Feedback 2 for Completeness.") < response.data.index(b"Feedback 3 for Executive Summary.")

    # Test sorting in descending order
    response = client.get("/feedback/", query_string={"sort": "desc"})
    assert response.status_code == 200
    assert response.data.index(b"Feedback 3 for Executive Summary.") < response.data.index(b"Feedback 2 for Completeness.")
    assert response.data.index(b"Feedback 2 for Completeness.") < response.data.index(b"Feedback 1 for Structure.")

def test_counts_route(client):
    """Test the counts route to ensure it returns correct counts for each related section."""

    # Prepopulate the database with test data
    feedback1 = Feedback(
        category="Structure",
        description="Feedback related to Appendix.",
        resolved_status="Yes",
        priority_level="High",
        related_section="Appendix",
        assigned_to="User1",
        created_date=datetime(2022, 1, 1, tzinfo=timezone.utc)
    )
    feedback2 = Feedback(
        category="Completeness",
        description="Feedback related to Abstract.",
        resolved_status="No",
        priority_level="Medium",
        related_section="Abstract",
        assigned_to="User2",
        created_date=datetime(2022, 2, 1, tzinfo=timezone.utc)
    )
    feedback3 = Feedback(
        category="Detail",
        description="Feedback related to Executive Summary.",
        resolved_status="No",
        priority_level="Low",
        related_section="Executive Summary",
        assigned_to="User3",
        created_date=datetime(2022, 3, 1, tzinfo=timezone.utc)
    )
    db.session.add_all([feedback1, feedback2, feedback3])
    db.session.commit()

    # Send a GET request to the /counts route
    response = client.get("/feedback/counts")

    # Assert that the response is successful
    assert response.status_code == 200

    print(response.data.decode('utf-8'))

    # Check the exact HTML structure
    assert b"<li><strong>Appendix:</strong> 1</li>" in response.data
    assert b"<li><strong>Abstract:</strong> 1</li>" in response.data
    assert b"<li><strong>Executive Summary:</strong> 1</li>" in response.data

    # Clean up after the test
    db.session.query(Feedback).delete()
    db.session.commit()

def test_edit_feedback(client):
    """Test the edit_feedback route to ensure feedback is updated correctly."""
    
    # Prepopulate the database with a feedback entry
    feedback = Feedback(
        category="Completeness",
        description="Original feedback description.",
        resolved_status="No",
        priority_level="Medium",
        related_section="Abstract",
        assigned_to="Original User",
        created_date=datetime(2022, 1, 1, tzinfo=timezone.utc),
        last_updated_date=datetime(2022, 1, 1, tzinfo=timezone.utc),
    )
    db.session.add(feedback)
    db.session.commit()

    # Define updated data for the feedback
    updated_data = {
        "category": "Structure",
        "description": "Updated feedback description.",
        "resolved_status": "Yes",
        "priority_level": "High",
        "related_section": "Appendix",
        "assigned_to": "Updated User"
    }

    # Send a POST request to the edit route with the updated data
    response = client.post(
        f"/feedback/edit/{feedback.id}",
        data=updated_data,
        follow_redirects=True
    )

    # Assert the response and flash message
    assert response.status_code == 200
    assert b"Comment successfully edited." in response.data

    # Fetch the feedback from the database and verify updates
    edited_feedback = Feedback.query.get(feedback.id)
    assert edited_feedback is not None  # Ensure feedback exists
    assert edited_feedback.category == "Structure"
    assert edited_feedback.description == "Updated feedback description."
    assert edited_feedback.resolved_status == "Yes"
    assert edited_feedback.priority_level == "High"
    assert edited_feedback.related_section == "Appendix"
    assert edited_feedback.assigned_to == "Updated User"

    # Cleanup: Remove the feedback after the test
    db.session.delete(edited_feedback)
    db.session.commit()

def test_delete_feedback(client):
    """Test the delete_feedback route to ensure feedback is deleted correctly."""
    
    # Prepopulate the database with a feedback entry
    feedback = Feedback(
        category="Completeness",
        description="Feedback to be deleted.",
        resolved_status="No",
        priority_level="Medium",
        related_section="Abstract",
        assigned_to="User1",
        created_date=datetime(2022, 1, 1, tzinfo=timezone.utc),
        last_updated_date=datetime(2022, 1, 1, tzinfo=timezone.utc),
    )
    db.session.add(feedback)
    db.session.commit()

    # Send a POST request to delete the feedback
    response = client.post(
        f"/feedback/delete/{feedback.id}",
        follow_redirects=True
    )

    # Assert the response and flash message
    assert response.status_code == 200
    assert b"Comment successfully deleted." in response.data

# Test for bulk_upload_feedback
def test_bulk_upload_feedback(client):
    data = {
        "feedbacks": [
            {
                "category": "Completeness",
                "description": "Bulk feedback 1",
                "resolved_status": "Yes",
                "priority_level": "Medium",
                "related_section": "Abstract",
                "assigned_to": "User 1"
            },
            {
                "category": "Detail",
                "description": "Bulk feedback 2",
                "resolved_status": "No",
                "priority_level": "Low",
                "related_section": "Executive Summary",
                "assigned_to": "User 2"
            }
        ]
    }
    response = client.post("/feedback/bulk-upload", json=data)
    assert response.status_code == 201
    assert response.json["message"] == "Feedback comments uploaded successfully"

# Test for get_feedback_by_phrase
def test_get_feedback_by_phrase(client):
    # Prepopulate data
    feedback = Feedback(category="Structure", description="Find this feedback.", resolved_status="Yes",
                        priority_level="High", related_section="Appendix", assigned_to="User")
    db.session.add(feedback)
    db.session.commit()

    response = client.get("/feedback/search?phrase=Find")
    assert response.status_code == 200
    assert len(response.json) > 0
    assert response.json[0]["description"] == "Find this feedback."

# Test for get_feedback_by_max_length
def test_get_feedback_by_max_length(client):
    # Prepopulate data
    feedback = Feedback(category="Length", description="Short feedback.", resolved_status="No",
                        priority_level="Low", related_section="Abstract", assigned_to="User")
    db.session.add(feedback)
    db.session.commit()

    response = client.get("/feedback/by-max-length?max_length=20")
    assert response.status_code == 200
    assert len(response.json) > 0
    assert response.json[0]["description"] == "Short feedback."

# Test for update_multiple_feedback_categories
def test_update_multiple_feedback_categories(client):
    # Prepopulate data
    feedback = Feedback(category="Old Category", description="Update this feedback.", resolved_status="Yes",
                        priority_level="High", related_section="Appendix", assigned_to="User")
    db.session.add(feedback)
    db.session.commit()

    data = {
        "feedback_ids": [feedback.id],
        "new_category": "New Category"
    }
    response = client.put("/feedback/update-category", json=data)
    assert response.status_code == 200
    assert response.json["message"] == "Feedback comments updated successfully."

# Test for delete_feedback_by_category
def test_delete_feedback_by_category(client):
    # Prepopulate data
    feedback = Feedback(category="Delete Category", description="Delete this feedback.", resolved_status="No",
                        priority_level="Low", related_section="Abstract", assigned_to="User")
    db.session.add(feedback)
    db.session.commit()

    response = client.delete("/feedback/delete-by-category?category=Delete Category")
    assert response.status_code == 200
    assert response.json["message"] == "All feedback comments in category 'Delete Category' deleted successfully."

# Test for get_average_comment_length
def test_get_average_comment_length(client):
    # Prepopulate data
    feedback = Feedback(category="Length", description="This is a test feedback.", resolved_status="No",
                        priority_level="High", related_section="Appendix", assigned_to="User")
    db.session.add(feedback)
    db.session.commit()

    response = client.get("/feedback/summary-statistics")
    assert response.status_code == 200
    assert "average_comment_length" in response.json

# Test for archive_old_feedback
def test_archive_old_feedback(client):
    # Prepopulate data
    feedback = Feedback(category="Archive", description="Archive this feedback.", resolved_status="No",
                        priority_level="Medium", related_section="Abstract", assigned_to="User",
                        last_updated_date=datetime(2022, 1, 1, tzinfo=timezone.utc))
    db.session.add(feedback)
    db.session.commit()

    data = {"date_threshold": "2023-01-01"}
    response = client.post("/feedback/archive", json=data)
    assert response.status_code == 200
    assert response.json["message"] == "Old feedback comments archived successfully."

