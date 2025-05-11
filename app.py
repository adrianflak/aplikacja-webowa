from flask import Flask, render_template, request, redirect, url_for
import json
import os
import re

app = Flask(__name__)

# Ścieżka do pliku JSON
DB_FILE = os.path.join(os.path.dirname(__file__), "data", "projects_db.json")


# Funkcja wczytująca projekty z JSON
def load_projects_from_json():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


# Funkcja zapisująca projekty do JSON
def save_projects_to_json(projects):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(projects, f, ensure_ascii=False, indent=4)


def _compare_features(cechy1, cechy2, all_features):
    """Porównuje cechy dwóch projektów."""
    matches = 0
    differences = []
    for feature in all_features:
        if feature in cechy1 and feature in cechy2:
            val1, val2 = cechy1[feature], cechy2[feature]
            val1_str, val2_str = str(val1), str(val2)
            if feature in ["Średnica Tłoka", "Skok Siłownika"]:
                match1, match2 = re.search(r"\d+", val1_str), re.search(r"\d+", val2_str)
                if match1 and match2 and float(match1.group()) == float(match2.group()):
                    matches += 1
                else:
                    differences.append(f"{feature}: {val1} vs {val2}")
            elif val1 == val2:
                matches += 1
            else:
                differences.append(f"{feature}: {val1} vs {val2}")
        else:
            differences.append(
                f"{feature}: {'Brak' if feature not in cechy1 else cechy1[feature]} vs {'Brak' if feature not in cechy2 else cechy2[feature]}")
    return matches, differences


def _filter_projects(projects, filters):
    """Filtruje projekty na podstawie podanych kryteriów."""
    filtered = {}
    for symbol, details in projects.items():
        matches = True
        cechy = details.get("Cechy", {})
        for feature, value in filters.items():
            if not value:
                continue
            if feature not in cechy:
                matches = False
                break
            if feature in ["Średnica Tłoka", "Skok Siłownika"]:
                match = re.search(r"\d+", cechy[feature])
                if not match or float(match.group()) != float(value):
                    matches = False
                    break
            elif cechy[feature].lower() != value.lower():
                matches = False
                break
        if matches:
            filtered[symbol] = details
    return filtered


@app.route('/')
def index():
    projects = load_projects_from_json()
    return render_template('index.html', projects=projects)


@app.route('/project/<symbol>')
def project_details(symbol):
    projects = load_projects_from_json()
    project = projects.get(symbol)
    if not project:
        return render_template('error.html', message="Projekt nie znaleziony"), 404
    return render_template('project_details.html', project=project, symbol=symbol)


@app.route('/compare', methods=['GET', 'POST'])
def compare_projects():
    projects = load_projects_from_json()
    if not projects or len(projects) < 2:
        return render_template('error.html', message="Potrzebne są co najmniej 2 projekty do porównania"), 400

    if request.method == 'POST':
        proj1 = request.form.get('proj1')
        proj2 = request.form.get('proj2')

        if not proj1 or not proj2:
            return render_template('compare.html', projects=projects, error="Wybierz dwa projekty"), 400
        if proj1 == proj2:
            return render_template('compare.html', projects=projects, error="Wybierz dwa różne projekty"), 400
        if proj1 not in projects or proj2 not in projects:
            return render_template('compare.html', projects=projects, error="Wybrane projekty nie istnieją"), 400

        cechy1, cechy2 = projects[proj1]["Cechy"], projects[proj2]["Cechy"]
        all_features = set(cechy1.keys()).union(cechy2.keys())
        matches, differences = _compare_features(cechy1, cechy2, all_features)
        similarity = (matches / len(all_features)) * 100 if all_features else 0

        return render_template('compare.html',
                               projects=projects,
                               proj1=proj1,
                               proj2=proj2,
                               similarity=similarity,
                               differences=differences,
                               proj1_name=projects[proj1]["Nazwa"],
                               proj2_name=projects[proj2]["Nazwa"],
                               proj1_id=projects[proj1]["ID"],
                               proj2_id=projects[proj2]["ID"])

    return render_template('compare.html', projects=projects)


@app.route('/filter', methods=['GET', 'POST'])
def filter_projects():
    projects = load_projects_from_json()
    if not projects:
        return render_template('error.html', message="Brak projektów do filtrowania"), 400

    available_features = ["Średnica Tłoka", "Skok Siłownika", "Tłok Magnetyczny"]

    if request.method == 'POST':
        filters = {}
        for feature in available_features:
            value = request.form.get(feature)
            if value:
                filters[feature] = value
        filtered_projects = _filter_projects(projects, filters)
        return render_template('filter.html',
                               projects=projects,
                               filtered_projects=filtered_projects,
                               available_features=available_features,
                               filters=filters)

    return render_template('filter.html',
                           projects=projects,
                           filtered_projects=projects,
                           available_features=available_features)


@app.route('/add_project', methods=['GET', 'POST'])
def add_project():
    projects = load_projects_from_json()
    available_features = ["Średnica Tłoka", "Skok Siłownika", "Tłok Magnetyczny"]

    if request.method == 'POST':
        symbol = request.form.get('symbol')
        nazwa = request.form.get('nazwa')
        id_proj = request.form.get('id')

        if not symbol or not nazwa or not id_proj:
            return render_template('add_project.html',
                                   available_features=available_features,
                                   error="Wszystkie pola (symbol, nazwa, ID) są wymagane"), 400

        if symbol in projects:
            return render_template('add_project.html',
                                   available_features=available_features,
                                   error="Projekt o podanym symbolu już istnieje"), 400

        cechy = {}
        for feature in available_features:
            value = request.form.get(feature)
            if value:
                cechy[feature] = value

        projects[symbol] = {
            "Nazwa": nazwa,
            "ID": id_proj,
            "Cechy": cechy
        }

        save_projects_to_json(projects)
        return redirect(url_for('index'))

    return render_template('add_project.html', available_features=available_features)


if __name__ == '__main__':
    app.run(debug=True)