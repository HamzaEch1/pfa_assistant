#!/usr/bin/env python3
"""
Script to populate Apache Atlas with data from the Excel catalog file.
This script reads the catalogue_donnees_bancaires_modifie.xlsx file and creates
Atlas entities for data sources, glossary terms, technical references, and data flows.
"""

import pandas as pd
import json
import requests
import uuid
from typing import Dict, List, Any
import logging
import time
import base64
from requests.auth import HTTPBasicAuth
import sys
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AtlasPopulator:
    def __init__(self, atlas_url: str = "http://localhost:21000", username: str = "admin", password: str = "admin"):
        self.atlas_url = atlas_url
        self.auth = HTTPBasicAuth(username, password)
        self.session = requests.Session()
        self.session.auth = self.auth
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
        
    def wait_for_atlas(self, max_retries: int = 30) -> bool:
        """Wait for Atlas to be ready"""
        logger.info("Waiting for Atlas to be ready...")
        for i in range(max_retries):
            try:
                response = self.session.get(f"{self.atlas_url}/api/atlas/admin/version")
                if response.status_code == 200:
                    logger.info("Atlas is ready!")
                    return True
            except Exception as e:
                logger.info(f"Atlas not ready yet (attempt {i+1}/{max_retries}): {e}")
                time.sleep(10)
        logger.error("Atlas failed to become ready")
        return False

    def create_entity(self, entity_data: Dict[str, Any]) -> str:
        """Create an entity in Atlas and return its GUID"""
        try:
            response = self.session.post(
                f"{self.atlas_url}/api/atlas/v2/entity",
                data=json.dumps({"entity": entity_data})
            )
            if response.status_code in [200, 201]:
                result = response.json()
                guid = result.get("guidAssignments", {}).get(entity_data.get("guid", ""), "")
                logger.info(f"Created entity: {entity_data.get('attributes', {}).get('name', 'Unknown')} (GUID: {guid})")
                return guid
            else:
                logger.error(f"Failed to create entity: {response.status_code} - {response.text}")
                return ""
        except Exception as e:
            logger.error(f"Error creating entity: {e}")
            return ""

    def create_bulk_entities(self, entities: List[Dict[str, Any]]) -> List[str]:
        """Create multiple entities in Atlas"""
        try:
            response = self.session.post(
                f"{self.atlas_url}/api/atlas/v2/entity/bulk",
                data=json.dumps({"entities": entities})
            )
            if response.status_code in [200, 201]:
                result = response.json()
                guids = list(result.get("guidAssignments", {}).values())
                logger.info(f"Created {len(guids)} entities in bulk")
                return guids
            else:
                logger.error(f"Failed to create bulk entities: {response.status_code} - {response.text}")
                return []
        except Exception as e:
            logger.error(f"Error creating bulk entities: {e}")
            return []

    def create_data_source_entity(self, row: pd.Series) -> Dict[str, Any]:
        """Create a DataSource entity from Référentiel Sources sheet"""
        guid = str(uuid.uuid4())
        return {
            "guid": guid,
            "typeName": "DataSet",
            "attributes": {
                "name": str(row.get("Nom source", "Unknown")),
                "qualifiedName": f"datasource.{str(row.get('Nom source', 'unknown')).lower().replace(' ', '_')}@banque_ma",
                "description": str(row.get("Description", "")),
                "owner": "BanqueMA",
                "createTime": int(time.time() * 1000),
                "updateTime": int(time.time() * 1000)
            },
            "customAttributes": {
                "type_source": str(row.get("Type Source", "")),
                "plateforme_source": str(row.get("Plateforme source", "")),
                "flux_scenario": str(row.get("Flux/Scénario SD", "")),
                "domaine": str(row.get("Domaine", "")),
                "sous_domaine": str(row.get("Sous domaine", "")),
                "application_source": str(row.get("Application Source", "")),
                "plateforme_cible": str(row.get("Plateforme cible", "")),
                "nom_cible": str(row.get("Nom cible", "")),
                "mode_chargement": str(row.get("Mode chargement", "")),
                "frequence_maj": str(row.get("Fréquence MAJ", "")),
                "technologie_chargement": str(row.get("Technologie de chargement(Outil)", "")),
                "technologie": str(row.get("Technologie", "")),
                "nom_flux_procedure": str(row.get("Nom Flux/Procedure", "")),
                "taille_objet": str(row.get("Taille Objet", "")),
                "format": str(row.get("Format", "")),
                "filiale": str(row.get("Filiale", ""))
            }
        }

    def create_glossary_term_entity(self, row: pd.Series) -> Dict[str, Any]:
        """Create a GlossaryTerm entity from Glossaire Métier sheet"""
        guid = str(uuid.uuid4())
        return {
            "guid": guid,
            "typeName": "AtlasGlossaryTerm",
            "attributes": {
                "name": str(row.get("Libellé Métier", "Unknown")),
                "qualifiedName": f"glossary.{str(row.get('Libellé Métier', 'unknown')).lower().replace(' ', '_')}@banque_ma",
                "shortDescription": str(row.get("Description", "")),
                "longDescription": str(row.get("Description", "")),
                "abbreviation": "",
                "usage": str(row.get("Commentaire", "")),
                "examples": []
            },
            "customAttributes": {
                "proprietaire": str(row.get("Propriétaire", "")),
                "confidentialite": str(row.get("Confidentialité", "")),
                "regle_metier": str(row.get("Règle métier", "")),
                "criticite": str(row.get("Criticité", "")),
                "qualite_adressee": str(row.get("Aspect de performance adressé (Qualité)", ""))
            }
        }

    def create_technical_field_entity(self, row: pd.Series) -> Dict[str, Any]:
        """Create a Column entity from Réf technique sheet"""
        guid = str(uuid.uuid4())
        return {
            "guid": guid,
            "typeName": "Column",
            "attributes": {
                "name": str(row.get("Libellé champ", "Unknown")),
                "qualifiedName": f"column.{str(row.get('Nom source', 'unknown')).lower().replace(' ', '_')}.{str(row.get('Libellé champ', 'unknown')).lower().replace(' ', '_')}@banque_ma",
                "type": str(row.get("Type", "")),
                "length": self._safe_int(row.get("Taille", 0)),
                "isNullable": str(row.get("Obligatoire", "")).lower() != "oui",
                "comment": str(row.get("Commentaire", ""))
            },
            "customAttributes": {
                "nom_source": str(row.get("Nom source", "")),
                "plateforme": str(row.get("Plateforme", "")),
                "confidentialite": str(row.get("Confidentialité", "")),
                "regle_metier": str(row.get("Règle métier", "")),
                "libelle_metier": str(row.get("Libellé Métier", ""))
            }
        }

    def create_data_flow_entity(self, row: pd.Series) -> Dict[str, Any]:
        """Create a Process entity from Référentiel Flux sheet"""
        guid = str(uuid.uuid4())
        return {
            "guid": guid,
            "typeName": "Process",
            "attributes": {
                "name": str(row.get("Nom Flux", "Unknown")),
                "qualifiedName": f"process.{str(row.get('Nom Flux', 'unknown')).lower().replace(' ', '_')}@banque_ma",
                "description": str(row.get("Description traitement", "")),
                "owner": "BanqueMA"
            },
            "customAttributes": {
                "nom_champ_source": str(row.get("Nom Champ SD Source", "")),
                "nom_sd_source": str(row.get("Nom SD Source", "")),
                "plateforme_source": str(row.get("Plateforme source", "")),
                "regle_gestion": str(row.get("Règle de Gestion", "")),
                "nom_champ_cible": str(row.get("Nom Champ Cible", "")),
                "nom_sd_cible": str(row.get("Nom SD Cible", "")),
                "plateforme_cible": str(row.get("Plateforme cible", "")),
                "confidentialite": str(row.get("Confidentialité", "")),
                "commentaire": str(row.get("Commentaire", ""))
            }
        }

    def _safe_int(self, value, default=0):
        """Safely convert value to int"""
        try:
            return int(float(value))
        except (ValueError, TypeError):
            return default

    def process_excel_file(self, excel_path: str) -> bool:
        """Process the Excel file and populate Atlas"""
        try:
            # Read all sheets
            logger.info(f"Reading Excel file: {excel_path}")
            all_sheets = pd.read_excel(excel_path, sheet_name=None)
            logger.info(f"Found sheets: {list(all_sheets.keys())}")

            # Process each sheet
            for sheet_name, df in all_sheets.items():
                logger.info(f"Processing sheet: {sheet_name} ({len(df)} rows)")
                df = df.fillna('')  # Replace NaN with empty strings
                
                entities = []
                
                if sheet_name == 'Référentiel Sources':
                    for _, row in df.iterrows():
                        entity = self.create_data_source_entity(row)
                        entities.append(entity)
                        
                elif sheet_name == 'Glossaire Métier':
                    for _, row in df.iterrows():
                        entity = self.create_glossary_term_entity(row)
                        entities.append(entity)
                        
                elif sheet_name == 'Réf technique':
                    for _, row in df.iterrows():
                        entity = self.create_technical_field_entity(row)
                        entities.append(entity)
                        
                elif sheet_name == 'Référentiel Flux':
                    for _, row in df.iterrows():
                        entity = self.create_data_flow_entity(row)
                        entities.append(entity)
                
                # Create entities in batches
                if entities:
                    batch_size = 10
                    for i in range(0, len(entities), batch_size):
                        batch = entities[i:i + batch_size]
                        self.create_bulk_entities(batch)
                        time.sleep(1)  # Rate limiting
                        
            logger.info("Successfully populated Atlas with data from Excel file")
            return True
            
        except Exception as e:
            logger.error(f"Error processing Excel file: {e}")
            return False

def main():
    excel_path = "/opt/atlas/input-data/catalogue_donnees_bancaires_modifie.xlsx"
    
    # Check if running inside container or locally
    if not os.path.exists(excel_path):
        excel_path = "./data/catalogue_donnees_bancaires_modifie.xlsx"
    
    if not os.path.exists(excel_path):
        logger.error(f"Excel file not found at {excel_path}")
        sys.exit(1)
    
    populator = AtlasPopulator()
    
    # Wait for Atlas to be ready
    if not populator.wait_for_atlas():
        logger.error("Atlas is not ready. Exiting.")
        sys.exit(1)
    
    # Process the Excel file
    success = populator.process_excel_file(excel_path)
    
    if success:
        logger.info("Atlas population completed successfully!")
        logger.info("You can access Atlas at: http://localhost:21000")
        logger.info("Username: admin, Password: admin")
    else:
        logger.error("Atlas population failed!")
        sys.exit(1)

if __name__ == "__main__":
    main() 