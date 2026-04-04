from datetime import date
from flask import Blueprint, render_template
from flask_login import login_required

agenda_bp = Blueprint("agenda", __name__, url_prefix="/agenda")


@agenda_bp.get("/")
@login_required
def index():
    eventos = []
    return render_template("agenda/index.html", eventos=eventos, data_hoje=date.today().strftime("%d/%m/%Y"))