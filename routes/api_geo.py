# -*- coding: utf-8 -*-
from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from models.localizacao import Localizacao, AcessibilidadeRegiao, DemandaPorRegiao
from models.unidade import Unidade
from models.vaga import Vaga, StatusVaga, SolicitacaoTransferencia
from models.internacao import Leito
from models.atendimento import Atendimento
from database.db import db
from datetime import datetime, date, timedelta
from decoradores.permissoes import requer_acesso_estadual
from sqlalchemy import func, and_
import math

api_geo_bp = Blueprint('api_geo', __name__, url_prefix='/api/geo')

# ========== LOCALIZAÇÃO ==========

@api_geo_bp.route('/unidades/mapa', methods=['GET'])
@login_required
def unidades_mapa():
    """Lista todas as unidades com coordenadas para mapa"""
    
    estado = request.args.get('estado')
    municipio = request.args.get('municipio')
    tipo = request.args.get('tipo')
    
    query = Unidade.query.join(Localizacao).filter(Unidade.ativo == True)
    
    if estado:
        query = query.filter(Localizacao.estado == estado)
    
    if municipio:
        query = query.filter(Localizacao.municipio == municipio)
    
    if tipo:
        query = query.filter(Unidade.tipo == tipo)
    
    unidades = query.all()
    
    features = []
    for u in unidades:
        # Calcular indicadores
        total_leitos = Leito.query.filter(
            Leito.setor.has(unidade_id=u.id),
            Leito.ativo == True
        ).count()
        
        leitos_ocupados = Leito.query.filter(
            Leito.setor.has(unidade_id=u.id),
            Leito.ativo == True,
            Leito.status == 'ocupado'
        ).count()
        
        taxa_ocupacao = (leitos_ocupados / total_leitos * 100) if total_leitos > 0 else 0
        
        # Transferências pendentes
        transf_pendentes = SolicitacaoTransferencia.query.filter(
            SolicitacaoTransferencia.unidade_destino_id == u.id,
            SolicitacaoTransferencia.status == 'pendente'
        ).count()
        
        # Cor baseado em ocupação
        if taxa_ocupacao >= 90:
            cor = '#DC2626'  # Vermelho
            status_ocupacao = 'critica'
        elif taxa_ocupacao >= 70:
            cor = '#F59E0B'  # Amarelo
            status_ocupacao = 'alta'
        else:
            cor = '#10B981'  # Verde
            status_ocupacao = 'normal'
        
        feature = {
            'type': 'Feature',
            'geometry': {
                'type': 'Point',
                'coordinates': [u.localizacao.longitude, u.localizacao.latitude]
            },
            'properties': {
                'id': u.id,
                'nome': u.nome,
                'tipo': u.tipo,
                'municipio': u.municipio,
                'estado': u.localizacao.estado,
                'latitude': u.localizacao.latitude,
                'longitude': u.localizacao.longitude,
                'telefone': u.telefone,
                'endereco': u.localizacao.endereco,
                'total_leitos': total_leitos,
                'leitos_ocupados': leitos_ocupados,
                'taxa_ocupacao': round(taxa_ocupacao, 2),
                'status_ocupacao': status_ocupacao,
                'transferencias_pendentes': transf_pendentes,
                'regiao_saude': u.localizacao.regiao_saude,
                'cor': cor,
                'raio': max(5, min(30, 5 + (taxa_ocupacao / 100) * 25))  # Aumenta com ocupação
            }
        }
        features.append(feature)
    
    return jsonify({
        'type': 'FeatureCollection',
        'features': features,
        'total': len(features),
        'timestamp': datetime.now().isoformat()
    })

@api_geo_bp.route('/unidade/<int:unidade_id>/localizacao', methods=['GET'])
@login_required
def localizacao_unidade(unidade_id):
    """Retorna localização detalhada de uma unidade"""
    
    if not current_user.pode_ver_unidade(unidade_id):
        return jsonify({'erro': 'Acesso negado'}), 403
    
    unidade = Unidade.query.get_or_404(unidade_id)
    localizacao = Localizacao.query.filter_by(unidade_id=unidade_id).first()
    
    if not localizacao:
        return jsonify({'erro': 'Localização não configurada'}), 404
    
    return jsonify(localizacao.to_dict())

