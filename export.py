import io

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter

from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Paragraph,
    Spacer
)
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4, landscape

from docx import Document
from docx.shared import Inches
import base64
from io import BytesIO

import pandas as pd
from openpyxl.styles import Font, PatternFill
from docx import Document
from docx.shared import Inches
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table,
    TableStyle, Image, PageBreak
)
from reportlab.lib.units import inch


def create_excel(data, columns, title):
    wb = Workbook()
    ws = wb.active
    ws.title = title[:31]

    ws.append([title])
    ws.merge_cells(
        start_row=1,
        start_column=1,
        end_row=1,
        end_column=len(columns)
    )

    ws["A1"].font = Font(size=16, bold=True, color="FFFFFF")
    ws["A1"].fill = PatternFill(
        start_color="167D8D",
        end_color="167D8D",
        fill_type="solid"
    )
    ws["A1"].alignment = Alignment(horizontal="center")

    ws.append([label for key, label in columns])

    for cell in ws[2]:
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill(
            start_color="167D8D",
            end_color="167D8D",
            fill_type="solid"
        )

    for row in data:
        ws.append([row.get(key, "") for key, label in columns])

    for column in ws.columns:
        max_length = max(
            len(str(cell.value or "")) for cell in column
        )
        ws.column_dimensions[
            get_column_letter(column[0].column)
        ].width = min(max_length + 4, 30)

    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)

    return buffer


def create_pdf(data, columns, title):
    buffer = io.BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4)
    )

    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph(title, styles["Title"]))
    elements.append(Spacer(1, 20))

    table_data = [
        [label for key, label in columns]
    ]

    for row in data:
        table_data.append([
            str(row.get(key, "") or "")
            for key, label in columns
        ])

    table = Table(table_data, repeatRows=1)

    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#167D8D")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
    ]))

    elements.append(table)
    doc.build(elements)

    buffer.seek(0)
    return buffer


def create_word(data, columns, title):
    document = Document()

    document.add_heading(title, level=1)

    table = document.add_table(
        rows=1,
        cols=len(columns)
    )

    table.style = "Table Grid"

    header_cells = table.rows[0].cells

    for index, (key, label) in enumerate(columns):
        header_cells[index].text = label

    for row in data:
        cells = table.add_row().cells

        for index, (key, label) in enumerate(columns):
            cells[index].text = str(row.get(key, "") or "")

    buffer = io.BytesIO()
    document.save(buffer)
    buffer.seek(0)

    return buffer
def create_dashboard_pdf(summary, charts, title, filters):
    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4
    )

    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph(title, styles["Title"]))
    elements.append(Spacer(1, 15))

    elements.append(Paragraph(
        f"Period: {filters['period']}", styles["Normal"]
    ))
    elements.append(Paragraph(
        f"Department: {filters['department']}", styles["Normal"]
    ))
    elements.append(Paragraph(
        f"Date Range: {filters['start_date']} to {filters['end_date']}",
        styles["Normal"]
    ))

    elements.append(Spacer(1, 15))
    elements.append(Paragraph("Summary Statistics", styles["Heading2"]))

    summary_data = [["Metric", "Value"]]

    for key, value in summary.items():
        summary_data.append([key, str(value)])

    table = Table(summary_data)

    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#167D8D")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("PADDING", (0, 0), (-1, -1), 8),
    ]))

    elements.append(table)

    chart_titles = {
        "department": "Department-wise Visits",
        "monthly": "Monthly Visit Trends",
        "age": "Patient Age-Band Distribution",
        "visit_type": "Visit-Type Distribution",
        "daily": "Daily Visit Trends"
    }

    for key, chart_title in chart_titles.items():
        if charts.get(key):
            image_data = charts[key].split(",", 1)[1]
            image_buffer = BytesIO(base64.b64decode(image_data))

            elements.append(Spacer(1, 20))
            elements.append(Paragraph(chart_title, styles["Heading2"]))
            elements.append(
                Image(image_buffer, width=6.5 * inch, height=3.8 * inch)
            )

    doc.build(elements)
    buffer.seek(0)

    return buffer
