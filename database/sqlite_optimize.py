# -*- coding: utf-8 -*-
"""
Otimizações para SQLite
Ativa WAL, indexação, e outras melhorias de performance
"""

from database.db import db
from sqlalchemy import text

def otimizar_sqlite():
    """Otimiza performance do SQLite com PRAGMA settings"""
    try:
        with db.engine.connect() as conn:
            # Write-Ahead Logging (permite múltiplas leituras simultâneas)
            conn.execute(text('PRAGMA journal_mode=WAL'))
            
            # Sincronização balanceada (rápida + segura)
            conn.execute(text('PRAGMA synchronous=NORMAL'))
            
            # Cache maior (32MB)
            conn.execute(text('PRAGMA cache_size=-32000'))
            
            # Temp storage em memória
            conn.execute(text('PRAGMA temp_store=MEMORY'))
            
            # Foreign keys ativadas
            conn.execute(text('PRAGMA foreign_keys=ON'))
            
            # Análise de query
            conn.execute(text('ANALYZE'))
            
            conn.commit()
        
        print("✓ SQLite otimizado com sucesso!")
    except Exception as e:
        print(f"⚠️  Erro ao otimizar SQLite: {e}")

def criar_indices():
    """Cria índices importantes para performance"""
    try:
        indices = [
            # Atendimento
            'CREATE INDEX IF NOT EXISTS idx_atendimento_data ON atendimento(data_hora)',
            'CREATE INDEX IF NOT EXISTS idx_atendimento_unidade ON atendimento(unidade_id)',
            'CREATE INDEX IF NOT EXISTS idx_atendimento_paciente ON atendimento(paciente_id)',
            
            # Internação
            'CREATE INDEX IF NOT EXISTS idx_internacao_data ON internacao(data_entrada)',
            'CREATE INDEX IF NOT EXISTS idx_internacao_unidade ON internacao(unidade_id)',
            'CREATE INDEX IF NOT EXISTS idx_internacao_status ON internacao(status)',
            'CREATE INDEX IF NOT EXISTS idx_internacao_paciente ON internacao(paciente_id)',
            
            # Cirurgia
            'CREATE INDEX IF NOT EXISTS idx_cirurgia_data ON cirurgia(data_agendada)',
            'CREATE INDEX IF NOT EXISTS idx_cirurgia_status ON cirurgia(status)',
            'CREATE INDEX IF NOT EXISTS idx_cirurgia_unidade ON cirurgia(unidade_id)',
            
            # Leito
            'CREATE INDEX IF NOT EXISTS idx_leito_status ON leito(status)',
            'CREATE INDEX IF NOT EXISTS idx_leito_setor ON leito(setor_id)',
            
            # Alerta
            'CREATE INDEX IF NOT EXISTS idx_alerta_timestamp ON alerta(timestamp)',
            'CREATE INDEX IF NOT EXISTS idx_alerta_critico ON alerta(nivel)',
            'CREATE INDEX IF NOT EXISTS idx_alerta_unidade ON alerta(unidade_id)',
            
            # KPI
            'CREATE INDEX IF NOT EXISTS idx_kpi_data ON kpi(data)',
            'CREATE INDEX IF NOT EXISTS idx_kpi_unidade ON kpi(unidade_id)',
            'CREATE INDEX IF NOT EXISTS idx_kpi_data_unidade ON kpi(data, unidade_id)',
            
            # Vaga
            'CREATE INDEX IF NOT EXISTS idx_vaga_status ON vaga(status)',
            'CREATE INDEX IF NOT EXISTS idx_vaga_unidade ON vaga(unidade_id)',
            'CREATE INDEX IF NOT EXISTS idx_vaga_setor ON vaga(setor_id)',
            
            # Localização
            'CREATE INDEX IF NOT EXISTS idx_localizacao_estado ON localizacao(estado)',
            'CREATE INDEX IF NOT EXISTS idx_localizacao_municipio ON localizacao(municipio)',
            
            # Demanda
            'CREATE INDEX IF NOT EXISTS idx_demanda_regiao_data ON demanda_por_regiao(municipio, estado, data)',
            
            # Faturamento
            'CREATE INDEX IF NOT EXISTS idx_faturamento_status ON faturamento(status)',
            'CREATE INDEX IF NOT EXISTS idx_faturamento_unidade ON faturamento(unidade_id)',
            'CREATE INDEX IF NOT EXISTS idx_faturamento_competencia ON faturamento(data_competencia)',
            
            # User
            'CREATE INDEX IF NOT EXISTS idx_user_email ON user(email)',
            'CREATE INDEX IF NOT EXISTS idx_user_cpf ON user(cpf)',
            
            # Paciente
            'CREATE INDEX IF NOT EXISTS idx_paciente_cpf ON paciente(cpf)',
            'CREATE INDEX IF NOT EXISTS idx_paciente_nome ON paciente(nome)',
        ]
        
        with db.engine.connect() as conn:
            for idx_sql in indices:
                try:
                    conn.execute(text(idx_sql))
                except Exception as e:
                    if 'no such table' not in str(e):
                        print(f"⚠️  Erro ao criar índice: {e}")
            
            conn.commit()
        
        print(f"✓ {len(indices)} índices criados com sucesso!")
    except Exception as e:
        print(f"⚠️  Erro ao criar índices: {e}")

def vacuum_database():
    """Recompacta o banco de dados"""
    try:
        with db.engine.connect() as conn:
            conn.execute(text('VACUUM'))
            conn.commit()
        
        print("✓ Banco de dados compactado (VACUUM)")
    except Exception as e:
        print(f"⚠️  Erro ao fazer VACUUM: {e}")

def analisar_database():
    """Analisa e atualiza estatísticas do banco"""
    try:
        with db.engine.connect() as conn:
            conn.execute(text('ANALYZE'))
            conn.commit()
        
        print("✓ Banco de dados analisado (ANALYZE)")
    except Exception as e:
        print(f"⚠️  Erro ao analisar banco: {e}")