@api_geo_bp.route('/localizacao', methods=['POST'])
@login_required
def criar_localizacao():
    """Cria ou atualiza localização de unidade"""
    
    if not current_user.is_admin():
        return jsonify({'erro': 'Acesso negado'}), 403
    
    dados = request.get_json()
    unidade_id = dados['unidade_id']
    
    unidade = Unidade.query.get_or_404(unidade_id)
    
    localizacao = Localizacao.query.filter_by(unidade_id=unidade_id).first()
    
    if not localizacao:
        localizacao = Localizacao(unidade_id=unidade_id)
        db.session.add(localizacao)
    
    localizacao.latitude = dados['latitude']
    localizacao.longitude = dados['longitude']
    localizacao.endereco = dados.get('endereco')
    localizacao.numero = dados.get('numero')
    localizacao.complemento = dados.get('complemento')
    localizacao.bairro = dados.get('bairro')
    localizacao.municipio = dados.get('municipio')
    localizacao.estado = dados.get('estado')
    localizacao.cep = dados.get('cep')
    localizacao.regiao_saude = dados.get('regiao_saude')
    localizacao.drs = dados.get('drs')
    localizacao.mesorregiao = dados.get('mesorregiao')
    localizacao.microrregiao = dados.get('microrregiao')
    
    db.session.commit()
    
    return jsonify(localizacao.to_dict()), 201

# ========== HEATMAP - MAPA DE CALOR ==========

@api_geo_bp.route('/heatmap/ocupacao', methods=['GET'])
@login_required
@requer_acesso_estadual()
def heatmap_ocupacao():
    """Gera dados de heatmap de ocupação por região"""
    
    estado = request.args.get('estado')
    
    query = db.session.query(
        Localizacao.latitude,
        Localizacao.longitude,
        func.avg(Leito.status == 'ocupado').label('intensidade')
    ).join(Unidade).join(Leito, Leito.setor.has(unidade_id=Unidade.id))
    
    if estado:
        query = query.filter(Localizacao.estado == estado)
    
    query = query.group_by(Localizacao.latitude, Localizacao.longitude)
    
    resultados = query.all()
    
    pontos = []
    for lat, lng, intensidade in resultados:
        if lat and lng:
            pontos.append({
                'latitude': float(lat),
                'longitude': float(lng),
                'intensidade': float(intensidade) if intensidade else 0
            })
    
    return jsonify({
        'tipo': 'heatmap',
        'estado': estado or 'Brasil',
        'pontos': pontos,
        'total_pontos': len(pontos),
        'timestamp': datetime.now().isoformat()
    })

@api_geo_bp.route('/heatmap/demanda', methods=['GET'])
@login_required
@requer_acesso_estadual()
def heatmap_demanda():
    """Gera dados de heatmap de demanda por região"""
    
    estado = request.args.get('estado')
    data = request.args.get('data', str(date.today()))
    
    # Buscar demanda do dia
    query = DemandaPorRegiao.query.filter(DemandaPorRegiao.data == data)
    
    if estado:
        query = query.filter(DemandaPorRegiao.estado == estado)
    
    demandas = query.all()
    
    pontos = []
    for demanda in demandas:
        # Buscar localização do município
        loc = db.session.query(Localizacao).filter(
            Localizacao.municipio == demanda.municipio,
            Localizacao.estado == demanda.estado
        ).first()
        
        if loc:
            intensidade = (demanda.score_urgencia / 100)
            pontos.append({
                'latitude': float(loc.latitude),
                'longitude': float(loc.longitude),
                'municipio': demanda.municipio,
                'intensidade': intensidade,
                'demanda': demanda.internacoes_solicitadas + demanda.transferencias_pendentes
            })
    
    return jsonify({
        'tipo': 'heatmap_demanda',
        'estado': estado or 'Brasil',
        'data': data,
        'pontos': pontos,
        'total_pontos': len(pontos),
        'timestamp': datetime.now().isoformat()
    })

# ========== ANÁLISE DE ACESSIBILIDADE ==========

@api_geo_bp.route('/acessibilidade/<string:estado>', methods=['GET'])
@login_required
@requer_acesso_estadual()
def acessibilidade_estado(estado):
    """Análise de acessibilidade por região do estado"""
    
    regioes = db.session.query(AcessibilidadeRegiao).filter(
        AcessibilidadeRegiao.estado == estado
    ).order_by(AcessibilidadeRegiao.municipio).all()
    
    resumo = {
        'total_municipios': len(regioes),
        'populacao_total': sum(r.populacao_total or 0 for r in regioes),
        'total_unidades': sum(r.total_unidades or 0 for r in regioes),
        'taxa_ocupacao_media': (sum(r.taxa_ocupacao_media or 0 for r in regioes) / len(regioes)) if regioes else 0,
        'municipios': [r.to_dict() for r in regioes]
    }
    
    return jsonify(resumo)

