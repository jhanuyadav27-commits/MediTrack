CREATE DATABASE IF NOT EXISTS hospital_db;
USE hospital_db;
CREATE TABLE IF NOT EXISTS patients (
patient_id INT PRIMARY KEY AUTO_INCREMENT,
age_band VARCHAR(20) NOT NULL,
gender_optional VARCHAR(20),
blood_group VARCHAR(10) NULL
);

CREATE TABLE IF NOT EXISTS departments (
department_id INT PRIMARY KEY AUTO_INCREMENT,
department_name VARCHAR(100) NOT NULL UNIQUE
);


CREATE TABLE IF NOT EXISTS visits (
visit_id INT PRIMARY KEY AUTO_INCREMENT,
patient_id INT NOT NULL,
department_id INT NOT NULL,
visit_date DATE NOT NULL DEFAULT (CURRENT_DATE),
visit_type VARCHAR(50) NOT NULL,
FOREIGN KEY (patient_id)
    REFERENCES patients(patient_id),
FOREIGN KEY (department_id)
    REFERENCES departments(department_id)
);

CREATE TABLE IF NOT EXISTS users (
    user_id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

