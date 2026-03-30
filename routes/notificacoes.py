# -*- coding: utf-8 -*-
from flask import Blueprint, render_template, jsonify
from flask_login import login_required, current_user
from models.internacao import Internacao, Leito
from models.exame import ExameSolicitado
from models.encaminhamento import Encaminhamento
from models.triagem import Triagem
from models.estoque import ItemEstoque
from models.pronto_socorro import AtendimentoPS
from database.db import db
from datetime import datetime, date, timedelta

notif_bp = Blueprint('notificacoes', __name__, url_prefix='/notificacoes')


def gerar_notificacoes(unidade_id):
    """Gera lista de notificações/alertas do sistema."""
    alertas = []
    hoje = date.today()

    # ── Triagens urgentes aguardando (vermelho/laranja) ──
    triagens_urg = Triagem.query.filter(
        Triagem.unidade_id == unidade_id,
        Triagem.classificacao.in_(['vermelho', 'laranja']),
        Triagem.status == 'aguardando',
        db.func.date(Triagem.criado_em) == hoje
    ).count()
    if triagens_urg:
        alertas.append({
            'tipo': 'critico',
            'icone': '🔴',
            'titulo': f'{triagens_urg} triagem(ns) urgente(s) aguardando',
            'descricao': 'Classificação vermelho ou laranja sem atendimento',
            'url': '/triagem/',
            'cor': 'vermelho',
        })

    # ── PS com pacientes aguardando há muito tempo ──
    try:
        ps_demorados = AtendimentoPS.query.filter(
            AtendimentoPS.unidade_id == unidade_id,
            AtendimentoPS.status.in_(['aguardando_triagem', 'triagem_realizada',
                                       'aguardando_atendimento']),
            AtendimentoPS.data_entrada <= datetime.utcnow() - timedelta(hours=2)
        ).count()
        if ps_demorados:
            alertas.append({
                'tipo': 'aviso',
                'icone': '⏰',
                'titulo': f'{ps_demorados} paciente(s) no PS há mais de 2h',
                'descricao': 'Aguardando atendimento no pronto-socorro',
                'url': '/ps/',
                'cor': 'amarelo',
            })
    except Exception:
        pass

    # ── Exames com resultado crítico pendente ──
    exames_criticos = ExameSolicitado.query.filter(
        ExameSolicitado.unidade_id == unidade_id,
        ExameSolicitado.status == 'resultado_critico'
    ).count()
    if exames_criticos:
        alertas.append({
            'tipo': 'critico',
            'icone': '⚠️',
            'titulo': f'{exames_criticos} resultado(s) crítico(s) de exame',
            'descricao': 'Exames com resultado crítico aguardando revisão',
            'url': '/exames/pendentes',
            'cor': 'vermelho',
        })

    # ── Exames pendentes há mais de 3 dias ──
    exames_velhos = ExameSolicitado.query.filter(
        ExameSolicitado.unidade_id == unidade_id,
        ExameSolicitado.status.in_(['solicitado', 'coletado', 'em_analise']),
        ExameSolicitado.data_solicitacao <= datetime.utcnow() - timedelta(days=3)
    ).count()
    if exames_velhos:
        alertas.append({
            'tipo': 'info',
            'icone': '🔬',
            'titulo': f'{exames_velhos} exame(s) pendente(s) há mais de 3 dias',
            'descricao': 'Exames solicitados sem resultado registrado',
            'url': '/exames/pendentes',
            'cor': 'amarelo',
        })

    # ── Encaminhamentos urgentes sem agendamento ──
    enc_urgentes = Encaminhamento.query.filter(
        Encaminhamento.unidade_origem_id == unidade_id,
        Encaminhamento.prioridade == 'urgente',
        Encaminhamento.status == 'solicitado',
    ).count()
    if enc_urgentes:
        alertas.append({
            'tipo': 'aviso',
            'icone': '📋',
            'titulo': f'{enc_urgentes} encaminhamento(s) urgente(s) sem agendamento',
            'descricao': 'Encaminhamentos com prioridade urgente ainda sem data',
            'url': '/encaminhamentos/painel',
            'cor': 'amarelo',
        })

    # ── Internações com alta prevista para hoje ──
    try:
        altas_hoje = Internacao.query.filter(
            Internacao.unidade_id == unidade_id,
            Internacao.status == 'ativa',
            db.func.date(Internacao.data_prevista_alta) == hoje
        ).count()
        if altas_hoje:
            alertas.append({
                'tipo': 'info',
                'icone': '🏥',
                'titulo': f'{altas_hoje} paciente(s) com alta prevista para hoje',
                'descricao': 'Internações com data prevista de alta no dia de hoje',
                'url': '/internacao/',
                'cor': 'azul',
            })
    except Exception:
        pass

    # ── Leitos em higienização ──
    try:
        leitos_hig = Leito.query.join(
            Leito.setor
        ).filter(
            Leito.status == 'em_higienizacao',
            Leito.ativo == True
        ).count()
        if leitos_hig:
            alertas.append({
                'tipo': 'info',
                'icone': '🛏️',
                'titulo': f'{leitos_hig} leito(s) em higienização',
                'descricao': 'Leitos aguardando liberação para novos pacientes',
                'url': '/internacao/leitos',
                'cor': 'cinza',
            })
    except Exception:
        pass

    # ── Estoque crítico ──
    try:
        estoque_critico = ItemEstoque.query.filter(
            ItemEstoque.unidade_id == unidade_id,
            ItemEstoque.ativo == True,
            ItemEstoque.quantidade <= ItemEstoque.estoque_minimo
        ).count()
        if estoque_critico:
            alertas.append({
                'tipo': 'aviso',
                'icone': '💊',
                'titulo': f'{estoque_critico} item(ns) com estoque crítico',
                'descricao': 'Medicamentos ou materiais abaixo do estoque mínimo',
                'url': '/estoque/alertas',
                'cor': 'amarelo',
            })

        # Itens vencendo em 30 dias
        limite = hoje + timedelta(days=30)
        vencendo = ItemEstoque.query.filter(
            ItemEstoque.unidade_id == unidade_id,
            ItemEstoque.ativo == True,
            ItemEstoque.validade.isnot(None),
            ItemEstoque.validade <= limite,
            ItemEstoque.validade >= hoje,
            ItemEstoque.quantidade > 0
        ).count()
        if vencendo:
            alertas.append({
                'tipo': 'info',
                'icone': '📅',
                'titulo': f'{vencendo} item(ns) vencendo em 30 dias',
                'descricao': 'Medicamentos ou materiais com validade próxima',
                'url': '/estoque/alertas',
                'cor': 'amarelo',
            })
    except Exception:
        pass

    # Ordenar: crítico primeiro, depois aviso, depois info
    ordem = {'critico': 0, 'aviso': 1, 'info': 2}
    alertas.sort(key=lambda a: ordem.get(a['tipo'], 3))
    return alertas


@notif_bp.route('/')
@login_required
def index():
    if not current_user.unidade_id:
        return redirect(url_for('dash_estadual.index'))
    alertas = gerar_notificacoes(current_user.unidade_id)
    return render_template('notificacoes/index.html', alertas=alertas)


@notif_bp.route('/api')
@login_required
def api():
    """Retorna contagem de notificações para o badge na sidebar."""
    if not current_user.unidade_id:
        return jsonify({'total': 0, 'criticos': 0, 'alertas': []})
    alertas = gerar_notificacoes(current_user.unidade_id)
    criticos = sum(1 for a in alertas if a['tipo'] == 'critico')
    total    = len(alertas)
    return jsonify({
        'total': total,
        'criticos': criticos,
        'alertas': alertas[:5]  # primeiros 5 para preview
    })
