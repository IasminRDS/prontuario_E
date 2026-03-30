# -*- coding: utf-8 -*-
from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from models.vaga import Vaga, SolicitacaoTransferencia, StatusVaga, NivelUrgencia
from models.unidade import Unidade
from models.internacao import Leito, Setor, Internacao
from models.paciente import Paciente
from models.user import User
from models.alerta import Alerta
from database.db import db
from datetime import datetime, timedelta
from decoradores.permissoes import requer_permissao, requer_acesso_unidade, requer_acesso_estadual
from sqlalchemy import and_, or_, func
import statistics

api_vagas_bp = Blueprint('api_vagas', __name__, url_prefix='/api/vagas')

# ========== VAGAS - LISTAR E BUSCAR ==========

@api_vagas_bp.route('/disponiveis', methods=['GET'])
@login_required
def vagas_disponiveis():
    """Lista vagas disponíveis com filtros avançados"""
    
    tipo_paciente = request.args.get('tipo_paciente')
    isolamento = request.args.get('isolamento', 'false').lower() == 'true'
    estado = request.args.get('estado')
    municipio = request.args.get('municipio')
    especialidade = request.args.get('especialidade')
    urgencia = request.args.get('urgencia', 'normal')
    limite = request.args.get('limite', 20, type=int)
    
    # Query base
    query = Vaga.query.filter(
        Vaga.status == StatusVaga.DISPONIVEL.value,
        Vaga.ativo == True
    )
    
    # Filtros
    if tipo_paciente:
        query = query.filter(Vaga.tipo_paciente == tipo_paciente)
    
    if isolamento:
        query = query.filter(Vaga.isolamento == True)
    
    # Filtros por localização
    if estado or municipio:
        query = query.join(Unidade)
        if estado:
            query = query.filter(Unidade.estado == estado)
        if municipio:
            query = query.filter(Unidade.municipio == municipio)
    
    vagas = query.limit(limite).all()
    
    # Liberar reservas expiradas
    for vaga in vagas:
        vaga.liberar_reserva()
    
    vagas_dict = [v.to_dict() for v in vagas]
    
    return jsonify({
        'total': len(vagas_dict),
        'urgencia': urgencia,
        'vagas': vagas_dict,
        'timestamp': datetime.now().isoformat()
    })

@api_vagas_bp.route('/<int:vaga_id>', methods=['GET'])
@login_required
def detalhes_vaga(vaga_id):
    """Retorna detalhes de uma vaga específica"""
    
    vaga = Vaga.query.get_or_404(vaga_id)
    
    if not current_user.pode_ver_unidade(vaga.unidade_id):
        return jsonify({'erro': 'Acesso negado'}), 403
    
    vaga.liberar_reserva()
    
    return jsonify({
        'vaga': vaga.to_dict(),
        'leito': {
            'id': vaga.leito.id,
            'numero': vaga.leito.numero,
            'tipo': vaga.leito.tipo,
        },
        'setor': {
            'id': vaga.setor.id,
            'nome': vaga.setor.nome,
        },
        'unidade': {
            'id': vaga.unidade.id,
            'nome': vaga.unidade.nome,
            'municipio': vaga.unidade.municipio,
            'estado': vaga.unidade.estado,
        }
    })

@api_vagas_bp.route('/por-setor/<int:setor_id>', methods=['GET'])
@login_required
def vagas_por_setor(setor_id):
    """Lista todas as vagas de um setor"""
    
    setor = Setor.query.get_or_404(setor_id)
    
    if not current_user.pode_ver_unidade(setor.unidade_id):
        return jsonify({'erro': 'Acesso negado'}), 403
    
    vagas = Vaga.query.filter_by(setor_id=setor_id).all()
    
    resumo = {
        'total': len(vagas),
        'disponivel': sum(1 for v in vagas if v.status == StatusVaga.DISPONIVEL.value),
        'reservada': sum(1 for v in vagas if v.status == StatusVaga.RESERVADA.value),
        'ocupada': sum(1 for v in vagas if v.status == StatusVaga.OCUPADA.value),
        'indisponivel': sum(1 for v in vagas if v.status == StatusVaga.INDISPONIVEL.value),
        'vagas': [v.to_dict() for v in vagas]
    }
    
    return jsonify(resumo)