@api_geo_bp.route('/acessibilidade/municipio/<string:municipio>/<string:estado>', methods=['GET'])
@login_required
def acessibilidade_municipio(municipio, estado):
    """Detalhes de acessibilidade de um município"""
    
    acesso = AcessibilidadeRegiao.query.filter_by(
        municipio=municipio,
        estado=estado
    ).first_or_404()
    
    # Buscar unidades do município
    unidades = Unidade.query.join(Localizacao).filter(
        Localizacao.municipio == municipio,
        Localizacao.estado == estado,
        Unidade.ativo == True
    ).all()
    
    detalhes = acesso.to_dict()
    detalhes['unidades'] = [
        {
            'id': u.id,
            'nome': u.nome,
            'tipo': u.tipo,
            'taxa_ocupacao': (Leito.query.filter(
                Leito.setor.has(unidade_id=u.id),
                Leito.status == 'ocupado',
                Leito.ativo == True
            ).count() / Leito.query.filter(
                Leito.setor.has(unidade_id=u.id),
                Leito.ativo == True
            ).count() * 100) if Leito.query.filter(
                Leito.setor.has(unidade_id=u.id),
                Leito.ativo == True
            ).count() > 0 else 0,
            'latitude': u.localizacao.latitude if u.localizacao else None,
            'longitude': u.localizacao.longitude if u.localizacao else None,
        }
        for u in unidades
    ]
    
    return jsonify(detalhes)

# ========== CLUSTERS E REGIÕES ==========

@api_geo_bp.route('/clusters', methods=['GET'])
@login_required
@requer_acesso_estadual()
def clusters_unidades():
    """Agrupa unidades em clusters geográficos"""
    
    estado = request.args.get('estado')
    zoom = request.args.get('zoom', 10, type=int)
    
    query = Unidade.query.join(Localizacao).filter(Unidade.ativo == True)
    
    if estado:
        query = query.filter(Localizacao.estado == estado)
    
    unidades = query.all()
    
    if not unidades:
        return jsonify({'clusters': [], 'total': 0})
    
    # Agrupar por proximidade (simplificado por município)
    clusters_dict = {}
    for u in unidades:
        municipio = u.municipio
        if municipio not in clusters_dict:
            clusters_dict[municipio] = {
                'municipio': municipio,
                'latitude': u.localizacao.latitude if u.localizacao else 0,
                'longitude': u.localizacao.longitude if u.localizacao else 0,
                'unidades': [],
                'total_leitos': 0,
                'leitos_ocupados': 0,
            }
        
        total_leitos = Leito.query.filter(
            Leito.setor.has(unidade_id=u.id),
            Leito.ativo == True
        ).count()
        
        leitos_ocu = Leito.query.filter(
            Leito.setor.has(unidade_id=u.id),
            Leito.ativo == True,
            Leito.status == 'ocupado'
        ).count()
        
        clusters_dict[municipio]['unidades'].append(u.nome)
        clusters_dict[municipio]['total_leitos'] += total_leitos
        clusters_dict[municipio]['leitos_ocupados'] += leitos_ocu
    
    # Calcular taxa de ocupação
    clusters = []
    for cluster_key, cluster_data in clusters_dict.items():
        taxa = (cluster_data['leitos_ocupados'] / cluster_data['total_leitos'] * 100) if cluster_data['total_leitos'] > 0 else 0
        cluster_data['taxa_ocupacao'] = round(taxa, 2)
        cluster_data['quantidade_unidades'] = len(cluster_data['unidades'])
        clusters.append(cluster_data)
    
    return jsonify({
        'clusters': clusters,
        'total_clusters': len(clusters),
        'timestamp': datetime.now().isoformat()
    })

# ========== DISTÂNCIA E PROXIMIDADE ==========

@api_geo_bp.route('/distancia', methods=['GET'])
@login_required
def calcular_distancia():
    """Calcula distância entre duas coordenadas (Haversine)"""
    
    lat1 = request.args.get('lat1', type=float)
    lng1 = request.args.get('lng1', type=float)
    lat2 = request.args.get('lat2', type=float)
    lng2 = request.args.get('lng2', type=float)
    
    if not all([lat1, lng1, lat2, lng2]):
        return jsonify({'erro': 'Parâmetros incompletos'}), 400
    
    # Haversine formula
    R = 6371  # Raio da Terra em km
    
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lng = math.radians(lng2 - lng1)
    
    a = math.sin(delta_lat/2) ** 2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lng/2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    
    distancia_km = R * c
    
    return jsonify({
        'distancia_km': round(distancia_km, 2),
        'distancia_mi': round(distancia_km * 0.621371, 2),
        'tempo_aproximado_minutos': round(distancia_km / 80 * 60)  # Aproximação de 80 km/h
    })

