# -*- coding: utf-8 -*-
from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from models.faturamento_sia_sih import Faturamento, ProcessoFaturamento, TipoFaturamento, StatusFaturamento
from models.atendimento import Atendimento
from models.internacao import Internacao
from models.unidade import Unidade
from database.db import db
from datetime import datetime, date
from decoradores.permissoes import requer_permissao
from sqlalchemy import func
import csv
from io import StringIO

api_sia_sih_bp = Blueprint('api_sia_sih', __name__, url_prefix='/api/sia-sih')

# ========== FATURAMENTO ==========

@api_sia_sih_bp.route('/processar-atendimentos', methods=['POST'])
@login_required
@requer_permissao('financeiro_editar')
def processar_atendimentos():
    """Processa atendimentos para faturamento SIA"""
    
    dados = request.get_json()
    unidade_id = dados.get('unidade_id')
    data_inicio = datetime.strptime(dados.get('data_inicio'), '%Y-%m-%d')
    data_fim = datetime.strptime(dados.get('data_fim'), '%Y-%m-%d')
    
    if not current_user.pode_ver_unidade(unidade_id):
        return jsonify({'erro': 'Acesso negado'}), 403
    
    # Buscar atendimentos
    atendimentos = Atendimento.query.filter(
        Atendimento.unidade_id == unidade_id,
        Atendimento.data_hora.between(data_inicio, data_fim),
        ~Atendimento.faturamento.any()  # Sem faturamento
    ).all()
    
    processados = 0
    valor_total = 0
    
    for atend in atendimentos:
        # Obter código SIGTAP (simplificado)
        codigo_proc = obter_codigo_procedimento(atend.tipo_atendimento)
        valor = obter_valor_tabela(codigo_proc)
        
        faturamento = Faturamento(
            tipo=TipoFaturamento.SIA.value,
            atendimento_id=atend.id,
            paciente_id=atend.paciente_id,
            unidade_id=unidade_id,
            codigo_procedimento=codigo_proc,
            descricao_procedimento=atend.tipo_atendimento,
            valor_tabela=valor,
            valor_cobrado=valor,
            data_competencia=atend.data_hora.date(),
            data_atendimento=atend.data_hora,
            diagnostico_principal=atend.diagnostico,
        )
        
        db.session.add(faturamento)
        processados += 1
        valor_total += valor
    
    db.session.commit()
    
    return jsonify({
        'status': 'processado',
        'total': processados,
        'valor': valor_total,
        'tipo': 'SIA'
    }), 201

@api_sia_sih_bp.route('/processar-internacoes', methods=['POST'])
@login_required
@requer_permissao('financeiro_editar')
def processar_internacoes():
    """Processa internações para faturamento SIH/AIH"""
    
    dados = request.get_json()
    unidade_id = dados.get('unidade_id')
    mes = dados.get('mes')
    ano = dados.get('ano')
    
    if not current_user.pode_ver_unidade(unidade_id):
        return jsonify({'erro': 'Acesso negado'}), 403
    
    # Buscar internações do período
    internacoes = Internacao.query.filter(
        Internacao.unidade_id == unidade_id,
        func.month(Internacao.data_entrada) == mes,
        func.year(Internacao.data_entrada) == ano,
        ~Internacao.faturamento.any()
    ).all()
    
    processados = 0
    valor_total = 0
    
    # Gerar número AIH
    numero_aih = gerar_numero_aih(unidade_id, mes, ano)
    
    for intern in internacoes:
        # Calcular dias internado
        data_alta = intern.data_alta or datetime.now()
        dias = (data_alta - intern.data_entrada).days
        
        # Obter valor por diária
        valor_diaria = obter_valor_diaria(intern.tipo_internacao)
        valor_total_intern = valor_diaria * dias
        
        faturamento = Faturamento(
            tipo=TipoFaturamento.SIH.value,
            internacao_id=intern.id,
            paciente_id=intern.paciente_id,
            unidade_id=unidade_id,
            numero_aih=numero_aih,
            codigo_procedimento='internacao_' + intern.tipo_internacao,
            descricao_procedimento=f'Internação {intern.tipo_internacao} - {dias} dias',
            valor_tabela=valor_total_intern,
            valor_cobrado=valor_total_intern,
            data_competencia=date(ano, mes, 1),
            data_atendimento=intern.data_entrada,
            diagnostico_principal=intern.diagnostico_principal,
            diagnosticos_secundarios=intern.diagnosticos_secundarios,
        )
        
        db.session.add(faturamento)
        processados += 1
        valor_total += valor_total_intern
    
    db.session.commit()
    
    return jsonify({
        'status': 'processado',
        'total': processados,
        'valor': valor_total,
        'tipo': 'SIH',
        'numero_aih': numero_aih
    }), 201

