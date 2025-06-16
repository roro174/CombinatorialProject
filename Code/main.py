"""
Project of Combinatorial Optimization: ISP problem
Main of the project
Authors:  
    - Fatima Ouchen - 000548670 - MA1-INFO
    - Rodolphe Prévot - 000550332 - MA1-INFO
    - Chahine Mabrouk Bouzouita - 000495542 - MA1-IRCI
Datum: 16/06/2025
"""


import sys
from isp_model import ISPModel
from handle_json import HandleJson



def main():
    """
    main of the program.
    """
    if len(sys.argv) != 4:
        print("Usage : python3 main.py "
        "<chemin_du_fichier_json>, question 2 (True/False), bridge (True/False)")
        return

    file_path = sys.argv[1]
    try:
        # load the data from the JSON file
        data_handler = HandleJson(file_path)

        question2 = sys.argv[2].lower() == 'true'
        bridge = sys.argv[3].lower() == 'true'

        # xreate the ISPModel instance
        model = ISPModel(data_handler, question2, bridge)

        # OF1
        print(f"\n--- Résolution de OF1 pour {file_path} ---")
        model.solve_of(False, True)
        # OF2
        print(f"\n--- Résolution de OF2 pour {file_path} ---")
        model.solve_of(False, False)


    except (FileNotFoundError, ValueError, KeyError) as e:
        print(f"Erreur : {e}")

if __name__ == "__main__":
    main()
