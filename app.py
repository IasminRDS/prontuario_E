# -*- coding: utf-8 -*-
"""
Sistema de Prontuário Único - SUS
Painel Estadual Integrado com IA
Author: GitHub Copilot
Version: 2.0.0
Enhanced with dynamic features, error handling, and professional logging
"""

from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
from database.db import db, login_manager, init_db
from config import get_config
import os
import sys
import logging
from datetime import datetime
from functools import wraps

# ========== CONFIGURAÇÃO DE LOGGING ==========
def setup_logging(app):
    """Configura logging profissional com múltiplos handlers"""
    if not app.debug:
        # Criar diretório de logs se não existir
        if not os.path.exists('logs'):
            os.mkdir('logs')
        
        # Handler para arquivo
        from logging.handlers import RotatingFileHandler
        file_handler = RotatingFileHandler(
            'logs/prontuario.log',
            maxBytes=10240000,  # 10MB
            backupCount=10
        )
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [%(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        
        # Handler para erros críticos
        error_handler = RotatingFileHandler(
            'logs/errors.log',
            maxBytes=5120000,  # 5MB
            backupCount=10
        )
        error_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [%(pathname)s:%(lineno)d]'
        ))
        error_handler.setLevel(logging.ERROR)
        app.logger.addHandler(error_handler)
        
        app.logger.setLevel(logging.INFO)
        app.logger.info('=' * 60)
        app.logger.info('SISTEMA DE PRONTUÁRIO ÚNICO - SUS')
        app.logger.info(f'Iniciado em: {datetime.now().strftime("%d/%m/%Y %H:%M:%S")}')
        app.logger.info('=' * 60)


