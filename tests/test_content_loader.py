# coding=utf-8

import unittest
import mock

import os
import tempfile
import yaml
import io

from dmutils.content_loader import YAMLLoader, ContentBuilder

from sys import version_info
if version_info.major == 2:
    import __builtin__ as builtins
else:
    import builtins


def get_mocked_yaml_reader(mocked_content={}):
    def read(yaml_file):
        return yaml.load(mocked_content[yaml_file])
    return read


@mock.patch("dmutils.content_loader.YAMLLoader.read")
class TestContentBuilder(unittest.TestCase):

    def test_a_simple_question(self, mocked_read_yaml_file):
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
        content = ContentBuilder(
            "manifest.yml",
            "folder/",
            YAMLLoader()
        )
        self.assertEqual(
            content.get_question("firstQuestion").get("question"),
            "First question"
        )
        self.assertEqual(
            content.get_question("firstQuestion").get("id"),
            "firstQuestion"
        )

    def test_a_question_with_a_dependency(self, mocked_read_yaml_file):
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
        content = ContentBuilder(
            "manifest.yml",
            "folder/",
            YAMLLoader()
        )
        content.filter({
            "lot": "SCS"
        })
        self.assertEqual(
            len(content.sections),
            1
        )

    def test_a_question_with_a_dependency_that_doesnt_match(
        self, mocked_read_yaml_file
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
        content = ContentBuilder(
            "manifest.yml",
            "folder/",
            YAMLLoader()
        )
        content.filter({
            "lot": "SaaS"
        })
        self.assertEqual(
            len(content.sections),
            0
        )

    def test_a_question_which_depends_on_one_of_several_answers(
        self, mocked_read_yaml_file
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
        content = ContentBuilder(
            "manifest.yml",
            "folder/",
            YAMLLoader()
        )
        content.filter({
            "lot": "SaaS"
        })
        self.assertEqual(
            len(content.sections),
            1
        )

    def test_a_question_which_shouldnt_be_shown(
        self, mocked_read_yaml_file
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
        content = ContentBuilder(
            "manifest.yml",
            "folder/",
            YAMLLoader()
        )
        content.filter({
            "lot": "IaaS"
        })
        self.assertEqual(
            len(content.sections),
            0
        )

    def test_a_section_which_has_a_mixture_of_dependencies(
        self, mocked_read_yaml_file
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
        content = ContentBuilder(
            "manifest.yml",
            "folder/",
            YAMLLoader()
        )
        content.filter({
            "lot": "IaaS"
        })
        self.assertEqual(
            len(content.sections),
            1
        )

    def test_that_filtering_isnt_cumulative(self, mocked_read_yaml_file):
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
        content = ContentBuilder(
            "manifest.yml",
            "folder/",
            YAMLLoader()
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

    def test_get_section(self, mocked_read_yaml_file):
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
        content = ContentBuilder(
            "manifest.yml",
            "folder/",
            YAMLLoader()
        )

        content.filter({
            "lot": "IaaS"
        })
        self.assertEqual(
            content.get_section("first_section").get("id"),
            "first_section"
        )

        content.filter({
            "lot": "SCS"
        })
        self.assertEqual(
            content.get_section("first_section"),
            None
        )

    def test_get_next_section(self, mocked_read_yaml_file):
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
                editable: True
                questions:
                  - firstQuestion
            """,
            "folder/firstQuestion.yml": "question: 'First question'"
        })

        content = ContentBuilder(
            "manifest.yml",
            "folder/",
            YAMLLoader()
        )

        sections = content.sections

        self.assertEqual(
            content.get_next_section_id(),
            "first_section"
        )
        self.assertEqual(
            content.get_next_section_id("first_section"),
            "second_section"
        )
        self.assertEqual(
            content.get_next_section_id("second_section"),
            "third_section"
        )
        self.assertEqual(
            content.get_next_section_id("third_section"),
            None
        )

        self.assertEqual(
            content.get_next_editable_section_id(),
            "third_section"
        )
        self.assertEqual(
            content.get_next_editable_section_id("second_section"),
            "third_section"
        )


class TestYAMLLoader(unittest.TestCase):

    @mock.patch('os.path.isfile', return_value=True)
    @mock.patch.object(builtins, 'open', return_value=io.StringIO(u'foo: bar'))
    def test_loading_existant_file(self, mocked_is_file, mocked_open):
        yaml_loader = YAMLLoader()
        self.assertEqual(
            yaml_loader.read('anything.yml'),
            {'foo': 'bar'}
        )

    @mock.patch('os.path.isfile', return_value=True)
    @mock.patch.object(builtins, 'open', return_value=io.StringIO(u'foo: bar'))
    def test_caching(self, mocked_open, mocked_is_file):
        yaml_loader = YAMLLoader()
        self.assertEqual(
            yaml_loader.read('something.yml'),
            {'foo': 'bar'}
        )
        self.assertEqual(
            yaml_loader.read('something.yml'),
            {'foo': 'bar'}
        )
        mocked_open.assert_called_once_with('something.yml', 'r')
        self.assertEqual(len(yaml_loader._cache), 1)

    @mock.patch('os.path.isfile', return_value=False)
    def test_file_not_found(self, mocked_is_file):
        yaml_loader = YAMLLoader()
        self.assertEqual(
            yaml_loader.read('something.yml'),
            {}
        )


@mock.patch('os.path.isfile', return_value=True)
class TestInCombination(unittest.TestCase):

    @mock.patch.object(builtins, 'open', side_effect=[
        io.StringIO(u"""
          -
            name: First section
            questions:
              - firstQuestion
              - secondQuestion
        """),
        io.StringIO(u"""
          question: 'First question'
          depends:
              -
                "on": lot
                being: IaaS
        """),
        io.StringIO(u"""
          question: 'Second question'
          depends:
              -
                "on": lot
                being: SaaS
        """)
    ])
    def test_that_filtering_doesnt_remove_original_objects(
        self, mocked_open, mocked_is_file
    ):
        content = ContentBuilder(
            "manifest.yml",
            "folder/",
            YAMLLoader()
        )
        self.assertEqual(
            len(content.sections[0]['questions']),
            2
        )
        content.filter({"lot": "SaaS"})
        self.assertEqual(
            len(content.sections[0]['questions']),
            1
        )
        content.filter({"lot": "IaaS"})
        self.assertEqual(
            len(content.sections[0]['questions']),
            1
        )

    @mock.patch.object(builtins, 'open', side_effect=[
        io.StringIO(u"""
          -
            name: First section
            questions:
              - firstQuestion
          -
            name: Second section
            questions:
              - secondQuestion
        """),
        io.StringIO(u"""
          question: 'First question'
          depends:
              -
                "on": lot
                being: IaaS
        """),
        io.StringIO(u"""
          question: 'Second question'
          depends:
              -
                "on": lot
                being: PaaS
        """)
    ])
    def test_sharing_of_yaml_loader(self, mocked_open, mocked_is_file):

        yaml_loader = YAMLLoader()

        will_only_have_iaas_questions = ContentBuilder(
            "manifest.yml",
            "folder/",
            yaml_loader
        )
        will_only_have_paas_questions = ContentBuilder(
            "manifest.yml",
            "folder/",
            yaml_loader
        )
        will_only_have_iaas_questions.filter({
            "lot": "IaaS"
        })
        will_only_have_paas_questions.filter({
            "lot": "PaaS"
        })

        self.assertEqual(
            len(will_only_have_iaas_questions.sections),
            1
        )
        self.assertEqual(
            len(will_only_have_paas_questions.sections),
            1
        )
