# -*- coding: utf-8 -*-
"""
Integração com RNDS (Rede Nacional de Dados em Saúde)
Sistema de troca de dados entre serviços de saúde
"""

import requests
import json
from datetime import datetime

class ClienteRNDS:
    def __init__(self, client_id, client_secret):
        self.client_id = client_id
        self.client_secret = client_secret
        self.base_url = "https://rnds.saude.gov.br/api"
        self.token = None
    
    def autenticar(self):
        """Autentica no RNDS"""
        url = f"{self.base_url}/token"
        payload = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret
        }
        
        try:
            response = requests.post(url, json=payload)
            if response.status_code == 200:
                self.token = response.json()['access_token']
                return True
        except Exception as e:
            print(f"Erro ao autenticar RNDS: {e}")
        
        return False
    
    def enviar_resultado_exame(self, paciente, exame):
        """Envia resultado de exame para RNDS"""
        
        if not self.token:
            self.autenticar()
        
        headers = {
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/fhir+json'
        }
        
        # Formato FHIR (Fast Healthcare Interoperability Resources)
        payload = {
            "resourceType": "DiagnosticReport",
            "status": "final",
            "code": {
                "coding": [{
                    "system": "http://loinc.org",
                    "code": exame.codigo_loinc
                }]
            },
            "subject": {
                "reference": f"Patient/{paciente.cpf}"
            },
            "issued": datetime.now().isoformat(),
            "performer": [{
                "reference": f"Organization/{exame.unidade.cnes}"
            }],
            "result": [{
                "reference": f"Observation/{exame.id}"
            }]
        }
        
        try:
            url = f"{self.base_url}/fhir/r4/DiagnosticReport"
            response = requests.post(url, json=payload, headers=headers)
            
            if response.status_code in [200, 201]:
                return True
        except Exception as e:
            print(f"Erro ao enviar para RNDS: {e}")
        
        return False
    
    def buscar_prescricoes_paciente(self, cpf):
        """Busca prescrições compartilhadas do paciente"""
        
        if not self.token:
            self.autenticar()
        
        headers = {'Authorization': f'Bearer {self.token}'}
        
        try:
            url = f"{self.base_url}/fhir/r4/MedicationRequest?subject=Patient/{cpf}"
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                return response.json()['entry']
        except Exception as e:
            print(f"Erro ao buscar prescrições: {e}")
        
        return []