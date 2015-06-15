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

    def test_a_question_with_a_dependency(self):
        ContentLoader._read_yaml_file = MonkeyPatch({
          "manifest.yml": """
              -
                name: First section
                questions:
                  - firstQuestion
          """,
          "folder/firstQuestion.yml": """
                question: 'First question'
                depends:
                    -
                      "on": lot
                      being: SCS

          """
        }).read_yaml_file
        content = ContentLoader(
            "manifest.yml",
            "folder/"
        )
        content.filter({
            "lot": "SCS"
        })
        self.assertEqual(
            len(content.sections),
            1
        )

    def test_a_question_with_a_dependency_that_doesnt_match(self):
        ContentLoader._read_yaml_file = MonkeyPatch({
          "manifest.yml": """
              -
                name: First section
                questions:
                  - firstQuestion
          """,
          "folder/firstQuestion.yml": """
            question: 'First question'
            depends:
                -
                  "on": lot
                  being: SCS
          """
        }).read_yaml_file
        content = ContentLoader(
            "manifest.yml",
            "folder/"
        )
        content.filter({
            "lot": "SaaS"
        })
        self.assertEqual(
            len(content.sections),
            0
        )

    def test_a_question_which_depends_on_one_of_several_answers(self):
        ContentLoader._read_yaml_file = MonkeyPatch({
          "manifest.yml": """
              -
                name: First section
                questions:
                  - firstQuestion
          """,
          "firstQuestion.yml": """
                question: 'First question'
                depends:
                    -
                      "on": lot
                      being:
                       - SCS
                       - SaaS
                       - PaaS

          """
        }).read_yaml_file
        content = ContentLoader(
            "manifest.yml",
            "folder/"
        )
        content.filter({
            "lot": "SaaS"
        })
        self.assertEqual(
            len(content.sections),
            1
        )

    def test_a_question_which_depends_on_one_of_several_answers(self):
        ContentLoader._read_yaml_file = MonkeyPatch({
          "manifest.yml": """
              -
                name: First section
                questions:
                  - firstQuestion
          """,
          "folder/firstQuestion.yml": """
                question: 'First question'
                depends:
                    -
                      "on": lot
                      being:
                       - SCS
                       - SaaS
                       - PaaS

          """
        }).read_yaml_file
        content = ContentLoader(
            "manifest.yml",
            "folder/"
        )
        content.filter({
            "lot": "IaaS"
        })
        self.assertEqual(
            len(content.sections),
            0
        )

    def test_a_section_which_has_a_mixture_of_dependencies(self):
        ContentLoader._read_yaml_file = MonkeyPatch({
          "manifest.yml": """
              -
                name: First section
                questions:
                  - firstQuestion
                  - secondQuestion
              -
                name: Second section
                questions:
                  - firstQuestion
          """,
          "folder/firstQuestion.yml": """
                question: 'First question'
                depends:
                    -
                      "on": lot
                      being:
                       - SCS
                       - SaaS
                       - PaaS
          """,
          "folder/secondQuestion.yml": """
                question: 'Second question'
                depends:
                    -
                      "on": lot
                      being: IaaS

          """
        }).read_yaml_file
        content = ContentLoader(
            "manifest.yml",
            "folder/"
        )
        content.filter({
            "lot": "IaaS"
        })
        self.assertEqual(
            len(content.sections),
            1
        )

    def test_that_filtering_isnt_cumulative(self):
        ContentLoader._read_yaml_file = MonkeyPatch({
          "manifest.yml": """
              -
                name: First section
                questions:
                  - firstQuestion
              -
                name: Second section
                questions:
                  - secondQuestion
          """,
          "folder/firstQuestion.yml": """
                question: 'First question'
                depends:
                    -
                      "on": lot
                      being: IaaS
          """,
          "folder/secondQuestion.yml": """
                question: 'Second question'
                depends:
                    -
                      "on": lot
                      being: PaaS

          """
        }).read_yaml_file
        content = ContentLoader(
            "manifest.yml",
            "folder/"
        )

        content.filter({
            "lot": "IaaS"
        })
        self.assertEqual(
            len(content.sections),
            1
        )

        content.filter({
            "lot": "PaaS"
        })
        self.assertEqual(
            len(content.sections),
            1
        )

        content.filter({
            "lot": "SCS"
        })
        self.assertEqual(
            len(content.sections),
            0
        )
