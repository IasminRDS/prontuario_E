# -*- coding: utf-8 -*-
"""
Configuração do banco de dados
Inicializa SQLAlchemy e LoginManager
"""

from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from datetime import datetime

db = SQLAlchemy()
login_manager = LoginManager()

def init_db(app):
    """Inicializa o banco de dados e importa todos os models"""
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Por favor, faça login para acessar esta página.'
    login_manager.login_message_category = 'warning'
    
    with app.app_context():
        print("\n📚 Carregando models...")
        
        # ========== IMPORTAR MODELS EXISTENTES ==========
        
        try:
            from models.user import User
            print("  ✓ User")
        except ImportError as e:
            print(f"  ✗ User: {e}")
        
        try:
            from models.paciente import Paciente
            print("  ✓ Paciente")
        except ImportError as e:
            print(f"  ✗ Paciente: {e}")
        
        try:
            from models.medico import Medico
            print("  ✓ Médico")
        except ImportError as e:
            print(f"  ✗ Médico: {e}")
        
        try:
            from models.unidade import Unidade
            print("  ✓ Unidade")
        except ImportError as e:
            print(f"  ✗ Unidade: {e}")
        
        try:
            from models.atendimento import Atendimento
            print("  ✓ Atendimento")
        except ImportError as e:
            print(f"  ✗ Atendimento: {e}")
        
        try:
            from models.prontuario import Prontuario
            print("  ✓ Prontuário")
        except ImportError as e:
            print(f"  ✗ Prontuário: {e}")
        
        try:
            from models.audit_log import AuditLog
            print("  ✓ AuditLog")
        except ImportError as e:
            print(f"  ✗ AuditLog: {e}")
        
        try:
            from models.agendamento import Agendamento
            print("  ✓ Agendamento")
        except ImportError as e:
            print(f"  ✗ Agendamento: {e}")
        
        try:
            from models.vacina import Vacina, VacinaAplicada
            print("  ✓ Vacina, VacinaAplicada")
        except ImportError as e:
            print(f"  ✗ Vacina: {e}")
        
        try:
            from models.triagem import Triagem
            print("  ✓ Triagem")
        except ImportError as e:
            print(f"  ✗ Triagem: {e}")
        
        try:
            from models.exame import TipoExame, ExameSolicitado
            print("  ✓ TipoExame, ExameSolicitado")
        except ImportError as e:
            print(f"  ✗ Exame: {e}")
        
        try:
            from models.encaminhamento import Encaminhamento
            print("  ✓ Encaminhamento")
        except ImportError as e:
            print(f"  ✗ Encaminhamento: {e}")
        
        try:
            from models.medicamento import Medicamento, Prescricao, ItemPrescricao
            print("  ✓ Medicamento, Prescricao, ItemPrescricao")
        except ImportError as e:
            print(f"  ✗ Medicamento: {e}")
        
        try:
            from models.internacao import Setor, Leito, Internacao, EvolucaoInternacao
            print("  ✓ Setor, Leito, Internacao, EvolucaoInternacao")
        except ImportError as e:
            print(f"  ✗ Internação: {e}")
        
        try:
            from models.prescricao_hospitalar import PrescricaoHospitalar, ItemPrescricaoHosp, AdministracaoMed
            print("  ✓ PrescricaoHospitalar, ItemPrescricaoHosp, AdministracaoMed")
        except ImportError as e:
            print(f"  ✗ PrescricaoHospitalar: {e}")
        
        try:
            from models.cirurgia import SalaCirurgica, Cirurgia
            print("  ✓ SalaCirurgica, Cirurgia")
        except ImportError as e:
            print(f"  ✗ Cirurgia: {e}")
        
        try:
            from models.estoque import ItemEstoque, MovEstoque
            print("  ✓ ItemEstoque, MovEstoque")
        except ImportError as e:
            print(f"  ✗ Estoque: {e}")
        
        try:
            from models.faturamento import AIH, APAC
            print("  ✓ AIH, APAC")
        except ImportError as e:
            print(f"  ✗ Faturamento: {e}")
        
        try:
            from models.pronto_socorro import AtendimentoPS
            print("  ✓ AtendimentoPS")
        except ImportError as e:
            print(f"  ✗ AtendimentoPS: {e}")
        
        try:
            from models.transferencia import TransferenciaPaciente
            print("  ✓ TransferenciaPaciente")
        except ImportError as e:
            print(f"  ✗ TransferenciaPaciente: {e}")
        
        # ========== NOVOS MODELS (OPCIONAIS) ==========
        
        try:
            from models.permissao import Permissao, Role, RolePermissao, AcessoEstadual
            print("  ✓ Permissão, Role, RolePermissao, AcessoEstadual")
        except ImportError:
            print("  ⚠️  Permissões não carregadas (opcional)")
        
        try:
            from models.alerta import Alerta, ConfiguradorAlerta
            print("  ✓ Alerta, ConfiguradorAlerta")
        except ImportError:
            print("  ⚠️  Alertas não carregados (opcional)")
        
        try:
            from models.kpi import KPI
            print("  ✓ KPI")
        except ImportError:
            print("  ⚠️  KPI não carregado (opcional)")
        
        try:
            from models.predicao import Predicao
            print("  ✓ Predicao")
        except ImportError:
            print("  ⚠️  Predicão não carregada (opcional)")
        
        try:
            from models.vaga import Vaga, SolicitacaoTransferencia
            print("  ✓ Vaga, SolicitacaoTransferencia")
        except ImportError:
            print("  ⚠️  Vagas não carregadas (opcional)")
        
        try:
            from models.localizacao import Localizacao, AcessibilidadeRegiao, DemandaPorRegiao
            print("  ✓ Localizacao, AcessibilidadeRegiao, DemandaPorRegiao")
        except ImportError:
            print("  ⚠️  Localização não carregada (opcional)")
        
        try:
            from models.faturamento_sia_sih import Faturamento, ProcessoFaturamento
            print("  ✓ Faturamento (SIA/SIH), ProcessoFaturamento")
        except ImportError:
            print("  ⚠️  Faturamento SIA/SIH não carregado (opcional)")
        
        try:
            from models.telemedicina import ConsultaTelemedicina, MonitoramentoPaciente
            print("  ✓ ConsultaTelemedicina, MonitoramentoPaciente")
        except ImportError:
            print("  ⚠️  Telemedicina não carregada (opcional)")
        
        try:
            from routes.api_notificacoes_push import SubscricaoPush
            print("  ✓ SubscricaoPush")
        except ImportError:
            print("  ⚠️  Push Notifications não carregadas (opcional)")
        
        print("\n✓ Modelos carregados!\n")
        
        # ========== CRIAR TABELAS ==========
        print("🗄️  Criando tabelas...")
        try:
            db.create_all()
            print("  ✓ Tabelas criadas/verificadas\n")
            
            # ========== POPULAR DADOS INICIAIS ==========
            _seed_data()
        except Exception as e:
            print(f"  ✗ Erro ao criar tabelas: {e}")
            print("\n⚠️  Verifique seus models!")
            import traceback
            traceback.print_exc()


