# coding=utf-8

import mock
from werkzeug.datastructures import ImmutableMultiDict
import pytest

import io

from dmutils.content_loader import ContentLoader, ContentSection, ContentManifest, read_yaml, ContentNotFoundError

from sys import version_info
if version_info.major == 2:
    import __builtin__ as builtins
else:
    import builtins


class TestContentManifest(object):
    def test_content_builder_init(self):
        content = ContentManifest([])

        assert content.sections == []

    def test_content_builder_init_copies_section_list(self):
        sections = []
        content = ContentManifest(sections)

        sections.append('new')
        assert content.sections == []

    def test_content_builder_iteration(self):
        def section(id):
            return {
                'slug': id,
                'name': 'name',
                'questions': []
            }

        content = ContentManifest([section(1), section(2), section(3)])

        assert [section.id for section in content] == [1, 2, 3]

    def test_a_question_with_a_dependency(self):
        content = ContentManifest([{
            "slug": "first_section",
            "name": "First section",
            "questions": [{
                "id": "q1",
                "question": 'First question',
                "depends": [{
                    "on": "lot",
                    "being": ["SCS"]
                }]
            }]
        }]).filter({"lot": "SCS"})

        assert len(content.sections) == 1

    def test_missing_depends_key_filter(self):
        content = ContentManifest([{
            "slug": "first_section",
            "name": "First section",
            "questions": [{
                "id": "q1",
                "question": 'First question',
                "depends": [{
                    "on": "lot",
                    "being": ["SCS"]
                }]
            }]
        }]).filter({})

        assert len(content.sections) == 0

    def test_question_without_dependencies(self):
        content = ContentManifest([{
            "slug": "first_section",
            "name": "First section",
            "questions": [{
                "id": "q1",
                "question": 'First question',
            }]
        }]).filter({'lot': 'SaaS'})

        assert len(content.sections) == 1

    def test_a_question_with_a_dependency_that_doesnt_match(self):
        content = ContentManifest([{
            "slug": "first_section",
            "name": "First section",
            "questions": [{
                "id": "q1",
                "question": 'First question',
                "depends": [{
                    "on": "lot",
                    "being": ["SCS"]
                }]
            }]
        }]).filter({"lot": "SaaS"})

        assert len(content.sections) == 0

    def test_a_question_which_depends_on_one_of_several_answers(self):
        content = ContentManifest([{
            "slug": "first_section",
            "name": "First section",
            "questions": [{
                "id": "q1",
                "question": 'First question',
                "depends": [{
                    "on": "lot",
                    "being": ["SCS", "SaaS", "PaaS"]
                }]
            }]
        }])

        assert len(content.filter({"lot": "SaaS"}).sections) == 1
        assert len(content.filter({"lot": "PaaS"}).sections) == 1
        assert len(content.filter({"lot": "SCS"}).sections) == 1

    def test_a_question_which_shouldnt_be_shown(self):
        content = ContentManifest([{
            "slug": "first_section",
            "name": "First section",
            "questions": [{
                "id": "q1",
                "question": 'First question',
                "depends": [{
                    "on": "lot",
                    "being": ["SCS", "SaaS", "PaaS"]
                }]
            }]
        }])

        assert len(content.filter({"lot": "IaaS"}).sections) == 0

    def test_a_section_which_has_a_mixture_of_dependencies(self):
        content = ContentManifest([{
            "slug": "first_section",
            "name": "First section",
            "questions": [
                {
                    "id": "q1",
                    "question": 'First question',
                    "depends": [{
                        "on": "lot",
                        "being": ["SCS", "SaaS", "PaaS"]
                    }]
                },
                {
                    "id": "q2",
                    "question": 'Second question',
                    "depends": [{
                        "on": "lot",
                        "being": ["IaaS"]
                    }]
                },
            ]
        }]).filter({"lot": "IaaS"})

        assert len(content.sections) == 1

    def test_section_modification(self):
        content = ContentManifest([{
            "slug": "first_section",
            "name": "First section",
            "questions": [
                {
                    "id": "q1",
                    "question": 'First question',
                    "depends": [{
                        "on": "lot",
                        "being": ["SCS", "SaaS", "PaaS"]
                    }]
                },
                {
                    "id": "q2",
                    "question": 'Second question',
                    "depends": [{
                        "on": "lot",
                        "being": ["IaaS"]
                    }]
                },
            ]
        }])

        content2 = content.filter({"lot": "IaaS"})

        assert len(content.sections[0]["questions"]) == 2
        assert len(content2.sections[0]["questions"]) == 1

    def test_that_filtering_is_cumulative(self):
        content = ContentManifest([{
            "slug": "first_section",
            "name": "First section",
            "questions": [
                {
                    "id": "q1",
                    "question": 'First question',
                    "depends": [{
                        "on": "lot",
                        "being": ["SCS", "SaaS", "PaaS"]
                    }]
                },
                {
                    "id": "q2",
                    "question": 'Second question',
                    "depends": [{
                        "on": "lot",
                        "being": ["SCS", "IaaS"]
                    }]
                },
                {
                    "id": "q3",
                    "question": 'Third question',
                    "depends": [{
                        "on": "lot",
                        "being": ["SaaS", "IaaS"]
                    }]
                },
            ]
        }])

        content = content.filter({"lot": "SCS"})
        assert len(content.sections[0]["questions"]) == 2

        content = content.filter({"lot": "IaaS"})
        assert len(content.sections[0]["questions"]) == 1

        content = content.filter({"lot": "PaaS"})
        assert len(content.sections) == 0

    def test_get_section(self):
        content = ContentManifest([{
            "slug": "first_section",
            "name": "First section",
            "questions": [
                {
                    "id": "q1",
                    "question": 'First question',
                    "depends": [{
                        "on": "lot",
                        "being": ["SCS", "SaaS", "PaaS"]
                    }]
                }
            ]
        }])

        assert content.get_section("first_section").id == "first_section"

        content = content.filter({"lot": "IaaS"})
        assert content.get_section("first_section") is None

    def test_get_question(self):
        content = ContentManifest([
            {
                "slug": "first_section",
                "name": "First section",
                "questions": [{
                    "id": "q1",
                    "question": 'First question',
                    "depends": [{
                        "on": "lot",
                        "being": ["SCS", "SaaS", "PaaS"]
                    }]
                }]
            },
            {
                "slug": "second_section",
                "name": "Second section",
                "questions": [{
                    "id": "q2",
                    "question": 'First question',
                    "depends": [{
                        "on": "lot",
                        "being": ["SCS", "SaaS", "PaaS"]
                    }]
                }]
            },
            {
                "slug": "third_section",
                "name": "Third section",
                "editable": True,
                "questions": [{
                    "id": "q3",
                    "question": 'First question',
                    "depends": [{
                        "on": "lot",
                        "being": ["SCS", "SaaS", "PaaS"]
                    }]
                }]
            },
        ])

        assert content.get_question('q1').get('id') == 'q1'

        content = content.filter({'lot': 'IaaS'})
        assert content.get_question('q1') is None

    def test_get_next_section(self):
        content = ContentManifest([
            {
                "slug": "first_section",
                "name": "First section",
                "questions": [{
                    "id": "q1",
                    "question": 'First question',
                    "depends": [{
                        "on": "lot",
                        "being": ["SCS", "SaaS", "PaaS"]
                    }]
                }]
            },
            {
                "slug": "second_section",
                "name": "Second section",
                "questions": [{
                    "id": "q2",
                    "question": 'First question',
                    "depends": [{
                        "on": "lot",
                        "being": ["SCS", "SaaS", "PaaS"]
                    }]
                }]
            },
            {
                "slug": "third_section",
                "name": "Third section",
                "editable": True,
                "questions": [{
                    "id": "q3",
                    "question": 'First question',
                    "depends": [{
                        "on": "lot",
                        "being": ["SCS", "SaaS", "PaaS"]
                    }]
                }]
            },
        ])

        assert content.get_next_section_id() == "first_section"
        assert content.get_next_section_id("first_section") == "second_section"
        assert content.get_next_section_id("second_section") == "third_section"
        assert content.get_next_section_id("third_section") is None

        assert content.get_next_editable_section_id() == "third_section"
        assert content.get_next_editable_section_id(
            "second_section") == "third_section"

    def test_get_all_data(self):
        content = ContentManifest([
            {
                "slug": "first_section",
                "name": "First section",
                "questions": [{
                    "id": "q1",
                    "question": "Question one",
                    "type": "text",
                }]
            },
            {
                "slug": "second_section",
                "name": "Second section",
                "questions": [{
                    "id": "q2",
                    "question": "Question two",
                    "type": "text",
                }]
            },
            {
                "slug": "third_section",
                "name": "Third section",
                "questions": [{
                    "id": "q3",
                    "question": "Question three",
                    "type": "text",
                }]
            }
        ])

        form = ImmutableMultiDict([
            ('q1', 'some text'),
            ('q2', 'other text'),
            ('q3', '  lots of      whitespace     \t\n'),
        ])

        data = content.get_all_data(form)

        assert data == {
            'q1': 'some text',
            'q2': 'other text',
            'q3': 'lots of      whitespace',
        }

    def test_question_numbering(self):
        content = ContentManifest([
            {
                "slug": "first_section",
                "name": "First section",
                "questions": [
                    {
                        "id": "q1",
                        "question": "Question one",
                        "type": "text",
                    },
                    {
                        "id": "q2",
                        "question": "Question one",
                        "type": "text",
                    }
                ]
            },
            {
                "slug": "second_section",
                "name": "Second section",
                "questions": [
                    {
                        "id": "q3",
                        "question": "Question three",
                        "type": "text",
                    }
                ]
            }
        ])

        assert content.get_question("q1")['number'] == 1
        assert content.get_question("q2")['number'] == 2
        assert content.get_question("q3")['number'] == 3

    def test_question_numbers_respect_filtering(self):
        content = ContentManifest([
            {
                "slug": "first_section",
                "name": "First section",
                "questions": [{
                    "id": "q1",
                    "question": 'First question',
                    "depends": [{
                        "on": "lot",
                        "being": ["SaaS"]
                    }]
                }]
            },
            {
                "slug": "second_section",
                "name": "Second section",
                "questions": [
                    {
                        "id": "q2",
                        "question": 'Second question',
                        "depends": [{
                            "on": "lot",
                            "being": ["SCS"]
                        }]
                    },
                    {
                        "id": "q3",
                        "question": 'Third question',
                        "depends": [{
                            "on": "lot",
                            "being": ["SCS"]
                        }]
                    },
                ]
            }
        ]).filter({"lot": "SCS"})

        assert content.sections[0].questions[0]['id'] == 'q2'
        assert content.get_question('q2')['number'] == 1
        assert content.sections[0].questions[0]['number'] == 1