@api_sia_sih_bp.route('/faturamentos', methods=['GET'])
@login_required
@requer_permissao('financeiro_ler')
def listar_faturamentos():
    """Lista faturamentos com filtros"""
    
    unidade_id = request.args.get('unidade_id', type=int)
    status = request.args.get('status')
    tipo = request.args.get('tipo')
    data_inicio = request.args.get('data_inicio')
    data_fim = request.args.get('data_fim')
    
    if unidade_id and not current_user.pode_ver_unidade(unidade_id):
        return jsonify({'erro': 'Acesso negado'}), 403
    
    query = Faturamento.query
    
    if unidade_id:
        query = query.filter_by(unidade_id=unidade_id)
    
    if status:
        query = query.filter_by(status=status)
    
    if tipo:
        query = query.filter_by(tipo=tipo)
    
    if data_inicio and data_fim:
        di = datetime.strptime(data_inicio, '%Y-%m-%d')
        df = datetime.strptime(data_fim, '%Y-%m-%d')
        query = query.filter(Faturamento.data_competencia.between(di.date(), df.date()))
    
    faturamentos = query.all()
    
    resumo = {
        'total': len(faturamentos),
        'pendentes': sum(1 for f in faturamentos if f.status == StatusFaturamento.PENDENTE.value),
        'processados': sum(1 for f in faturamentos if f.status == StatusFaturamento.PROCESSADO.value),
        'enviados': sum(1 for f in faturamentos if f.status == StatusFaturamento.ENVIADO.value),
        'aprovados': sum(1 for f in faturamentos if f.status == StatusFaturamento.APROVADO.value),
        'valor_total': sum(f.valor_cobrado or 0 for f in faturamentos),
        'valor_aprovado': sum(f.valor_apurado or 0 for f in faturamentos if f.status == StatusFaturamento.APROVADO.value),
        'faturamentos': [f.to_dict() for f in faturamentos]
    }
    
    return jsonify(resumo)

@api_sia_sih_bp.route('/exportar-lote', methods=['POST'])
@login_required
@requer_permissao('financeiro_editar')
def exportar_lote_sia_sih():
    """Exporta lote em formato SIA/SIH para SISAP"""
    
    dados = request.get_json()
    tipo = dados.get('tipo')  # sia ou sih
    faturamento_ids = dados.get('faturamento_ids', [])
    
    faturamentos = Faturamento.query.filter(
        Faturamento.id.in_(faturamento_ids)
    ).all()
    
    if tipo == 'sia':
        csv_data = gerar_lote_sia(faturamentos)
        nome_arquivo = f'lote_sia_{datetime.now().strftime("%Y%m%d_%H%M%S")}.txt'
    else:  # sih
        csv_data = gerar_lote_sih(faturamentos)
        nome_arquivo = f'lote_sih_{datetime.now().strftime("%Y%m%d_%H%M%S")}.txt'
    
    # Marcar como enviados
    for fat in faturamentos:
        fat.status = StatusFaturamento.ENVIADO.value
        fat.data_envio = datetime.now()
    
    db.session.commit()
    
    return jsonify({
        'status': 'exportado',
        'arquivo': nome_arquivo,
        'total_registros': len(faturamentos),
        'tipo': tipo,
        'data': datetime.now().isoformat()
    }), 200

# ========== UTILITÁRIOS ==========

def obter_codigo_procedimento(tipo_atendimento):
    """Retorna código SIGTAP para o tipo de atendimento"""
    tabela = {
        'consulta': '0101010016',
        'triagem': '0301010021',
        'urgencia': '0401010011',
        'cirurgia': '0401100019',
    }
    return tabela.get(tipo_atendimento.lower(), '0101010016')

def obter_valor_tabela(codigo_sigtap):
    """Obtém valor da tabela SIGTAP (simplificado)"""
    valores = {
        '0101010016': 20.50,  # Consulta
        '0301010021': 5.00,   # Triagem
        '0401010011': 50.00,  # Urgência
        '0401100019': 200.00, # Cirurgia
    }
    return valores.get(codigo_sigtap, 25.00)

def obter_valor_diaria(tipo_internacao):
    """Obtém valor de diária por tipo"""
    valores = {
        'clinico': 150.00,
        'cirurgico': 200.00,
        'critico': 350.00,
        'pediatrico': 120.00,
        'obstetrico': 180.00,
    }
    return valores.get(tipo_internacao, 150.00)

def gerar_numero_aih(unidade_id, mes, ano):
    """Gera número de AIH sequencial"""
    contador = db.session.query(func.count()).filter(
        ProcessoFaturamento.unidade_id == unidade_id,
        ProcessoFaturamento.mes_competencia == mes,
        ProcessoFaturamento.ano_competencia == ano
    ).scalar() or 0
    
    return f"{unidade_id:06d}{ano:04d}{mes:02d}{contador+1:05d}"

def gerar_lote_sia(faturamentos):
    """Gera arquivo de lote SIA"""
    buf = StringIO()
    writer = csv.writer(buf, delimiter=';')
    
    # Cabeçalho
    writer.writerow([
        'CODIGO_SIGTAP',
        'PACIENTE',
        'CPF',
        'DATA_ATENDIMENTO',
        'VALOR',
        'DIAGNOSTICO',
    ])
    
    for fat in faturamentos:
        writer.writerow([
            fat.codigo_procedimento,
            fat.paciente.nome,
            fat.paciente.cpf,
            fat.data_atendimento.strftime('%d/%m/%Y'),
            str(fat.valor_cobrado),
            fat.diagnostico_principal or '',
        ])
    
    return buf.getvalue()

def gerar_lote_sih(faturamentos):
    """Gera arquivo de lote SIH/AIH"""
    buf = StringIO()
    writer = csv.writer(buf, delimiter=';')
    
    # Cabeçalho SIH
    writer.writerow([
        'NUMERO_AIH',
        'PACIENTE',
        'CPF',
        'DATA_INTERNACAO',
        'DATA_ALTA',
        'DIAGNOSTICO_PRINCIPAL',
        'DIAGNOSTICOS_SECUNDARIOS',
        'VALOR',
    ])
    
    for fat in faturamentos:
        internacao = fat.internacao
        writer.writerow([
            fat.numero_aih,
            fat.paciente.nome,
            fat.paciente.cpf,
            internacao.data_entrada.strftime('%d/%m/%Y'),
            internacao.data_alta.strftime('%d/%m/%Y') if internacao.data_alta else '',
            fat.diagnostico_principal or '',
            ','.join(fat.diagnosticos_secundarios or []),
            str(fat.valor_cobrado),
        ])
    
    return buf.getvalue()