def _seed_data():
    """Popula dados iniciais no banco"""
    from models.user import User
    from models.unidade import Unidade
    from models.medico import Medico
    
    if User.query.first():
        print("✓ Dados iniciais já existem\n")
        return

    print("🌱 Populando dados iniciais...\n")

    try:
        # ========== CRIAR UNIDADE PADRÃO ==========
        unidade = Unidade(
            nome='UBS Central',
            cnes='1234567',
            endereco='Rua da Saúde, 100',
            municipio='Bom Jesus da Lapa',
            uf='BA',
            telefone='(77) 3481-0000',
            tipo='UBS'
        )
        db.session.add(unidade)
        db.session.flush()
        print("  ✓ Unidade criada: UBS Central")

        # ========== CRIAR ADMIN PADRÃO ==========
        admin = User(
            nome='Administrador',
            email='admin@sus.gov.br',
            cpf='00000000001',
            perfil='admin',
            unidade_id=unidade.id,
            ativo=True
        )
        admin.set_password('admin123')
        db.session.add(admin)
        print("  ✓ Admin criado: admin@sus.gov.br / admin123")

        # ========== CRIAR MÉDICO PADRÃO ==========
        medico_user = User(
            nome='Dr. João Silva',
            email='medico@sus.gov.br',
            cpf='00000000002',
            perfil='medico',
            unidade_id=unidade.id,
            ativo=True
        )
        medico_user.set_password('medico123')
        db.session.add(medico_user)
        db.session.flush()
        print("  ✓ Médico criado: medico@sus.gov.br / medico123")

        medico = Medico(
            user_id=medico_user.id,
            crm='12345-BA',
            especialidade='Clínica Geral',
            unidade_id=unidade.id
        )
        db.session.add(medico)
        db.session.commit()

        # ========== SEED DE DADOS COMPLEMENTARES ==========
        _seed_vacinas()
        _seed_exames()
        _seed_hospital()
        _seed_gestor_estadual()
        
        print("\n✓ Dados iniciais populados com sucesso!\n")

    except Exception as e:
        print(f"\n✗ Erro ao popular dados: {e}\n")
        import traceback
        traceback.print_exc()
        db.session.rollback()


