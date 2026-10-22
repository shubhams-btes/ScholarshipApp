import openpyxl
from openpyxl.styles import Font
from io import BytesIO
from tests.models import Result
from decimal import Decimal

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




def talentquest_percentage(result):
    """Exam score as % out of 100."""
    if not result.total_questions:
        return Decimal("0")
    return round(Decimal(result.score) / Decimal(result.total_questions) * 100, 2)


def final_percentage(academic_pct, tq_pct, interview_pct):
    """Equal-thirds average of academics, TalentQuest, interview.
    Returns None if interview not done (final can't be computed yet)."""
    if interview_pct is None or academic_pct is None:
        return None
    return round((Decimal(academic_pct) + Decimal(tq_pct) + Decimal(interview_pct)) / 3, 2)


def scholarship_slab(final_pct):
    """A/B/C slab + scholarship %. 90+ → A/30, 80-90 → B/20, 70-80 → C/10, else none."""
    if final_pct is None:
        return (None, None)
    if final_pct >= 90:
        return ("A", 30)
    if final_pct >= 80:
        return ("B", 20)
    if final_pct >= 70:
        return ("C", 10)
    return ("—", 0)


def build_shortlist_workbook(schedule, results):
    """Build the final shortlisted-students Excel with the full scoring pipeline."""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = f"Shortlist_{schedule.college.name}"[:31]

    headers = [
        "ID", "Hall Ticket", "Roll No", "Name", "Email", "Contact Number", "College",
        "10th %", "12th %", "Graduation %", "Masters %",   # ← individual breakdown
        "Academic %", "TalentQuest %", "Interview %", "Final %",
        "Slab", "Scholarship %",
        "Interview Status", "Stream", "Panelist", "Interview Remarks", "Shortlist Remarks",
    ]
    for col_index, header in enumerate(headers, start=1):
        cell = ws.cell(row=1, column=col_index, value=header.upper())
        cell.font = Font(bold=True)

    for idx, result in enumerate(results, start=1):
        s = result.student
        academic = s.academic_percentage
        tq = talentquest_percentage(result)

        interview = getattr(result, "interview", None)
        interview_pct = interview.interview_percentage if interview else None

        final = final_percentage(academic, tq, interview_pct)
        slab, scholarship = scholarship_slab(final)

        row = [
            idx,
            s.hall_ticket.upper() if s.hall_ticket else "",
            s.roll_no.upper() if s.roll_no else "",
            s.name.upper() if s.name else "",
            s.email.upper() if s.email else "",
            s.mobile_number if s.mobile_number else "",
            result.exam_schedule.college.name.upper() if result.exam_schedule.college.name else "",
            # ── individual academic breakdown ──
            s.tenth_percentage if s.tenth_percentage is not None else "",
            s.twelfth_percentage if s.twelfth_percentage is not None else "",
            s.graduation_percentage if s.graduation_percentage is not None else "",
            s.masters_percentage if s.masters_percentage is not None else "",
            # ── aggregate + pipeline ──
            academic if academic is not None else "",
            tq,
            interview_pct if interview_pct is not None else "",
            final if final is not None else "",
            slab if slab else "",
            scholarship if scholarship else "",
            interview.get_status_display() if interview else "Pending",
            interview.get_stream_display() if interview and interview.stream else "",
            interview.panelist_name if interview else "",
            interview.remarks if interview else "",
            result.shortlist_remarks or "",
        ]

        for col_index, value in enumerate(row, start=1):
            ws.cell(row=idx + 1, column=col_index, value=value)

    return wb