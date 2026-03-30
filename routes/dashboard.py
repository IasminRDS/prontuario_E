# -*- coding: utf-8 -*-
from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user
from models.paciente import Paciente
from models.atendimento import Atendimento
from models.prontuario import Prontuario
from models.agendamento import Agendamento
from models.triagem import Triagem
from models.exame import ExameSolicitado
from models.encaminhamento import Encaminhamento
from database.db import db
from datetime import datetime, date, timedelta

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/')
@login_required
def index():
    # Só gestor_estadual SEM unidade vai para o painel estadual
    # Admin com unidade continua no dashboard normal
    if current_user.is_gestor_estadual():
        return redirect(url_for('dash_estadual.index'))

    hoje       = date.today()
    inicio_mes = hoje.replace(day=1)
    uid        = current_user.unidade_id

    total_pacientes          = Paciente.query.filter_by(ativo=True).count()
    atendimentos_hoje        = Atendimento.query.filter(db.func.date(Atendimento.data_hora) == hoje).count()
    atendimentos_mes         = Atendimento.query.filter(Atendimento.data_hora >= inicio_mes).count()
    prontuarios_hoje         = Prontuario.query.filter(db.func.date(Prontuario.criado_em) == hoje).count()
    agendamentos_hoje        = Agendamento.query.filter(db.func.date(Agendamento.data_hora) == hoje, Agendamento.unidade_id == uid).count()
    triagens_hoje            = Triagem.query.filter(db.func.date(Triagem.criado_em) == hoje, Triagem.unidade_id == uid).count()
    exames_pendentes         = ExameSolicitado.query.filter(ExameSolicitado.status.in_(['solicitado','coletado','em_analise']), ExameSolicitado.unidade_id == uid).count()
    encaminhamentos_abertos  = Encaminhamento.query.filter(Encaminhamento.status.in_(['solicitado','agendado']), Encaminhamento.unidade_origem_id == uid).count()

    ultimos_atendimentos = Atendimento.query.order_by(Atendimento.data_hora.desc()).limit(8).all()

    # Últimos 7 dias
    labels_7d, atend_7d = [], []
    for i in range(6, -1, -1):
        d = hoje - timedelta(days=i)
        labels_7d.append(d.strftime('%d/%m'))
        atend_7d.append(Atendimento.query.filter(db.func.date(Atendimento.data_hora) == d).count())

    # Atendimentos por tipo no mês
    tipos_raw    = db.session.query(Atendimento.tipo, db.func.count(Atendimento.id)).filter(Atendimento.data_hora >= inicio_mes).group_by(Atendimento.tipo).all()
    tipos_labels = [t[0].capitalize() for t in tipos_raw] or ['Sem dados']
    tipos_dados  = [t[1] for t in tipos_raw] or [0]

    # Triagens por cor no mês
    cores_triagem = ['vermelho','laranja','amarelo','verde','azul']
    triagem_dados = [Triagem.query.filter(Triagem.classificacao == c, Triagem.criado_em >= inicio_mes, Triagem.unidade_id == uid).count() for c in cores_triagem]

    # Sexo
    masc  = Paciente.query.filter_by(ativo=True, sexo='M').count()
    fem   = Paciente.query.filter_by(ativo=True, sexo='F').count()
    outro = total_pacientes - masc - fem

    # Faixas etárias
    from dateutil.relativedelta import relativedelta
    faixas = [('0-12',0,12),('13-17',13,17),('18-39',18,39),('40-59',40,59),('60+',60,200)]
    faixas_dados = []
    for _, imin, imax in faixas:
        d_max = date.today() - relativedelta(years=imin)
        d_min = date.today() - relativedelta(years=imax+1)
        faixas_dados.append(Paciente.query.filter(Paciente.ativo==True, Paciente.data_nascimento<=d_max, Paciente.data_nascimento>d_min).count())

    # Agendamentos por status hoje
    ag_status = {s: Agendamento.query.filter(db.func.date(Agendamento.data_hora)==hoje, Agendamento.status==s, Agendamento.unidade_id==uid).count()
                 for s in ['agendado','confirmado','em_atendimento','finalizado','cancelado','falta']}

    return render_template('dashboard.html',
        hoje=hoje,
        total_pacientes=total_pacientes,
        atendimentos_hoje=atendimentos_hoje,
        atendimentos_mes=atendimentos_mes,
        prontuarios_hoje=prontuarios_hoje,
        agendamentos_hoje=agendamentos_hoje,
        triagens_hoje=triagens_hoje,
        exames_pendentes=exames_pendentes,
        encaminhamentos_abertos=encaminhamentos_abertos,
        ultimos_atendimentos=ultimos_atendimentos,
        labels_7d=labels_7d,
        atend_7d=atend_7d,
        tipos_labels=tipos_labels,
        tipos_dados=tipos_dados,
        triagem_dados=triagem_dados,
        sexo_dados=[masc, fem, outro],
        faixas_labels=[f[0] for f in faixas],
        faixas_dados=faixas_dados,
        ag_status=ag_status,
    )