def _seed_gestor_estadual():
    """Cria gestor estadual padrão"""
    from models.user import User
    
    if User.query.filter_by(perfil='gestor_estadual').first():
        return
    
    gestor = User(
        nome='Gestor Estadual',
        email='gestor@saude.gov.br',
        cpf='00000000003',
        perfil='gestor_estadual',
        ativo=True,
        unidade_id=None,
    )
    gestor.set_password('gestor123')
    db.session.add(gestor)
    db.session.commit()
    print("  ✓ Gestor Estadual criado: gestor@saude.gov.br / gestor123")


def _seed_hospital():
    """Cria setores e leitos padrão"""
    from models.internacao import Setor, Leito
    from models.cirurgia import SalaCirurgica
    
    if Setor.query.first():
        return
    
    print("  Criando setores e leitos...")
    
    setores_data = [
        ('Clínica Médica', 'CM', 'enfermaria', '2º andar', 10),
        ('Pronto-Socorro', 'PS', 'ps', 'Térreo', 8),
        ('UTI Adulto', 'UTI', 'uti', '3º andar', 6),
        ('Pediatria', 'PED', 'enfermaria', '2º andar', 8),
        ('Maternidade', 'MAT', 'obstetricia', '1º andar', 6),
        ('Cirurgia Geral', 'CG', 'enfermaria', '2º andar', 8),
    ]
    
    for nome, sigla, tipo, andar, qtd in setores_data:
        s = Setor(nome=nome, sigla=sigla, tipo=tipo, andar=andar)
        db.session.add(s)
        db.session.flush()
        
        for i in range(1, qtd + 1):
            l = Leito(
                setor_id=s.id,
                numero=f'{sigla}-{i:02d}',
                tipo='uti' if tipo == 'uti' else 'comum'
            )
            db.session.add(l)
    
    print("  Criando salas cirúrgicas...")
    salas = [
        ('CC-01', 'geral'),
        ('CC-02', 'geral'),
        ('CC-Ortopedia', 'ortopedia'),
        ('CC-Urgência', 'urgencia')
    ]
    
    for nome, tipo in salas:
        db.session.add(SalaCirurgica(nome=nome, tipo=tipo))
    
    db.session.commit()
    print("  ✓ Setores e leitos criados")


