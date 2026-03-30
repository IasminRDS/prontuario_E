# -*- coding: utf-8 -*-
"""
Sistema de Prontuário Único - SUS
Painel Estadual Integrado com IA
Author: GitHub Copilot
Version: 1.0.0
"""

from flask import Flask, render_template
from database.db import db, login_manager, init_db
from config import get_config
import os
import sys
from datetime import datetime

def create_app():
    """Factory pattern para criar a aplicação Flask"""
    app = Flask(__name__)
    
    # ========== CONFIGURAÇÕES ==========
    config_class = get_config()
    app.config.from_object(config_class)
    
    # Inicializar extensões
    init_db(app)
    
    print("\n" + "="*60)
    print("  SISTEMA DE PRONTUÁRIO ÚNICO - SUS")
    print("  Painel Estadual Integrado")
    print("="*60 + "\n")
    
    # ========== LOGIN MANAGER ==========
    @login_manager.user_loader
    def load_user(user_id):
        from models.user import User
        return User.query.get(int(user_id))
    
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
    
    # Novas APIs (Novos Módulos)
    from routes.api_kpi import api_kpi_bp
    from routes.api_alertas import api_alertas_bp
    from routes.api_predicoes import api_predicoes_bp
    from routes.api_permissoes import api_permissoes_bp
    from routes.api_vagas import api_vagas_bp
    from routes.api_geo import api_geo_bp
    
    # Registrar todos os blueprints
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
    
    print("📚 Registrando blueprints...")
    for blueprint in blueprints:
        app.register_blueprint(blueprint)
        print(f"  ✓ {blueprint.name}")
    
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
                print(f"  ⚠️  Erro ao carregar permissões: {e}")
            
            # 3. Seed de vagas (opcional)
            try:
                from models.vaga import Vaga
                if Vaga.query.count() == 0:
                    from seeds.seed_vagas import seed_vagas
                    seed_vagas()
                    print("  ✓ Vagas de teste carregadas")
            except Exception as e:
                print(f"  ⚠️  Erro ao carregar vagas: {e}")
            
            # 4. Otimizar SQLite
            if 'sqlite' in app.config['SQLALCHEMY_DATABASE_URI']:
                from database.sqlite_optimize import otimizar_sqlite
                otimizar_sqlite()
                print("  ✓ SQLite otimizado")
        except Exception as e:
            print(f"  ✗ Erro ao inicializar banco: {e}")
            sys.exit(1)
    
    # ========== INICIAR SCHEDULER (Background Tasks) ==========
    print("\n⏲️  Configurando scheduler...")
    if not app.debug or os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
        try:
            from tasks.scheduler import agendar_tarefas
            agendar_tarefas(app)
            print("  ✓ Scheduler iniciado")
            print("    - KPIs (a cada hora)")
            print("    - Alertas (a cada 30 minutos)")
            print("    - Predições (diariamente 23:00)")
            print("    - Demanda (a cada hora)")
        except Exception as e:
            print(f"  ⚠️  Scheduler não iniciou: {e}")
    
    # ========== ERROR HANDLERS ==========
    @app.errorhandler(401)
    def unauthorized(e):
        return render_template('errors/401.html'), 401
    
    @app.errorhandler(403)
    def forbidden(e):
        return render_template('errors/403.html'), 403
    
    @app.errorhandler(404)
    def not_found(e):
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(500)
    def server_error(e):
        return render_template('errors/500.html'), 500
    
    # ========== CONTEXT PROCESSORS ==========
    @app.context_processor
    def inject_user():
        from flask_login import current_user
        return dict(current_user=current_user)
    
    @app.context_processor
    def inject_config():
        return dict(
            app_name="Prontuário Único SUS",
            app_version="1.0.0"
        )
    
    # ========== LOGGING ==========
    if not app.debug:
        import logging
        from logging.handlers import RotatingFileHandler
        
        file_handler = RotatingFileHandler('prontuario.log', maxBytes=10240000, backupCount=10)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info('Prontuário iniciado')
    
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
    print(f"⏰ Iniciado em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
    
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
        sys.exit(1)