def create_dashboard_word(summary, charts, title, filters):
    document = Document()

    document.add_heading(title, level=1)

    document.add_paragraph(f"Period: {filters['period']}")
    document.add_paragraph(f"Department: {filters['department']}")
    document.add_paragraph(
        f"Date Range: {filters['start_date']} to {filters['end_date']}"
    )

    document.add_heading("Summary Statistics", level=2)

    table = document.add_table(rows=1, cols=2)
    table.style = "Table Grid"

    table.rows[0].cells[0].text = "Metric"
    table.rows[0].cells[1].text = "Value"

    for key, value in summary.items():
        cells = table.add_row().cells
        cells[0].text = str(key)
        cells[1].text = str(value)

    chart_titles = {
        "department": "Department-wise Visits",
        "monthly": "Monthly Visit Trends",
        "age": "Patient Age-Band Distribution",
        "visit_type": "Visit-Type Distribution",
        "daily": "Daily Visit Trends"
    }

    for key, chart_title in chart_titles.items():
        if charts.get(key):
            image_data = charts[key].split(",", 1)[1]
            image_buffer = BytesIO(base64.b64decode(image_data))

            document.add_page_break()
            document.add_heading(chart_title, level=2)
            document.add_picture(
                image_buffer,
                width=Inches(6)
            )

    buffer = BytesIO()
    document.save(buffer)
    buffer.seek(0)

    return buffer


def generate_export(data, columns, title, file_format):

    if file_format == "excel":
        return create_excel(data, columns, title), "xlsx"

    elif file_format == "pdf":
        return create_pdf(data, columns, title), "pdf"

    elif file_format == "word":
        return create_word(data, columns, title), "docx"

    else:
        raise ValueError("Unsupported export format")

def create_dashboard_excel(summary, visits, title, filters):
    workbook = Workbook()

    # Summary sheet
    sheet = workbook.active
    sheet.title = "Summary"

    sheet.append([title])
    sheet.append(["Period", filters["period"]])
    sheet.append(["Department", filters["department"]])
    sheet.append(["Start Date", str(filters["start_date"])])
    sheet.append(["End Date", str(filters["end_date"])])
    sheet.append([])

    for key, value in summary.items():
        sheet.append([key.replace("_", " ").title(), value])

    # Visit records sheet
    visit_sheet = workbook.create_sheet("Visit Records")

    visit_sheet.append([
        "Visit ID",
        "Patient ID",
        "Department",
        "Visit Date",
        "Visit Type",
        "Age Group",
        "Gender"
    ])

    for row in visits.itertuples(index=False, name=None):
        visit_sheet.append([
            str(value) if pd.notna(value) else ""
            for value in row
        ])

    # Formatting
    for ws in workbook.worksheets:
        ws.freeze_panes = "A2"

        for cell in ws[1]:
            cell.font = Font(bold=True, color="FFFFFF")
            cell.fill = PatternFill(
                start_color="167D8D",
                end_color="167D8D",
                fill_type="solid"
            )

        for column_cells in ws.columns:
            max_length = max(
                len(str(cell.value or ""))
                for cell in column_cells
            )
            ws.column_dimensions[
                column_cells[0].column_letter
            ].width = min(max_length + 3, 35)

    buffer = BytesIO()
    workbook.save(buffer)
    buffer.seek(0)

    return buffer

