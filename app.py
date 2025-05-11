from flask import Flask, render_template
import json
import os

app = Flask(__name__)

# Ścieżka do pliku JSON
DB_FILE = os.path.join(os.path.dirname(__file__), "projects_db.json")

# Funkcja wczytująca projekty z JSON
def load_projects_from_json():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

@app.route('/')
def index():
    projects = load_projects_from_json()
    return render_template('index.html', projects=projects)

if __name__ == '__main__':
    app.run(debug=True)