def create_app():
    """Factory pattern para criar a aplicação Flask com configurações otimizadas"""
    app = Flask(__name__)
    
    # ========== CONFIGURAÇÕES BÁSICAS ==========
    config_class = get_config()
    app.config.from_object(config_class)
    
    # CORS para APIs
    CORS(app, resources={r"/api/*": {"origins": "*"}})
    
    # Inicializar extensões
    init_db(app)
    setup_logging(app)
    
    # ========== BANNER DE INICIALIZAÇÃO ==========
    banner = """
    ╔════════════════════════════════════════════════════════════╗
    ║  🏥 SISTEMA DE PRONTUÁRIO ÚNICO - SUS                      ║
    ║  📊 Painel Estadual Integrado com IA                       ║
    ║  ✨ Versão 2.0.0                                           ║
    ║  🚀 Status: Pronto para Operação                           ║
    ╚════════════════════════════════════════════════════════════╝
    """
    print(banner)
    
    # ========== LOGIN MANAGER ==========
    @login_manager.user_loader
    def load_user(user_id):
        from models.user import User
        return User.query.get(int(user_id))
    
    @login_manager.unauthorized_handler
    def unauthorized():
        return jsonify({"error": "Não autenticado"}), 401
    
    # ========== REGISTRAR BLUEPRINTS ==========
    
    # Rotas principais
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
    from routes.dashboard_estadual import dash_estadual_bp
    from routes.transferencia import transferencia_bp
    from routes.regulacao import regulacao_bp
    from routes.gestao_unidades import gestao_unidades_bp
    from routes.relatorio_estadual import rel_estadual_bp
    
    # Novas APIs
    from routes.api_kpi import api_kpi_bp
    from routes.api_alertas import api_alertas_bp
    from routes.api_predicoes import api_predicoes_bp
    from routes.api_permissoes import api_permissoes_bp
    from routes.api_vagas import api_vagas_bp
    from routes.api_geo import api_geo_bp
    
    # Lista de blueprints para registro dinâmico
    blueprints = [
        # Rotas principais
        auth_bp, pacientes_bp, prontuario_bp, dashboard_bp, pdf_bp, admin_bp,
        agendamento_bp, vacinas_bp, triagem_bp, exames_bp, encaminhamentos_bp,
        medicamentos_bp, relatorios_bp, importar_bp, backup_bp, configuracoes_bp,
        internacao_bp, pres_hosp_bp, cirurgia_bp, estoque_bp, faturamento_bp,
        ps_bp, rel_hosp_bp, notif_bp, dash_estadual_bp, transferencia_bp,
        regulacao_bp, gestao_unidades_bp, rel_estadual_bp,
        # Novas APIs
        api_kpi_bp, api_alertas_bp, api_predicoes_bp, 
        api_permissoes_bp, api_vagas_bp, api_geo_bp
    ]
    
    print(f"\n📚 Registrando {len(blueprints)} blueprints...")
    for blueprint in blueprints:
        try:
            app.register_blueprint(blueprint)
            print(f"  ✓ {blueprint.name:30} | Prefixo: {blueprint.url_prefix or 'raiz'}")
        except Exception as e:
            print(f"  ✗ {blueprint.name:30} | Erro: {e}")
            app.logger.error(f"Erro ao registrar blueprint {blueprint.name}: {e}")
    
    # ========== INICIALIZAR BANCO DE DADOS ==========
    print("\n🗄️  Inicializando banco de dados...")
    with app.app_context():
        try:
            # 1. Criar tabelas
            db.create_all()
            print("  ✓ Tabelas criadas/verificadas")
            
            # 2. Seed de permissões e roles
            try:
                from seeds.seed_permissoes import seed_permissoes
                seed_permissoes()
                print("  ✓ Permissões carregadas")
            except Exception as e:
                print(f"  ⚠️  Permissões: {e}")
                app.logger.warning(f"Erro ao carregar permissões: {e}")
            
            # 3. Seed de vagas
            try:
                from models.vaga import Vaga
                if Vaga.query.count() == 0:
                    from seeds.seed_vagas import seed_vagas
                    seed_vagas()
                    print("  ✓ Vagas de teste carregadas")
            except Exception as e:
                print(f"  ⚠️  Vagas: {e}")
                app.logger.warning(f"Erro ao carregar vagas: {e}")
            
            # 4. Otimizar SQLite
            if 'sqlite' in app.config['SQLALCHEMY_DATABASE_URI']:
                from database.sqlite_optimize import otimizar_sqlite
                otimizar_sqlite()
                print("  ✓ SQLite otimizado")
        except Exception as e:
            print(f"  ✗ Erro ao inicializar banco: {e}")
            app.logger.critical(f"Erro crítico ao inicializar banco: {e}")
            sys.exit(1)
    
    # ========== INICIAR SCHEDULER (Background Tasks) ==========
    print("\n⏲️  Configurando scheduler...")
    if not app.debug or os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
        try:
            from tasks.scheduler import agendar_tarefas
            agendar_tarefas(app)
            print("  ✓ Scheduler iniciado")
            print("    ├─ KPIs (a cada hora)")
            print("    ├─ Alertas (a cada 30 minutos)")
            print("    ├─ Predições (diariamente 23:00)")
            print("    └─ Demanda (a cada hora)")
        except Exception as e:
            print(f"  ⚠️  Scheduler não iniciou: {e}")
            app.logger.warning(f"Scheduler não iniciou: {e}")
    
    # ========== ERRO HANDLERS - 4XX ==========
    
    @app.errorhandler(400)
    def bad_request(e):
        """Requisição inválida/malformada"""
        app.logger.warning(f"400 Bad Request: {request.path}")
        if request.is_json:
            return jsonify({"error": "Requisição inválida"}), 400
        return render_template('errors/400.html', error=str(e)), 400
    
    @app.errorhandler(401)
    def unauthorized(e):
        """Usuário não autenticado"""
        app.logger.warning(f"401 Unauthorized: {request.path}")
        if request.is_json:
            return jsonify({"error": "Não autenticado"}), 401
        return render_template('errors/401.html', error=str(e)), 401
    
    @app.errorhandler(403)
    def forbidden(e):
        """Acesso não autorizado"""
        app.logger.warning(f"403 Forbidden: {request.path}")
        if request.is_json:
            return jsonify({"error": "Acesso proibido"}), 403
        return render_template('errors/403.html', error=str(e)), 403
    
    @app.errorhandler(404)
    def not_found(e):
        """Recurso não encontrado"""
        app.logger.info(f"404 Not Found: {request.path}")
        if request.is_json:
            return jsonify({"error": "Recurso não encontrado"}), 404
        return render_template('errors/404.html', error=str(e)), 404
    
    @app.errorhandler(405)
    def method_not_allowed(e):
        """Método HTTP não permitido"""
        app.logger.warning(f"405 Method Not Allowed: {request.method} {request.path}")
        if request.is_json:
            return jsonify({"error": "Método não permitido"}), 405
        return render_template('errors/405.html', error=str(e)), 405
    
    @app.errorhandler(408)
    def request_timeout(e):
        """Timeout na requisição"""
        app.logger.error(f"408 Request Timeout: {request.path}")
        if request.is_json:
            return jsonify({"error": "Requisição expirou"}), 408
        return render_template('errors/408.html', error=str(e)), 408
    
    @app.errorhandler(429)
    def too_many_requests(e):
        """Muitas requisições - Rate limit"""
        app.logger.warning(f"429 Too Many Requests: {request.path}")
        if request.is_json:
            return jsonify({"error": "Muitas requisições"}), 429
        return render_template('errors/429.html', error=str(e)), 429
    
    # ========== ERRO HANDLERS - 5XX ==========
    
    @app.errorhandler(500)
    def server_error(e):
        """Erro interno do servidor"""
        app.logger.error(f"500 Internal Server Error: {request.path}", exc_info=True)
        if request.is_json:
            return jsonify({"error": "Erro interno do servidor"}), 500
        return render_template('errors/500.html', error=str(e)), 500
    
    @app.errorhandler(501)
    def not_implemented(e):
        """Funcionalidade não implementada"""
        app.logger.warning(f"501 Not Implemented: {request.path}")
        if request.is_json:
            return jsonify({"error": "Não implementado"}), 501
        return render_template('errors/501.html', error=str(e)), 501
    
    @app.errorhandler(502)
    def bad_gateway(e):
        """Gateway inválido"""
        app.logger.error(f"502 Bad Gateway: {request.path}")
        if request.is_json:
            return jsonify({"error": "Gateway inválido"}), 502
        return render_template('errors/502.html', error=str(e)), 502
    
    @app.errorhandler(503)
    def service_unavailable(e):
        """Serviço indisponível"""
        app.logger.error(f"503 Service Unavailable: {request.path}")
        if request.is_json:
            return jsonify({"error": "Serviço indisponível"}), 503
        return render_template('errors/503.html', error=str(e)), 503
    
    @app.errorhandler(504)
    def gateway_timeout(e):
        """Timeout do gateway"""
        app.logger.error(f"504 Gateway Timeout: {request.path}")
        if request.is_json:
            return jsonify({"error": "Timeout do gateway"}), 504
        return render_template('errors/504.html', error=str(e)), 504
    
    # ========== CONTEXT PROCESSORS ==========
    @app.context_processor
    def inject_user():
        """Injeta usuário atual no contexto de templates"""
        from flask_login import current_user
        return dict(current_user=current_user)
    
    @app.context_processor
    def inject_config():
        """Injeta configurações da aplicação no contexto"""
        return dict(
            app_name="Prontuário Único SUS",
            app_version="2.0.0",
            year=datetime.now().year
        )
    
    # ========== REQUEST HOOKS ==========
    @app.before_request
    def before_request():
        """Hook executado antes de cada requisição"""
        from flask_login import current_user
        if current_user.is_authenticated:
            current_user.last_activity = datetime.now()
            db.session.commit()
    
    @app.after_request
    def after_request(response):
        """Hook executado após cada requisição"""
        # Headers de segurança
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        return response
    
    # ========== ROTAS UTILITÁRIAS ==========
    
    @app.route('/health')
    def health():
        """Verifica a saúde da aplicação"""
        return jsonify({
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "version": "2.0.0"
        }), 200
    
    @app.route('/api/status')
    def api_status():
        """Status da API em JSON"""
        try:
            # Teste de banco de dados
            from models.user import User
            User.query.first()
            db_status = "ok"
        except:
            db_status = "error"
        
        return jsonify({
            "status": "running",
            "database": db_status,
            "timestamp": datetime.now().isoformat(),
            "version": "2.0.0"
        }), 200
    
    print("\n" + "="*60)
    print("  ✓✓✓ SISTEMA PRONTO PARA OPERAÇÃO ✓✓✓")
    print("="*60 + "\n")
    
    return app