def create_demographics_excel(
    total_patients,
    age_distribution,
    gender_distribution,
    blood_group_distribution
):
    workbook = Workbook()

    # Summary sheet
    sheet = workbook.active
    sheet.title = "Summary"

    sheet.append(["Patient Demographics Report"])
    sheet.append(["Total Registered Patients", total_patients])
    sheet.append(["Age Groups", len(age_distribution)])
    sheet.append(["Gender Categories", len(gender_distribution)])
    sheet.append(["Blood Group Categories", len(blood_group_distribution)])

    # Age distribution sheet
    age_sheet = workbook.create_sheet("Age Distribution")
    age_sheet.append(["Age Group", "Patient Count", "Percentage"])

    for item in age_distribution:
        percentage = (
            item["patient_count"] * 100 / total_patients
            if total_patients > 0 else 0
        )

        age_sheet.append([
            item["age_band"],
            item["patient_count"],
            f"{percentage:.1f}%"
        ])

    # Gender distribution sheet
    gender_sheet = workbook.create_sheet("Gender Distribution")
    gender_sheet.append(["Gender", "Patient Count", "Percentage"])

    for item in gender_distribution:
        percentage = (
            item["patient_count"] * 100 / total_patients
            if total_patients > 0 else 0
        )

        gender_sheet.append([
            item["gender"],
            item["patient_count"],
            f"{percentage:.1f}%"
        ])

    # Blood group distribution sheet
    blood_sheet = workbook.create_sheet("Blood Group Distribution")
    blood_sheet.append(["Blood Group", "Patient Count", "Percentage"])

    for item in blood_group_distribution:
        percentage = (
            item["patient_count"] * 100 / total_patients
            if total_patients > 0 else 0
        )

        blood_sheet.append([
            item["blood_group"],
            item["patient_count"],
            f"{percentage:.1f}%"
        ])

    # Formatting
    for ws in workbook.worksheets:
        ws.freeze_panes = "A2"

        for cell in ws[1]:
            cell.font = Font(bold=True, color="FFFFFF")
            cell.fill = PatternFill(
                start_color="167D8D",
                end_color="167D8D",
                fill_type="solid"
            )

        for column in ws.columns:
            max_length = max(
                len(str(cell.value or "")) for cell in column
            )

            ws.column_dimensions[
                column[0].column_letter
            ].width = min(max_length + 4, 35)

    buffer = BytesIO()
    workbook.save(buffer)
    buffer.seek(0)

    return buffer

def create_demographics_pdf(
    total_patients,
    age_distribution,
    gender_distribution,
    blood_group_distribution
):
    buffer = BytesIO()

    doc = SimpleDocTemplate(buffer, pagesize=A4)

    styles = getSampleStyleSheet()
    elements = []

    elements.append(
        Paragraph("Patient Demographics Report", styles["Title"])
    )
    elements.append(Spacer(1, 20))

    # Summary statistics
    elements.append(
        Paragraph("Summary Statistics", styles["Heading2"])
    )

    summary_data = [
        ["Metric", "Value"],
        ["Total Registered Patients", str(total_patients)],
        ["Age Groups", str(len(age_distribution))],
        ["Gender Categories", str(len(gender_distribution))],
        ["Blood Group Categories", str(len(blood_group_distribution))]
    ]

    summary_table = Table(summary_data)
    summary_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#167D8D")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("PADDING", (0, 0), (-1, -1), 8)
    ]))

    elements.append(summary_table)
    elements.append(Spacer(1, 20))

    # Helper to create each distribution table
    def add_distribution_table(title, headers, rows):
        elements.append(Paragraph(title, styles["Heading2"]))

        table_data = [headers] + rows
        table = Table(table_data, repeatRows=1)

        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#167D8D")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("PADDING", (0, 0), (-1, -1), 8)
        ]))

        elements.append(table)
        elements.append(Spacer(1, 20))

    # Age distribution
    age_rows = []

    for item in age_distribution:
        percentage = (
            item["patient_count"] * 100 / total_patients
            if total_patients > 0 else 0
        )

        age_rows.append([
            item["age_band"],
            str(item["patient_count"]),
            f"{percentage:.1f}%"
        ])

    add_distribution_table(
        "Age-Group Distribution",
        ["Age Group", "Patient Count", "Percentage"],
        age_rows
    )

    # Gender distribution
    gender_rows = []

    for item in gender_distribution:
        percentage = (
            item["patient_count"] * 100 / total_patients
            if total_patients > 0 else 0
        )

        gender_rows.append([
            item["gender"],
            str(item["patient_count"]),
            f"{percentage:.1f}%"
        ])

    add_distribution_table(
        "Gender Distribution",
        ["Gender", "Patient Count", "Percentage"],
        gender_rows
    )

    # Blood group distribution
    blood_rows = []

    for item in blood_group_distribution:
        percentage = (
            item["patient_count"] * 100 / total_patients
            if total_patients > 0 else 0
        )

        blood_rows.append([
            item["blood_group"],
            str(item["patient_count"]),
            f"{percentage:.1f}%"
        ])

    add_distribution_table(
        "Blood Group Distribution",
        ["Blood Group", "Patient Count", "Percentage"],
        blood_rows
    )

    doc.build(elements)
    buffer.seek(0)

    return buffer

