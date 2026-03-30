from flask import Flask, render_template
from database.db import db, login_manager, init_db
import os
from logging.handlers import RotatingFileHandler
import logging
from datetime import datetime

def create_app():
    """Factory para criar a aplicação Flask com todas as configurações"""
    app = Flask(__name__)

    # Detectar ambiente
    is_production = (
        os.environ.get('RAILWAY_ENVIRONMENT') 
        or os.environ.get('RENDER') 
        or os.environ.get('PRODUCTION')
    )

    # ================== CONFIGURAÇÕES ==================
    app.config['SECRET_KEY'] = os.environ.get(
        'SECRET_KEY', 
        'sus-prontuario-secret-2024-mude-em-producao'
    )

    # Banco de dados
    database_url = os.environ.get('DATABASE_URL', 'sqlite:///prontuario.db')
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['WTF_CSRF_ENABLED'] = False

    # ================== LOGGING ==================
    log_dir = 'logs'
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # Handler para logs gerais
    file_handler = RotatingFileHandler(
        os.path.join(log_dir, 'prontuario.log'),
        maxBytes=10485760,  # 10MB
        backupCount=10
    )
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(logging.INFO)

    # Handler para erros
    error_handler = RotatingFileHandler(
        os.path.join(log_dir, 'errors.log'),
        maxBytes=10485760,  # 10MB
        backupCount=10
    )
    error_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    error_handler.setLevel(logging.ERROR)

    # Adicionar handlers ao logger da app
    if not app.logger.hasHandlers():
        app.logger.addHandler(file_handler)
        app.logger.addHandler(error_handler)
        app.logger.setLevel(logging.INFO)

    # ================== LOGIN MANAGER ==================
    @login_manager.user_loader
    def load_user(user_id):
        from models.user import User
        return User.query.get(int(user_id))

    # Inicializar banco
    init_db(app)

    # ================== BLUEPRINTS (23 rotas) ==================
    blueprints_list = [
        ('routes.auth', 'auth_bp'),
        ('routes.pacientes', 'pacientes_bp'),
        ('routes.prontuario', 'prontuario_bp'),
        ('routes.dashboard', 'dashboard_bp'),
        ('routes.pdf', 'pdf_bp'),
        ('routes.admin', 'admin_bp'),
        ('routes.agendamento', 'agendamento_bp'),
        ('routes.vacinas', 'vacinas_bp'),
        ('routes.triagem', 'triagem_bp'),
        ('routes.exames', 'exames_bp'),
        ('routes.encaminhamentos', 'encaminhamentos_bp'),
        ('routes.medicamentos', 'medicamentos_bp'),
        ('routes.relatorios', 'relatorios_bp'),
        ('routes.importar', 'importar_bp'),
        ('routes.backup', 'backup_bp'),
        ('routes.configuracoes', 'configuracoes_bp'),
        ('routes.internacao', 'internacao_bp'),
        ('routes.prescricao_hosp', 'pres_hosp_bp'),
        ('routes.cirurgia', 'cirurgia_bp'),
        ('routes.estoque', 'estoque_bp'),
        ('routes.faturamento', 'faturamento_bp'),
        ('routes.pronto_socorro', 'ps_bp'),
        ('routes.relatorios_hosp', 'rel_hosp_bp'),
        ('routes.notificacoes', 'notif_bp'),
    ]

    registered_blueprints = []
    for module_name, blueprint_var in blueprints_list:
        try:
            module = __import__(module_name, fromlist=[blueprint_var])
            blueprint = getattr(module, blueprint_var)
            app.register_blueprint(blueprint)
            registered_blueprints.append(module_name)
            app.logger.info(f"✓ Blueprint registrado: {module_name}")
        except ImportError as e:
            app.logger.error(f"✗ Erro ao importar {module_name}: {e}")
        except Exception as e:
            app.logger.error(f"✗ Erro ao registrar {module_name}: {e}")

    # ================== CONTEXT PROCESSORS ==================
    @app.context_processor
    def inject_globals():
        return {
            'current_user': None,
            'app_name': 'Sistema de Prontuário Único',
            'app_version': '2.0.0',
            'year': datetime.now().year,
        }

    # ================== REQUEST HOOKS ==================
    @app.before_request
    def before_request():
        from flask import request, g
        g.start_time = datetime.now()
        app.logger.debug(f"Requisição: {request.method} {request.path}")

    @app.after_request
    def after_request(response):
        # Headers de segurança
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        
        from flask import g
        if hasattr(g, 'start_time'):
            duration = (datetime.now() - g.start_time).total_seconds()
            app.logger.debug(f"Resposta: {response.status_code} ({duration:.2f}s)")
        
        return response

    # ================== ERROR HANDLERS ==================
    @app.errorhandler(400)
    def bad_request(e):
        app.logger.warning(f"400 Bad Request: {e}")
        return render_template('errors/400.html', error=e), 400

    @app.errorhandler(401)
    def unauthorized(e):
        app.logger.warning(f"401 Unauthorized: {e}")
        return render_template('errors/401.html', error=e), 401

    @app.errorhandler(403)
    def forbidden(e):
        app.logger.warning(f"403 Forbidden: {e}")
        return render_template('errors/403.html', error=e), 403

    @app.errorhandler(404)
    def not_found(e):
        app.logger.warning(f"404 Not Found: {e}")
        return render_template('errors/404.html', error=e), 404

    @app.errorhandler(405)
    def method_not_allowed(e):
        app.logger.warning(f"405 Method Not Allowed: {e}")
        return render_template('errors/405.html', error=e), 405

    @app.errorhandler(408)
    def request_timeout(e):
        app.logger.error(f"408 Request Timeout: {e}")
        return render_template('errors/408.html', error=e), 408

    @app.errorhandler(429)
    def too_many_requests(e):
        app.logger.warning(f"429 Too Many Requests: {e}")
        return render_template('errors/429.html', error=e), 429

    @app.errorhandler(500)
    def internal_error(e):
        app.logger.error(f"500 Internal Server Error: {e}")
        return render_template('errors/500.html', error=e), 500

    @app.errorhandler(501)
    def not_implemented(e):
        app.logger.error(f"501 Not Implemented: {e}")
        return render_template('errors/501.html', error=e), 501

    @app.errorhandler(502)
    def bad_gateway(e):
        app.logger.error(f"502 Bad Gateway: {e}")
        return render_template('errors/502.html', error=e), 502

    @app.errorhandler(503)
    def service_unavailable(e):
        app.logger.error(f"503 Service Unavailable: {e}")
        return render_template('errors/503.html', error=e), 503

    @app.errorhandler(504)
    def gateway_timeout(e):
        app.logger.error(f"504 Gateway Timeout: {e}")
        return render_template('errors/504.html', error=e), 504

    # ================== HEALTH CHECK ==================
    @app.route('/health')
    def health():
        """Verifica se a aplicação está saudável"""
        return {'status': 'healthy', 'timestamp': datetime.now().isoformat()}, 200

    @app.route('/api/status')
    def api_status():
        """Status detalhado da API"""
        try:
            # Teste de conexão com BD
            db.session.execute('SELECT 1')
            db_status = 'connected'
        except Exception as e:
            db_status = f'error: {str(e)}'
            app.logger.error(f"BD desconectado: {e}")

        return {
            'status': 'operational',
            'app_name': 'Sistema de Prontuário Único',
            'version': '2.0.0',
            'database': db_status,
            'timestamp': datetime.now().isoformat(),
            'blueprints_registered': len(registered_blueprints),
        }, 200

    # ================== BANNER ==================
    if not is_production:
        app.logger.info("""
╔════════════════════════════════════╗
║  🏥 SISTEMA DE PRONTUÁRIO ÚNICO    ║
║  📊 Painel Estadual Integrado      ║
║  ✨ Versão 2.0.0                  ║
║  🚀 Status: Pronto para Operação   ║
╚════════════════════════════════════╝
        """)

    return app


# ================== EXPORT PARA GUNICORN/RAILWAY ==================
app = create_app()


# ================== EXECUÇÃO LOCAL ==================
if __name__ == '__main__':
    debug = not (os.environ.get('RAILWAY_ENVIRONMENT') or os.environ.get('PRODUCTION'))
    port = int(os.environ.get('PORT', 5000))
    host = os.environ.get('HOST', '0.0.0.0')
    
    app.run(
        debug=debug,
        host=host,
        port=port,
        threaded=True
    )