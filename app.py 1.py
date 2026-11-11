import pandas as pd
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify, send_file
from flask_wtf.csrf import CSRFProtect
from database import get_db_connection
from analysis.data_analysis import main, generate_charts
from datetime import datetime, date, timedelta
import os
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from export import (
    generate_export,
    generate_dashboard_export,
    generate_demographics_export,
    generate_reports_export
)
app = Flask(__name__)

secret_key = os.environ.get("FLASK_SECRET_KEY")

if os.environ.get("RENDER") and not secret_key:
    raise RuntimeError("FLASK_SECRET_KEY must be configured.")

app.secret_key = secret_key or "dev-only-change-this"

app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=bool(os.environ.get("RENDER"))
)

csrf = CSRFProtect(app)
# Protect pages that require login
def login_required(route_function):
    @wraps(route_function)
    def wrapper(*args, **kwargs):
        if not session.get("logged_in"):
            flash("Please sign in to access this page.", "error")
            return redirect(url_for("login"))

        return route_function(*args, **kwargs)

    return wrapper
# Home page
@app.route("/")
def home():
    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute("SELECT COUNT(*) AS total_patients FROM patients")
        total_patients = cursor.fetchone()["total_patients"]

        cursor.execute("SELECT COUNT(*) AS total_visits FROM visits")
        total_visits = cursor.fetchone()["total_visits"]

        cursor.execute("SELECT COUNT(*) AS total_departments FROM departments")
        total_departments = cursor.fetchone()["total_departments"]

        return render_template(
            "index.html",
            total_patients=total_patients,
            total_visits=total_visits,
            total_departments=total_departments
        )

    finally:
        if cursor is not None:
            cursor.close()

        if connection is not None and connection.is_connected():
            connection.close()

# Patient records page
@app.route("/patients")
@login_required
def patients():
    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute("""
            SELECT patient_id, age_band, gender_optional
            FROM patients
            ORDER BY patient_id
        """)

        patients = cursor.fetchall()

        return render_template(
            "patients.html",
            patients=patients
        )

    finally:
        if cursor is not None:
            cursor.close()

        if connection is not None and connection.is_connected():
            connection.close()

# Add a new patient
@app.route("/add_patient", methods=["POST"])
@login_required
def add_patient():
    age_band = request.form.get("age_band", "").strip()
    gender = request.form.get("gender_optional", "").strip()

    allowed_age_bands = {"0-17", "18-35", "36-59", "60+"}
    allowed_genders = {"", "Female", "Male", "Other"}

    if age_band not in allowed_age_bands:
        flash("Please select a valid age group.", "error")
        return redirect(url_for("patients"))

    if gender not in allowed_genders:
        flash("Please select a valid gender option.", "error")
        return redirect(url_for("patients"))

    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute(
            """
            INSERT INTO patients (age_band, gender_optional)
            VALUES (%s, %s)
            """,
            (age_band, gender or None)
        )

        connection.commit()
        flash("Patient record added successfully!", "success")

    except Exception:
        if connection is not None:
            connection.rollback()

        app.logger.exception("Failed to add patient.")
        flash("Could not add the patient record. Please try again.", "error")

    finally:
        if cursor is not None:
            cursor.close()

        if connection is not None and connection.is_connected():
            connection.close()

    return redirect(url_for("patients"))
