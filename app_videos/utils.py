from django.utils.html import format_html


def get_video_file_status(obj):
    """Return status HTML for VideoFile processing (admin/inline)."""
    from django_rq import get_queue

    if obj.is_ready:
        return format_html("✅ <b>done</b>")
    queue = get_queue("default")
    error_found = False
    uploading_found = False
    pending_found = False

    for job_id in queue.failed_job_registry.get_job_ids():
        job = queue.fetch_job(job_id)
        if job and job.args and str(obj.id) in [str(a) for a in job.args]:
            error_found = True

    for job_id in queue.started_job_registry.get_job_ids():
        job = queue.fetch_job(job_id)
        if job and job.args and str(obj.id) in [str(a) for a in job.args]:
            uploading_found = True

    for job in queue.jobs:
        if job.args and str(obj.id) in [str(a) for a in job.args]:
            if job.is_started or getattr(job, "status", None) == "started":
                uploading_found = True
            else:
                pending_found = True

    if error_found:
        return format_html("❌ <b>error</b>")
    if uploading_found:
        return format_html("⏳ <b>uploading</b>")
    if pending_found:
        return format_html("🕒 <b>pending</b>")
    return format_html("⏸️ <b>not started</b>")