class TestContentSection(object):
    def test_get_question_ids(self):
        section = ContentSection.create({
            "slug": "first_section",
            "name": "First section",
            "questions": [{
                "id": "q1",
                "question": "Boolean question",
                "type": "boolean",
            }, {
                "id": "q2",
                "question": "Text question",
                "type": "text",
            }]
        })
        assert section.get_question_ids() == ['q1', 'q2']

    def test_get_question_ids_filtered_by_type(self):
        section = ContentSection.create({
            "slug": "first_section",
            "name": "First section",
            "questions": [{
                "id": "q1",
                "question": "Boolean question",
                "type": "boolean",
            }, {
                "id": "q2",
                "question": "Text question",
                "type": "text",
            }]
        })
        assert section.get_question_ids('boolean') == ['q1']

    def test_get_data(self):
        section = ContentSection.create({
            "slug": "first_section",
            "name": "First section",
            "questions": [{
                "id": "q1",
                "question": "Boolean question",
                "type": "boolean",
            }, {
                "id": "q2",
                "question": "Text question",
                "type": "text",
            }, {
                "id": "q3",
                "question": "Radios question",
                "type": "radios",
            }, {
                "id": "q4",
                "question": "List question",
                "type": "list",
            }, {
                "id": "q5",
                "question": "Checkboxes question",
                "type": "checkboxes",
            }, {
                "id": "q6",
                "question": "Service ID question",
                "type": "service_id",
                "assuranceApproach": "2answers-type1",
            }, {
                "id": "q7",
                "question": "Pricing question",
                "type": "pricing",
            }, {
                "id": "q8",
                "question": "Upload question",
                "type": "upload",
            }, {
                "id": "q9",
                "question": "Percentage question",
                "type": "percentage",
            }, {
                "id": "q10",
                "question": "Large text question",
                "type": "textbox_large",
            }, {
                "id": "q11",
                "question": "Text question",
                "type": "text"
            }]
        })

        form = ImmutableMultiDict([
            ('q1', 'true'),
            ('q2', 'Some text stuff'),
            ('q3', 'value'),
            ('q3', 'Should be lost'),
            ('q4', 'value 1'),
            ('q4', 'value 2'),
            ('q5', 'check 1'),
            ('q5', 'check 2'),
            ('q6', '71234567890'),
            ('q6--assurance', 'yes I am'),
            ('q7', '12.12'),
            ('q7', '13.13'),
            ('q7', 'Unit'),
            ('q7', 'Hour'),
            ('q8', 'blah blah'),
            ('q9', '12.12'),
            ('q10', 'Looooooooaaaaaaaaads of text'),
            ('extra_field', 'Should be lost'),
            ('q12', 'Should be lost'),
        ])

        data = section.get_data(form)

        assert data == {
            'q1': True,
            'q2': 'Some text stuff',
            'q3': 'value',
            'q4': ['value 1', 'value 2'],
            'q5': ['check 1', 'check 2'],
            'q6': {'assurance': 'yes I am', 'value': '71234567890'},
            'priceMin': '12.12',
            'priceMax': '13.13',
            'priceUnit': 'Unit',
            'priceInterval': 'Hour',
            'q9': 12.12,
            'q10': 'Looooooooaaaaaaaaads of text',
        }

        # Failure modes
        form = ImmutableMultiDict([
            ('q1', 'not boolean')
        ])
        assert section.get_data(form)['q1'] == 'not boolean'

        form = ImmutableMultiDict([
            ('q9', 'not a number')
        ])
        assert section.get_data(form)['q9'] == 'not a number'

        with pytest.raises(ValueError):
            form = ImmutableMultiDict([
                ('q7', '12.12'),
            ])
            section.get_data(form)

        # Test 'orphaned' assurance is returned
        form = ImmutableMultiDict([
            ('q6--assurance', 'yes I am'),
        ])
        data = section.get_data(form)
        print("DATA: {}".format(data))
        assert data == {
            'q6': {'assurance': 'yes I am'},
        }

    def test_unformat_data(self):
        section = ContentSection.create({
            "slug": "first_section",
            "name": "First section",
            "questions": [{
                "id": "q1",
                "question": "Boolean question",
                "type": "boolean",
            }, {
                "id": "q2",
                "question": "Text question",
                "type": "text",
            }, {
                "id": "q3",
                "question": "Radios question",
                "type": "radios",
            }, {
                "id": "q4",
                "question": "List question",
                "type": "list",
            }, {
                "id": "q5",
                "question": "Checkboxes question",
                "type": "checkboxes",
            }, {
                "id": "q6",
                "question": "Service ID question",
                "type": "service_id",
                "assuranceApproach": "2answers-type1",
            }, {
                "id": "q7",
                "question": "Pricing question",
                "type": "pricing",
            }, {
                "id": "q8",
                "question": "Upload question",
                "type": "upload",
            }, {
                "id": "q9",
                "question": "Percentage question",
                "type": "percentage",
            }, {
                "id": "q10",
                "question": "Large text question",
                "type": "textbox_large",
            }, {
                "id": "q11",
                "question": "Text question",
                "type": "text"
            }]
        })

        data = {
            'q1': True,
            'q2': 'Some text stuff',
            'q3': 'value',
            'q4': ['value 1', 'value 2'],
            'q5': ['check 1', 'check 2'],
            'q6': {'assurance': 'yes I am', 'value': '71234567890'},
            'priceMin': '12.12',
            'priceMax': '13.13',
            'priceUnit': 'Unit',
            'priceInterval': 'Hour',
            'q9': 12.12,
            'q10': 'Looooooooaaaaaaaaads of text',
        }

        form = section.unformat_data(data)

        assert form == {
            'q1': True,
            'q2': 'Some text stuff',
            'q3': 'value',
            'q4': ['value 1', 'value 2'],
            'q5': ['check 1', 'check 2'],
            'q6': '71234567890',
            'q6--assurance': 'yes I am',
            'priceMin': '12.12',
            'priceMax': '13.13',
            'priceUnit': 'Unit',
            'priceInterval': 'Hour',
            'q9': 12.12,
            'q10': 'Looooooooaaaaaaaaads of text',
        }

    def test_get_question(self):
        section = ContentSection.create({
            "slug": "first_section",
            "name": "First section",
            "questions": [{
                "id": "q1",
                "question": 'First question',
                "depends": [{
                    "on": "lot",
                    "being": ["SCS", "SaaS", "PaaS"]
                }]
            }]
        })

        assert section.get_question('q1').get('id') == 'q1'

    def test_get_field_names_with_pricing_question(self):
        section = ContentSection.create({
            "slug": "first_section",
            "name": "First section",
            "questions": [{
                "id": "q1",
                "question": "First question",
                "type": "pricing"
            }]
        })

        assert section.get_field_names() == ['priceMin', 'priceMax', 'priceUnit', 'priceInterval']

    def test_get_field_names_with_no_pricing_question(self):
        section = ContentSection.create({
            "slug": "second_section",
            "name": "Second section",
            "questions": [{
                "id": "q2",
                "question": "Second question",
                "type": "text",
            }]
        })

        assert section.get_field_names() == ['q2']

    def test_has_changes_to_save_no_changes(self):
        section = ContentSection.create({
            "slug": "second_section",
            "name": "Second section",
            "questions": [{
                "id": "q2",
                "question": "Second question",
                "type": "text",
            }]
        })
        assert not section.has_changes_to_save({'q2': 'foo'}, {'q2': 'foo'})

    def test_hash_changes_to_save_field_different(self):
        section = ContentSection.create({
            "slug": "second_section",
            "name": "Second section",
            "questions": [{
                "id": "q2",
                "question": "Second question",
                "type": "text",
            }]
        })
        assert section.has_changes_to_save({'q2': 'foo'}, {'q2': 'blah'})

    def test_has_changes_to_save_field_not_set_on_service(self):
        section = ContentSection.create({
            "slug": "second_section",
            "name": "Second section",
            "questions": [{
                "id": "q2",
                "question": "Second question",
                "type": "text",
            }]
        })
        assert section.has_changes_to_save({}, {})

    def test_get_error_message(self):
        section = ContentSection.create({
            "slug": "second_section",
            "name": "Second section",
            "questions": [{
                "id": "q2",
                "question": "Second question",
                "type": "text",
                "validations": [
                    {'name': 'the_error', 'message': 'This is the error message'},
                ],
            }]
        })

        assert section.get_error_message('q2', 'the_error') == "This is the error message"

    def test_get_error_message_returns_default(self):
        section = ContentSection.create({
            "slug": "second_section",
            "name": "Second section",
            "questions": [{
                "id": "q2",
                "question": "Second question",
                "type": "text",
                "validations": [
                    {'name': 'the_error', 'message': 'This is the error message'},
                ],
            }]
        })

        assert section.get_error_message('q2', 'other_error') == "There was a problem with the answer to this question"

    def test_get_error_messages(self):
        section = ContentSection.create({
            "slug": "second_section",
            "name": "Second section",
            "questions": [{
                "id": "q2",
                "question": "Second question",
                "type": "text",
                "validations": [
                    {'name': 'the_error', 'message': 'This is the error message'},
                ],
            }, {
                "id": "serviceTypeSCS",
                "question": "Third question",
                "type": "text",
                "validations": [
                    {'name': 'the_error', 'message': 'This is the error message'},
                ],
            }, {
                "id": "priceString",
                "question": "Price question",
                "type": "price",
                "validations": [
                    {"name": "no_min_price_specified", "message": "No min price"},
                ]
            }, {
                "id": "q3",
                "question": "With assurance",
                "type": "text",
                "validations": [
                    {"name": "assurance_required", "message": "There there, it'll be ok."},
                ]
            }]
        })

        errors = {
            "q2": "the_error",
            "serviceTypes": "the_error",
            "priceMin": "answer_required",
            "q3": "assurance_required",
        }

        result = section.get_error_messages(errors, 'SCS')

        assert result['priceString']['message'] == "No min price"
        assert result['q2']['message'] == "This is the error message"
        assert result['q3--assurance']['message'] == "There there, it'll be ok."
        assert result['serviceTypeSCS']['message'] == "This is the error message"

    def test_section_description(self):
        section = ContentSection.create({
            "slug": "first_section",
            "name": "First section",
            "questions": [],
            "description": "This is the first section"
        })
        assert section.description == "This is the first section"

        copy_of_section = section.copy()
        assert copy_of_section.description == "This is the first section"


