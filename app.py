# Importing the necessary modules from Flask
from flask import Flask, render_template
from extensions import db
from flask_bootstrap import Bootstrap
from feedback import feedback_bp
import os

# Create a Flask application and specify the template folder
app = Flask(__name__, static_folder='static')

# Set the secret key to enable flash functionality
app.secret_key = 'supersecretkey'

# Initialising Flask-Bootstrap to manage the layout and components
bootstrap = Bootstrap(app)

# Setting up the database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///your_database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialise the database with the app
db.init_app(app)

# Register the Feedback Blueprint with a URL prefix
app.register_blueprint(feedback_bp, url_prefix='/feedback')

@app.route('/')
def home():
    return render_template('base.html')

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
