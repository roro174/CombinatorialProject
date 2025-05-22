"""
Project of Combinatorial Optimization: ISP problem
Main of the project
Authors:  
    - Fatima Ouchen - 000548670 - MA1-INFO
    - Rodolphe Prévot - 000550332 - MA1-INFO
Datum: 16/06/2025
"""

import json
import sys


def read_json(file_path):
    """
    Lit le contenu d'un fichier JSON  et le retourne sous forme de dictionnaire.
    
    :param file_path: Chemin vers le fichier JSON à lire.
    :return: Contenu du fichier sous forme de dictionnaire.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return json.load(file)
    except FileNotFoundError:
        print(f"Erreur : Le fichier '{file_path}' est introuvable.")
    except (PermissionError, IsADirectoryError, json.JSONDecodeError) as e:
        print(f"Erreur lors de la lecture du fichier JSON : {e}")


def main():
    """
    Fonction principale du programme.
    """
    if len(sys.argv) != 2:
        print("Usage : python main.py <chemin_du_fichier_json>")
        return

    file_path = sys.argv[1]
    content = read_json(file_path)
    if content is not None:
        print("Contenu du fichier :")
        print(content)
if __name__ == "__main__":
    main()