@api_vagas_bp.route('/por-unidade/<int:unidade_id>', methods=['GET'])
@login_required
def vagas_por_unidade(unidade_id):
    """Resumo de vagas por unidade"""
    
    if not current_user.pode_ver_unidade(unidade_id):
        return jsonify({'erro': 'Acesso negado'}), 403
    
    unidade = Unidade.query.get_or_404(unidade_id)
    
    vagas = Vaga.query.filter_by(unidade_id=unidade_id).all()
    
    resumo_por_setor = {}
    for setor in unidade.setores:
        setores_vagas = [v for v in vagas if v.setor_id == setor.id]
        resumo_por_setor[setor.nome] = {
            'total': len(setores_vagas),
            'disponivel': sum(1 for v in setores_vagas if v.status == StatusVaga.DISPONIVEL.value),
            'reservada': sum(1 for v in setores_vagas if v.status == StatusVaga.RESERVADA.value),
            'ocupada': sum(1 for v in setores_vagas if v.status == StatusVaga.OCUPADA.value),
        }
    
    taxa_ocupacao = (sum(1 for v in vagas if v.status == StatusVaga.OCUPADA.value) / len(vagas) * 100) if vagas else 0
    
    return jsonify({
        'unidade': unidade.nome,
        'total_vagas': len(vagas),
        'taxa_ocupacao': round(taxa_ocupacao, 2),
        'resumo_por_setor': resumo_por_setor,
    })

# ========== TRANSFERÊNCIAS - MATCHING INTELIGENTE ==========

def calcular_score_vaga(vaga, solicitacao):
    """Calcula score da vaga para esta solicitação (0-100)"""
    score = 0
    
    # Tipo de paciente compatível (30 pontos)
    if vaga.tipo_paciente == solicitacao.tipo_leito_necessario:
        score += 30
    elif not solicitacao.tipo_leito_necessario:
        score += 15
    
    # Isolamento (20 pontos)
    if solicitacao.tipo_isolamento:
        if vaga.isolamento:
            score += 20
    else:
        if not vaga.isolamento:
            score += 10
    
    # Status (25 pontos)
    if vaga.status == StatusVaga.DISPONIVEL.value:
        score += 25
    elif vaga.status == StatusVaga.RESERVADA.value:
        score += 10
    
    # Disponibilidade rápida (10 pontos)
    dias_sem_atualizacao = (datetime.now() - vaga.ultima_atualizacao).days
    if dias_sem_atualizacao < 7:
        score += 10
    
    # Proximidade geográfica (bonus 15 pontos se mesmo estado)
    if vaga.unidade.estado == solicitacao.unidade_origem.estado:
        score += 15
    
    # Urgência vs dias ocupado (bonus por vagas que esvaziam em breve)
    if solicitacao.urgencia in ['urgente', 'emergencia']:
        if vaga.dias_ocupado > 10:
            score += 5
    
    return min(score, 100)

