import os
from pathlib import Path
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from datetime import datetime

from .models import db, Job, RunLog
from .discovery import discover_apps
from .scheduler import scheduler, init_scheduler, schedule_job, unschedule_job
from .tasks import run_task


def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.urandom(24).hex()

    data_dir = Path(__file__).parent / "data"
    data_dir.mkdir(exist_ok=True)
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{data_dir / 'scheduler.db'}"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)

    with app.app_context():
        db.create_all()
        _sync_discovered_apps()
        init_scheduler(app)

    register_routes(app)
    return app


def _sync_discovered_apps():
    discovered = discover_apps()
    for app_info in discovered:
        existing = Job.query.get(app_info["id"])
        if not existing:
            job = Job(
                id=app_info["id"],
                name=app_info["name"],
                module_path=app_info["module"],
                description=f"Auto-discovered CLI app at {app_info['path']}",
            )
            db.session.add(job)
    db.session.commit()


def register_routes(app):

    @app.route("/")
    def dashboard():
        jobs = Job.query.all()
        recent_logs = RunLog.query.order_by(RunLog.started_at.desc()).limit(10).all()
        discovered = discover_apps()
        return render_template("dashboard.html", jobs=jobs, recent_logs=recent_logs, discovered=discovered)

    @app.route("/jobs")
    def jobs_list():
        jobs = Job.query.all()
        discovered = discover_apps()
        return render_template("jobs.html", jobs=jobs, discovered=discovered)

    @app.route("/jobs/<job_id>/schedule", methods=["POST"])
    def update_schedule(job_id):
        job = Job.query.get_or_404(job_id)
        cron_expr = request.form.get("cron_expr", job.cron_expr)
        job.cron_expr = cron_expr
        db.session.commit()

        if job.enabled:
            unschedule_job(job_id)
            schedule_job(job)

        flash(f"Schedule updated for {job.name}", "success")
        return redirect(url_for("jobs_list"))

    @app.route("/jobs/<job_id>/toggle", methods=["POST"])
    def toggle_job(job_id):
        job = Job.query.get_or_404(job_id)
        job.enabled = not job.enabled
        db.session.commit()

        if job.enabled:
            schedule_job(job)
        else:
            unschedule_job(job_id)
            job.status = "disabled"
            db.session.commit()

        state = "enabled" if job.enabled else "disabled"
        flash(f"{job.name} {state}", "success")
        return redirect(url_for("jobs_list"))

    @app.route("/jobs/<job_id>/run", methods=["POST"])
    def run_now(job_id):
        job = Job.query.get_or_404(job_id)
        job.status = "running"
        db.session.commit()

        from flask import current_app
        with current_app.app_context():
            log = run_task(job_id, job.module_path)
            status = log.status
            job.status = status
            job.last_run = datetime.utcnow()
            db.session.commit()

        flash(f"{job.name} executed — {status}", "success")
        return redirect(url_for("jobs_list"))

    @app.route("/logs")
    def logs_list():
        job_id = request.args.get("job_id")
        page = request.args.get("page", 1, type=int)
        query = RunLog.query.order_by(RunLog.started_at.desc())
        if job_id:
            query = query.filter_by(job_id=job_id)
        logs = query.paginate(page=page, per_page=20)
        jobs = Job.query.all()
        return render_template("logs.html", logs=logs, jobs=jobs, selected_job=job_id)

    @app.route("/api/status")
    def api_status():
        jobs = Job.query.all()
        return jsonify([j.to_dict() for j in jobs])

    @app.route("/api/logs/<job_id>")
    def api_logs(job_id):
        logs = RunLog.query.filter_by(job_id=job_id).order_by(RunLog.started_at.desc()).limit(50).all()
        return jsonify([l.to_dict() for l in logs])
