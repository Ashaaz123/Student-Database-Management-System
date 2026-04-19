# config.py
# Database configuration
DB_CONFIG = {
    'user': 'root',
    'password': 'admin',
    'host': 'localhost',
    'database': 'sdms5_dbase'
}


# utils/export_excel.py
# Utility to export query results to Excel
import pandas as pd
from io import BytesIO
from flask import send_file

def export_to_excel(columns, rows, filename):
    """
    columns: list of column names
    rows: list of tuples (rows)
    filename: name of the downloaded file
    """
    df = pd.DataFrame(rows, columns=columns)
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Sheet1')
    output.seek(0)
    return send_file(
        output,
        as_attachment=True,
        download_name=filename,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )


# app.py
from flask import Flask, render_template, request, redirect, url_for, flash
import mysql.connector
from config import DB_CONFIG
from utils.export_excel import export_to_excel

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Helper to get DB connection
def get_db_connection():
    return mysql.connector.connect(**DB_CONFIG)

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/create_table', methods=['GET','POST'])
def create_table():
    if request.method=='POST':
        conn = get_db_connection()
        cursor = conn.cursor()

        # 1) Drop the constraint if it's already there
        try:
            cursor.execute("ALTER TABLE enrollment DROP INDEX uc_student_course;")
        except mysql.connector.Error as e:
            # ignore “unknown key” errors
            if e.errno != 1091:  # 1091 = ER_CANT_DROP_FIELD_OR_KEY
                raise

        # 2) Now (re)create tables and add the constraint
        queries = [
            # Students Table
            """
            CREATE TABLE IF NOT EXISTS students (
                student_id INT AUTO_INCREMENT PRIMARY KEY,
                first_name VARCHAR(50) NOT NULL,
                last_name VARCHAR(50) NOT NULL,
                email VARCHAR(100) UNIQUE,
                dept VARCHAR(50),
                INDEX idx_students_dept (dept)
            ) ENGINE=InnoDB;
            """,

        # Courses Table
        """
        CREATE TABLE IF NOT EXISTS courses (
            course_id INT AUTO_INCREMENT PRIMARY KEY,
            course_name VARCHAR(100) NOT NULL,
            instructor VARCHAR(100),
            credits INT,
            INDEX idx_courses_instructor (instructor)
) ENGINE=InnoDB;
        """,

       # Enrollment Table
       """
       CREATE TABLE IF NOT EXISTS enrollment (
           enroll_id INT AUTO_INCREMENT PRIMARY KEY,
           student_id INT NOT NULL,
           course_id INT NOT NULL,
           score DECIMAL(5,2) NOT NULL CHECK (score BETWEEN 0 AND 100),
           FOREIGN KEY (student_id) REFERENCES students(student_id)
               ON DELETE CASCADE ON UPDATE CASCADE,
           FOREIGN KEY (course_id) REFERENCES courses(course_id)
               ON DELETE CASCADE ON UPDATE CASCADE,
           INDEX idx_enrollment_student (student_id),
           INDEX idx_enrollment_course  (course_id)
       ) ENGINE=InnoDB;
       """,

       # Unique constraint
       "ALTER TABLE enrollment ADD CONSTRAINT uc_student_course UNIQUE (student_id, course_id);"
       ]

        for q in queries:
            cursor.execute(q)
        conn.commit()
        cursor.close()
        conn.close()
        flash('Tables and constraints created/updated!')
        return redirect(url_for('create_table'))
    return render_template('create_table.html')


@app.route('/insert_data', methods=['GET', 'POST'])
def insert_data():
    conn = get_db_connection()
    cursor = conn.cursor()
    # Fetch existing students and courses for dropdowns
    cursor.execute("SELECT student_id, CONCAT(first_name,' ',last_name) AS name FROM students")
    students = cursor.fetchall()
    cursor.execute("SELECT course_id, course_name FROM courses")
    courses = cursor.fetchall()

    if request.method == 'POST':
        student_id = request.form['student_id']
        course_id  = request.form['course_id']
        score      = request.form['score']
        cursor.execute(
            "INSERT INTO enrollment (student_id, course_id, score) VALUES (%s,%s,%s)",
            (student_id, course_id, score)
        )
        conn.commit()
        flash('Enrollment record added!')
        return redirect(url_for('insert_data'))

    # Show all enrollments
    cursor.execute(
        "SELECT e.enroll_id, s.first_name, s.last_name, c.course_name, e.score "
        "FROM enrollment e "
        "JOIN students s ON e.student_id = s.student_id "
        "JOIN courses c ON e.course_id = c.course_id"
    )
    rows = cursor.fetchall()
    columns = [desc[0] for desc in cursor.description]
    cursor.close()
    conn.close()

    # Excel download
    if 'download' in request.args:
        return export_to_excel(columns, rows, 'enrollment.xlsx')

    return render_template('insert_data.html', students=students, courses=courses, rows=rows, columns=columns)

@app.route('/retrieve_data')
def retrieve_data():
    table = request.args.get('table', 'students')
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM {table}")
    rows = cursor.fetchall()
    columns = [desc[0] for desc in cursor.description]
    cursor.close()
    conn.close()

    if 'download' in request.args:
        return export_to_excel(columns, rows, f'{table}.xlsx')

    return render_template('retrieve_data.html', table=table, rows=rows, columns=columns)