@api_vagas_bp.route('/sugerir-transferencia', methods=['POST'])
@login_required
def sugerir_transferencia():
    """API inteligente: sugere melhores vagas para transferência"""
    
    dados = request.get_json()
    internacao_id = dados.get('internacao_id')
    motivo = dados.get('motivo')
    urgencia = dados.get('urgencia', 'normal')
    
    internacao = Internacao.query.get_or_404(internacao_id)
    paciente = internacao.paciente
    
    if not current_user.pode_ver_unidade(internacao.unidade_id):
        return jsonify({'erro': 'Acesso negado'}), 403
    
    # Criar solicitação
    solicitacao = SolicitacaoTransferencia(
        paciente_id=paciente.id,
        internacao_id=internacao_id,
        unidade_origem_id=internacao.unidade_id,
        motivo=motivo,
        urgencia=urgencia,
        tipo_leito_necessario=internacao.tipo_internacao,
        criado_por=current_user.id,
        descricao=dados.get('descricao', ''),
        especialidade_necessaria=dados.get('especialidade'),
        tipo_isolamento=dados.get('tipo_isolamento'),
        observacoes_clinicas=dados.get('observacoes', ''),
    )
    
    solicitacao.calcular_prioridade()
    db.session.add(solicitacao)
    db.session.commit()
    
    # Buscar vagas compatíveis
    vagas_compatibles = Vaga.query.filter(
        Vaga.status.in_([StatusVaga.DISPONIVEL.value, StatusVaga.RESERVADA.value]),
        Vaga.ativo == True,
        Vaga.unidade_id != internacao.unidade_id  # Não sugerir mesma unidade
    ).all()
    
    # Calcular score e ordenar
    vagas_scored = []
    for vaga in vagas_compatibles:
        score = calcular_score_vaga(vaga, solicitacao)
        if score > 0:
            vagas_scored.append({
                'vaga': vaga.to_dict(),
                'score': round(score, 2),
                'tempo_reserva': 120,
                'distancia_km': calcular_distancia_aproximada(
                    solicitacao.unidade_origem.estado,
                    vaga.unidade.estado
                )
            })
    
    vagas_scored.sort(key=lambda x: x['score'], reverse=True)
    top_vagas = vagas_scored[:10]
    
    # Guardar IDs de vagas sugeridas
    solicitacao.vagas_alternativas = [v['vaga']['id'] for v in top_vagas]
    db.session.commit()
    
    # Criar alerta para gestor da unidade destino
    if top_vagas:
        melhor_vaga = top_vagas[0]
        alerta = Alerta(
            unidade_id=melhor_vaga['vaga']['unidade_id'],
            tipo='transferencia',
            nivel=1 if urgencia == 'normal' else 2,
            titulo=f'📊 Solicitação de Transferência: {paciente.nome}',
            mensagem=f'Paciente de {solicitacao.unidade_origem.nome} solicitando transferência. Urgência: {urgencia}',
            dados_json={
                'solicitacao_id': solicitacao.id,
                'melhor_vaga_id': melhor_vaga['vaga']['id'],
                'score': melhor_vaga['score']
            }
        )
        db.session.add(alerta)
        db.session.commit()
    
    return jsonify({
        'solicitacao_id': solicitacao.id,
        'paciente': paciente.nome,
        'urgencia': urgencia,
        'prioridade': solicitacao.prioridade,
        'vagas_sugeridas': top_vagas,
        'total_vagas_compativeis': len(top_vagas),
        'timestamp': datetime.now().isoformat()
    }), 201

@api_vagas_bp.route('/transferencias/pendentes', methods=['GET'])
@login_required
@requer_acesso_estadual()
def transferencias_pendentes():
    """Lista todas as solicitações de transferência pendentes"""
    
    estado = request.args.get('estado')
    urgencia = request.args.get('urgencia')
    
    query = SolicitacaoTransferencia.query.filter(
        SolicitacaoTransferencia.status == 'pendente'
    )
    
    if estado:
        query = query.join(Unidade, Unidade.id == SolicitacaoTransferencia.unidade_origem_id).filter(
            Unidade.estado == estado
        )
    
    if urgencia:
        query = query.filter(SolicitacaoTransferencia.urgencia == urgencia)
    
    solicitacoes = query.order_by(SolicitacaoTransferencia.prioridade.desc()).all()
    
    return jsonify({
        'total': len(solicitacoes),
        'solicitacoes': [s.to_dict() for s in solicitacoes]
    })

