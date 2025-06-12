"""
Project of Combinatorial Optimization: ISP problem
Main of the project
Authors:  
    - Fatima Ouchen - 000548670 - MA1-INFO
    - Rodolphe Prévot - 000550332 - MA1-INFO
    - Chahine Mabrouk Bouzouita - 000495542 - MA1-IRCI
Datum: 16/06/2025
"""
import gurobipy as gp
from gurobipy import GRB
import numpy as np
import pandas as pd
import os
import json
import sys
from isp_model import ISPModel
from handle_json import HandleJson

def decision_variables(data):
    """
    Crée les variables de décision pour le modèle Gurobi.
    
    :param data: Le modèle Gurobi.
    """

    assigned_inter = {}
    assigned_inter_lang = {}
    

def main():
    """
    Fonction principale du programme.
    """
    if len(sys.argv) != 2:
        print("Usage : python main.py <chemin_du_fichier_json>")
        return

    file_path = sys.argv[1]
    
    try:
        # Charger les données JSON
        data_handler = HandleJson(file_path)

        # Créer le modèle
        model = ISPModel(data_handler)

        # Résoudre OF1
        print(f"\n--- Résolution de OF1 pour {file_path} ---")
        model.solve_OF1()
        # Résoudre OF2
        print(f"\n--- Résolution de OF2 pour {file_path} ---")
        model.solve_OF2()


    except Exception as e:
        print(f"Erreur : {e}")

if __name__ == "__main__":
    main()
