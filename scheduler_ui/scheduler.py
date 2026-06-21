from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime

from .models import db, Job
from .tasks import run_task

scheduler = BackgroundScheduler()
_app = None


def init_scheduler(app):
    global _app
    _app = app
    if not scheduler.running:
        scheduler.start()
    with app.app_context():
        jobs = Job.query.filter_by(enabled=True).all()
        for job in jobs:
            schedule_job(job)


def schedule_job(job: Job):
    try:
        parts = job.cron_expr.split()
        if len(parts) == 5:
            trigger = CronTrigger(
                minute=parts[0], hour=parts[1],
                day=parts[2], month=parts[3], day_of_week=parts[4],
            )
        else:
            trigger = CronTrigger.from_crontab(job.cron_expr)

        scheduler.add_job(
            func=_execute_job,
            trigger=trigger,
            args=[job.id, job.module_path],
            id=f"job_{job.id}",
            replace_existing=True,
            misfire_grace_time=60,
        )
        job.status = "scheduled"
        db.session.commit()
    except Exception as e:
        job.status = f"error: {e}"
        db.session.commit()


def unschedule_job(job_id: str):
    try:
        scheduler.remove_job(f"job_{job_id}")
    except Exception:
        pass


def _execute_job(job_id: str, module_path: str):
    with _app.app_context():
        job = Job.query.get(job_id)
        if job:
            job.last_run = datetime.utcnow()
            job.status = "running"
            db.session.commit()

        log = run_task(job_id, module_path)

        if job:
            job.status = log.status
            db.session.commit()
