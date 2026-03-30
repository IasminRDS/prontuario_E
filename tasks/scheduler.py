# -*- coding: utf-8 -*-
"""
Agendador de Tarefas (Scheduler)
Executa tarefas automáticas em tempo real
"""

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime, date, timedelta
from pytz import utc
import logging

logger = logging.getLogger(__name__)

def agendar_tarefas(app):
    """Inicializa e agenda todas as tarefas automáticas"""
    
    scheduler = BackgroundScheduler(timezone=utc)
    
    if scheduler.running:
        return
    
    print("\n⏲️  Configurando tarefas automáticas...\n")
    
    # ========== TAREFA 1: Atualizar KPIs a cada hora ==========
    def job_atualizar_kpis():
        with app.app_context():
            try:
                from models.kpi import KPI
                from models.unidade import Unidade
                from models.atendimento import Atendimento
                from models.internacao import Internacao, Leito
                from models.cirurgia import Cirurgia
                from models.pronto_socorro import AtendimentoPS
                from database.db import db
                
                unidades = Unidade.query.filter_by(ativo=True).all()
                hoje = date.today()
                
                for u in unidades:
                    kpi_existente = KPI.query.filter_by(unidade_id=u.id, data=hoje).first()
                    
                    atendimentos = Atendimento.query.filter(
                        Atendimento.unidade_id == u.id,
                        db.func.date(Atendimento.data_hora) == hoje
                    ).count()
                    
                    internacoes = Internacao.query.filter(
                        Internacao.unidade_id == u.id,
                        db.func.date(Internacao.data_entrada) == hoje
                    ).count()
                    
                    altas = Internacao.query.filter(
                        Internacao.unidade_id == u.id,
                        db.func.date(Internacao.data_alta) == hoje,
                        Internacao.status == 'alta'
                    ).count()
                    
                    obitos = Internacao.query.filter(
                        Internacao.unidade_id == u.id,
                        db.func.date(Internacao.data_alta) == hoje,
                        Internacao.status == 'obito'
                    ).count()
                    
                    cirurgias = Cirurgia.query.filter(
                        Cirurgia.unidade_id == u.id,
                        db.func.date(Cirurgia.data_agendada) == hoje,
                        Cirurgia.status == 'realizada'
                    ).count()
                    
                    ps = AtendimentoPS.query.filter(
                        AtendimentoPS.unidade_id == u.id,
                        db.func.date(AtendimentoPS.data_entrada) == hoje
                    ).count()
                    
                    total_leitos = Leito.query.filter_by(ativo=True).count()
                    leitos_ocupados = Leito.query.filter_by(ativo=True, status='ocupado').count()
                    taxa_ocupacao = round((leitos_ocupados / total_leitos * 100) if total_leitos else 0)
                    taxa_mortalidade = round((obitos / internacoes * 100) if internacoes > 0 else 0)
                    taxa_altas = round((altas / internacoes * 100) if internacoes > 0 else 0)
                    
                    if kpi_existente:
                        kpi_existente.atendimentos = atendimentos
                        kpi_existente.internacoes = internacoes
                        kpi_existente.altas = altas
                        kpi_existente.obitos = obitos
                        kpi_existente.cirurgias = cirurgias
                        kpi_existente.taxa_ocupacao = taxa_ocupacao
                        kpi_existente.taxa_mortalidade = taxa_mortalidade
                        kpi_existente.taxa_altas = taxa_altas
                        kpi_existente.ps_atendimentos = ps
                    else:
                        kpi = KPI(
                            unidade_id=u.id,
                            data=hoje,
                            atendimentos=atendimentos,
                            internacoes=internacoes,
                            altas=altas,
                            obitos=obitos,
                            cirurgias=cirurgias,
                            taxa_ocupacao=taxa_ocupacao,
                            taxa_mortalidade=taxa_mortalidade,
                            taxa_altas=taxa_altas,
                            ps_atendimentos=ps,
                        )
                        db.session.add(kpi)
                
                db.session.commit()
                logger.info("✓ KPIs atualizados")
            except Exception as e:
                logger.error(f"✗ Erro ao atualizar KPIs: {e}")
    
    # ========== TAREFA 2: Gerar alertas a cada 30 minutos ==========
    def job_gerar_alertas():
        with app.app_context():
            try:
                from models.alerta import Alerta, ConfiguradorAlerta
                from models.unidade import Unidade
                from models.internacao import Leito
                from database.db import db
                
                unidades = Unidade.query.filter_by(ativo=True).all()
                
                for u in unidades:
                    config = ConfiguradorAlerta.query.filter_by(unidade_id=u.id, ativo=True).all()
                    
                    for cfg in config:
                        if cfg.tipo == 'ocupacao':
                            total_leitos = Leito.query.filter_by(ativo=True).count()
                            leitos_ocu = Leito.query.filter_by(ativo=True, status='ocupado').count()
                            taxa = (leitos_ocu / total_leitos * 100) if total_leitos else 0
                            
                            if taxa >= cfg.limiar_maximo:
                                alerta_recente = Alerta.query.filter(
                                    Alerta.unidade_id == u.id,
                                    Alerta.tipo == 'ocupacao',
                                    Alerta.nivel == 2,
                                    Alerta.timestamp >= datetime.now() - timedelta(hours=1)
                                ).first()
                                
                                if not alerta_recente:
                                    alerta = Alerta(
                                        unidade_id=u.id,
                                        tipo='ocupacao',
                                        nivel=2,
                                        titulo=f'⚠️ CRÍTICO: Ocupação em {taxa:.0f}%',
                                        mensagem=f'{leitos_ocu} de {total_leitos} leitos ocupados',
                                        dados_json={'taxa': taxa, 'leitos': leitos_ocu, 'total': total_leitos}
                                    )
                                    db.session.add(alerta)
                            
                            elif taxa >= cfg.limiar_minimo:
                                alerta_recente = Alerta.query.filter(
                                    Alerta.unidade_id == u.id,
                                    Alerta.tipo == 'ocupacao',
                                    Alerta.nivel == 1,
                                    Alerta.timestamp >= datetime.now() - timedelta(hours=1)
                                ).first()
                                
                                if not alerta_recente:
                                    alerta = Alerta(
                                        unidade_id=u.id,
                                        tipo='ocupacao',
                                        nivel=1,
                                        titulo=f'ℹ️ Ocupação em {taxa:.0f}%',
                                        mensagem=f'{leitos_ocu} de {total_leitos} leitos ocupados',
                                    )
                                    db.session.add(alerta)
                
                db.session.commit()
                logger.info("✓ Alertas gerados")
            except Exception as e:
                logger.error(f"✗ Erro ao gerar alertas: {e}")
    
    # ========== TAREFA 3: Calcular predições diariamente ==========
    def job_calcular_predicoes():
        with app.app_context():
            try:
                from models.predicao import Predicao
                from models.kpi import KPI
                from models.unidade import Unidade
                from database.db import db
                import statistics
                
                def regressao_linear(valores):
                    if len(valores) < 2:
                        return valores[-1] if valores else 0
                    n = len(valores)
                    x = list(range(n))
                    y = valores
                    x_media = statistics.mean(x)
                    y_media = statistics.mean(y)
                    numerador = sum((x[i] - x_media) * (y[i] - y_media) for i in range(n))
                    denominador = sum((x[i] - x_media) ** 2 for i in range(n))
                    if denominador == 0:
                        return y_media
                    inclinacao = numerador / denominador
                    intercepto = y_media - inclinacao * x_media
                    return intercepto + inclinacao * n
                
                unidades = Unidade.query.filter_by(ativo=True).all()
                
                for u in unidades:
                    try:
                        data_inicio = date.today() - timedelta(days=30)
                        kpis = KPI.query.filter(
                            KPI.unidade_id == u.id,
                            KPI.data >= data_inicio
                        ).order_by(KPI.data).all()
                        
                        if len(kpis) >= 5:
                            ocupacoes = [k.taxa_ocupacao for k in kpis]
                            valor_pred_ocup = regressao_linear(ocupacoes)
                            
                            atendimentos = [k.atendimentos for k in kpis]
                            valor_pred_atend = regressao_linear(atendimentos)
                            
                            pred_ocup = Predicao(
                                unidade_id=u.id,
                                tipo='ocupacao',
                                data_predicao=date.today() + timedelta(days=1),
                                valor_predito=valor_pred_ocup,
                            )
                            pred_atend = Predicao(
                                unidade_id=u.id,
                                tipo='atendimentos',
                                data_predicao=date.today() + timedelta(days=1),
                                valor_predito=valor_pred_atend,
                            )
                            db.session.add(pred_ocup)
                            db.session.add(pred_atend)
                    except Exception as e:
                        logger.warning(f"Erro na unidade {u.nome}: {e}")
                
                db.session.commit()
                logger.info("✓ Predições calculadas")
            except Exception as e:
                logger.error(f"✗ Erro ao calcular predições: {e}")
    
    # ========== TAREFA 4: Atualizar demanda por região ==========
    def job_atualizar_demanda():
        with app.app_context():
            try:
                from models.localizacao import DemandaPorRegiao, Localizacao
                from models.vaga import Vaga, StatusVaga, SolicitacaoTransferencia
                from models.internacao import Internacao, Leito
                from models.atendimento import Atendimento
                from models.unidade import Unidade
                from database.db import db
                from sqlalchemy import func
                
                municipios = db.session.query(
                    Localizacao.municipio,
                    Localizacao.estado
                ).distinct().all()
                
                hoje = date.today()
                hora = datetime.now().hour
                
                for municipio, estado in municipios:
                    atendimentos_ps = db.session.query(func.count()).filter(
                        db.and_(
                            func.date(Atendimento.data_hora) == hoje,
                            Atendimento.unidade.has(municipio=municipio)
                        )
                    ).scalar() or 0
                    
                    internacoes = db.session.query(func.count()).filter(
                        db.and_(
                            func.date(Internacao.data_entrada) == hoje,
                            Internacao.unidade.has(municipio=municipio)
                        )
                    ).scalar() or 0
                    
                    transferencias = SolicitacaoTransferencia.query.filter(
                        db.and_(
                            SolicitacaoTransferencia.status == 'pendente',
                            SolicitacaoTransferencia.unidade_origem.has(municipio=municipio)
                        )
                    ).count()
                    
                    vagas_disp = Vaga.query.filter(
                        db.and_(
                            Vaga.status == StatusVaga.DISPONIVEL.value,
                            Vaga.unidade.has(municipio=municipio)
                        )
                    ).count()
                    
                    total_vagas = Vaga.query.filter(
                        Vaga.unidade.has(municipio=municipio)
                    ).count()
                    
                    taxa_ocupacao = ((total_vagas - vagas_disp) / total_vagas * 100) if total_vagas > 0 else 0
                    score = (atendimentos_ps * 0.3 + internacoes * 0.4 + transferencias * 0.3) * 100
                    score = min(score, 100)
                    
                    demanda = DemandaPorRegiao.query.filter_by(
                        municipio=municipio,
                        estado=estado,
                        data=hoje,
                        hora=hora
                    ).first()
                    
                    if not demanda:
                        demanda = DemandaPorRegiao(
                            municipio=municipio,
                            estado=estado,
                            data=hoje,
                            hora=hora
                        )
                        db.session.add(demanda)
                    
                    demanda.atendimentos_ps = atendimentos_ps
                    demanda.internacoes_solicitadas = internacoes
                    demanda.transferencias_pendentes = transferencias
                    demanda.vagas_disponiveis = vagas_disp
                    demanda.taxa_ocupacao = taxa_ocupacao
                    demanda.score_urgencia = int(score)
                
                db.session.commit()
                logger.info("✓ Demanda por região atualizada")
            except Exception as e:
                logger.error(f"✗ Erro ao atualizar demanda: {e}")
    
    # ========== AGENDAR TODAS AS TAREFAS ==========
    
    try:
        # Job 1: KPIs (a cada hora)
        scheduler.add_job(
            job_atualizar_kpis,
            'interval',
            hours=1,
            id='kpi_job',
            name='Atualizar KPIs'
        )
        print("  ✓ KPIs agendado (a cada hora)")
        
        # Job 2: Alertas (a cada 30 minutos)
        scheduler.add_job(
            job_gerar_alertas,
            'interval',
            minutes=30,
            id='alertas_job',
            name='Gerar Alertas'
        )
        print("  ✓ Alertas agendado (a cada 30 minutos)")
        
        # Job 3: Predições (diariamente às 23:00)
        scheduler.add_job(
            job_calcular_predicoes,
            'cron',
            hour=23,
            minute=0,
            id='predicoes_job',
            name='Calcular Predições'
        )
        print("  ✓ Predições agendado (diariamente 23:00)")
        
        # Job 4: Demanda (a cada hora)
        scheduler.add_job(
            job_atualizar_demanda,
            'interval',
            hours=1,
            id='demanda_job',
            name='Atualizar Demanda'
        )
        print("  ✓ Demanda agendado (a cada hora)")
        
        scheduler.start()
        print("\n  ✓ Scheduler iniciado com sucesso!\n")
        
    except Exception as e:
        logger.error(f"Erro ao iniciar scheduler: {e}")
        print(f"\n  ✗ Erro ao iniciar scheduler: {e}\n")