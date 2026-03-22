from database.db import db
from datetime import datetime

class Unidade(db.Model):
    __tablename__ = 'unidades'

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(200), nullable=False)
    cnes = db.Column(db.String(7), unique=True, nullable=True)
    tipo = db.Column(db.String(50), nullable=True)  # UBS, UPA, Hospital, etc.
    endereco = db.Column(db.String(200), nullable=True)
    municipio = db.Column(db.String(100), nullable=True)
    uf = db.Column(db.String(2), nullable=True)
    telefone = db.Column(db.String(20), nullable=True)
    ativo = db.Column(db.Boolean, default=True)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Unidade {self.nome}>'