# Update an existing patient
@app.route("/edit_patient/<int:patient_id>", methods=["GET", "POST"])
@login_required
def edit_patient(patient_id):

    allowed_age_bands = {"0-17", "18-35", "36-59", "60+"}
    allowed_genders = {"", "Female", "Male", "Other"}

    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        if request.method == "POST":
            age_band = request.form.get("age_band", "").strip()
            gender = request.form.get("gender_optional", "").strip()

            if age_band not in allowed_age_bands:
                flash("Please select a valid age group.", "error")
                return redirect(url_for("edit_patient", patient_id=patient_id))

            if gender not in allowed_genders:
                flash("Please select a valid gender.", "error")
                return redirect(url_for("edit_patient", patient_id=patient_id))

            cursor.execute("""
                UPDATE patients
                SET age_band = %s, gender_optional = %s
                WHERE patient_id = %s
            """, (age_band, gender or None, patient_id))

            connection.commit()

            flash("Patient record updated successfully!", "success")
            return redirect(url_for("patients"))

        cursor.execute("""
            SELECT patient_id, age_band, gender_optional
            FROM patients
            WHERE patient_id = %s
        """, (patient_id,))

        patient = cursor.fetchone()

        if patient is None:
            flash("Patient record not found.", "error")
            return redirect(url_for("patients"))

        return render_template("edit_patient.html", patient=patient)

    except Exception:
        if connection is not None:
            connection.rollback()

        app.logger.exception("Failed to update patient.")
        flash("Unable to update patient record.", "error")
        return redirect(url_for("patients"))

    finally:
        if cursor is not None:
            cursor.close()

        if connection is not None and connection.is_connected():
            connection.close()

# Delete a patient
@app.route("/delete_patient/<int:patient_id>", methods=["POST"])
@login_required
def delete_patient(patient_id):

    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute("""
            SELECT patient_id
            FROM patients
            WHERE patient_id = %s
        """, (patient_id,))

        patient = cursor.fetchone()

        if patient is None:
            flash("Patient record not found.", "error")
            return redirect(url_for("patients"))

        cursor.execute("""
            SELECT COUNT(*) AS visit_count
            FROM visits
            WHERE patient_id = %s
        """, (patient_id,))

        visit_count = cursor.fetchone()["visit_count"]

        if visit_count > 0:
            flash(
                "This patient has recorded visits and cannot be deleted.",
                "error"
            )
            return redirect(url_for("patients"))

        cursor.execute("""
            DELETE FROM patients
            WHERE patient_id = %s
        """, (patient_id,))

        connection.commit()

        flash("Patient record deleted successfully!", "success")

    except Exception:
        if connection is not None:
            connection.rollback()

        app.logger.exception("Failed to delete patient.")
        flash("Unable to delete patient record.", "error")

    finally:
        if cursor is not None:
            cursor.close()

        if connection is not None and connection.is_connected():
            connection.close()

    return redirect(url_for("patients"))
