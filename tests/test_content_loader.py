# coding=utf-8

import unittest
import mock

import os
import tempfile
import yaml
import io

from dmutils.content_loader import ContentLoader, ContentBuilder, read_yaml

from sys import version_info
if version_info.major == 2:
    import __builtin__ as builtins
else:
    import builtins


class TestContentBuilder(unittest.TestCase):
    def test_content_builder_init(self):
        content = ContentBuilder([])

        self.assertEqual(content.sections, [])

    def test_content_builder_init_copies_section_list(self):
        sections = []
        content = ContentBuilder(sections)

        sections.append('new')
        self.assertEqual(content.sections, [])

    def test_a_question_with_a_dependency(self):
        content = ContentBuilder([{
            "name": "First section",
            "questions": [{
                "question": 'First question',
                "depends": [{
                    "on": "lot",
                    "being": ["SCS"]
                }]
            }]
        }]).filter({"lot": "SCS"})

        self.assertEqual(len(content.sections), 1)

    def test_missing_depends_key_filter(self):
        content = ContentBuilder([{
            "name": "First section",
            "questions": [{
                "question": 'First question',
                "depends": [{
                    "on": "lot",
                    "being": ["SCS"]
                }]
            }]
        }]).filter({})

        self.assertEqual(len(content.sections), 0)

    def test_question_without_dependencies(self):
        content = ContentBuilder([{
            "name": "First section",
            "questions": [{
                "question": 'First question',
            }]
        }]).filter({'lot': 'SaaS'})

        self.assertEqual(len(content.sections), 1)

    def test_a_question_with_a_dependency_that_doesnt_match(self):
        content = ContentBuilder([{
            "name": "First section",
            "questions": [{
                "question": 'First question',
                "depends": [{
                    "on": "lot",
                    "being": ["SCS"]
                }]
            }]
        }]).filter({"lot": "SaaS"})

        self.assertEqual(len(content.sections), 0)

    def test_a_question_which_depends_on_one_of_several_answers(self):
        content = ContentBuilder([{
            "name": "First section",
            "questions": [{
                "question": 'First question',
                "depends": [{
                    "on": "lot",
                    "being": ["SCS", "SaaS", "PaaS"]
                }]
            }]
        }])

        self.assertEqual(len(content.filter({"lot": "SaaS"}).sections), 1)
        self.assertEqual(len(content.filter({"lot": "PaaS"}).sections), 1)
        self.assertEqual(len(content.filter({"lot": "SCS"}).sections), 1)

    def test_a_question_which_shouldnt_be_shown(self):
        content = ContentBuilder([{
            "name": "First section",
            "questions": [{
                "question": 'First question',
                "depends": [{
                    "on": "lot",
                    "being": ["SCS", "SaaS", "PaaS"]
                }]
            }]
        }])

        self.assertEqual(len(content.filter({"lot": "IaaS"}).sections), 0)

    def test_a_section_which_has_a_mixture_of_dependencies(self):
        content = ContentBuilder([{
            "name": "First section",
            "questions": [
                {
                    "question": 'First question',
                    "depends": [{
                        "on": "lot",
                        "being": ["SCS", "SaaS", "PaaS"]
                    }]
                },
                {
                    "question": 'Second question',
                    "depends": [{
                        "on": "lot",
                        "being": ["IaaS"]
                    }]
                },
            ]
        }]).filter({"lot": "IaaS"})

        self.assertEqual(len(content.sections), 1)

    def test_section_modification(self):
        content = ContentBuilder([{
            "name": "First section",
            "questions": [
                {
                    "question": 'First question',
                    "depends": [{
                        "on": "lot",
                        "being": ["SCS", "SaaS", "PaaS"]
                    }]
                },
                {
                    "question": 'Second question',
                    "depends": [{
                        "on": "lot",
                        "being": ["IaaS"]
                    }]
                },
            ]
        }])

        content2 = content.filter({"lot": "IaaS"})

        self.assertEqual(len(content.sections[0]["questions"]), 2)
        self.assertEqual(len(content2.sections[0]["questions"]), 1)

    def test_that_filtering_is_cumulative(self):
        content = ContentBuilder([{
            "name": "First section",
            "questions": [
                {
                    "question": 'First question',
                    "depends": [{
                        "on": "lot",
                        "being": ["SCS", "SaaS", "PaaS"]
                    }]
                },
                {
                    "question": 'Second question',
                    "depends": [{
                        "on": "lot",
                        "being": ["SCS", "IaaS"]
                    }]
                },
                {
                    "question": 'Third question',
                    "depends": [{
                        "on": "lot",
                        "being": ["SaaS", "IaaS"]
                    }]
                },
            ]
        }])

        content = content.filter({"lot": "SCS"})
        self.assertEqual(len(content.sections[0]["questions"]), 2)

        content = content.filter({"lot": "IaaS"})
        self.assertEqual(len(content.sections[0]["questions"]), 1)

        content = content.filter({"lot": "PaaS"})
        self.assertEqual(len(content.sections), 0)

    def test_get_section(self):
        content = ContentBuilder([{
            "id": "first_section",
            "name": "First section",
            "questions": [
                {
                    "question": 'First question',
                    "depends": [{
                        "on": "lot",
                        "being": ["SCS", "SaaS", "PaaS"]
                    }]
                }
            ]
        }])

        self.assertEqual(
            content.get_section("first_section").get("id"),
            "first_section"
        )

        content = content.filter({"lot": "IaaS"})
        self.assertEqual(
            content.get_section("first_section"),
            None
        )

    def test_get_next_section(self):
        content = ContentBuilder([
            {
                "id": "first_section",
                "name": "First section",
                "questions": [{
                    "question": 'First question',
                    "depends": [{
                        "on": "lot",
                        "being": ["SCS", "SaaS", "PaaS"]
                    }]
                }]
            },
            {
                "id": "second_section",
                "name": "Second section",
                "questions": [{
                    "question": 'First question',
                    "depends": [{
                        "on": "lot",
                        "being": ["SCS", "SaaS", "PaaS"]
                    }]
                }]
            },
            {
                "id": "third_section",
                "name": "Third section",
                "editable": True,
                "questions": [{
                    "question": 'First question',
                    "depends": [{
                        "on": "lot",
                        "being": ["SCS", "SaaS", "PaaS"]
                    }]
                }]
            },
        ])

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