@api_vagas_bp.route('/transferencias/<int:solicitacao_id>/aceitar/<int:vaga_id>', methods=['POST'])
@login_required
def aceitar_transferencia(solicitacao_id, vaga_id):
    """Aceita transferência e reserva vaga"""
    
    solicitacao = SolicitacaoTransferencia.query.get_or_404(solicitacao_id)
    vaga = Vaga.query.get_or_404(vaga_id)
    
    if not current_user.pode_ver_unidade(vaga.unidade_id):
        return jsonify({'erro': 'Acesso negado'}), 403
    
    # Verificar permissão
    if not current_user.tem_permissao('transferencia_aceitar'):
        return jsonify({'erro': 'Sem permissão'}), 403
    
    # Reservar vaga
    if vaga.reservar(solicitacao.paciente_id, solicitacao.internacao_id):
        solicitacao.aceitar(vaga_id, current_user.id)
        
        # Criar alerta para unidade de origem
        alerta = Alerta(
            unidade_id=solicitacao.unidade_origem_id,
            tipo='transferencia',
            nivel=0,
            titulo=f'✓ Transferência Aceita: {solicitacao.paciente.nome}',
            mensagem=f'Vaga confirmada em {vaga.unidade.nome} - Setor {vaga.setor.nome}',
            dados_json={'solicitacao_id': solicitacao_id, 'vaga_id': vaga_id}
        )
        db.session.add(alerta)
        db.session.commit()
        
        return jsonify({
            'status': 'transferência aceita',
            'solicitacao_id': solicitacao_id,
            'vaga_id': vaga_id,
            'unidade_destino': vaga.unidade.nome,
            'setor_destino': vaga.setor.nome,
            'tempo_reserva_minutos': vaga.tempo_reserva_minutos,
            'timestamp': datetime.now().isoformat()
        }), 200
    
    return jsonify({'erro': 'Vaga indisponível'}), 400

@api_vagas_bp.route('/transferencias/<int:solicitacao_id>/recusar', methods=['POST'])
@login_required
def recusar_transferencia(solicitacao_id):
    """Recusa transferência"""
    
    solicitacao = SolicitacaoTransferencia.query.get_or_404(solicitacao_id)
    dados = request.get_json()
    
    if not current_user.pode_ver_unidade(solicitacao.unidade_destino_id or solicitacao.unidade_origem_id):
        return jsonify({'erro': 'Acesso negado'}), 403
    
    solicitacao.recusar(dados.get('motivo', ''), current_user.id)
    
    # Alerta para origem
    alerta = Alerta(
        unidade_id=solicitacao.unidade_origem_id,
        tipo='transferencia',
        nivel=1,
        titulo=f'✗ Transferência Recusada: {solicitacao.paciente.nome}',
        mensagem=f'Motivo: {dados.get("motivo", "Não especificado")}',
        dados_json={'solicitacao_id': solicitacao_id}
    )
    db.session.add(alerta)
    db.session.commit()
    
    return jsonify({
        'status': 'transferência recusada',
        'motivo': dados.get('motivo'),
        'timestamp': datetime.now().isoformat()
    })

# ========== GESTÃO DE VAGAS ==========

@api_vagas_bp.route('/<int:vaga_id>/ocupar', methods=['POST'])
@login_required
@requer_acesso_unidade()
def ocupar_vaga(vaga_id):
    """Marca vaga como ocupada"""
    
    vaga = Vaga.query.get_or_404(vaga_id)
    dados = request.get_json()
    
    if not current_user.pode_ver_unidade(vaga.unidade_id):
        return jsonify({'erro': 'Acesso negado'}), 403
    
    if not current_user.tem_permissao('vaga_gerenciar'):
        return jsonify({'erro': 'Sem permissão'}), 403
    
    paciente_id = dados.get('paciente_id')
    internacao_id = dados.get('internacao_id')
    
    if vaga.ocupar(paciente_id, internacao_id):
        return jsonify({
            'status': 'vaga ocupada',
            'vaga_id': vaga_id,
            'timestamp': datetime.now().isoformat()
        })
    
    return jsonify({'erro': 'Vaga não pode ser ocupada'}), 400

@api_vagas_bp.route('/<int:vaga_id>/liberar', methods=['POST'])
@login_required
@requer_acesso_unidade()
def liberar_vaga(vaga_id):
    """Libera uma vaga"""
    
    vaga = Vaga.query.get_or_404(vaga_id)
    
    if not current_user.pode_ver_unidade(vaga.unidade_id):
        return jsonify({'erro': 'Acesso negado'}), 403
    
    if not current_user.tem_permissao('vaga_gerenciar'):
        return jsonify({'erro': 'Sem permissão'}), 403
    
    vaga.liberar()
    
    return jsonify({
        'status': 'vaga liberada',
        'vaga_id': vaga_id,
        'timestamp': datetime.now().isoformat()
    })