class TestReadYaml(object):
    @mock.patch.object(builtins, 'open', return_value=io.StringIO(u'foo: bar'))
    def test_loading_existant_file(self, mocked_open):
        assert read_yaml('anything.yml') == {'foo': 'bar'}

    @mock.patch.object(builtins, 'open', side_effect=IOError)
    def test_file_not_found(self, mocked_open):
        with pytest.raises(IOError):
            assert read_yaml('something.yml')


@mock.patch('dmutils.content_loader.read_yaml')
class TestContentLoader(object):
    def set_read_yaml_mock_response(self, read_yaml_mock):
        read_yaml_mock.side_effect = [
            self.manifest1(),
            self.question1(),
            self.question2(),
        ]

    def manifest1(self):
        return [{"name": "section1", "questions": ["question1", "question2"]}]

    def manifest2(self):
        return [{"name": "section1", "questions": ["question2", "question3"]}]

    def question1(self):
        return {"name": "question1", "depends": [{"on": "lot", "being": "SaaS"}]}

    def question2(self):
        return {"name": "question2", "depends": [{"on": "lot", "being": "SaaS"}]}

    def question3(self):
        return {"name": "question3", "depends": [{"on": "lot", "being": "SaaS"}]}

    def test_manifest_loading(self, read_yaml_mock):
        self.set_read_yaml_mock_response(read_yaml_mock)

        yaml_loader = ContentLoader('content/')

        sections = yaml_loader.load_manifest('framework-slug', 'question-set', 'my-manifest')

        assert sections == [
            {'name': 'section1',
                'questions': [
                    {'depends': [{'being': 'SaaS', 'on': 'lot'}],
                     'name': 'question1', 'id': 'question1'},
                    {'depends': [{'being': 'SaaS', 'on': 'lot'}],
                     'name': 'question2', 'id': 'question2'}],
                'slug': 'section1'}
        ]
        read_yaml_mock.assert_has_calls([
            mock.call('content/frameworks/framework-slug/manifests/my-manifest.yml'),
            mock.call('content/frameworks/framework-slug/questions/question-set/question1.yml'),
            mock.call('content/frameworks/framework-slug/questions/question-set/question2.yml'),
        ])

    def test_manifest_loading_fails_if_manifest_cannot_be_read(self, read_yaml_mock):
        read_yaml_mock.side_effect = IOError

        yaml_loader = ContentLoader('content/')

        with pytest.raises(ContentNotFoundError):
            yaml_loader.load_manifest('framework-slug', 'question-set', 'my-manifest')

    def test_manifest_loading_fails_if_question_cannot_be_read(self, read_yaml_mock):
        read_yaml_mock.side_effect = [
            self.manifest1(),
            IOError
        ]

        yaml_loader = ContentLoader('content')

        with pytest.raises(ContentNotFoundError):
            yaml_loader.load_manifest('framework-slug', 'question-set', 'my-manifest')

    def test_get_question(self, read_yaml_mock):
        read_yaml_mock.return_value = self.question1()

        yaml_loader = ContentLoader('content/')

        assert yaml_loader.get_question('framework-slug', 'question-set', 'question1') == {
            'depends': [{'being': 'SaaS', 'on': 'lot'}],
            'name': 'question1', 'id': 'question1'
        }
        read_yaml_mock.assert_called_with(
            'content/frameworks/framework-slug/questions/question-set/question1.yml')

    def test_get_question_loads_nested_questions(self, read_yaml_mock):
        read_yaml_mock.side_effect = [
            {"name": "question1", "type": "multiquestion", "questions": ["question10", "question20"]},
            {"name": "question10", "type": "text"},
            {"name": "question20", "type": "checkboxes"},
        ]

        yaml_loader = ContentLoader('content/')

        assert yaml_loader.get_question('framework-slug', 'question-set', 'question1')

        read_yaml_mock.assert_has_calls([
            mock.call('content/frameworks/framework-slug/questions/question-set/question1.yml'),
            mock.call('content/frameworks/framework-slug/questions/question-set/question10.yml'),
            mock.call('content/frameworks/framework-slug/questions/question-set/question20.yml'),
        ])

    def test_get_question_fails_if_question_cannot_be_read(self, read_yaml_mock):
        read_yaml_mock.side_effect = IOError

        yaml_loader = ContentLoader('content/')

        with pytest.raises(ContentNotFoundError):
            yaml_loader.get_question('framework-slug', 'question-set', 'question111')

    def test_get_same_question_id_from_same_question_set_only_loads_once(self, read_yaml_mock):
        read_yaml_mock.side_effect = [
            self.question1(),
        ]

        yaml_loader = ContentLoader('content/')
        yaml_loader.get_question('framework-slug', 'question-set-1', 'question1')
        yaml_loader.get_question('framework-slug', 'question-set-1', 'question1')

        read_yaml_mock.assert_has_calls([
            mock.call('content/frameworks/framework-slug/questions/question-set-1/question1.yml'),
        ])

    def test_get_same_question_id_from_different_question_sets(self, read_yaml_mock):
        read_yaml_mock.side_effect = [
            self.question1(),
            self.question1(),
        ]

        yaml_loader = ContentLoader('content/')
        yaml_loader.get_question('framework-slug', 'question-set-1', 'question1')
        yaml_loader.get_question('framework-slug', 'question-set-2', 'question1')

        read_yaml_mock.assert_has_calls([
            mock.call('content/frameworks/framework-slug/questions/question-set-1/question1.yml'),
            mock.call('content/frameworks/framework-slug/questions/question-set-2/question1.yml'),
        ])

    def test_get_question_returns_a_copy(self, read_yaml_mock):
        read_yaml_mock.return_value = self.question1()

        yaml_loader = ContentLoader('content/')

        q1 = yaml_loader.get_question('framework-slug', 'question-set', 'question1')
        q1["id"] = "modified"
        q1["depends"] = []

        assert yaml_loader.get_question('framework-slug', 'question-set', 'question1') != q1

    def test_message_key_format(self, mock_read_yaml):
        messages = ContentLoader('content/')

        assert messages._message_key(
            'coming', 'submitted'
        ) == 'coming-submitted'

        assert messages._message_key(
            'coming', None
        ) == 'coming'

        # frameworks must have a state
        with pytest.raises(TypeError):
            messages._message_key()

    def test_get_message(self, mock_read_yaml):

        mock_read_yaml.return_value = {
            'coming': {
                'heading': 'G-Cloud 7 is coming',
                'message': 'Get ready'
            }
        }
        messages = ContentLoader('content/')
        messages.load_messages('g-cloud-7', ['index'])

        assert messages.get_message('g-cloud-7', 'index', 'coming') == {
            'heading': 'G-Cloud 7 is coming',
            'message': 'Get ready'
        }
        mock_read_yaml.assert_called_with('content/frameworks/g-cloud-7/messages/index.yml')

    def test_load_message_argument_types(self, mock_read_yaml):

        mock_read_yaml.return_value = {}
        messages = ContentLoader('content/')

        with pytest.raises(TypeError):
            messages.load_messages('g-cloud-7', 'index')  # blocks argument must be a list

    def test_get_message_non_existant_state(self, mock_read_yaml):

        mock_read_yaml.return_value = {
            'coming': {
                'heading': 'G-Cloud 7 is coming',
                'message': 'This message won’t be looked for'
            }
        }
        messages = ContentLoader('content/')
        messages.load_messages('g-cloud-7', ['index'])

        assert messages.get_message('g-cloud-7', 'index', 'open') is None

    def test_get_message_with_supplier_status(self, mock_read_yaml):

        mock_read_yaml.return_value = {
            'open-registered_interest': {
                'heading': 'G-Cloud 8 is open',
                'message': 'You have registered interest'
            }
        }
        messages = ContentLoader('content/')
        messages.load_messages('g-cloud-8', ['index'])

        assert messages.get_message('g-cloud-8', 'index', 'open', 'registered_interest') == {
            'heading': 'G-Cloud 8 is open',
            'message': 'You have registered interest'
        }
        mock_read_yaml.assert_called_with('content/frameworks/g-cloud-8/messages/index.yml')

    def test_get_message_must_preload(self, mock_read_yaml):

        mock_read_yaml.return_value = {}
        messages = ContentLoader('content/')
        messages.load_messages('g-cloud-8', ['index'])

        with pytest.raises(ContentNotFoundError):
            messages.get_message('g-cloud-8', 'dashboard', 'open')
            mock_read_yaml.assert_not_called()

    def test_caching_of_messages(self, mock_read_yaml):

        messages = ContentLoader('content/')
        messages.load_messages('g-cloud-7', ['index'])
        messages.get_message('g-cloud-7', 'index', 'coming')
        messages.get_message('g-cloud-7', 'index', 'coming')

        mock_read_yaml.assert_called_once_with('content/frameworks/g-cloud-7/messages/index.yml')

    def test_load_message_raises(self, mock_read_yaml):

        mock_read_yaml.side_effect = IOError
        messages = ContentLoader('content/')

        with pytest.raises(ContentNotFoundError):
            messages.load_messages('not-a-framework', ['index'])

    def test_get_builder(self, read_yaml_mock):
        self.set_read_yaml_mock_response(read_yaml_mock)

        yaml_loader = ContentLoader('content/')
        yaml_loader.load_manifest('framework-slug', 'question-set', 'manifest')

        builder = yaml_loader.get_builder('framework-slug', 'manifest')
        assert isinstance(builder, ContentManifest)

        assert [
            section.id for section in builder.sections
        ] == ['section1']

    def test_multple_builders(self, read_yaml_mock):
        self.set_read_yaml_mock_response(read_yaml_mock)

        yaml_loader = ContentLoader('content/')
        yaml_loader.load_manifest('framework-slug', 'question-set', 'manifest')

        builder1 = yaml_loader.get_builder('framework-slug', 'manifest')
        builder2 = yaml_loader.get_builder('framework-slug', 'manifest')

        assert builder1 != builder2

    def test_get_builder_fails_if_manifest_has_not_been_loaded(self, read_yaml_mock):
        with pytest.raises(ContentNotFoundError):
            yaml_loader = ContentLoader('content/')
            yaml_loader.get_builder('framework-slug', 'manifest')
