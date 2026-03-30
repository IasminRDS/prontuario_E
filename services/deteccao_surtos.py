# -*- coding: utf-8 -*-
from models.atendimento import Atendimento
from models.alerta import Alerta
from database.db import db
from datetime import datetime, date, timedelta
from sqlalchemy import func
import statistics

class DetectorSurtos:
    """Detecta possíveis surtos e anomalias epidemiológicas"""
    
    def __init__(self):
        self.limiar_anomalia = 2.0  # 2x desvio padrão
    
    def detectar_surtos(self, estado=None, dias=30):
        """Detecta surtos por município/estado"""
        
        data_inicio = date.today() - timedelta(days=dias)
        
        # Agrupar por diagnóstico e município
        query = db.session.query(
            Atendimento.diagnostico,
            Atendimento.unidade.has(state=estado) if estado else True,
            func.count().label('total'),
            func.date(Atendimento.data_hora).label('data')
        ).filter(
            Atendimento.data_hora >= data_inicio
        ).group_by(
            Atendimento.diagnostico,
            func.date(Atendimento.data_hora)
        ).all()
        
        anomalias = []
        
        for diagnostico, _, total, data in query:
            # Calcular média histórica
            historico = db.session.query(func.count()).filter(
                Atendimento.diagnostico == diagnostico,
                Atendimento.data_hora < data_inicio
            ).scalar()
            
            if historico > 0:
                media = historico / 30
                desvio = statistics.stdev([historico - media, media])
                
                # Se aumento anormal
                if total > media + (self.limiar_anomalia * desvio):
                    anomalias.append({
                        'diagnostico': diagnostico,
                        'data': data,
                        'casos': total,
                        'media_historica': media,
                        'desvio_padrao': desvio,
                        'z_score': (total - media) / desvio if desvio > 0 else 0
                    })
        
        # Criar alertas para anomalias
        for anomalia in anomalias:
            if anomalia['z_score'] > 2.5:  # Muito anormal
                alerta = Alerta(
                    unidade_id=None,  # Estadual
                    tipo='surto',
                    nivel=2,
                    titulo=f"⚠️ POSSÍVEL SURTO: {anomalia['diagnostico']}",
                    mensagem=f"{anomalia['casos']} casos em {anomalia['data']} (normal: {anomalia['media_historica']:.0f})",
                    dados_json=anomalia
                )
                db.session.add(alerta)
        
        db.session.commit()
        return anomalias

def detectar_anomalias():
    """Função chamada pelo scheduler"""
    detector = DetectorSurtos()
    surtos = detector.detectar_surtos()
    return len(surtos)