# coding=utf-8

import unittest
import mock

import os
import tempfile
import yaml

from dmutils.content_loader import ContentLoader


class MockedYamlFiles:
    def __init__(self, mocked_content=""):
        self.mocked_content = mocked_content

    def read(self, yaml_file):
        return yaml.load(self.mocked_content[yaml_file])


class TestContentLoader(unittest.TestCase):

    def setUp(self):
        ContentLoader._yaml_file_exists = mock.patch(
            "ContentLoader._yaml_file_exists",
            return_value=True
        )

    @mock.patch("dmutils.content_loader.ContentLoader._read_yaml_file")
    def test_a_simple_question(self, mocked_read_yaml_file):
        mocked_read_yaml_file.side_effect = MockedYamlFiles({
            "manifest.yml": """
                -
                  name: First section
                  questions:
                    - firstQuestion
            """,
            "folder/firstQuestion.yml": """
                question: 'First question'
            """
        }).read

        content = ContentLoader(
            "manifest.yml",
            "folder/"
        )
        self.assertEqual(
            content.get_question("firstQuestion").get("question"),
            "First question"
        )

    @mock.patch("dmutils.content_loader.ContentLoader._read_yaml_file")
    def test_a_question_with_a_dependency(self, mocked_read_yaml_file):
        mocked_read_yaml_file.side_effect = MockedYamlFiles({
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
        }).read
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

    @mock.patch("dmutils.content_loader.ContentLoader._read_yaml_file")
    def test_a_question_with_a_dependency_that_doesnt_match(
        self, mocked_read_yaml_file
    ):
        mocked_read_yaml_file.side_effect = MockedYamlFiles({
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
        }).read
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

    @mock.patch("dmutils.content_loader.ContentLoader._read_yaml_file")
    def ftest_a_question_which_depends_on_one_of_several_answers(
        self, mocked_read_yaml_file
    ):
        mocked_read_yaml_file.side_effect = MockedYamlFiles({
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
        }).read
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

    @mock.patch("dmutils.content_loader.ContentLoader._read_yaml_file")
    def test_a_question_which_depends_on_one_of_several_answers(
        self, mocked_read_yaml_file
    ):
        mocked_read_yaml_file.side_effect = MockedYamlFiles({
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
        }).read
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

    @mock.patch("dmutils.content_loader.ContentLoader._read_yaml_file")
    def test_a_section_which_has_a_mixture_of_dependencies(
        self, mocked_read_yaml_file
    ):
        mocked_read_yaml_file.side_effect = MockedYamlFiles({
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
        }).read
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

    @mock.patch("dmutils.content_loader.ContentLoader._read_yaml_file")
    def test_that_filtering_isnt_cumulative(
        self, mocked_read_yaml_file
    ):
        mocked_read_yaml_file.side_effect = MockedYamlFiles({
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
        }).read
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
