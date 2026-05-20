import os
from flask import Flask
from flask_wtf.csrf import CSRFProtect
from dotenv import load_dotenv

from config import get_config_class
from database.db import init_db

# Carrega as variáveis de ambiente
load_dotenv()

# Inicializa o CSRF
csrf = CSRFProtect()

def create_app():
    # Inicializa o Flask
    app = Flask(__name__, template_folder="templates", static_folder="static")
    csrf.init_app(app)

    # 1. Configurações (carregadas do seu config.py)
    config_obj = get_config_class()
    app.config.from_object(config_obj)

    # 2. Inicializa o Banco de Dados e Login Manager (via init_db do db.py)
    init_db(app)

    # Chama a função específica de configuração extra, se existir no config
    config_obj.init_app(app)

    # 3. Registro de Blueprints (Feito aqui para evitar importações circulares)
    # Recomendação: Agrupe os registros para manter o código limpo
    from routes.auth import auth_bp
    from routes.dashboard import dashboard_bp
    from routes.pacientes import pacientes_bp
    from routes.triagem import triagem_bp
    from routes.atendimento import atendimento_bp
    from routes.admin import admin_bp
    from routes.prontuario import prontuario_bp
    from routes.estoque import estoque_bp
    from routes.alertas import alertas_bp
    from routes.agenda import agenda_bp
    from routes.leitos import leitos_bp
    from routes.internacao import internacao_bp
    from routes.pronto_socorro import pronto_socorro_bp
    from routes.exames import exames_bp
    from routes.catalogo_exames import catalogo_exames_bp
    from routes.catalogo_vacinas import catalogo_vacinas_bp
    from routes.backup import backup_bp
    from routes.auditoria import auditoria_bp
    from routes.unidades import unidades_bp

    try:
        from routes.importacao import importacao_bp
    except ModuleNotFoundError:
        from routes.importar import importacao_bp

    # Lista de blueprints para registro
    blueprints = [
        auth_bp, dashboard_bp, pacientes_bp, triagem_bp, atendimento_bp,
        admin_bp, prontuario_bp, estoque_bp, alertas_bp, agenda_bp,
        leitos_bp, internacao_bp, pronto_socorro_bp, exames_bp,
        catalogo_exames_bp, catalogo_vacinas_bp, backup_bp,
        auditoria_bp, unidades_bp, importacao_bp
    ]

    for bp in blueprints:
        app.register_blueprint(bp)

    @app.context_processor
    def inject_available_endpoints():
        return {"available_endpoints": set(app.view_functions.keys())}

    return app

# O app é criado chamando a fábrica
app = create_app()

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
        debug=os.environ.get("FLASK_DEBUG", "1") == "1",
    )