# ========== FACTORY - Cria a app ==========
app = create_app()


# ========== PONTO DE ENTRADA - Railway/Render/Gunicorn ==========
if __name__ == '__main__':
    # Detectar ambiente
    is_production = bool(os.environ.get('RAILWAY_ENVIRONMENT') or 
                        os.environ.get('RENDER') or 
                        os.environ.get('PRODUCTION'))
    
    debug = not is_production
    port = int(os.environ.get('PORT', 5000))
    host = os.environ.get('HOST', '0.0.0.0')
    
    # Imprimir informações de inicialização
    env_str = '🔵 DEVELOPMENT' if debug else '🔴 PRODUCTION'
    print(f"\n{env_str}")
    print(f"🌐 Servidor: {host}:{port}")
    print(f"📍 URL: http://localhost:{port}")
    print(f"⏰ Iniciado em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print(f"📋 Debug: {'Ativado' if debug else 'Desativado'}\n")
    
    # Iniciar servidor
    try:
        app.run(
            debug=debug,
            host=host,
            port=port,
            use_reloader=debug,
            use_debugger=debug
        )
    except KeyboardInterrupt:
        print("\n\n👋 Sistema encerrado pelo usuário")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Erro ao iniciar servidor: {e}")
        app.logger.critical(f"Erro crítico ao iniciar servidor: {e}", exc_info=True)
        sys.exit(1)