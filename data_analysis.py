import os
import sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import mysql.connector
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(PROJECT_ROOT)
from database import get_db_connection
CHART_DIR = os.path.join(PROJECT_ROOT, "static", "images")
os.makedirs(CHART_DIR, exist_ok=True)

def main():
    print("Hospital Data Analysis Project")

    connection = None

    try:
        # Connect Python to MySQL
        connection = get_db_connection()

        print("Connected to MySQL successfully!")

        # Read hospital visit data
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

        print("\nHospital Data:")
        print(df.head())
        print("\nTotal visits:", len(df))

        # 1. Department-wise visit counts
        department_counts = df["department_name"].value_counts()

        plt.figure(figsize=(10, 6))
        department_counts.plot(kind="bar", color="skyblue")
        plt.title("Department-wise Hospital Visits")
        plt.xlabel("Department")
        plt.ylabel("Number of Visits")
        plt.xticks(rotation=45, ha="right")
        plt.tight_layout()
        plt.savefig(os.path.join(CHART_DIR, "department_wise_visits.png"))
        print("Chart saved: department_wise_visits.png")
        plt.close()
        
        # 2. Monthly visit trends
        monthly_visits = df.groupby(
        df["visit_date"].dt.to_period("M")
        ).size()
        monthly_visits.index = monthly_visits.index.strftime("%b")

        plt.figure(figsize=(10, 6))
        monthly_visits.plot(kind="line", marker="o")

        plt.title("Monthly Hospital Visit Trends")
        plt.xlabel("Month")
        plt.ylabel("Number of Visits")
        plt.xticks(rotation=0)
        plt.tight_layout()

        plt.savefig(os.path.join(CHART_DIR, "monthly_visit_trends.png"))
        print("Chart saved: monthly_visit_trends.png")
        plt.close()

        # 3. Patient age-band distribution
        age_counts = df["age_band"].value_counts().sort_index()

        plt.figure(figsize=(8, 6))
        age_counts.plot(kind="bar", color="lightgreen")
        plt.title("Patient Age-Band Distribution")
        plt.xlabel("Age Group")
        plt.ylabel("Number of Visits")
        plt.xticks(rotation=0)
        plt.tight_layout()
        plt.savefig(os.path.join(CHART_DIR, "patient_age_band_distribution.png"))
        print("Chart saved: patient_age_band_distribution.png")
        plt.close()

        # 4. Visit-type distribution
        visit_type_counts = df["visit_type"].value_counts()

        plt.figure(figsize=(8, 6))
        visit_type_counts.plot(kind="bar", color="orange")
        plt.title("Hospital Visit-Type Distribution")
        plt.xlabel("Visit Type")
        plt.ylabel("Number of Visits")
        plt.xticks(rotation=0)
        plt.tight_layout()
        plt.savefig(os.path.join(CHART_DIR, "visit_type_distribution.png"))
        print("Chart saved: visit_type_distribution.png")
        plt.close()

        # 5. Daily visit trends
        daily_visits = df.groupby(
            df["visit_date"].dt.date
        ).size()

        plt.figure(figsize=(12, 6))
        daily_visits.plot(kind="line", marker="o")
        plt.title("Daily Hospital Visit Trends")
        plt.xlabel("Date")
        plt.ylabel("Number of Visits")
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig(os.path.join(CHART_DIR, "daily_visit_trends.png"))
        print("Chart saved: daily_visit_trends.png")
        plt.close()

        print("\nAll five analyses completed successfully!")

    except mysql.connector.Error as error:
        print("MySQL connection or query error:", error)

    except Exception as error:
        print("An error occurred:", error)

    finally:
        if connection is not None and connection.is_connected():
            connection.close()
            print("MySQL connection closed.")


if __name__ == "__main__":
    main()
