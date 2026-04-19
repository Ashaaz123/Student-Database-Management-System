# utils/export_excel.py
import pandas as pd
from io import BytesIO
from flask import send_file

def export_to_excel(columns, rows, filename):
    """
    columns: list of column names
    rows: list of tuples
    filename: the .xlsx filename to download
    """
    # Build a DataFrame
    df = pd.DataFrame(rows, columns=columns)

    # Write to an in-memory buffer
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Sheet1')
    output.seek(0)

    # Send as file download
    return send_file(
        output,
        as_attachment=True,
        download_name=filename,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
