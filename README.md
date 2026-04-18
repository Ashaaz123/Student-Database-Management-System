# Student Database Management System (SDMS)

## Project Overview

The Student Database Management System (SDMS) is a web-based application
built using Flask and MySQL. It allows users to perform CRUD operations,
advanced SQL queries, and manage student-related data through a browser
interface.

## Technologies Used

-   Flask (Python)
-   MySQL (Workbench)
-   HTML, CSS
-   pandas, openpyxl

## Project Structure

SDMS_Project/ ├── app.py ├── requirements.txt ├── utils/ │ └──
export_excel.py ├── templates/ │ ├── home.html │ ├── create_table.html │
├── insert_data.html │ ├── retrieve_data.html │ ├── update_delete.html │
├── aggregate_group.html │ ├── joins_relationships.html │ └──
constraints_indexing.html ├── static/ │ └── style.css

## Setup Instructions

1.  Install dependencies: pip install -r requirements.txt

2.  Configure MySQL in app.py

3.  Run the app: python app.py

4.  Open browser: http://127.0.0.1:5000/

## Features

-   CRUD Operations
-   Joins & Relationships
-   Aggregate Queries
-   Constraints & Indexing
-   Excel Export

## Author

Ashaaz Ahmed Khan A
