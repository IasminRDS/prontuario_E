from database.db import db
from datetime import datetime

class Vacina(db.Model):
    """Cadastro de vacinas disponíveis (tabela de referência)."""
    __tablename__ = 'vacinas'

    id           = db.Column(db.Integer, primary_key=True)
    nome         = db.Column(db.String(150), nullable=False)
    sigla        = db.Column(db.String(20),  nullable=True)
    fabricante   = db.Column(db.String(100), nullable=True)
    doses_total  = db.Column(db.Integer,     default=1)
    intervalo_dias = db.Column(db.Integer,   nullable=True)   # entre doses
    idade_min_dias = db.Column(db.Integer,   nullable=True)   # faixa etária mínima em dias
    idade_max_dias = db.Column(db.Integer,   nullable=True)   # faixa etária máxima em dias
    descricao    = db.Column(db.Text,        nullable=True)
    ativo        = db.Column(db.Boolean,     default=True)

    aplicacoes   = db.relationship('VacinaAplicada', backref='vacina', lazy='dynamic')

    def __repr__(self):
        return f'<Vacina {self.sigla or self.nome}>'


class VacinaAplicada(db.Model):
    """Registro de cada dose aplicada a um paciente."""
    __tablename__ = 'vacinas_aplicadas'

    id           = db.Column(db.Integer, primary_key=True)
    paciente_id  = db.Column(db.Integer, db.ForeignKey('pacientes.id'),  nullable=False)
    vacina_id    = db.Column(db.Integer, db.ForeignKey('vacinas.id'),    nullable=False)
    unidade_id   = db.Column(db.Integer, db.ForeignKey('unidades.id'),   nullable=True)
    aplicado_por = db.Column(db.Integer, db.ForeignKey('users.id'),      nullable=True)

    dose_numero  = db.Column(db.Integer,     default=1)
    data_aplicacao = db.Column(db.Date,      nullable=False)
    lote         = db.Column(db.String(50),  nullable=True)
    via          = db.Column(db.String(30),  nullable=True)   # IM, SC, oral, ID
    local_aplicacao = db.Column(db.String(50), nullable=True) # deltoide D/E, vasto lateral...
    observacoes  = db.Column(db.Text,        nullable=True)

    criado_em    = db.Column(db.DateTime, default=datetime.utcnow)

    paciente    = db.relationship('Paciente', backref='vacinas_aplicadas')
    unidade     = db.relationship('Unidade',  backref='vacinas_aplicadas')
    profissional= db.relationship('User',     backref='vacinas_aplicadas')

    def __repr__(self):
        return f'<VacinaAplicada {self.vacina_id} dose {self.dose_numero}>'
