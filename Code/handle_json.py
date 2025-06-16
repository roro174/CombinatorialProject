"""
Project of Combinatorial Optimization: ISP problem
handle all the json data
Authors:  
    - Fatima Ouchen - 000548670 - MA1-INFO
    - Rodolphe Prévot - 000550332 - MA1-INFO
    - Chahine Mabrouk Bouzouita - 000495542 - MA1-IRCI
Datum: 16/06/2025
"""

import json

class HandleJson:
    """A class to handle JSON data from a file."""
    def __init__(self, json_path: str):
        self._json_dic = self.__read_json(json_path)
        self._interpreters_lang = self._json_dic['Languages_i']
        self._sessions_blocks = self._json_dic['Sessions_b']
        self._blocks = self._json_dic['Blocks']
        self._sessions = self._json_dic['Sessions']
        self._interpreters = self._json_dic['Interpreters']
        self._languages = self._json_dic['Languages']
        self._sessions_lang = self._json_dic['Languages_s']

    def __read_json(self, file_path: str) -> dict:
        """
        read the JSON file and put its content in dictionnaries.
        
        :param file_path: path of the JSON file.
        :return: a dictionary containing the JSON data.
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                return json.load(file)
        except Exception as exc:
            raise RuntimeError(f"Error in the lecture of the JSON file : {exc}") from exc

    def get_interpreters(self) -> list[str]:
        """
        Getter for the interpreter list.
        
        :return: interpreters list.
        """
        return self._interpreters


    def get_sessions(self) -> list[str]:
        """
        Getter for the sessions list.
        
        :return: sessions list.
        """
        return self._sessions


    def get_interpreters_lang(self) ->dict[str, list[str]]:
        """
        Getter for the interpreters' languages.
        
        :return: List of interpreters' languages.
        """
        return self._interpreters_lang

    def get_sessions_blocks(self) -> dict[str, list[str]]:
        """
        Getter for the sessions blocks.
        
        :return: List of sessions blocks.
        """
        return self._sessions_blocks

    def get_blocks(self) -> list[str]:
        """
        Getter for the blocks.
        
        :return: List of blocks.
        """
        return self._blocks

    def get_languages(self) -> list[str]:
        """
        Getter for the languages.
        
        :return: Dictionary of languages.
        """
        return self._languages

    def get_sessions_lang(self) -> dict[str, list[str]]:
        """
        Getter for the sessions' languages.
        
        :return: Dictionary of sessions' languages.
        """
        return self._sessions_lang
