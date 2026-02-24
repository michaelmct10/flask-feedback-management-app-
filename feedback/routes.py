from flask import Blueprint, render_template, request, redirect, url_for, jsonify, flash
from extensions import db
from .models import Feedback
from datetime import datetime, timezone
from sqlalchemy import func  # Import func to handle length operations
import json
import csv

# Initialise the Blueprint
feedback_bp = Blueprint('feedback', __name__, template_folder='../templates')

@feedback_bp.route("/add", methods=["GET", "POST"])
def add_feedback():
    """Route to add a new feedback comment using a form submission."""
    if request.method == "POST":
        category = request.form.get("category")  # This could be "Appendix" or "Abstract"
        description = request.form.get("description")
        resolved_status = request.form.get("resolved_status")
        priority_level = request.form.get("priority_level")
        related_section = request.form.get("related_section")
        assigned_to = request.form.get("assigned_to")

        # Create a new Feedback instance
        new_feedback = Feedback(
            category=category,
            description=description,
            resolved_status=resolved_status,
            priority_level=priority_level,
            related_section=related_section,
            assigned_to=assigned_to,
        )        
        db.session.add(new_feedback)
        db.session.commit()

        flash("Comment added successfully!", "success") # Flash a success message

        # After adding the new feedback, calculate the last page
        total_comments = Feedback.query.count()
        comments_per_page = 5
        last_page = (total_comments // comments_per_page) + (1 if total_comments % comments_per_page else 0)

        # Redirect to view_feedback after adding
        return redirect(url_for('feedback.view_feedback', page=last_page))
    
    return render_template("add_feedback.html")

@feedback_bp.route("/counts")
def counts():
    """Route to display feedback counts for each related section."""
    appendix_count = Feedback.query.filter(Feedback.related_section.ilike("%Appendix%")).count()
    abstract_count = Feedback.query.filter(Feedback.related_section.ilike("%Abstract%")).count()
    executive_summary_count = Feedback.query.filter(Feedback.related_section.ilike("%Executive Summary%")).count()

    return render_template(
        "counts.html",
        appendix_count=appendix_count,
        abstract_count=abstract_count,
        executive_summary_count=executive_summary_count,
    )

@feedback_bp.route("/")
def view_feedback():
    """Route to view all feedback with optional category filter and sorting."""
    # Retrieve the query parameters with defaults
    related_section_filter = request.args.get("related_section", "").strip()  # Default to empty string if None
    sort_order = request.args.get("sort", "asc").lower()  # Default to "asc" for ascending order and ensure lowercase
    page = request.args.get("page", 1, type=int)  # Get the page number, default to 1
    edited_feedback_id = request.args.get("edited_feedback_id", None)  # Get the edited feedback ID if present

    # Start with a base query for all feedback
    query = Feedback.query

    # Apply related section filter
    query = query.filter(Feedback.related_section.ilike(f"%{related_section_filter}%"))  # Case-insensitive filter

    # Apply sorting based on sort_order parameter
    if sort_order == "asc":
        query = query.order_by(Feedback.created_date.asc())  # Order by created_date in ascending order
    elif sort_order == "desc":
        query = query.order_by(Feedback.created_date.desc())  # Order by created_date in descending order
    else:
        # Fallback to ascending order by ID if sort_order is invalid
        query = query.order_by(Feedback.created_date.asc())

    # Paginate the results
    feedbacks = query.paginate(page=page, per_page=5)  # Adjust per_page to control the number of items per page

   # Pass the feedback, filter, sorting, and counts parameters to the template
    return render_template(
        "view_feedback.html",
        feedbacks=feedbacks,
        related_section_filter=related_section_filter,
        sort_order=sort_order,
        edited_feedback_id=edited_feedback_id
    )

@feedback_bp.route("/edit/<int:feedback_id>", methods=["GET", "POST"])
def edit_feedback(feedback_id):
    """Route to edit an existing feedback comment."""
    feedback = Feedback.query.get_or_404(feedback_id)
    page = request.args.get("page", 1, type=int)  # Capture the current page number

    if request.method == "POST":
        feedback.category = request.form.get("category")
        feedback.description = request.form.get("description")
        feedback.resolved_status = request.form.get("resolved_status")
        feedback.priority_level = request.form.get("priority_level")
        feedback.related_section = request.form.get("related_section")
        feedback.assigned_to = request.form.get("assigned_to")
        
        db.session.commit()
        flash("Comment successfully edited.", "success")  # Flashing a success message
        return redirect(url_for("feedback.view_feedback", page=page, edited_feedback_id=feedback_id))  # Pass the edited feedback and redirect to the correct page after editing
    
    return render_template("edit_feedback.html", feedback=feedback, page=page)

@feedback_bp.route("/delete/<int:feedback_id>", methods=["POST"])
def delete_feedback(feedback_id):
    """Route to delete a feedback comment by ID."""
    feedback = Feedback.query.get_or_404(feedback_id)
    db.session.delete(feedback)
    db.session.commit()
    flash("Comment successfully deleted.", "success")  # Flashing a success message
    return redirect(url_for("feedback.view_feedback"))

@feedback_bp.route("/bulk-upload", methods=["POST"])
def bulk_upload_feedback():
    """Route to bulk upload multiple feedback comments using JSON data in a single request."""
    # Get the list of feedbacks from the request JSON body
    feedback_data = request.json.get("feedbacks", [])

    # Check if feedbacks are provided
    if not feedback_data:
        return jsonify({"error": "No feedback entries provided in the request body."}), 400

    # Loop over each feedback entry in the list
    for feedback_entry in feedback_data:
        # Validate required fields
        required_fields = ["category", "description", "resolved_status", "priority_level", "related_section", "assigned_to"]
        for field in required_fields:
            if field not in feedback_entry or feedback_entry[field] is None:
                return jsonify({"error": "Validation failed. Please ensure all required fields are provided for each feedback entry."}), 400

        new_feedback = Feedback(
            category=feedback_entry.get("category"),
            description=feedback_entry.get("description"),
            resolved_status=feedback_entry.get("resolved_status"),
            priority_level=feedback_entry.get("priority_level"),
            related_section=feedback_entry.get("related_section"),
            assigned_to=feedback_entry.get("assigned_to"),
            created_date=datetime.now(timezone.utc)
        )
        # Add the new feedback entry to the database session
        db.session.add(new_feedback)

    # Commit the changes to save all new feedback comments
    db.session.commit()

    return jsonify({"message": "Feedback comments uploaded successfully"}), 201

@feedback_bp.route("/search", methods=["GET"])
def get_feedback_by_phrase():
    """Route to retrieve feedback comments containing a specific phrase in the description."""
    phrase = request.args.get("phrase", "").strip()  # Extract the value of the 'phrase' query parameter

    # If a phrase is provided, filter the feedback entries
    feedbacks = Feedback.query.filter(Feedback.description.ilike(f"%{phrase}%")).all()

    # Check if feedbacks are found
    if not feedbacks:
        return jsonify({"message": "No feedback comments found."}), 404

    # Convert the feedback objects to dictionaries and return as JSON
    return jsonify([feedback.to_dict() for feedback in feedbacks]), 200

@feedback_bp.route("/by-max-length", methods=["GET"])
def get_feedback_by_max_length():
    """Route to retrieve feedback comments with a maximum text length."""
    # Retrieve the 'max_length' parameter and ensure it's an integer
    max_length = request.args.get("max_length")
    
    try:
        max_length = int(max_length)
    except (ValueError, TypeError):
        return jsonify({"error": "Invalid max length value. Please provide a valid integer."}), 400

    # Start with the base query for all feedback
    query = Feedback.query

    # Apply filtering for maximum length
    if max_length is not None:
        query = query.filter(func.length(Feedback.description) <= max_length)

    # Execute the query to get filtered feedback comments
    feedbacks = query.all()

    # Check if feedbacks are found
    if not feedbacks:
        return jsonify({"message": "Sorry, no comments meet this criteria."}), 404

    # Convert the feedback objects to dictionaries and return as JSON
    return jsonify([feedback.to_dict() for feedback in feedbacks])

@feedback_bp.route("/update-category", methods=["PUT", "PATCH"])
def update_multiple_feedback_categories():
    """Route to batch update the category of multiple feedback comments."""
    # Retrieve the list of feedback IDs and the new category from the request JSON body
    feedback_ids = request.json.get("feedback_ids", [])
    new_category = request.json.get("new_category")

    # Validate input
    if not feedback_ids or not new_category:
        return jsonify({"error": "Please provide both feedback IDs and a new category."}), 400

    # Update the category for the specified feedback comments
    try:
        Feedback.query.filter(Feedback.id.in_(feedback_ids)).update({"category": new_category}, synchronize_session=False)
        db.session.commit()
    except Exception as e:
        return jsonify({"error": f"Failed to update feedback comments: {str(e)}"}), 500

    return jsonify({"message": "Feedback comments updated successfully."}), 200

@feedback_bp.route("/delete-by-category", methods=["DELETE"])
def delete_feedback_by_category():
    """Route to delete all feedback comments of a specified category."""
    # Retrieve the category parameter from the query string
    category = request.args.get("category")

    # Validate input
    if not category:
        return jsonify({"error": "Please provide a category to delete."}), 400

    # Delete all feedback comments of the specified category
    try:
        Feedback.query.filter_by(category=category).delete()
        db.session.commit()
    except Exception as e:
        return jsonify({"error": f"Failed to delete feedback comments: {str(e)}"}), 500

    return jsonify({"message": f"All feedback comments in category '{category}' deleted successfully."}), 200

@feedback_bp.route("/summary-statistics", methods=["GET"])
def get_average_comment_length():
    """Route to get the average length of feedback comments."""
    try:
        # Calculate average length of comments
        avg_length = db.session.query(db.func.avg(db.func.length(Feedback.description))).scalar()

        # Construct the summary
        summary = {
            "average_comment_length": avg_length
        }

        return jsonify(summary), 200
    except Exception as e:
        return jsonify({"error": f"Failed to retrieve average comment length: {str(e)}"}), 500

@feedback_bp.route("archive", methods=["POST", "PUT"])
def archive_old_feedback():
    """Route to archive feedback comments older than a specified date."""
    # Get the date from the request body
    data = request.get_json()
    date_threshold = data.get('date_threshold')

    # Validate the date input
    try:
        date_threshold = datetime.strptime(date_threshold, "%Y-%m-%d")
    except (ValueError, TypeError):
        return jsonify({"error": "Invalid date format. Use YYYY-MM-DD for the date"}), 400

    # Query feedback comments older than the specified date
    old_feedbacks = Feedback.query.filter(Feedback.last_updated_date < date_threshold).all()
    
    if not old_feedbacks:
        return jsonify({"message": "No feedback comments older than the specified date."}), 200

    # Prepare feedback comments to be archived
    archived_feedbacks = []
    for feedback in old_feedbacks:
        archived_feedbacks.append({
            "id": feedback.id,
            "category": feedback.category,
            "description": feedback.description,
            "resolved_status": feedback.resolved_status,
            "priority_level": feedback.priority_level,
            "related_section": feedback.related_section,
            "assigned_to": feedback.assigned_to,
            "created_date": feedback.created_date,
            "last_updated_date": feedback.last_updated_date
        })

    # Write to a JSON file
    try:
        with open('archived_feedback.json', 'a') as f:
            json.dump(archived_feedbacks, f, default=str, indent=4)
            f.write('\n')  # Newline between each entry
    except Exception as e:
        return jsonify({"error": f"Error writing to JSON file: {str(e)}"}), 500

    # Prepare feedback comments for CSV archiving
    archived_feedback_csv = [
        [
            feedback.id,
            feedback.category,
            feedback.description,
            feedback.resolved_status,
            feedback.priority_level,
            feedback.related_section,
            feedback.assigned_to,
            feedback.created_date,
            feedback.last_updated_date
        ]
        for feedback in old_feedbacks
    ]

    # Write to a CSV file
    try:
        with open('archived_feedback.csv', 'a', newline='') as f:
            writer = csv.writer(f)
            # If it's the first time writing to the file, write the header
            if f.tell() == 0:
                writer.writerow(['ID', 'Category', 'Description', 'Resolved Status', 'Priority Level', 'Related Section', 'Assigned To', 'Created Date', 'Last Updated Date'])
            # Write each feedback to the CSV
            writer.writerows(archived_feedback_csv)
    except Exception as e:
        return jsonify({"error": f"Error writing to CSV file: {str(e)}"}), 500

    return jsonify({"message": "Old feedback comments archived successfully."}), 200


    