def _seed_exames():
    """Cria tipos de exame padrão"""
    from models.exame import TipoExame
    
    if TipoExame.query.first():
        return
    
    print("  Criando tipos de exame...")
    
    exames = [
        TipoExame(codigo='HMG', nome='Hemograma completo', categoria='laboratorial', instrucoes='Não requer jejum'),
        TipoExame(codigo='GLI', nome='Glicemia em jejum', categoria='laboratorial', instrucoes='Jejum de 8 horas'),
        TipoExame(codigo='URE', nome='Ureia', categoria='laboratorial', instrucoes='Jejum de 4 horas'),
        TipoExame(codigo='CRE', nome='Creatinina', categoria='laboratorial', instrucoes='Jejum de 4 horas'),
        TipoExame(codigo='PCR', nome='Proteína C-reativa (PCR)', categoria='laboratorial', instrucoes='Jejum de 4 horas'),
        TipoExame(codigo='VHS', nome='Velocidade de hemossedimentação', categoria='laboratorial'),
        TipoExame(codigo='TGO', nome='TGO (AST)', categoria='laboratorial', instrucoes='Jejum de 4 horas'),
        TipoExame(codigo='TGP', nome='TGP (ALT)', categoria='laboratorial', instrucoes='Jejum de 4 horas'),
        TipoExame(codigo='COL', nome='Colesterol total e frações', categoria='laboratorial', instrucoes='Jejum de 12 horas'),
        TipoExame(codigo='TRI', nome='Triglicerídeos', categoria='laboratorial', instrucoes='Jejum de 12 horas'),
        TipoExame(codigo='TSH', nome='TSH', categoria='laboratorial', instrucoes='Não requer jejum'),
        TipoExame(codigo='T4L', nome='T4 livre', categoria='laboratorial', instrucoes='Não requer jejum'),
        TipoExame(codigo='URO', nome='Urina tipo I (EAS)', categoria='laboratorial', instrucoes='Primeira urina da manhã'),
        TipoExame(codigo='URC', nome='Urocultura', categoria='laboratorial', instrucoes='Primeira urina da manhã'),
        TipoExame(codigo='HBA1', nome='Hemoglobina glicada (HbA1c)', categoria='laboratorial', instrucoes='Não requer jejum'),
        TipoExame(codigo='RXTO', nome='Raio-X de tórax', categoria='imagem'),
        TipoExame(codigo='RXAB', nome='Raio-X de abdome', categoria='imagem'),
        TipoExame(codigo='USAB', nome='Ultrassom abdominal', categoria='imagem', instrucoes='Jejum de 6 horas'),
        TipoExame(codigo='USPV', nome='Ultrassom pélvico', categoria='imagem', instrucoes='Bexiga cheia'),
        TipoExame(codigo='ECG', nome='Eletrocardiograma', categoria='funcional'),
        TipoExame(codigo='PICO', nome='Peak flow / espirometria', categoria='funcional'),
    ]
    
    for e in exames:
        db.session.add(e)
    
    db.session.commit()
    print("  ✓ Tipos de exame criados")


def _seed_vacinas():
    """Cria vacinas padrão"""
    from models.vacina import Vacina
    
    if Vacina.query.first():
        return
    
    print("  Criando vacinas padrão...")
    
    vacinas = [
        Vacina(nome='BCG', sigla='BCG', doses_total=1),
        Vacina(nome='Hepatite B', sigla='HepB', doses_total=3, intervalo_dias=30),
        Vacina(nome='Pentavalente (DTP+Hib+HepB)', sigla='Penta', doses_total=3, intervalo_dias=60),
        Vacina(nome='VIP — Poliomielite inativada', sigla='VIP', doses_total=3, intervalo_dias=60),
        Vacina(nome='VRH — Rotavírus humano', sigla='VRH', doses_total=2, intervalo_dias=60),
        Vacina(nome='Pneumocócica 10-valente', sigla='Pneumo', doses_total=3, intervalo_dias=60),
        Vacina(nome='Meningocócica C', sigla='MenC', doses_total=2, intervalo_dias=60),
        Vacina(nome='Febre Amarela', sigla='FA', doses_total=1),
        Vacina(nome='Tríplice Viral (SCR)', sigla='SCR', doses_total=2, intervalo_dias=30),
        Vacina(nome='Varicela', sigla='VZV', doses_total=1),
        Vacina(nome='Hepatite A', sigla='HepA', doses_total=1),
        Vacina(nome='dT — Dupla adulto', sigla='dT', doses_total=3, intervalo_dias=60),
        Vacina(nome='dTpa — Tríplice bacteriana', sigla='dTpa', doses_total=1),
        Vacina(nome='Influenza', sigla='Flu', doses_total=1),
        Vacina(nome='Covid-19', sigla='COVID', doses_total=2, intervalo_dias=28),
        Vacina(nome='HPV quadrivalente', sigla='HPV', doses_total=2, intervalo_dias=180),
    ]
    
    for v in vacinas:
        db.session.add(v)
    
    db.session.commit()
    print("  ✓ Vacinas criadas")