@app.route('/update_delete', methods=['GET', 'POST'])
def update_delete():
    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == 'POST':
        action = request.form['action']
        if action == 'update_student_email':
            student_id = request.form['student_id']
            new_email  = request.form['new_email']
            cursor.execute(
                "UPDATE students SET email=%s WHERE student_id=%s",
                (new_email, student_id)
            )
            conn.commit()
            flash('Student email updated!')
        elif action == 'delete_enrollment':
            enroll_id = request.form['enroll_id']
            cursor.execute(
                "DELETE FROM enrollment WHERE enroll_id=%s",
                (enroll_id,)
            )
            conn.commit()
            flash('Enrollment record deleted!')
        return redirect(url_for('update_delete'))

    # GET: fetch data for forms
    cursor.execute("SELECT student_id, CONCAT(first_name,' ',last_name) FROM students")
    students = cursor.fetchall()
    cursor.execute(
        "SELECT e.enroll_id, CONCAT(s.first_name,' ',s.last_name), c.course_name "
        "FROM enrollment e "
        "JOIN students s ON e.student_id = s.student_id "
        "JOIN courses c ON e.course_id = c.course_id"
    )
    enrollments = cursor.fetchall()
    cursor.close()
    conn.close()

    return render_template('update_delete.html', students=students, enrollments=enrollments)

@app.route('/aggregate_group')
def aggregate_group():
    conn = get_db_connection()
    cursor = conn.cursor()
    # Dept counts
    cursor.execute("SELECT dept, COUNT(*) AS num_students FROM students GROUP BY dept")
    dept_counts = cursor.fetchall()
    # Avg score per student
    cursor.execute(
        "SELECT CONCAT(s.first_name,' ',s.last_name) AS student_name, ROUND(AVG(e.score),2) AS avg_score "
        "FROM students s "
        "JOIN enrollment e ON s.student_id = e.student_id "
        "GROUP BY s.student_id"
    )
    avg_scores = cursor.fetchall()
    # High/Low scores
    cursor.execute("SELECT MAX(score), MIN(score) FROM enrollment")
    high_low = cursor.fetchone()
    cursor.close()
    conn.close()

    if 'download' in request.args:
        return export_to_excel(['dept','num_students'], dept_counts, 'dept_counts.xlsx')

    return render_template('aggregate_group.html', dept_counts=dept_counts, avg_scores=avg_scores, high_low=high_low)

@app.route('/joins_relationship')
def joins_relationship():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT s.student_id, CONCAT(s.first_name,' ',s.last_name) AS student_name, "
        "c.course_name, e.score "
        "FROM students s "
        "LEFT JOIN enrollment e ON s.student_id = e.student_id "
        "LEFT JOIN courses c ON e.course_id = c.course_id "
        "ORDER BY s.student_id"
    )
    data = cursor.fetchall()
    cursor.close()
    conn.close()

    if 'download' in request.args:
        return export_to_excel(['student_id','student_name','course_name','score'], data, 'student_courses.xlsx')

    return render_template('joins_relationship.html', data=data)

@app.route('/constraints_indexing')
def constraints_indexing():
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        # Indexes
        cursor.execute("SHOW INDEX FROM students")
        student_index = cursor.fetchall()

        cursor.execute("SHOW INDEX FROM courses")
        course_index = cursor.fetchall()

        cursor.execute("SHOW INDEX FROM enrollment")
        enrollment_index = cursor.fetchall()

        # DDLs
        cursor.execute("SHOW CREATE TABLE students")
        student_ddl = cursor.fetchone()['Create Table']

        cursor.execute("SHOW CREATE TABLE courses")
        course_ddl = cursor.fetchone()['Create Table']

        cursor.execute("SHOW CREATE TABLE enrollment")
        enrollment_ddl = cursor.fetchone()['Create Table']

        return render_template("constraints_indexing.html",
                               student_index=student_index,
                               course_index=course_index,
                               enrollment_index=enrollment_index,
                               student_ddl=student_ddl,
                               course_ddl=course_ddl,
                               enrollment_ddl=enrollment_ddl)

    except Exception as e:
        return f"<h3>Error: {e}</h3>"

    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

@app.route('/high_scorers')
def high_scorers():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM high_scorers")
    rows = cursor.fetchall()
    columns = [desc[0] for desc in cursor.description]
    cursor.close()
    conn.close()

    if 'download' in request.args:
        return export_to_excel(columns, rows, 'high_scorers.xlsx')

    return render_template('high_scorers.html', rows=rows, columns=columns)

@app.route('/top_5_students')
def top_5_students():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM top5_students")
    rows = cursor.fetchall()
    columns = [desc[0] for desc in cursor.description]
    cursor.close()
    conn.close()

    if 'download' in request.args:
        return export_to_excel(columns, rows, 'top5_students.xlsx')

    return render_template('top_5_students.html', rows=rows, columns=columns)

if __name__ == '__main__':
    app.run(debug=True)
