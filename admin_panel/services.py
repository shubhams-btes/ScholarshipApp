import openpyxl
from openpyxl.styles import Font
from io import BytesIO
from tests.models import Result


def build_results_workbook(schedule, results, include_score=False):
    """Build the results Excel for a schedule. `results` is an already-filtered queryset.
    include_score=True adds the Score column (internal/official use);
    default False omits it (for sharing with colleges)."""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = f"Results_{schedule.college.name}"[:31]

    headers = ["ID", "Student Name", "Email", "College", "Contact Number"]
    if include_score:
        headers.append("Score")
        headers.append("Hall Ticket")
        headers.append("Roll No")
        headers.extend(["10th %", "12th %", "Graduation Degree", "Graduation %", "Masters Degree", "Masters %"])

    for col_index, header in enumerate(headers, start=1):
        cell = ws.cell(row=1, column=col_index, value=header.upper())
        cell.font = Font(bold=True)

    for idx, result in enumerate(results, start=1):
        s = result.student
        row = [
            idx,
            s.name.upper() if s.name else "",
            s.email.upper() if s.email else "",
            result.exam_schedule.college.name.upper() if result.exam_schedule.college.name else "",
            s.mobile_number if s.mobile_number else "",
        ]
        if include_score:
            row.append(result.score)
            row.append(s.hall_ticket.upper() if s.hall_ticket else "")
            row.append(s.roll_no.upper() if s.roll_no else "")
            row.extend([
                s.tenth_percentage if s.tenth_percentage is not None else "",
                s.twelfth_percentage if s.twelfth_percentage is not None else "",
                s.get_graduation_degree_display() if s.graduation_degree else "",
                s.graduation_percentage if s.graduation_percentage is not None else "",
                s.get_masters_degree_display() if s.masters_degree else "",
                s.masters_percentage if s.masters_percentage is not None else "",
            ])

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