@app.route('/export/patients/<file_format>')
@login_required
def export_patients(file_format):

    if file_format not in ['excel', 'pdf', 'word']:
        flash("Invalid export format.", "danger")
        return redirect(url_for('patients'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT
                patient_id,
                age_band,
                gender_optional
            FROM patients
            ORDER BY patient_id
        """)

        data = cursor.fetchall()

        columns = [
            ('patient_id', 'Patient ID'),
            ('age_band', 'Age Group'),
            ('gender_optional', 'Gender')
        ]

        buffer, extension = generate_export(
            data,
            columns,
            "Patient Records",
            file_format
        )

        return send_file(
            buffer,
            as_attachment=True,
            download_name=f"patient_records.{extension}",
            mimetype={
                'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                'pdf': 'application/pdf',
                'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            }[extension]
        )

    finally:
        cursor.close()
        conn.close()
@app.route('/export/visits/<file_format>')
@login_required
def export_visits(file_format):

    if file_format not in ['excel', 'pdf', 'word']:
        flash("Invalid export format.", "error")
        return redirect(url_for('visits'))

    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute("""
            SELECT
                v.visit_id,
                v.patient_id,
                d.department_name,
                v.visit_date,
                v.visit_type
            FROM visits v
            JOIN departments d
                ON v.department_id = d.department_id
            ORDER BY v.visit_date DESC, v.visit_id DESC
        """)

        data = cursor.fetchall()

        columns = [
            ('visit_id', 'Visit ID'),
            ('patient_id', 'Patient ID'),
            ('department_name', 'Department'),
            ('visit_date', 'Visit Date'),
            ('visit_type', 'Visit Type')
        ]

        buffer, extension = generate_export(
            data,
            columns,
            "Visit Records",
            file_format
        )

        return send_file(
            buffer,
            as_attachment=True,
            download_name=f"visit_records.{extension}",
            mimetype={
                'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                'pdf': 'application/pdf',
                'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            }[extension]
        )

    except Exception:
        app.logger.exception("Failed to export visit records.")
        flash("Unable to export visit records.", "error")
        return redirect(url_for('visits'))

    finally:
        if cursor is not None:
            cursor.close()

        if connection is not None and connection.is_connected():
            connection.close()

# Hospital visits page
@app.route("/visits")
@login_required
def visits():
    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute("""
            SELECT
                v.visit_id,
                v.patient_id,
                v.department_id,
                d.department_name,
                v.visit_date,
                v.visit_type
            FROM visits v
            JOIN departments d
                ON v.department_id = d.department_id
            ORDER BY v.visit_date DESC, v.visit_id DESC
        """)

        visits = cursor.fetchall()
        # Fetch patients for the Add Visit form
        cursor.execute("""
            SELECT patient_id
            FROM patients
            ORDER BY patient_id
        """)
        patients = cursor.fetchall()

        # Fetch departments for the Add Visit form
        cursor.execute("""
            SELECT department_id, department_name
            FROM departments
            ORDER BY department_name
        """)
        departments = cursor.fetchall()

        return render_template(
            "visits.html",
            visits=visits,
            patients=patients,
            departments=departments
        )

    finally:
        if cursor is not None:
            cursor.close()

        if connection is not None and connection.is_connected():
            connection.close()
@app.route("/add_visit", methods=["POST"])
@login_required
def add_visit():
    patient_id = request.form.get("patient_id", "").strip()
    department_id = request.form.get("department_id", "").strip()
    visit_date = request.form.get("visit_date", "").strip()
    visit_type = request.form.get("visit_type", "").strip()

    allowed_visit_types = {"Check-up", "Consultation", "Follow-up"}

    if (
        not patient_id.isdigit()
        or not department_id.isdigit()
        or not visit_date
        or visit_type not in allowed_visit_types
    ):
        flash("Please enter valid visit details.", "error")
        return redirect(url_for("visits"))
    try:
        parsed_date = datetime.strptime(visit_date, "%Y-%m-%d").date()

        if parsed_date > datetime.now().date():
            flash("Visit date cannot be in the future.", "error")
            return redirect(url_for("visits"))

    except ValueError:
        flash("Please enter a valid visit date.", "error")
        return redirect(url_for("visits"))

    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        # Verify patient exists
        cursor.execute(
            "SELECT patient_id FROM patients WHERE patient_id = %s",
            (int(patient_id),)
        )

        if cursor.fetchone() is None:
            flash("Selected patient does not exist.", "error")
            return redirect(url_for("visits"))

        # Verify department exists
        cursor.execute(
            "SELECT department_id FROM departments WHERE department_id = %s",
            (int(department_id),)
        )

        if cursor.fetchone() is None:
            flash("Selected department does not exist.", "error")
            return redirect(url_for("visits"))

        cursor.execute("""
            INSERT INTO visits
            (patient_id, department_id, visit_date, visit_type)
            VALUES (%s, %s, %s, %s)
        """, (
            int(patient_id),
            int(department_id),
            visit_date,
            visit_type
        ))

        connection.commit()
        flash("Visit record added successfully!", "success")

    except Exception:
        if connection is not None:
            connection.rollback()

        app.logger.exception("Error adding visit")
        flash("Unable to add visit record. Please try again.", "error")

    finally:
        if cursor is not None:
            cursor.close()

        if connection is not None and connection.is_connected():
            connection.close()

    return redirect(url_for("visits"))
@app.route("/edit_visit/<int:visit_id>", methods=["POST"])
@login_required
def edit_visit(visit_id):

    patient_id = request.form.get("patient_id", "").strip()
    department_id = request.form.get("department_id", "").strip()
    visit_date = request.form.get("visit_date", "").strip()
    visit_type = request.form.get("visit_type", "").strip()

    allowed_visit_types = {"Check-up", "Consultation", "Follow-up"}

    if (not patient_id.isdigit() or
        not department_id.isdigit() or
        not visit_date or
        visit_type not in allowed_visit_types):

        flash("Please enter valid visit details.", "error")
        return redirect(url_for("visits"))

    try:
        parsed_date = datetime.strptime(visit_date, "%Y-%m-%d").date()

        if parsed_date > datetime.now().date():
            flash("Visit date cannot be in the future.", "error")
            return redirect(url_for("visits"))

    except ValueError:
        flash("Please enter a valid visit date.", "error")
        return redirect(url_for("visits"))

    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        # Verify patient exists
        cursor.execute(
            "SELECT patient_id FROM patients WHERE patient_id = %s",
            (int(patient_id),)
        )

        if cursor.fetchone() is None:
            flash("Selected patient does not exist.", "error")
            return redirect(url_for("visits"))

        # Verify department exists
        cursor.execute(
            "SELECT department_id FROM departments WHERE department_id = %s",
            (int(department_id),)
        )

        if cursor.fetchone() is None:
            flash("Selected department does not exist.", "error")
            return redirect(url_for("visits"))

        cursor.execute("""
            SELECT visit_id FROM visits WHERE visit_id = %s
        """, (visit_id,))

        if cursor.fetchone() is None:
            flash("Visit record not found.", "error")
            return redirect(url_for("visits"))

        cursor.execute("""
            UPDATE visits
            SET patient_id = %s,
                department_id = %s,
                visit_date = %s,
                visit_type = %s
            WHERE visit_id = %s
        """, (
            int(patient_id),
            int(department_id),
            visit_date,
            visit_type,
            visit_id
        ))

        connection.commit()
        flash("Visit record updated successfully!", "success")

    except Exception:
        if connection is not None:
            connection.rollback()

        app.logger.exception("Failed to update visit.")
        flash("Unable to update visit record.", "error")

    finally:
        if cursor is not None:
            cursor.close()

        if connection is not None and connection.is_connected():
            connection.close()

    return redirect(url_for("visits"))
@app.route("/delete_visit/<int:visit_id>", methods=["POST"])
@login_required
def delete_visit(visit_id):

    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute("""
            DELETE FROM visits
            WHERE visit_id = %s
        """, (visit_id,))

        if cursor.rowcount == 0:
            flash("Visit record not found.", "error")
        else:
            connection.commit()
            flash("Visit record deleted successfully!", "success")

    except Exception:
        if connection is not None:
            connection.rollback()

        app.logger.exception("Failed to delete visit.")
        flash("Unable to delete visit record.", "error")

    finally:
        if cursor is not None:
            cursor.close()

        if connection is not None and connection.is_connected():
            connection.close()

    return redirect(url_for("visits"))

# Analytics dashboard
@app.route("/dashboard")
@login_required
def dashboard():
    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute("SELECT COUNT(*) AS total_patients FROM patients")
        total_patients = cursor.fetchone()["total_patients"]

        cursor.execute("SELECT COUNT(*) AS total_visits FROM visits")
        total_visits = cursor.fetchone()["total_visits"]

        cursor.execute("SELECT COUNT(*) AS total_departments FROM departments")
        total_departments = cursor.fetchone()["total_departments"]

        cursor.execute("""
            SELECT department_id, department_name
            FROM departments
            ORDER BY department_name
        """)

        departments = cursor.fetchall()

        return render_template(
            "dashboard.html",
            total_patients=total_patients,
            total_visits=total_visits,
            total_departments=total_departments,
            departments=departments
        )

    finally:
        if cursor is not None:
            cursor.close()

        if connection is not None and connection.is_connected():
            connection.close()

# API for dynamically updating dashboard charts
@app.route("/api/dashboard-charts")
@login_required
def dashboard_charts():

    period = request.args.get("period", "3m")
    department_id = request.args.get("department", "all")

    today = date.today()

    # Calculate selected date range
    if period == "7d":
        start_date = today - timedelta(days=6)
        end_date = today

    elif period == "30d":
        start_date = today - timedelta(days=29)
        end_date = today

    elif period == "3m":
        start_date = today - timedelta(days=89)
        end_date = today

    elif period == "custom":
        try:
            start_date = datetime.strptime(
                request.args.get("start_date", ""),
                "%Y-%m-%d"
            ).date()

            end_date = datetime.strptime(
                request.args.get("end_date", ""),
                "%Y-%m-%d"
            ).date()

        except ValueError:
            return jsonify({"error": "Please select valid dates."}), 400

        if start_date > end_date:
            return jsonify({"error": "Start date cannot be after end date."}), 400

        if end_date > today:
            return jsonify({"error": "End date cannot be in the future."}), 400

    else:
        return jsonify({"error": "Invalid time period selected."}), 400

    if department_id != "all" and not department_id.isdigit():
        return jsonify({"error": "Invalid department selected."}), 400

    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        query = """
            SELECT
                v.visit_id,
                v.visit_date,
                v.visit_type,
                d.department_name,
                p.age_band,
                p.gender_optional
            FROM visits v
            JOIN departments d
                ON v.department_id = d.department_id
            JOIN patients p
                ON v.patient_id = p.patient_id
            WHERE v.visit_date >= %s
              AND v.visit_date < %s
        """

        params = [
            start_date,
            end_date + timedelta(days=1)
        ]

        if department_id != "all":
            query += " AND d.department_id = %s"
            params.append(int(department_id))

        cursor.execute(query, tuple(params))

        records = cursor.fetchall()

        import pandas as pd

        df = pd.DataFrame(records)

        if not df.empty:
            df["visit_date"] = pd.to_datetime(df["visit_date"])

        charts = generate_charts(df, start_date, end_date)
        print("Chart keys:", list(charts.keys()) if charts else charts)

        return jsonify({
            "charts": charts,
            "filtered_visits": len(df)
        })

    except Exception:
        app.logger.exception("Dashboard chart generation failed.")
        return jsonify({
            "error": "Unable to generate dashboard charts."
        }), 500

    finally:
        if cursor is not None:
            cursor.close()

        if connection is not None and connection.is_connected():
            connection.close()
@app.route('/export/dashboard/<file_format>')
@login_required
def export_dashboard(file_format):

    if file_format not in ['excel', 'pdf', 'word']:
        flash("Invalid export format.", "error")
        return redirect(url_for('dashboard'))

    period = request.args.get("period", "3m")
    department_id = request.args.get("department", "all")
    today = date.today()

    # Date filter
    if period == "7d":
        start_date = today - timedelta(days=6)
        end_date = today

    elif period == "30d":
        start_date = today - timedelta(days=29)
        end_date = today

    elif period == "3m":
        start_date = today - timedelta(days=89)
        end_date = today

    elif period == "custom":
        try:
            start_date = datetime.strptime(
                request.args.get("start_date", ""), "%Y-%m-%d"
            ).date()

            end_date = datetime.strptime(
                request.args.get("end_date", ""), "%Y-%m-%d"
            ).date()

        except ValueError:
            flash("Please select valid dates.", "error")
            return redirect(url_for('dashboard'))

        if start_date > end_date or end_date > today:
            flash("Please select a valid date range.", "error")
            return redirect(url_for('dashboard'))

    else:
        flash("Invalid time period selected.", "error")
        return redirect(url_for('dashboard'))

    if department_id != "all" and not department_id.isdigit():
        flash("Invalid department selected.", "error")
        return redirect(url_for('dashboard'))

    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        # Overall dashboard statistics
        cursor.execute("SELECT COUNT(*) AS total FROM patients")
        total_patients = cursor.fetchone()["total"]

        cursor.execute("SELECT COUNT(*) AS total FROM visits")
        total_visits = cursor.fetchone()["total"]

        cursor.execute("SELECT COUNT(*) AS total FROM departments")
        total_departments = cursor.fetchone()["total"]

        # Department name
        department_name = "All Departments"

        if department_id != "all":
            cursor.execute(
                "SELECT department_name FROM departments WHERE department_id = %s",
                (int(department_id),)
            )

            department = cursor.fetchone()

            if department is None:
                flash("Department not found.", "error")
                return redirect(url_for('dashboard'))

            department_name = department["department_name"]

        # Fetch filtered visit records
        query = """
            SELECT
                v.visit_id,
                v.patient_id,
                d.department_name,
                v.visit_date,
                v.visit_type,
                p.age_band,
                p.gender_optional
            FROM visits v
            JOIN departments d ON v.department_id = d.department_id
            JOIN patients p ON v.patient_id = p.patient_id
            WHERE v.visit_date >= %s
              AND v.visit_date < %s
        """

        params = [start_date, end_date + timedelta(days=1)]

        if department_id != "all":
            query += " AND d.department_id = %s"
            params.append(int(department_id))

        query += " ORDER BY v.visit_date DESC, v.visit_id DESC"

        cursor.execute(query, tuple(params))
        records = cursor.fetchall()

        columns = [
            "visit_id",
            "patient_id",
            "department_name",
            "visit_date",
            "visit_type",
            "age_band",
            "gender_optional"
        ]

        df = pd.DataFrame(records, columns=columns)

        if not df.empty:
            df["visit_date"] = pd.to_datetime(df["visit_date"])

        # Generate charts using the existing analysis function
        charts = generate_charts(df, start_date, end_date)

        summary = {
            "Total Patients": total_patients,
            "Total Visits": total_visits,
            "Total Departments": total_departments,
            "Filtered Visits": len(df)
        }

        filters = {
            "period": {
                "7d": "Last 7 Days",
                "30d": "Last 30 Days",
                "3m": "Last 3 Months",
                "custom": "Custom Range"
            }[period],
            "department": department_name,
            "start_date": start_date,
            "end_date": end_date
        }

        buffer, extension = generate_dashboard_export(
            summary,
            df,
            charts,
            "MediTrack Dashboard Report",
            filters,
            file_format
        )

        mimetypes = {
            "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "pdf": "application/pdf",
            "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        }

        return send_file(
            buffer,
            as_attachment=True,
            download_name=f"dashboard_report.{extension}",
            mimetype=mimetypes[extension]
        )

    except Exception:
        app.logger.exception("Dashboard export failed.")
        flash("Unable to export dashboard report.", "error")
        return redirect(url_for('dashboard'))

    finally:
        if cursor is not None:
            cursor.close()

        if connection is not None and connection.is_connected():
            connection.close()

# Patient demographics page
@app.route("/demographics")
@login_required
def demographics():
    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        # Patient distribution by age group
        cursor.execute("""
            SELECT age_band, COUNT(*) AS patient_count
            FROM patients
            GROUP BY age_band
            ORDER BY age_band
        """)
        age_distribution = cursor.fetchall()

        # Patient distribution by gender
        cursor.execute("""
            SELECT
                COALESCE(NULLIF(gender_optional, ''), 'Not specified') AS gender,
                COUNT(*) AS patient_count
            FROM patients
            GROUP BY gender
            ORDER BY gender
        """)
        gender_distribution = cursor.fetchall()

        # Total registered patients
        cursor.execute("SELECT COUNT(*) AS total FROM patients")
        total_patients = cursor.fetchone()["total"]

        return render_template(
            "demographics.html",
            age_distribution=age_distribution,
            gender_distribution=gender_distribution,
            total_patients=total_patients
        )

    finally:
        if cursor is not None:
            cursor.close()

        if connection is not None and connection.is_connected():
            connection.close()

@app.route('/export/demographics/<file_format>')
@login_required
def export_demographics(file_format):

    if file_format not in ['excel', 'pdf', 'word']:
        flash("Invalid export format.", "error")
        return redirect(url_for('demographics'))

    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        # Total registered patients
        cursor.execute("SELECT COUNT(*) AS total FROM patients")
        total_patients = cursor.fetchone()["total"]

        # Age-group distribution
        cursor.execute("""
            SELECT
                age_band,
                COUNT(*) AS patient_count
            FROM patients
            GROUP BY age_band
            ORDER BY FIELD(age_band, '0-17', '18-35', '36-59', '60+')
        """)

        age_distribution = cursor.fetchall()

        # Gender distribution
        cursor.execute("""
            SELECT
                COALESCE(gender_optional, 'Unspecified') AS gender,
                COUNT(*) AS patient_count
            FROM patients
            GROUP BY gender_optional
            ORDER BY gender
        """)

        gender_distribution = cursor.fetchall()

        # Generate export
        buffer, extension = generate_demographics_export(
            total_patients,
            age_distribution,
            gender_distribution,
            file_format
        )

        mimetypes = {
            "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "pdf": "application/pdf",
            "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        }

        return send_file(
            buffer,
            as_attachment=True,
            download_name=f"patient_demographics.{extension}",
            mimetype=mimetypes[extension]
        )

    except Exception:
        app.logger.exception("Demographics export failed.")
        flash("Unable to export demographics report.", "error")
        return redirect(url_for('demographics'))

    finally:
        if cursor is not None:
            cursor.close()

        if connection is not None and connection.is_connected():
            connection.close()

# Reports page
@app.route("/reports")
@login_required
def reports():
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        # Overall statistics
        cursor.execute("""
            SELECT
                (SELECT COUNT(*) FROM patients) AS total_patients,
                (SELECT COUNT(*) FROM visits) AS total_visits,
                (SELECT COUNT(*) FROM departments) AS total_departments
        """)
        summary = cursor.fetchone()

        # Department-wise visit counts
        cursor.execute("""
            SELECT
                d.department_name,
                COUNT(v.visit_id) AS visit_count
            FROM departments d
            LEFT JOIN visits v
                ON d.department_id = v.department_id
            GROUP BY d.department_id, d.department_name
            ORDER BY visit_count DESC, d.department_name
        """)
        department_reports = cursor.fetchall()

        # Monthly visit counts
        cursor.execute("""
            SELECT
                DATE_FORMAT(MIN(visit_date), '%b %Y') AS month,
                COUNT(*) AS visit_count
            FROM visits
            GROUP BY YEAR(visit_date), MONTH(visit_date)
            ORDER BY YEAR(visit_date), MONTH(visit_date)
        """)

        monthly_reports = cursor.fetchall()

        # Daily visit counts for the latest 14 dates with recorded visits
        cursor.execute("""
            SELECT
                visit_date,
                COUNT(*) AS visit_count
            FROM visits
            GROUP BY visit_date
            ORDER BY visit_date DESC
            LIMIT 14
        """)
        daily_reports = cursor.fetchall()
        daily_reports.reverse()

        return render_template(
            "reports.html",
            summary=summary,
            department_reports=department_reports,
            monthly_reports=monthly_reports,
            daily_reports=daily_reports,
            now=datetime.now()
        )

    finally:
        if cursor is not None:
            cursor.close()

        if connection is not None and connection.is_connected():
            connection.close()

@app.route('/export/reports/<file_format>')
@login_required
def export_reports(file_format):

    if file_format not in ['excel', 'word']:
        flash("Invalid export format.", "error")
        return redirect(url_for('reports'))

    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        # Overall summary
        cursor.execute("""
            SELECT
                (SELECT COUNT(*) FROM patients) AS total_patients,
                (SELECT COUNT(*) FROM visits) AS total_visits,
                (SELECT COUNT(*) FROM departments) AS total_departments
        """)
        summary = cursor.fetchone()

        # Department-wise reports
        cursor.execute("""
            SELECT
                d.department_name,
                COUNT(v.visit_id) AS visit_count
            FROM departments d
            LEFT JOIN visits v
                ON d.department_id = v.department_id
            GROUP BY d.department_id, d.department_name
            ORDER BY d.department_name
        """)
        department_reports = cursor.fetchall()

        # Monthly reports
        cursor.execute("""
            SELECT
                DATE_FORMAT(visit_date, '%b %Y') AS month,
                COUNT(*) AS visit_count
            FROM visits
            GROUP BY YEAR(visit_date), MONTH(visit_date)
            ORDER BY YEAR(visit_date), MONTH(visit_date)
        """)
        monthly_reports = cursor.fetchall()

        # Daily reports (latest 14 days with recorded visits)
        cursor.execute("""
            SELECT
                visit_date,
                COUNT(*) AS visit_count
            FROM visits
            GROUP BY visit_date
            ORDER BY visit_date DESC
            LIMIT 14
        """)
        daily_reports = cursor.fetchall()
        daily_reports.reverse()

        report_date = datetime.now().strftime('%d %B %Y')

        buffer, extension = generate_reports_export(
            summary,
            department_reports,
            monthly_reports,
            daily_reports,
            report_date,
            file_format
        )

        mimetypes = {
            "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        }

        return send_file(
            buffer,
            as_attachment=True,
            download_name=f"hospital_reports.{extension}",
            mimetype=mimetypes[extension]
        )

    except Exception:
        app.logger.exception("Reports export failed.")
        flash("Unable to export hospital reports.", "error")
        return redirect(url_for('reports'))

    finally:
        if cursor is not None:
            cursor.close()

        if connection is not None and connection.is_connected():
            connection.close()

# Account registration
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        # Validate form fields
        if not username or not email or not password:
            flash("Please fill in all required fields.", "error")
            return render_template("register.html")

        if len(username) < 3 or len(username) > 50:
            flash("Username must contain 3–50 characters.", "error")
            return render_template("register.html")

        if len(password) < 8:
            flash("Password must contain at least 8 characters.", "error")
            return render_template("register.html")

        if password != confirm_password:
            flash("Passwords do not match.", "error")
            return render_template("register.html")

        connection = None
        cursor = None

        try:
            connection = get_db_connection()
            cursor = connection.cursor(dictionary=True)

            # Check whether username or email already exists
            cursor.execute(
                """
                SELECT user_id
                FROM users
                WHERE username = %s OR email = %s
                """,
                (username, email)
            )

            if cursor.fetchone():
                flash("That username or email is already registered.", "error")
                return render_template("register.html")

            # Hash the password before saving
            password_hash = generate_password_hash(password)

            cursor.execute(
                """
                INSERT INTO users (username, email, password_hash)
                VALUES (%s, %s, %s)
                """,
                (username, email, password_hash)
            )

            connection.commit()

            flash("Account created successfully! Please sign in.", "success")
            return redirect(url_for("login"))

        except Exception:
            if connection is not None:
                connection.rollback()

            app.logger.exception("Account registration failed.")
            flash("Unable to create your account right now. Please try again.", "error")

        finally:
            if cursor is not None:
                cursor.close()

            if connection is not None and connection.is_connected():
                connection.close()

    return render_template("register.html")

# Login page
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        connection = None
        cursor = None

        try:
            connection = get_db_connection()
            cursor = connection.cursor(dictionary=True)

            cursor.execute(
                """
                SELECT user_id, username, password_hash
                FROM users
                WHERE username = %s
                """,
                (username,)
            )

            user = cursor.fetchone()

            if user and check_password_hash(user["password_hash"], password):
                session.clear()
                session["logged_in"] = True
                session["user_id"] = user["user_id"]
                session["username"] = user["username"]

                return redirect(url_for("home"))

            flash("Invalid username or password.", "error")

        except Exception:
            app.logger.exception("Login failed.")
            flash("Unable to sign in right now. Please try again.", "error")

        finally:
            if cursor is not None:
                cursor.close()

            if connection is not None and connection.is_connected():
                connection.close()

    return render_template("login.html")

@app.route("/logout", methods=["POST"])
@login_required
def logout():
    session.clear()
    flash("You have been logged out successfully.", "success")
    return redirect(url_for("login"))

# User profile page

@app.route("/profile")
@login_required
def profile():
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT username, email, created_at
            FROM users
            WHERE user_id = %s
            """,
            (session["user_id"],)
        )

        user = cursor.fetchone()

        if user is None:
            session.clear()
            flash("Please sign in again.", "error")
            return redirect(url_for("login"))

        return render_template("profile.html", user=user)

    except Exception:
        app.logger.exception("Could not load profile.")
        flash("Unable to load your profile. Please try again.", "error")
        return redirect(url_for("home"))

    finally:
        if cursor is not None:
            cursor.close()

        if connection is not None and connection.is_connected():
            connection.close()

print(app.url_map)
# Run the application
if __name__ == "__main__":
    app.run(debug=False)