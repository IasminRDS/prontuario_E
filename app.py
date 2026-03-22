from flask import Flask, render_template
from database.db import db, login_manager, init_db
import os

def create_app():
    app = Flask(__name__)

    # Configurações
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'sus-prontuario-secret-2024')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
        'DATABASE_URL', 'sqlite:///prontuario.db'
    )
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['WTF_CSRF_ENABLED'] = False  # Habilitar em produção

    # Login manager
    @login_manager.user_loader
    def load_user(user_id):
        from models.user import User
        return User.query.get(int(user_id))

    # Inicializar banco
    init_db(app)

    # Registrar blueprints
    from routes.auth import auth_bp
    from routes.pacientes import pacientes_bp
    from routes.prontuario import prontuario_bp
    from routes.dashboard import dashboard_bp
    from routes.pdf import pdf_bp
    from routes.admin import admin_bp
    from routes.agendamento import agendamento_bp
    from routes.vacinas import vacinas_bp
    from routes.triagem import triagem_bp
    from routes.exames import exames_bp
    from routes.encaminhamentos import encaminhamentos_bp
    from routes.medicamentos import medicamentos_bp
    from routes.relatorios import relatorios_bp
    from routes.importar import importar_bp
    from routes.backup import backup_bp
    from routes.configuracoes import configuracoes_bp
    from routes.internacao import internacao_bp
    from routes.prescricao_hosp import pres_hosp_bp
    from routes.cirurgia import cirurgia_bp
    from routes.estoque import estoque_bp
    from routes.faturamento import faturamento_bp
    from routes.pronto_socorro import ps_bp
    from routes.relatorios_hosp import rel_hosp_bp
    from routes.notificacoes import notif_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(pacientes_bp)
    app.register_blueprint(prontuario_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(pdf_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(agendamento_bp)
    app.register_blueprint(vacinas_bp)
    app.register_blueprint(triagem_bp)
    app.register_blueprint(exames_bp)
    app.register_blueprint(encaminhamentos_bp)
    app.register_blueprint(medicamentos_bp)
    app.register_blueprint(relatorios_bp)
    app.register_blueprint(importar_bp)
    app.register_blueprint(backup_bp)
    app.register_blueprint(configuracoes_bp)
    app.register_blueprint(internacao_bp)
    app.register_blueprint(pres_hosp_bp)
    app.register_blueprint(cirurgia_bp)
    app.register_blueprint(estoque_bp)
    app.register_blueprint(faturamento_bp)
    app.register_blueprint(ps_bp)
    app.register_blueprint(rel_hosp_bp)
    app.register_blueprint(notif_bp)

    # Error handlers
    @app.errorhandler(403)
    def forbidden(e):
        return render_template('errors/403.html'), 403

    @app.errorhandler(404)
    def not_found(e):
        return render_template('errors/404.html'), 404

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000)
