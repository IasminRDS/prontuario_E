import os
from flask import Flask
from flask_login import LoginManager
from dotenv import load_dotenv

from database.db import db
import models
from models.user import User

# principais
import routes.auth
from routes.pacientes import pacientes_bp
from routes.triagem import triagem_bp
from routes.atendimento import atendimento_bp
from routes.admin import admin_bp
from routes.prontuario import prontuario_bp
from routes.estoque import estoque_bp

# bloco 1
from routes.dashboard import dashboard_bp
from routes.alertas import alertas_bp
from routes.agenda import agenda_bp
from routes.leitos import leitos_bp
from routes.internacao import internacao_bp  # <- NOVO

# bloco 2
from routes.pronto_socorro import pronto_socorro_bp
from routes.exames import exames_bp
from routes.catalogo_exames import catalogo_exames_bp
from routes.catalogo_vacinas import catalogo_vacinas_bp

try:
    from routes.importacao import importacao_bp
except ModuleNotFoundError:
    from routes.importar import importacao_bp

# bloco 3
from routes.backup import backup_bp
from routes.auditoria import auditoria_bp

# novo
from routes.unidades import unidades_bp

load_dotenv()


def create_app():
    app = Flask(__name__, template_folder="templates", static_folder="static")

    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-change-me")
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
        "DATABASE_URL", "sqlite:///prontuario.db"
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["APP_ENV"] = os.environ.get("APP_ENV", "dev")
    app.config["PACIENTES_PER_PAGE"] = int(os.environ.get("PACIENTES_PER_PAGE", 20))

    db.init_app(app)

    login_manager = LoginManager()
    login_manager.login_view = "auth.login"
    login_manager.login_message = "Faça login para continuar."
    login_manager.login_message_category = "warning"
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        try:
            return User.query.get(int(user_id))
        except Exception:
            return None

    @app.context_processor
    def inject_available_endpoints():
        return {"available_endpoints": set(app.view_functions.keys())}

    # registro
    app.register_blueprint(routes.auth.auth_bp)
    app.register_blueprint(dashboard_bp)

    app.register_blueprint(alertas_bp)
    app.register_blueprint(agenda_bp)
    app.register_blueprint(internacao_bp)  # <- registra antes de leitos (opcional)
    app.register_blueprint(leitos_bp)  # <- /leitos/ redireciona para internacao.leitos

    app.register_blueprint(pronto_socorro_bp)
    app.register_blueprint(exames_bp)
    app.register_blueprint(catalogo_exames_bp)
    app.register_blueprint(catalogo_vacinas_bp)
    app.register_blueprint(unidades_bp)

    app.register_blueprint(importacao_bp)
    app.register_blueprint(backup_bp)
    app.register_blueprint(auditoria_bp)

    app.register_blueprint(pacientes_bp)
    app.register_blueprint(triagem_bp)
    app.register_blueprint(atendimento_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(prontuario_bp)
    app.register_blueprint(estoque_bp)

    with app.app_context():
        db.create_all()

    return app


app = create_app()

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
        debug=os.environ.get("FLASK_DEBUG", "1") == "1",
    )