class TestReadYaml(unittest.TestCase):

    @mock.patch('os.path.isfile', return_value=True)
    @mock.patch.object(builtins, 'open', return_value=io.StringIO(u'foo: bar'))
    def test_loading_existant_file(self, mocked_is_file, mocked_open):
        self.assertEqual(
            read_yaml('anything.yml'),
            {'foo': 'bar'}
        )

    @mock.patch('os.path.isfile', return_value=False)
    def test_file_not_found(self, mocked_is_file):
        self.assertEqual(
            read_yaml('something.yml'),
            {}
        )


@mock.patch('dmutils.content_loader.read_yaml')
class TestContentLoader(unittest.TestCase):

    def set_read_yaml_mock_response(self, read_yaml_mock):
        read_yaml_mock.side_effect = [
            [
                {"name": "section1", "questions": ["question1", "question2"]},
            ],
            {"name": "question1", "depends": [{"on": "lot", "being": "SaaS"}]},
            {"name": "question2", "depends": [{"on": "lot", "being": "SaaS"}]}
        ]

    def test_question_loading(self, read_yaml_mock):
        self.set_read_yaml_mock_response(read_yaml_mock)

        yaml_loader = ContentLoader('anything.yml', 'content/')

        self.assertEqual(
            yaml_loader._questions,
            {
                'question1': {'depends': [{'being': 'SaaS', 'on': 'lot'}],
                              'name': 'question1', 'id': 'question1'},
                'question2': {'depends': [{'being': 'SaaS', 'on': 'lot'}],
                              'name': 'question2', 'id': 'question2'}
            }
        )

        self.assertEqual(
            yaml_loader._sections,
            [
                {'name': 'section1',
                 'questions': [
                     {'depends': [{'being': 'SaaS', 'on': 'lot'}],
                      'name': 'question1', 'id': 'question1'},
                     {'depends': [{'being': 'SaaS', 'on': 'lot'}],
                      'name': 'question2', 'id': 'question2'}],
                 'id': 'section1'}
            ]
        )

    def test_get_question(self, read_yaml_mock):
        self.set_read_yaml_mock_response(read_yaml_mock)

        yaml_loader = ContentLoader('anything.yml', 'content/')

        self.assertEqual(
            yaml_loader.get_question('question1'),
            {'depends': [{'being': 'SaaS', 'on': 'lot'}],
             'name': 'question1', 'id': 'question1'},
        )

    def test_get_missing_question(self, read_yaml_mock):
        self.set_read_yaml_mock_response(read_yaml_mock)

        yaml_loader = ContentLoader('anything.yml', 'content/')

        self.assertEqual(
            yaml_loader.get_question('question111'),
            {}
        )

    def test_get_question_returns_a_copy(self, read_yaml_mock):
        self.set_read_yaml_mock_response(read_yaml_mock)

        yaml_loader = ContentLoader('anything.yml', 'content/')

        q1 = yaml_loader.get_question('question1')
        q1["id"] = "modified"
        q1["depends"] = []

        self.assertNotEqual(
            yaml_loader.get_question('question1'),
            q1
        )

    def test_get_builder(self, read_yaml_mock):
        self.set_read_yaml_mock_response(read_yaml_mock)

        yaml_loader = ContentLoader('anything.yml', 'content/')

        self.assertIsInstance(
            yaml_loader.get_builder(),
            ContentBuilder
        )

        self.assertEqual(
            yaml_loader.get_builder().sections,
            yaml_loader._sections
        )

    def test_multple_builders(self, read_yaml_mock):
        self.set_read_yaml_mock_response(read_yaml_mock)

        yaml_loader = ContentLoader('anything.yml', 'content/')

        builder1 = yaml_loader.get_builder()
        builder2 = yaml_loader.get_builder()

        self.assertNotEqual(builder1, builder2)
