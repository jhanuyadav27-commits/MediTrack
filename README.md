# MediTrack – Hospital Patient Data Analysis System

## Project Overview

MediTrack is a web-based Hospital Patient Data Analysis System developed using Python and Flask. It helps maintain hospital patient and visit records and provides analytical insights through interactive dashboards and reports.

The system uses synthetic patient data for analysis and demonstration purposes.

## Live Demo

**Project Link:** https://meditrack-wk50.onrender.com

## Features

* User registration and login
* Patient record management (Add, View, Edit and Delete)
* Hospital visit management
* Search and filter functionality
* Dashboard with analytical charts
* Patient demographic analysis
* Reports and data visualisation
* Form validation and CSRF protection

## Technologies Used

* **Frontend:** HTML, CSS, JavaScript
* **Backend:** Python, Flask
* **Database:** MySQL
* **Data Analysis:** Pandas, NumPy
* **Visualisation:** Matplotlib

## 📁Project Structure

* `app.py` – Main Flask application
* `database.py` – Database connection
* `export.py` – Handles exporting reports and data into PDF, Excel, and Word formats
* `database.sql` – Database schema and sample data
* `analysis/` – Data analysis scripts
* `templates/` – HTML templates
* `static/` – CSS and JavaScript files
* `requirements.txt` – Python dependencies

## Prerequisites

- Python 3.x
- MySQL Server
- MySQL Workbench (optional)
- Visual Studio Code or any code editor
- A modern web browser

## Installation and Setup

Follow these steps to install and run the MediTrack application locally.

### 1. Clone the Repository

Clone the project repository using Git:

```bash[
https://github.com/jhanuyadav27-commits/MediTrack.git
```

Navigate to the project directory:

```bash
cd MediTrack
```

### 2. Create a Virtual Environment

Create a Python virtual environment:

```bash
python -m venv venv
```

Activate the virtual environment.

**For Windows:**

```bash
venv\Scripts\activate
```

**For Linux/macOS:**

```bash
source venv/bin/activate
```

### 3. Install Dependencies

Install the required Python packages using the requirements file:

```bash
pip install -r requirements.txt
```

### 4. Configure the MySQL Database

1. Open MySQL Workbench or your preferred MySQL client.
2. Create the database by executing the `database.sql` file.
3. Verify that the database and required tables have been created successfully.

The database used in this project is named `hospital_db`.

### 5. Configure Environment Variables

Create a `.env` file in the root directory of the project.

Add the required database configuration details using the variable names expected by `database.py`.

Make sure to provide your own MySQL credentials and configuration.

**Note:** Do not upload the `.env` file or expose database credentials in the public GitHub repository.

### 6. Run the Application

Start the Flask application using:

```bash
python app.py
```

### 7. Access the Application

After successfully starting the application, open your web browser and navigate to the local address displayed in the terminal.

The MediTrack application is now ready to use.

## 👥Team Members

<img width="619" height="363" alt="image" src="https://github.com/user-attachments/assets/3bd25a99-3755-45ea-870d-5e5f0c5f8494" />

## My Contributions

**Golla Krishna Jhansi – Backend Development**

- Developed the Flask backend for the application.
- Implemented application routes and request handling.
- Integrated backend functionality with frontend templates.
- Worked on user authentication and session management.
- Assisted in debugging and improving application functionality.

## Future Scope

* Advanced analytics and reporting
* Exporting reports in different formats
* Additional dashboard insights
* Improved deployment and scalability

## Note

This project uses synthetic/de-identified data and is intended for academic and demonstration purposes.
