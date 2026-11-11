import os
import sys
import base64
from io import BytesIO
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import mysql.connector

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(PROJECT_ROOT)

from database import get_db_connection

CHART_DIR = os.path.join(PROJECT_ROOT, "static", "images")
os.makedirs(CHART_DIR, exist_ok=True)

# Fetch hospital visit data from MySQL
def get_hospital_data():

    connection = None

    try:
        connection = get_db_connection()

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
        """

        df = pd.read_sql(query, connection)
        df["visit_date"] = pd.to_datetime(df["visit_date"])

        return df

    finally:
        if connection is not None and connection.is_connected():
            connection.close()


# Convert a Matplotlib figure into a Base64 image
def figure_to_base64(fig):

    buffer = BytesIO()

    fig.savefig(
        buffer,
        format="png",
        bbox_inches="tight"
    )

    buffer.seek(0)

    image_data = base64.b64encode(
        buffer.getvalue()
    ).decode("utf-8")

    buffer.close()
    plt.close(fig)

    return "data:image/png;base64," + image_data


# Generate all five charts using filtered data
def generate_charts(df, start_date=None, end_date=None):

    charts = {}

    df = df.copy()

    if not df.empty:
        df["visit_date"] = pd.to_datetime(df["visit_date"])

    # 1. Department-wise Visits
    fig, ax = plt.subplots(figsize=(10, 6))

    if not df.empty:
        department_counts = df["department_name"].value_counts()
        department_counts.plot(
            kind="bar",
            ax=ax,
            color="skyblue"
        )
    else:
        ax.text(0.5, 0.5, "No visit data available",
                ha="center", va="center")

    ax.set_title("Department-wise Hospital Visits")
    ax.set_xlabel("Department")
    ax.set_ylabel("Number of Visits")
    ax.tick_params(axis="x", rotation=45)

    fig.tight_layout()
    charts["department"] = figure_to_base64(fig)

    # 2. Monthly Visit Trends
    fig, ax = plt.subplots(figsize=(10, 6))

    if not df.empty:
        monthly_visits = df.groupby(
            df["visit_date"].dt.to_period("M")
        ).size()

        monthly_visits.index = monthly_visits.index.strftime("%b %Y")

        monthly_visits.plot(
            kind="line",
            marker="o",
            ax=ax
        )
    else:
        ax.text(0.5, 0.5, "No visit data available",
                ha="center", va="center")

    ax.set_title("Monthly Hospital Visit Trends")
    ax.set_xlabel("Month")
    ax.set_ylabel("Number of Visits")
    ax.tick_params(axis="x", rotation=30)

    fig.tight_layout()
    charts["monthly"] = figure_to_base64(fig)

    # 3. Patient Age-Band Distribution
    fig, ax = plt.subplots(figsize=(8, 6))

    if not df.empty:
        age_order = ["0-17", "18-35", "36-59", "60+"]

        age_counts = (
            df["age_band"]
            .value_counts()
            .reindex(age_order, fill_value=0)
        )

        age_counts.plot(
            kind="bar",
            ax=ax,
            color="lightgreen"
        )
    else:
        ax.text(0.5, 0.5, "No visit data available",
                ha="center", va="center")

    ax.set_title("Patient Age-Band Distribution")
    ax.set_xlabel("Age Group")
    ax.set_ylabel("Number of Visits")
    ax.tick_params(axis="x", rotation=0)

    fig.tight_layout()
    charts["age"] = figure_to_base64(fig)

    # 4. Visit-Type Distribution
    fig, ax = plt.subplots(figsize=(8, 6))

    if not df.empty:
        visit_type_counts = df["visit_type"].value_counts()

        visit_type_counts.plot(
            kind="bar",
            ax=ax,
            color="orange"
        )
    else:
        ax.text(0.5, 0.5, "No visit data available",
                ha="center", va="center")

    ax.set_title("Hospital Visit-Type Distribution")
    ax.set_xlabel("Visit Type")
    ax.set_ylabel("Number of Visits")
    ax.tick_params(axis="x", rotation=0)

    fig.tight_layout()
    charts["visit_type"] = figure_to_base64(fig)

        # 5. Daily Visit Trends
    fig, ax = plt.subplots(figsize=(12, 6))

    import matplotlib.dates as mdates

    if start_date is not None and end_date is not None:
        first_date = pd.Timestamp(start_date)
        last_date = pd.Timestamp(end_date)
    elif not df.empty:
        first_date = df["visit_date"].min().normalize()
        last_date = df["visit_date"].max().normalize()
    else:
        first_date = last_date = None

    if first_date is not None:

        all_dates = pd.date_range(
            start=first_date,
            end=last_date,
            freq="D"
        )

        if not df.empty:
            daily_visits = (
                df.groupby(df["visit_date"].dt.normalize())
                .size()
                .reindex(all_dates, fill_value=0)
                .sort_index()
            )
        else:
            daily_visits = pd.Series(0, index=all_dates)

        ax.plot(
            daily_visits.index,
            daily_visits.values,
            marker="o"
        )

        date_range = (last_date - first_date).days

        if date_range <= 7:
            interval = 1
        elif date_range <= 30:
            interval = 3
        else:
            interval = 7

        ax.xaxis.set_major_locator(
            mdates.DayLocator(interval=interval)
        )

        ax.xaxis.set_major_formatter(
            mdates.DateFormatter("%d %b")
        )

        plt.setp(
            ax.get_xticklabels(),
            rotation=45,
            ha="right"
        )

    else:
        ax.text(
            0.5, 0.5,
            "No visit data available",
            ha="center",
            va="center"
        )

    ax.set_title("Daily Hospital Visit Trends")
    ax.set_xlabel("Date")
    ax.set_ylabel("Number of Visits")

    fig.tight_layout()
    charts["daily"] = figure_to_base64(fig)
    return charts


# Original analysis function - preserved
def main():

    print("Hospital Data Analysis Project")

    try:
        df = get_hospital_data()

        print("Connected to MySQL successfully!")
        print("\nHospital Data:")
        print(df.head())
        print("\nTotal visits:", len(df))

        charts = generate_charts(df)

        filenames = {
            "department": "department_wise_visits.png",
            "monthly": "monthly_visit_trends.png",
            "age": "patient_age_band_distribution.png",
            "visit_type": "visit_type_distribution.png",
            "daily": "daily_visit_trends.png"
        }

        for key, filename in filenames.items():

            image_data = charts[key].split(",", 1)[1]

            image_bytes = base64.b64decode(image_data)

            with open(os.path.join(CHART_DIR, filename), "wb") as file:
                file.write(image_bytes)

            print("Chart saved:", filename)

        print("\nAll five analyses completed successfully!")

    except mysql.connector.Error as error:
        print("MySQL connection or query error:", error)

    except Exception as error:
        print("An error occurred:", error)


if __name__ == "__main__":
    main()

