from flask import Blueprint, current_app, render_template
from flask_login import login_required

audit_bp = Blueprint("audit", __name__, url_prefix="/audit")


@audit_bp.get("")
@login_required
def audit_log():
    audit_service = current_app.extensions["audit_service"]
    return render_template(
        "audit/index.html",
        entries=audit_service.recent_entries(limit=50),
        errors=audit_service.recent_entries(limit=10, errors_only=True),
    )
