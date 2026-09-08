import openpyxl
from openpyxl.styles import Font
from io import BytesIO
from tests.models import Result


def build_results_workbook(schedule, results):
    """Build the results Excel for a schedule. `results` is an already-filtered queryset."""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = f"Results_{schedule.college.name}"[:31]  # Excel sheet-name max 31 chars

    headers = ["ID", "Student Name", "Email", "College", "Contact Number"]
    for col_index, header in enumerate(headers, start=1):
        cell = ws.cell(row=1, column=col_index, value=header.upper())
        cell.font = Font(bold=True)

    for idx, result in enumerate(results, start=1):
        row = [
            idx,
            result.student.name.upper() if result.student.name else "",
            result.student.email.upper() if result.student.email else "",
            result.exam_schedule.college.name.upper() if result.exam_schedule.college.name else "",
            result.student.mobile_number.upper() if result.student.mobile_number else "",
        ]
        for col_index, value in enumerate(row, start=1):
            ws.cell(row=idx + 1, column=col_index, value=value)

    return wb

def get_filtered_results(schedule, cutoff=None, top_n=None):
    results = Result.objects.filter(
        exam_schedule=schedule
    ).select_related("student", "exam_schedule__college").order_by("-score")

    if cutoff:
        try:
            results = results.filter(score__gte=int(cutoff))
        except (ValueError, TypeError):
            pass

    if top_n:
        try:
            results = results[:int(top_n)]
        except (ValueError, TypeError):
            pass

    return results