@api_vagas_bp.route('/<int:vaga_id>/indisponibilizar', methods=['POST'])
@login_required
@requer_acesso_unidade()
def indisponibilizar_vaga(vaga_id):
    """Marca vaga como indisponível"""
    
    vaga = Vaga.query.get_or_404(vaga_id)
    dados = request.get_json()
    
    if not current_user.pode_ver_unidade(vaga.unidade_id):
        return jsonify({'erro': 'Acesso negado'}), 403
    
    if not current_user.tem_permissao('vaga_gerenciar'):
        return jsonify({'erro': 'Sem permissão'}), 403
    
    vaga.indisponibilizar(dados.get('motivo', 'Manutenção'))
    
    return jsonify({
        'status': 'vaga indisponibilizada',
        'motivo': dados.get('motivo'),
        'timestamp': datetime.now().isoformat()
    })

@api_vagas_bp.route('/<int:vaga_id>/disponibilizar', methods=['POST'])
@login_required
@requer_acesso_unidade()
def disponibilizar_vaga(vaga_id):
    """Torna vaga disponível novamente"""
    
    vaga = Vaga.query.get_or_404(vaga_id)
    
    if not current_user.pode_ver_unidade(vaga.unidade_id):
        return jsonify({'erro': 'Acesso negado'}), 403
    
    if not current_user.tem_permissao('vaga_gerenciar'):
        return jsonify({'erro': 'Sem permissão'}), 403
    
    vaga.disponibilizar()
    
    return jsonify({
        'status': 'vaga disponibilizada',
        'timestamp': datetime.now().isoformat()
    })

# ========== UTILITÁRIOS ==========

def calcular_distancia_aproximada(estado1, estado2):
    """Calcula distância aproximada entre estados (simplificado)"""
    if estado1 == estado2:
        return 0
    return 100  # Aproximação básica

@api_vagas_bp.route('/dashboard', methods=['GET'])
@login_required
@requer_acesso_estadual()
def dashboard_vagas():
    """Dashboard estadual de vagas"""
    
    estado = request.args.get('estado')
    
    # Vagas por estado
    query_vagas = Vaga.query.join(Unidade)
    if estado:
        query_vagas = query_vagas.filter(Unidade.estado == estado)
    
    vagas = query_vagas.all()
    
    resumo_geral = {
        'total': len(vagas),
        'disponivel': sum(1 for v in vagas if v.status == StatusVaga.DISPONIVEL.value),
        'reservada': sum(1 for v in vagas if v.status == StatusVaga.RESERVADA.value),
        'ocupada': sum(1 for v in vagas if v.status == StatusVaga.OCUPADA.value),
        'indisponivel': sum(1 for v in vagas if v.status == StatusVaga.INDISPONIVEL.value),
        'taxa_ocupacao': (sum(1 for v in vagas if v.status == StatusVaga.OCUPADA.value) / len(vagas) * 100) if vagas else 0,
    }
    
    # Transferências pendentes
    transferencias = SolicitacaoTransferencia.query.filter(
        SolicitacaoTransferencia.status == 'pendente'
    )
    if estado:
        transferencias = transferencias.join(
            Unidade, Unidade.id == SolicitacaoTransferencia.unidade_origem_id
        ).filter(Unidade.estado == estado)
    
    transferencias = transferencias.all()
    
    return jsonify({
        'estado': estado or 'Brasil',
        'vagas': resumo_geral,
        'transferencias_pendentes': len(transferencias),
        'transferencias_urgentes': sum(1 for t in transferencias if t.urgencia == 'urgente'),
        'transferencias_emergencia': sum(1 for t in transferencias if t.urgencia == 'emergencia'),
        'timestamp': datetime.now().isoformat()
    })