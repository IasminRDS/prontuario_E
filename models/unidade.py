# ... imports que você já tem
from database.db import db

class Unidade(db.Model):
    __tablename__ = "unidades"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(150), nullable=False)
    cnes = db.Column(db.String(20), nullable=True, unique=True)
    endereco = db.Column(db.String(200), nullable=True)
    municipio = db.Column(db.String(120), nullable=True, index=True)
    uf = db.Column(db.String(2), nullable=True, index=True)
    telefone = db.Column(db.String(20), nullable=True)
    tipo = db.Column(db.String(50), nullable=True)

    # NOVOS CAMPOS TERRITORIAIS
    municipio_ibge = db.Column(db.String(7), nullable=True, index=True)
    regional_id = db.Column(db.Integer, db.ForeignKey("regionais.id"), nullable=True, index=True)

    ativo = db.Column(db.Boolean, default=True, nullable=False)