@api_geo_bp.route('/unidades-proximas', methods=['GET'])
@login_required
def unidades_proximas():
    """Encontra unidades próximas a uma coordenada"""
    
    latitude = request.args.get('latitude', type=float)
    longitude = request.args.get('longitude', type=float)
    raio_km = request.args.get('raio_km', 50, type=float)
    tipo = request.args.get('tipo')
    
    if not latitude or not longitude:
        return jsonify({'erro': 'Coordenadas requeridas'}), 400
    
    unidades = Unidade.query.join(Localizacao).filter(
        Unidade.ativo == True
    ).all()
    
    proximas = []
    
    for u in unidades:
        if not u.localizacao:
            continue
        
        # Calcular distância
        R = 6371
        lat1_rad = math.radians(latitude)
        lat2_rad = math.radians(u.localizacao.latitude)
        delta_lat = math.radians(u.localizacao.latitude - latitude)
        delta_lng = math.radians(u.localizacao.longitude - longitude)
        
        a = math.sin(delta_lat/2) ** 2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lng/2) ** 2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        distancia = R * c
        
        if distancia <= raio_km:
            # Calcular ocupação
            total_leitos = Leito.query.filter(
                Leito.setor.has(unidade_id=u.id),
                Leito.ativo == True
            ).count()
            
            leitos_ocu = Leito.query.filter(
                Leito.setor.has(unidade_id=u.id),
                Leito.ativo == True,
                Leito.status == 'ocupado'
            ).count()
            
            taxa = (leitos_ocu / total_leitos * 100) if total_leitos > 0 else 0
            
            if tipo is None or u.tipo == tipo:
                proximas.append({
                    'id': u.id,
                    'nome': u.nome,
                    'tipo': u.tipo,
                    'municipio': u.municipio,
                    'distancia_km': round(distancia, 2),
                    'tempo_minutos': round(distancia / 80 * 60),
                    'taxa_ocupacao': round(taxa, 2),
                    'leitos_disponiveis': total_leitos - leitos_ocu,
                    'latitude': u.localizacao.latitude,
                    'longitude': u.localizacao.longitude,
                })
    
    # Ordenar por distância
    proximas.sort(key=lambda x: x['distancia_km'])
    
    return jsonify({
        'total': len(proximas),
        'unidades': proximas,
        'raio_km': raio_km,
        'timestamp': datetime.now().isoformat()
    })

# ========== DEMANDA POR REGIÃO ==========

@api_geo_bp.route('/demanda/atualizar', methods=['POST'])
@login_required
def atualizar_demanda_regiao():
    """Atualiza dados de demanda por região (chamado por scheduler)"""
    
    if not current_user.is_admin():
        return jsonify({'erro': 'Acesso negado'}), 403
    
    # Buscar todos os municipios
    municipios = db.session.query(
        Localizacao.municipio,
        Localizacao.estado
    ).distinct().all()
    
    hoje = date.today()
    hora = datetime.now().hour
    
    for municipio, estado in municipios:
        # Calcular demanda
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
        
        # Calcular ocupação
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
        
        # Score de urgência
        score = (atendimentos_ps * 0.3 + internacoes * 0.4 + transferencias * 0.3) * 100
        score = min(score, 100)
        
        # Buscar ou criar registro
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
    
    return jsonify({'status': 'demanda atualizada', 'municipios': len(municipios)})

@api_geo_bp.route('/demanda/<string:estado>', methods=['GET'])
@login_required
@requer_acesso_estadual()
def demanda_estado(estado):
    """Retorna dados de demanda do estado"""
    
    data = request.args.get('data', str(date.today()))
    
    demandas = DemandaPorRegiao.query.filter(
        db.and_(
            DemandaPorRegiao.estado == estado,
            DemandaPorRegiao.data == data
        )
    ).order_by(DemandaPorRegiao.score_urgencia.desc()).all()
    
    return jsonify({
        'estado': estado,
        'data': data,
        'regioes': [d.to_dict() for d in demandas],
        'total': len(demandas),
        'score_medio': sum(d.score_urgencia for d in demandas) / len(demandas) if demandas else 0,
        'timestamp': datetime.now().isoformat()
    })