"""
Topic routes.

Handles the landing page (topic list with search/sort) and full CRUD
for topics. The mind map page itself (`/topic/<id>`) is added in
Phase 2.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify

from services import topic_service
from services.topic_service import TopicValidationError

topics_bp = Blueprint("topics", __name__)


@topics_bp.route("/")
def index():
    search = request.args.get("q", "").strip()
    sort_by = request.args.get("sort_by", "updated_at")
    sort_dir = request.args.get("sort_dir", "desc")

    topics = topic_service.get_all_topics(search=search, sort_by=sort_by, sort_dir=sort_dir)

    return render_template(
        "index.html",
        topics=topics,
        search=search,
        sort_by=sort_by,
        sort_dir=sort_dir,
    )


@topics_bp.route("/topics/new", methods=["GET", "POST"])
def new_topic():
    if request.method == "POST":
        try:
            topic = topic_service.create_topic(
                name=request.form.get("name"),
                description=request.form.get("description"),
            )
            flash(f'Topic "{topic.name}" created successfully.', "success")
            return redirect(url_for("topics.index"))
        except TopicValidationError as e:
            flash(str(e), "danger")
            return render_template(
                "topic_form.html",
                mode="create",
                topic=None,
                form_name=request.form.get("name", ""),
                form_description=request.form.get("description", ""),
            )

    return render_template("topic_form.html", mode="create", topic=None, form_name="", form_description="")


@topics_bp.route("/topics/<int:topic_id>/edit", methods=["GET", "POST"])
def edit_topic(topic_id):
    topic = topic_service.get_topic_or_404(topic_id)

    if request.method == "POST":
        try:
            topic = topic_service.update_topic(
                topic_id,
                name=request.form.get("name"),
                description=request.form.get("description"),
            )
            flash(f'Topic "{topic.name}" updated successfully.', "success")
            return redirect(url_for("topics.index"))
        except TopicValidationError as e:
            flash(str(e), "danger")
            return render_template(
                "topic_form.html",
                mode="edit",
                topic=topic,
                form_name=request.form.get("name", ""),
                form_description=request.form.get("description", ""),
            )

    return render_template(
        "topic_form.html",
        mode="edit",
        topic=topic,
        form_name=topic.name,
        form_description=topic.description or "",
    )


@topics_bp.route("/topics/<int:topic_id>/delete", methods=["POST"])
def delete_topic(topic_id):
    topic = topic_service.get_topic_or_404(topic_id)
    name = topic.name
    topic_service.delete_topic(topic_id)
    flash(f'Topic "{name}" deleted.', "success")
    return redirect(url_for("topics.index"))
