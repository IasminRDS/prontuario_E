from flask import Blueprint, render_template
from flask_login import login_required

leitos_bp = Blueprint("leitos", __name__, url_prefix="/leitos")


@leitos_bp.get("/")
@login_required
def index():
    resumo = {
        "total": 0,
        "ocupados": 0,
        "livres": 0,
        "higienizacao": 0,
    }
    return render_template("leitos/index.html", resumo=resumo)