def create_demographics_word(
    total_patients,
    age_distribution,
    gender_distribution,
    blood_group_distribution
):
    document = Document()

    document.add_heading("Patient Demographics Report", level=1)
    document.add_heading("Summary Statistics", level=2)

    summary_table = document.add_table(rows=1, cols=2)
    summary_table.style = "Table Grid"

    summary_table.rows[0].cells[0].text = "Metric"
    summary_table.rows[0].cells[1].text = "Value"

    summary = {
        "Total Registered Patients": total_patients,
        "Age Groups": len(age_distribution),
        "Gender Categories": len(gender_distribution),
        "Blood Group Categories": len(blood_group_distribution)
    }

    for key, value in summary.items():
        cells = summary_table.add_row().cells
        cells[0].text = str(key)
        cells[1].text = str(value)

    # Helper to create distribution tables
    def add_distribution_table(title, headers, data):
        document.add_heading(title, level=2)

        table = document.add_table(rows=1, cols=len(headers))
        table.style = "Table Grid"

        for i, header in enumerate(headers):
            table.rows[0].cells[i].text = header

        for row in data:
            cells = table.add_row().cells

            for i, value in enumerate(row):
                cells[i].text = str(value)

    # Age distribution
    age_rows = []

    for item in age_distribution:
        percentage = (
            item["patient_count"] * 100 / total_patients
            if total_patients > 0 else 0
        )

        age_rows.append([
            item["age_band"],
            item["patient_count"],
            f"{percentage:.1f}%"
        ])

    add_distribution_table(
        "Age-Group Distribution",
        ["Age Group", "Patient Count", "Percentage"],
        age_rows
    )

    # Gender distribution
    gender_rows = []

    for item in gender_distribution:
        percentage = (
            item["patient_count"] * 100 / total_patients
            if total_patients > 0 else 0
        )

        gender_rows.append([
            item["gender"],
            item["patient_count"],
            f"{percentage:.1f}%"
        ])

    add_distribution_table(
        "Gender Distribution",
        ["Gender", "Patient Count", "Percentage"],
        gender_rows
    )

    # Blood group distribution
    blood_rows = []

    for item in blood_group_distribution:
        percentage = (
            item["patient_count"] * 100 / total_patients
            if total_patients > 0 else 0
        )

        blood_rows.append([
            item["blood_group"],
            item["patient_count"],
            f"{percentage:.1f}%"
        ])

    add_distribution_table(
        "Blood Group Distribution",
        ["Blood Group", "Patient Count", "Percentage"],
        blood_rows
    )

    buffer = BytesIO()
    document.save(buffer)
    buffer.seek(0)

    return buffer

    current_app.logger.info("Total patients: %s", total_patients)
    current_app.logger.info("Age data: %s", age_distribution)
    current_app.logger.info("Gender data: %s", gender_distribution)
    current_app.logger.info("Blood group data: %s", blood_group_distribution)

def generate_demographics_export(
    total_patients,
    age_distribution,
    gender_distribution,
    blood_group_distribution,
    file_format
):
    if file_format == "excel":
        return create_demographics_excel(
            total_patients,
            age_distribution,
            gender_distribution,
            blood_group_distribution
        ), "xlsx"

    elif file_format == "pdf":
        return create_demographics_pdf(
            total_patients,
            age_distribution,
            gender_distribution,
            blood_group_distribution
        ), "pdf"

    elif file_format == "word":
        return create_demographics_word(
            total_patients,
            age_distribution,
            gender_distribution,
            blood_group_distribution
        ), "docx"

    raise ValueError("Invalid export format.")

def generate_dashboard_export(summary, visits, charts, title, filters, file_format):

    if file_format == "excel":
        return create_dashboard_excel(
            summary, visits, title, filters
        ), "xlsx"

    elif file_format == "pdf":
        return create_dashboard_pdf(
            summary, charts, title, filters
        ), "pdf"

    elif file_format == "word":
        return create_dashboard_word(
            summary, charts, title, filters
        ), "docx"

    raise ValueError("Invalid export format.")

