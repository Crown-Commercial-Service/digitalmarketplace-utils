# coding=utf-8

import unittest
import mock

import os
import tempfile
import yaml

from dmutils.content_loader import ContentLoader


def get_mocked_yaml_reader(mocked_content={}):
    def read(yaml_file):
        return yaml.load(mocked_content[yaml_file])
    return read


@mock.patch("dmutils.content_loader.ContentLoader._yaml_file_exists")
@mock.patch("dmutils.content_loader.ContentLoader._read_yaml_file")
class TestContentLoader(unittest.TestCase):

    def test_a_simple_question(
        self, mocked_read_yaml_file, mocked_yaml_file_exists
    ):
        mocked_read_yaml_file.side_effect = get_mocked_yaml_reader({
            "manifest.yml": """
                -
                  name: First section
                  questions:
                    - firstQuestion
            """,
            "folder/firstQuestion.yml": """
                question: 'First question'
            """
        })
        content = ContentLoader(
            "manifest.yml",
            "folder/"
        )
        self.assertEqual(
            content.get_question("firstQuestion").get("question"),
            "First question"
        )

    def test_a_question_with_a_dependency(
        self, mocked_read_yaml_file, mocked_yaml_file_exists
    ):
        mocked_read_yaml_file.side_effect = get_mocked_yaml_reader({
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
        })
        content = ContentLoader(
            "manifest.yml",
            "folder/"
        )
        sections = content.get_sections_filtered_by({
            "lot": "SCS"
        })
        self.assertEqual(
            len(sections),
            1
        )

    def test_a_question_with_a_dependency_that_doesnt_match(
        self, mocked_read_yaml_file, mocked_yaml_file_exists
    ):
        mocked_read_yaml_file.side_effect = get_mocked_yaml_reader({
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
        })
        content = ContentLoader(
            "manifest.yml",
            "folder/"
        )
        sections = content.get_sections_filtered_by({
            "lot": "SaaS"
        })
        self.assertEqual(
            len(sections),
            0
        )

    def test_a_question_which_depends_on_one_of_several_answers(
        self, mocked_read_yaml_file, mocked_yaml_file_exists
    ):
        mocked_read_yaml_file.side_effect = get_mocked_yaml_reader({
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
        })
        content = ContentLoader(
            "manifest.yml",
            "folder/"
        )
        sections = content.get_sections_filtered_by({
            "lot": "SaaS"
        })
        self.assertEqual(
            len(sections),
            1
        )

    def test_a_question_which_depends_on_one_of_several_answers(
        self, mocked_read_yaml_file, mocked_yaml_file_exists
    ):
        mocked_read_yaml_file.side_effect = get_mocked_yaml_reader({
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
        })
        content = ContentLoader(
            "manifest.yml",
            "folder/"
        )
        sections = content.get_sections_filtered_by({
            "lot": "IaaS"
        })
        self.assertEqual(
            len(sections),
            0
        )

    def test_a_section_which_has_a_mixture_of_dependencies(
        self, mocked_read_yaml_file, mocked_yaml_file_exists
    ):
        mocked_read_yaml_file.side_effect = get_mocked_yaml_reader({
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
        })
        content = ContentLoader(
            "manifest.yml",
            "folder/"
        )
        sections = content.get_sections_filtered_by({
            "lot": "IaaS"
        })
        self.assertEqual(
            len(sections),
            1
        )

    def test_that_filtering_isnt_cumulative(
        self, mocked_read_yaml_file, mocked_yaml_file_exists
    ):
        mocked_read_yaml_file.side_effect = get_mocked_yaml_reader({
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
        })
        content = ContentLoader(
            "manifest.yml",
            "folder/"
        )

        sections = content.get_sections_filtered_by({
            "lot": "IaaS"
        })
        self.assertEqual(
            len(sections),
            1
        )

        sections = content.get_sections_filtered_by({
            "lot": "PaaS"
        })
        self.assertEqual(
            len(sections),
            1
        )

        sections = content.get_sections_filtered_by({
            "lot": "SCS"
        })
        self.assertEqual(
            len(sections),
            0
        )

    def test_get_next_section(
        self, mocked_read_yaml_file, mocked_yaml_file_exists
    ):
        mocked_read_yaml_file.side_effect = get_mocked_yaml_reader({
            "manifest.yml": """
              -
                name: First section
                questions:
                  - firstQuestion
              -
                name: Second section
                questions:
                  - firstQuestion
              -
                name: Third section
                questions:
                  - firstQuestion
            """,
            "folder/firstQuestion.yml": "question: 'First question'"
        })

        content = ContentLoader(
            "manifest.yml",
            "folder/"
        )

        sections = content.sections

        self.assertEqual(
            content.get_next_section_id("first_section", sections),
            "second_section"
        )

        self.assertEqual(
            content.get_next_section_id("second_section", sections),
            "third_section"
        )

        self.assertEqual(
            content.get_next_section_id("third_section", sections),
            None
        )
