"""
Mind map routes.

`GET /topic/<id>` renders the interactive mind map page for a topic.
`POST /topic/<id>/mindmap/save` accepts the full current tree (as
produced by Mind Elixir's `getData().nodeData`) and persists it.
"""
from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from models import UserMapping
from services import topic_service
from services.topic_service import TopicValidationError
from storage import get_storage

topics_bp = Blueprint("topics", __name__)


def _current_user_and_storage():
    """Return (mapping, storage) for the logged-in user, or (None, None) if not authenticated."""
    user_id = session.get("user_id")
    if not user_id:
        return None, None
    mapping = UserMapping.query.get(user_id)
    if not mapping:
        session.clear()
        return None, None
    access_token = session.get("access_token")
    if not access_token:
        return None, None
    return mapping, get_storage(mapping, access_token)


@topics_bp.route("/")
def index():
    mapping, storage = _current_user_and_storage()
    if storage is None:
        return render_template("index.html", topics=[], search="", sort_by="updated_at", sort_dir="desc")

    search = request.args.get("q", "").strip()
    sort_by = request.args.get("sort_by", "updated_at")
    sort_dir = request.args.get("sort_dir", "desc")
    topics = topic_service.get_all_topics(storage, search=search, sort_by=sort_by, sort_dir=sort_dir)
    return render_template(
        "index.html",
        topics=topics,
        search=search,
        sort_by=sort_by,
        sort_dir=sort_dir,
    )
    
@topics_bp.route("/topics/new", methods=["GET", "POST"])
def new_topic():
    mapping, storage = _current_user_and_storage()
    if storage is None:
        flash("Please sign in to continue.", "warning")
        return redirect(url_for("topics.index"))

    if request.method == "POST":
        try:
            topic = topic_service.create_topic(
                storage,
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

    return render_template(
        "topic_form.html",
        mode="create",
        topic=None,
        form_name="",
        form_description="",
    )
    
@topics_bp.route("/topics/<int:topic_id>/edit", methods=["GET", "POST"])
def edit_topic(topic_id):
    mapping, storage = _current_user_and_storage()
    if storage is None:
        flash("Please sign in to continue.", "warning")
        return redirect(url_for("topics.index"))

    topic = topic_service.get_topic_or_404(storage, topic_id)

    if request.method == "POST":
        try:
            topic = topic_service.update_topic(
                storage,
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
    mapping, storage = _current_user_and_storage()
    if storage is None:
        flash("Please sign in to continue.", "warning")
        return redirect(url_for("topics.index"))

    topic = topic_service.get_topic_or_404(storage, topic_id)
    name = topic.name
    topic_service.delete_topic(storage, topic_id)
    flash(f'Topic "{name}" deleted.', "success")
    return redirect(url_for("topics.index"))
    