def create_reports_excel(summary, department_reports,
                         monthly_reports, daily_reports, report_date):

    wb = Workbook()

    # Summary sheet
    ws = wb.active
    ws.title = "Summary"

    ws.append(["Hospital Reports"])
    ws.append(["Generated On", str(report_date)])
    ws.append([])
    ws.append(["Metric", "Count"])
    ws.append(["Total Patients", summary["total_patients"]])
    ws.append(["Total Visits", summary["total_visits"]])
    ws.append(["Total Departments", summary["total_departments"]])

    # Department-wise report
    ws = wb.create_sheet("Department Reports")
    ws.append(["Department", "Visit Count"])

    for row in department_reports:
        ws.append([
            row["department_name"],
            row["visit_count"]
        ])

    # Monthly report
    ws = wb.create_sheet("Monthly Reports")
    ws.append(["Month", "Visit Count"])

    for row in monthly_reports:
        ws.append([
            row["month"],
            row["visit_count"]
        ])

    # Daily report
    ws = wb.create_sheet("Daily Reports")
    ws.append(["Date", "Visit Count"])

    for row in daily_reports:
        ws.append([
            str(row["visit_date"]),
            row["visit_count"]
        ])

    # Basic formatting
    for sheet in wb.worksheets:
        for cell in sheet[1]:
            cell.font = Font(bold=True)

        for column in sheet.columns:
            max_length = max(
                len(str(cell.value or "")) for cell in column
            )
            sheet.column_dimensions[
                get_column_letter(column[0].column)
            ].width = max_length + 4

    buffer = BytesIO()
    wb.save(buffer)
    buffer.seek(0)

    return buffer
def create_reports_word(summary, department_reports,
                        monthly_reports, daily_reports, report_date):

    doc = Document()

    doc.add_heading("Hospital Reports", 0)
    doc.add_paragraph(f"Generated On: {report_date}")

    doc.add_heading("Overall Summary", level=1)

    summary_table = doc.add_table(rows=1, cols=2)
    summary_table.style = "Table Grid"

    summary_table.rows[0].cells[0].text = "Metric"
    summary_table.rows[0].cells[1].text = "Count"

    summary_items = [
        ("Total Patients", summary["total_patients"]),
        ("Total Visits", summary["total_visits"]),
        ("Total Departments", summary["total_departments"])
    ]

    for metric, count in summary_items:
        cells = summary_table.add_row().cells
        cells[0].text = metric
        cells[1].text = str(count)

    def add_report_table(title, headers, rows):
        doc.add_heading(title, level=1)

        table = doc.add_table(rows=1, cols=len(headers))
        table.style = "Table Grid"

        for i, header in enumerate(headers):
            table.rows[0].cells[i].text = header

        if rows:
            for row in rows:
                cells = table.add_row().cells

                for i, value in enumerate(row):
                    cells[i].text = str(value)
        else:
            cells = table.add_row().cells
            cells[0].text = "No data available"

    add_report_table(
        "Department-wise Reports",
        ["Department", "Visit Count"],
        [
            (row["department_name"], row["visit_count"])
            for row in department_reports
        ]
    )

    add_report_table(
        "Monthly Reports",
        ["Month", "Visit Count"],
        [
            (row["month"], row["visit_count"])
            for row in monthly_reports
        ]
    )

    add_report_table(
        "Daily Reports",
        ["Date", "Visit Count"],
        [
            (row["visit_date"], row["visit_count"])
            for row in daily_reports
        ]
    )

    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)

    return buffer

    current_app.logger.info("Summary: %s", summary)
    current_app.logger.info("Department data: %s", department_reports)
    current_app.logger.info("Monthly data: %s", monthly_reports)
    current_app.logger.info("Daily data: %s", daily_reports)

def generate_reports_export(summary, department_reports,
                            monthly_reports, daily_reports,
                            report_date, file_format):

    if file_format == "excel":
        return create_reports_excel(
            summary, department_reports,
            monthly_reports, daily_reports, report_date
        ), "xlsx"

    elif file_format == "word":
        return create_reports_word(
            summary, department_reports,
            monthly_reports, daily_reports, report_date
        ), "docx"

    else:
        raise ValueError("Unsupported export format")
