"""
Project of Combinatorial Optimization: ISP problem
Main of the project
Authors:  
    - Fatima Ouchen - 000548670 - MA1-INFO
    - Rodolphe Prévot - 000550332 - MA1-INFO
Datum: 16/06/2025
"""

import sys
from handle_json import HandleJson

def main():
    """
    Fonction principale du programme.
    """
    if len(sys.argv) != 2:
        print("Usage : python main.py <chemin_du_fichier_json>")
        return

    file_path = sys.argv[1]
    json_class = HandleJson(file_path)

if __name__ == "__main__":
    main()
