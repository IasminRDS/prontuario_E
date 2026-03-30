# -*- crypto: utf-8 -*-
"""
Seed de vagas de teste
Popula banco com vagas para testes
"""

from models.vaga import Vaga, StatusVaga
from models.unidade import Unidade
from models.internacao import Leito, Setor
from database.db import db
import random
from datetime import datetime, timedelta

def seed_vagas():
    """Popula banco com vagas de teste"""
    
    print("\n🛏️  Carregando vagas de teste...\n")
    
    unidades = Unidade.query.all()[:3]  # Apenas 3 primeiras unidades
    
    total_vagas = 0
    
    for unidade in unidades:
        setores = unidade.setores[:2]  # Apenas 2 primeiros setores
        
        for setor in setores:
            leitos = Leito.query.filter_by(setor_id=setor.id).limit(5).all()
            
            for leito in leitos:
                status = random.choice([
                    StatusVaga.DISPONIVEL.value,
                    StatusVaga.DISPONIVEL.value,
                    StatusVaga.DISPONIVEL.value,
                    StatusVaga.OCUPADA.value,
                    StatusVaga.RESERVADA.value,
                ])
                
                tipo = random.choice(['clinico', 'cirurgico', 'critico'])
                isolamento = random.choice([True, False])
                
                vaga = Vaga(
                    leito_id=leito.id,
                    setor_id=setor.id,
                    unidade_id=unidade.id,
                    status=status,
                    tipo_paciente=tipo,
                    isolamento=isolamento,
                    ativo=True
                )
                
                # Se ocupada, adicionar dados
                if status == StatusVaga.OCUPADA.value:
                    pacientes = Paciente.query.limit(1).all()
                    if pacientes:
                        paciente = pacientes[0]
                        internacoes = Internacao.query.filter_by(paciente_id=paciente.id).limit(1).all()
                        
                        if internacoes:
                            internacao = internacoes[0]
                            vaga.paciente_id = paciente.id
                            vaga.internacao_id = internacao.id
                            vaga.data_ocupacao = datetime.now() - timedelta(days=random.randint(1, 10))
                
                db.session.add(vaga)
                total_vagas += 1
    
    db.session.commit()
    print(f"  ✓ {total_vagas} vagas criadas")
    print("\n✓ Vagas de teste carregadas!\n")