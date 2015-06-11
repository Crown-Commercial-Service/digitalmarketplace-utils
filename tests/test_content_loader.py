# coding=utf-8

import unittest
import mock

import os
import tempfile
import yaml

from dmutils.content_loader import ContentLoader


class MonkeyPatch:
    def __init__(self, mocked_content=""):
        self.mocked_content = mocked_content

    def read_yaml_file(self, yaml_file):
        return yaml.load(self.mocked_content[yaml_file])

    def yaml_file_exists(self, file):
        return True


class TestContentLoader(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        ContentLoader._yaml_file_exists = MonkeyPatch().yaml_file_exists

    def test_a_simple_question(self):
        ContentLoader._read_yaml_file = MonkeyPatch({
            "manifest.yml": """
                -
                  name: First section
                  questions:
                    - firstQuestion
            """,
            "folder/firstQuestion.yml": """
                question: 'First question'
                dependsOnLots: 'SaaS'
            """
        }).read_yaml_file
        content = ContentLoader(
            "manifest.yml",
            "folder/"
        )
        self.assertEqual(
            content.get_question("firstQuestion").get("question"),
            "First question"
        )
