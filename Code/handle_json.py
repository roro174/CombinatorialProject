"""
Project of Combinatorial Optimization: ISP problem
handle all the json data
Authors:  
    - Fatima Ouchen - 000548670 - MA1-INFO
    - Rodolphe Prévot - 000550332 - MA1-INFO
Datum: 16/06/2025
"""

import json


class HandleJson:
    """A class to handle JSON data from a file."""
    def __init__(self, json_path: str):
        self._json_dic = self.__read_json(json_path)
        self._interpreters = self._json_dic.get('Languages_i', [])
        self._sessions = self._json_dic.get('__Sessions_b', [])

    def __read_json(self, file_path: str) -> dict:
        """
        Lit le contenu d'un fichier JSON  et le retourne sous forme de dictionnaire.
        
        :param file_path: Chemin vers le fichier JSON à lire.
        :return: Contenu du fichier sous forme de dictionnaire.
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                return json.load(file)
        except FileNotFoundError as exc:
            raise FileNotFoundError(f"Erreur : Le fichier '{file_path}' est introuvable.") from exc

        except (PermissionError, IsADirectoryError, json.JSONDecodeError) as exc:
            raise RuntimeError(f"Erreur lors de la lecture du fichier JSON : {exc}") from exc


    def get_interpreters(self) -> dict[str, list[str]]:
        """
        Getter pour la liste des interprètes.
        
        :return: Liste des interprètes.
        """
        return self._interpreters


    def get_sessions(self) -> dict[str, list[str]]:
        """
        Getter pour la liste des __sessions.
        
        :return: Liste des __sessions.
        """
        return self._sessions
