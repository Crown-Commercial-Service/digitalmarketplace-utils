# coding=utf-8

import mock
from werkzeug.datastructures import ImmutableOrderedMultiDict, OrderedMultiDict
import pytest

import io

from dmutils.content_loader import (
    ContentLoader, ContentSection, ContentQuestion, ContentManifest,
    read_yaml, ContentNotFoundError, QuestionNotFoundError, _make_slug
)

try:
    import builtins
except ImportError:
    import __builtin__ as builtins


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

        assert [s.id for s in content] == [1, 2, 3]

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

    def test_summary(self):
        content = ContentManifest([{
            "slug": "first_section",
            "name": "First section",
            "questions": [
                {
                    "id": "q1",
                    "question": 'First question',
                    "questions": [
                        {"id": "q2", "type": "text"},
                        {"id": "q3", "type": "text"}
                    ]
                },
                {"id": "q4", "type": "text", "optional": True},
                {"id": "q5", "type": "text", "optional": False},
                {"id": "q6", "type": "text", "optional": False},
                {
                    "id": "q7",
                    "type": "pricing",
                    "fields": {
                        "minimum_price": "q7.min",
                        "maximum_price": "q7.max",
                        "price_unit": "q7.unit",
                    },
                    "optional_fields": [
                        "maximum_price"
                    ]
                },
                {
                    "id": "q8",
                    "type": "pricing",
                    "fields": {
                        "minimum_price": "q8.min",
                        "maximum_price": "q8.max",
                    },
                    "optional_fields": [
                        "maximum_price"
                    ]
                },
                {
                    "id": "q9",
                    "question": 'Never required question',
                    "optional": True,
                    "questions": [
                        {"id": "q71", "type": "text"},
                        {"id": "q72", "type": "text"}
                    ]
                },
                {
                    "id": "q10",
                    "question": 'Are you sure you are assured?',
                    'type': 'boolean',
                    "optional": False,
                    'assuranceApproach': '2answers-type1',
                }
            ]
        }])

        summary = content.summary({
            'q2': 'some value',
            'q6': 'another value',
            'q7.min': '10',
            'q7.unit': 'day',
            'q10': {'value': True, 'assurance': 'Service provider assertion'},
            'q11': {'value': True}
        })

        assert summary.get_question('q1').value == [
            summary.get_question('q2')
        ]
        assert summary.get_question('q1').answer_required
        assert summary.get_question('q2').value == 'some value'
        assert not summary.get_question('q2').answer_required
        assert summary.get_question('q3').answer_required
        assert summary.get_question('q4').value == ''
        assert not summary.get_question('q4').answer_required
        assert summary.get_question('q4').assurance == ''  # question without assurance returns an empty string
        assert summary.get_question('q5').answer_required
        assert not summary.get_question('q6').answer_required
        assert summary.get_question('q7').value == u'£10 per day'
        assert not summary.get_question('q7').answer_required
        assert summary.get_question('q8').answer_required
        assert not summary.get_question('q9').answer_required
        assert summary.get_question('q10').value is True
        assert summary.get_question('q10').assurance == 'Service provider assertion'

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

    def test_get_question_by_slug(self):
        content = ContentManifest([
            {
                "slug": "first_section",
                "name": "First section",
                "questions": [{
                    "id": "q1",
                    "type": "multiquestion",
                    "question": 'Section one question',
                    "slug": "section-one-question",
                    "questions": [{"id": "sec1One"}, {"id": "sec1Two"}],
                    "depends": [{
                        "on": "lot",
                        "being": ["digital-specialists"]
                    }]
                }]
            },
            {
                "slug": "second_section",
                "name": "Second section",
                "questions": [{
                    "id": "q2",
                    "type": "multiquestion",
                    "question": 'Section two question',
                    "slug": "section-two-question",
                    "questions": [{"id": "sec2One"}, {"id": "sec2Two"}],
                    "depends": [{
                        "on": "lot",
                        "being": ["digital-specialists"]
                    }]
                }]
            }
        ])

        assert content.get_question_by_slug('section-two-question').get('id') == 'q2'

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

        form = ImmutableOrderedMultiDict([
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
    def setup_for_boolean_list_tests(self):
        section = {
            "slug": "first_section",
            "name": "First section",
            "questions": [{
                "id": "q0",
                "question": "Boolean list question",
                "type": "boolean_list",
            }]
        }

        brief = {
            "briefs": {
                "id": "0",
                "q0": [
                    "Can you do Sketch, Photoshop, Illustrator, and InDesign?",
                    "Can you can communicate like a boss?",
                    "Can you write clean and semantic HTML, CSS and Javascript?",
                    "Can you fight injustice full time?"
                ]
            }
        }

        form = OrderedMultiDict([
            ('q0-0', 'true'),
            ('q0-1', 'true'),
            ('q0-2', 'true'),
            ('q0-3', 'true')
        ])

        return section, brief, form

    def test_has_summary_page_if_multiple_questions(self):
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
        assert section.has_summary_page is True

    def test_has_no_summary_page_if_single_question_no_description(self):
        section = ContentSection.create({
            "slug": "first_section",
            "name": "First section",
            "questions": [{
                "id": "q1",
                "question": "Boolean question",
                "type": "boolean",
            }]
        })
        assert section.has_summary_page is False

    def test_has_summary_page_if_single_question_with_description(self):
        section = ContentSection.create({
            "slug": "first_section",
            "name": "First section",
            "description": "Section about a single topic",
            "questions": [{
                "id": "q1",
                "question": "Boolean question",
                "type": "boolean",
            }]
        })
        assert section.has_summary_page is True

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

    def test_get_multiquestion_ids(self):
        section = ContentSection.create({
            "slug": "first_section",
            "name": "First section",
            "questions": [{
                "id": "q0",
                "question": "Boolean question",
                "type": "Boolean question",
                "questions": [
                    {
                        "id": "q2",
                        "type": "text"
                    },
                    {
                        "id": "q3",
                        "type": "text"
                    }
                ]
            }]
        })
        assert section.get_question_ids() == ['q2', 'q3']

    def test_get_question_as_section(self):
        section = ContentSection.create({
            "slug": "first_section",
            "edit_questions": False,
            "name": "First section",
            "questions": [{
                "id": "q0",
                "slug": "q0-slug",
                "question": "Q0",
                "type": "multiquestion",
                "hint": "Some description",
                "questions": [
                    {
                        "id": "q2",
                        "type": "text"
                    },
                    {
                        "id": "q3",
                        "type": "text"
                    }
                ]
            }]
        })

        question_section = section.get_question_as_section('q0-slug')
        assert question_section.name == "Q0"
        assert question_section.description == "Some description"
        assert question_section.editable == section.edit_questions
        assert question_section.get_question_ids() == ['q2', 'q3']

    def test_get_question_as_section_missing_question(self):
        section = ContentSection.create({
            "slug": "first_section",
            "name": "First section",
            "questions": [{
                "id": "q0",
                "question": "Q0",
            }]
        })

        question_section = section.get_question_as_section('q0-slug')
        assert question_section is None

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
                "id": "q0",
                "questions": [
                    {"id": "q01", "type": "text"},
                    {"id": "q02", "type": "radios"}
                ]
            }, {
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
                "question": "Boolean list question",
                "type": "boolean_list",
            }, {
                "id": "q6",
                "question": "Checkboxes question",
                "type": "checkboxes",
            }, {
                "id": "q7",
                "question": "Service ID question",
                "type": "service_id",
                "assuranceApproach": "2answers-type1",
            }, {
                "id": "q8",
                "question": "Pricing question",
                "type": "pricing",
                "fields": {
                    "minimum_price": "q8-min_price",
                    "maximum_price": "q8-max_price",
                    "price_unit": "q8-price_unit",
                    "price_interval": "q8-price_interval"
                }
            }, {
                "id": "q9",
                "question": "Upload question",
                "type": "upload",
            }, {
                "id": "q10",
                "question": "number question",
                "type": "number",
            }, {
                "id": "q101",
                "question": "zero number question",
                "type": "number",
            }, {
                "id": "q11",
                "question": "Large text question",
                "type": "textbox_large",
            }, {
                "id": "q12",
                "question": "Text question",
                "type": "text"
            }, {
                "id": "q13",
                "question": "Text question",
                "type": "text"
            }]
        })

        form = ImmutableOrderedMultiDict([
            ('q1', 'true'),
            ('q01', 'some nested question'),
            ('q2', 'Some text stuff'),
            ('q3', 'value'),
            ('q3', 'Should be lost'),
            ('q4', 'value 1'),
            ('q4', 'value 2'),
            ('q5-0', 'true'),
            ('q5-1', 'false'),
            ('q5-4', 'true'),
            ('q5-not-valid', 'true'),
            ('q6', 'check 1'),
            ('q6', 'check 2'),
            ('q7', '71234567890'),
            ('q7--assurance', 'yes I am'),
            ('q8-min_price', '12.12'),
            ('q8-max_price', ''),
            ('q8-price_unit', 'Unit'),
            ('q8-price_interval', 'Hour'),
            ('q9', 'blah blah'),
            ('q10', '12.12'),
            ('q101', '0'),
            ('q11', 'Looooooooaaaaaaaaads of text'),
            ('extra_field', 'Should be lost'),
            ('q13', ''),
        ])

        data = section.get_data(form)

        assert data == {
            'q01': 'some nested question',
            'q1': True,
            'q2': 'Some text stuff',
            'q3': 'value',
            'q4': ['value 1', 'value 2'],
            'q5': [True, False, None, None, True],
            'q6': ['check 1', 'check 2'],
            'q7': {'assurance': 'yes I am', 'value': '71234567890'},
            'q8-min_price': '12.12',
            'q8-max_price': None,
            'q8-price_unit': 'Unit',
            'q8-price_interval': 'Hour',
            'q10': 12.12,
            'q101': 0,
            'q11': 'Looooooooaaaaaaaaads of text',
            'q13': None,
        }

        # Failure modes
        form = ImmutableOrderedMultiDict([
            ('q1', 'not boolean')
        ])
        assert section.get_data(form)['q1'] == 'not boolean'

        form = ImmutableOrderedMultiDict([
            ('q1', 'false')
        ])
        assert section.get_data(form)['q1'] is False

        form = ImmutableOrderedMultiDict([
            ('q10', 'not a number')
        ])
        assert section.get_data(form)['q10'] == 'not a number'

        # Test 'orphaned' assurance is returned
        form = ImmutableOrderedMultiDict([
            ('q7--assurance', 'yes I am'),
        ])
        data = section.get_data(form)
        assert data == {
            'q4': None,
            'q6': None,
            'q7': {'assurance': 'yes I am'},
        }

        # Test empty lists are not converted to `None`
        form = ImmutableOrderedMultiDict([
            ('q4', '')
        ])
        assert section.get_data(form)['q4'] == ['']

        # if we have one empty value
        form = ImmutableOrderedMultiDict([
            ('q5-0', '')
        ])
        assert section.get_data(form)['q5'] == ['']

        # if we have a value without an index number, we ignore it
        form = ImmutableOrderedMultiDict([
            ('q5', 'true'),
            ('q5-', 'true')
        ])
        assert 'q5' not in section.get_data(form)

    def test_unformat_data(self):
        section = ContentSection.create({
            "slug": "first_section",
            "name": "First section",
            "questions": [{
                "id": "q0",
                "questions": [
                    {"id": "q01", "type": "text"},
                    {"id": "q02", "type": "radios"}
                ]
            }, {
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
                "question": "Boolean list question",
                "type": "boolean_list",
            }, {
                "id": "q6",
                "question": "Checkboxes question",
                "type": "checkboxes",
            }, {
                "id": "q7",
                "question": "Service ID question",
                "type": "service_id",
                "assuranceApproach": "2answers-type1",
            }, {
                "id": "q8",
                "question": "Pricing question",
                "type": "pricing",
                "fields": {
                    "minimim_price": "q8-min",
                    "maximum_price": "q8-min",
                    "price_unit": "q8-unit",
                    "price_interval": "q8-interval"
                }
            }, {
                "id": "q9",
                "question": "Upload question",
                "type": "upload",
            }, {
                "id": "q10",
                "question": "number question",
                "type": "number",
            }, {
                "id": "q11",
                "question": "Large text question",
                "type": "textbox_large",
            }, {
                "id": "q12",
                "question": "Text question",
                "type": "text"
            }]
        })

        data = {
            'q01': 'q01 value',
            'q1': True,
            'q2': 'Some text stuff',
            'q3': 'value',
            'q4': ['value 1', 'value 2'],
            'q5': [True, False],
            'q6': ['check 1', 'check 2'],
            'q7': {'assurance': 'yes I am', 'value': '71234567890'},
            'q8-min': '12.12',
            'q8-max': '13.13',
            'q8-unit': 'Unit',
            'q8-interval': 'Hour',
            'q10': 12.12,
            'q11': 'Looooooooaaaaaaaaads of text',
        }

        form = section.unformat_data(data)

        assert form == {
            'q01': 'q01 value',
            'q1': True,
            'q2': 'Some text stuff',
            'q3': 'value',
            'q4': ['value 1', 'value 2'],
            'q5': [True, False],
            'q6': ['check 1', 'check 2'],
            'q7': '71234567890',
            'q7--assurance': 'yes I am',
            'q8-min': '12.12',
            'q8-max': '13.13',
            'q8-unit': 'Unit',
            'q8-interval': 'Hour',
            'q10': 12.12,
            'q11': 'Looooooooaaaaaaaaads of text',
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

    def test_get_field_names_with_incomplete_pricing_question(self):
        section = ContentSection.create({
            "slug": "first_section",
            "name": "First section",
            "questions": [{
                "id": "q1",
                "question": "First question",
                "type": "pricing",
            }]
        })
        with pytest.raises(AssertionError):
            section.get_field_names()

    def test_get_field_names_with_good_pricing_question(self):
        section = ContentSection.create({
            "slug": "first_section",
            "name": "First section",
            "questions": [{
                "id": "q1",
                "question": "First question",
                "type": "pricing",
                "fields": {
                    "minimum_price": "q1-minprice",
                    "maximum_price": "q1-maxprice"
                }
            }]
        })

        # using sets because sort order -TM
        expected = set(['q1-minprice', 'q1-maxprice'])
        assert set(section.get_field_names()) == expected

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

        expected = "This is the error message"
        assert section.get_question('q2').get_error_message('the_error') == expected

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

        expected = "There was a problem with the answer to this question"
        assert section.get_question('q2').get_error_message('other_error') == expected

    def test_get_error_messages(self):
        section = ContentSection.create({
            "slug": "second_section",
            "name": "Second section",
            "questions": [{
                "id": "q2",
                "question": "Second question",
                "name": "second",
                "type": "text",
                "validations": [
                    {'name': 'the_error', 'message': 'This is the error message'},
                ],
            }, {
                "id": "serviceTypes",
                "question": "Third question",
                "type": "text",
                "validations": [
                    {'name': 'the_error', 'message': 'This is the error message'},
                ],
            }, {
                "id": "priceString",
                "question": "Price question",
                "type": "pricing",
                "fields": {
                    "minimum_price": "priceString-min"
                },
                "validations": [
                    {
                        "name": "answer_required",
                        "field": "priceString-min",
                        "message": "No min price"
                    },
                ]
            }, {
                "id": "q3",
                "question": "With assurance",
                "type": "text",
                "validations": [
                    {"name": "assurance_required", "message": "There there, it'll be ok."},
                ]
            }, {
                "id": "q4",
                "question": "No Errors",
                "type": "text"
            }]
        })

        errors = {
            "q2": "the_error",
            "q3": "assurance_required",
            "serviceTypes": "the_error",
            "priceString-min": "answer_required",
        }

        result = section.get_error_messages(errors)

        assert result['priceString']['message'] == "No min price"
        assert result['q2']['message'] == "This is the error message"
        assert result['q2']['question'] == "second"
        assert result['q3--assurance']['message'] == "There there, it'll be ok."
        assert result['serviceTypes']['message'] == "This is the error message"

        assert result["priceString"]["input_name"] == "priceString"

        assert list(result.keys()) == ["q2", "serviceTypes", "priceString", "q3--assurance"]

    def test_get_error_messages_with_unknown_error_key(self):
        section = ContentSection.create({
            "slug": "second_section",
            "name": "Second section",
            "questions": []
        })
        errors = {
            "q1": "the_error"
        }

        with pytest.raises(QuestionNotFoundError):
            section.get_error_messages(errors)

    def test_get_error_messages_for_boolean_list_one_question_missing(self):

        section, brief, form_data = self.setup_for_boolean_list_tests()
        form_data.pop('q0-3')
        errors = {"q0": "boolean_list_error"}

        section = ContentSection.create(section)
        section.inject_brief_questions_into_boolean_list_question(brief['briefs'])
        response_data = section.get_data(form_data)
        section_summary = section.summary(response_data)
        error_messages = section_summary.get_error_messages(errors)

        assert error_messages['q0'] is True
        for error_key in ['q0-3']:
            assert error_key in error_messages
            base_error_key, index = error_key.split('-')[0], int(error_key.split('-')[-1])
            assert brief['briefs'][base_error_key][index] == error_messages[error_key]['question']

    def test_get_error_messages_for_boolean_list_all_questions_missing(self):

        section, brief, form_data = self.setup_for_boolean_list_tests()
        form_data.pop('q0-0')
        form_data.pop('q0-1')
        form_data.pop('q0-2')
        form_data.pop('q0-3')
        errors = {"q0": "boolean_list_error"}

        section = ContentSection.create(section)
        section.inject_brief_questions_into_boolean_list_question(brief['briefs'])
        response_data = section.get_data(form_data)
        section_summary = section.summary(response_data)
        error_messages = section_summary.get_error_messages(errors)

        assert error_messages['q0'] is True
        for error_key in ['q0-0', 'q0-1', 'q0-2', 'q0-3']:
            assert error_key in error_messages
            base_error_key, index = error_key.split('-')[0], int(error_key.split('-')[-1])
            assert brief['briefs'][base_error_key][index] == error_messages[error_key]['question']

    def test_get_error_messages_no_boolean_list_questions_missing(self):

        section, brief, form_data = self.setup_for_boolean_list_tests()
        section['questions'].append({
            "id": "q1",
            "question": "Text question",
            "type": "text"
        })
        errors = {"q1": "text_error"}

        section = ContentSection.create(section)
        section.inject_brief_questions_into_boolean_list_question(brief['briefs'])
        response_data = section.get_data(form_data)
        section_summary = section.summary(response_data)
        error_messages = section_summary.get_error_messages(errors)

        assert 'q1' in error_messages
        for error_key in ['q0', 'q0-0', 'q0-1', 'q0-2', 'q0-3']:
            assert error_key not in error_messages

    def test_cannot_get_boolean_list_error_messages_without_section_summary(self):

        section, brief, form_data = self.setup_for_boolean_list_tests()
        form_data.pop('q0-3')
        errors = {"q0": "boolean_list_error"}

        section = ContentSection.create(section)
        section.inject_brief_questions_into_boolean_list_question(brief['briefs'])
        error_messages = section.get_error_messages(errors)

        assert 'q0' in error_messages
        assert 'q0-3' not in error_messages
        assert len(error_messages.keys()) == 1

    def test_get_wrong_boolean_list_error_messages_without_brief_questions_injected(self):

        section, brief, form_data = self.setup_for_boolean_list_tests()
        form_data.pop('q0-3')
        errors = {"q0": "boolean_list_error"}

        section = ContentSection.create(section)
        response_data = section.get_data(form_data)
        section_summary = section.summary(response_data)
        error_messages = section_summary.get_error_messages(errors)

        assert 'q0' in error_messages
        assert 'q0-3' not in error_messages
        assert len(error_messages.keys()) == 1

    def test_get_wrong_boolean_list_error_messages_without_response_data(self):

        section, brief, form_data = self.setup_for_boolean_list_tests()
        form_data.pop('q0-3')
        errors = {"q0": "boolean_list_error"}

        section = ContentSection.create(section)
        section.inject_brief_questions_into_boolean_list_question(brief['briefs'])
        section_summary = section.summary({})
        error_messages = section_summary.get_error_messages(errors)

        # when an error key exists but no response data, all questions are assumed empty
        for error_key in ['q0', 'q0-0', 'q0-1', 'q0-2', 'q0-3']:
            assert error_key in error_messages

    def test_section_description(self):
        section = ContentSection.create({
            "slug": "first_section",
            "name": "First section",
            "questions": [],
            "description": "This is the first section",
            "summary_page_description": "This is a summary of the first section"
        })
        assert section.description == "This is the first section"
        assert section.summary_page_description == "This is a summary of the first section"

        copy_of_section = section.copy()
        assert copy_of_section.description == "This is the first section"
        assert copy_of_section.summary_page_description == "This is a summary of the first section"

    def test_section_step(self):
        section = ContentSection.create({
            "slug": "first_section",
            "name": "First section",
            "questions": [],
            "step": 1
        })
        assert section.step == 1

        copy_of_section = section.copy()
        assert copy_of_section.step == 1

    def test_inject_messages_into_section(self):

        section, brief, form_data = self.setup_for_boolean_list_tests()

        section = ContentSection.create(section)
        section.inject_brief_questions_into_boolean_list_question(brief['briefs'])
        assert section.get_question('q0').get('boolean_list_questions') == brief['briefs']['q0']

    def test_inject_messages_into_section_optional_question_missing(self):

        section, brief, form_data = self.setup_for_boolean_list_tests()
        # add an optional boolean list question
        section['questions'].append({
            "id": "q1",
            "question": "Optional boolean list question",
            "type": "boolean_list",
            "optional": True
        })

        section = ContentSection.create(section)
        section.inject_brief_questions_into_boolean_list_question(brief['briefs'])
        assert section.get_question('q0').get('boolean_list_questions') == brief['briefs']['q0']

    def test_inject_messages_into_section_non_optional_question_missing(self):

        section, brief, form_data = self.setup_for_boolean_list_tests()
        # add an optional boolean list question
        brief['briefs'].pop("q0")

        section = ContentSection.create(section)
        with pytest.raises(ContentNotFoundError):
            section.inject_brief_questions_into_boolean_list_question(brief['briefs'])

    def test_inject_messages_into_section_and_section_summary(self):

        section, brief, form_data = self.setup_for_boolean_list_tests()
        section['questions'].append({
            "id": "q1",
            "question": "Text question",
            "type": "text"
        })
        form_data['q1'] = 'Some text stuff'

        section = ContentSection.create(section)
        section.inject_brief_questions_into_boolean_list_question(brief['briefs'])
        response_data = section.get_data(form_data)
        section_summary = section.summary(response_data)
        assert section_summary.get_question('q0').value == [True, True, True, True]
        assert section_summary.get_question('q0').get('boolean_list_questions') == brief['briefs']['q0']

        assert section_summary.get_question('q1').value == 'Some text stuff'
        assert section_summary.get_question('q1').get('boolean_list_questions') is None


class TestContentQuestion(object):
    def test_form_fields_property(self):
        question = ContentQuestion({
            "id": "example",
            "type": "text"
        })
        assert question.form_fields == ['example']

    def test_form_fields_property_with_pricing_field(self):
        question = ContentQuestion({
            "id": "example",
            "type": "pricing",
            "fields": {
                "minimum_price": "priceMin",
                "maximum_price": "priceMax",
            }
        })
        assert sorted(question.form_fields) == sorted(['priceMin', 'priceMax'])

    def test_form_fields_property_with_multiquestion(self):
        question = ContentQuestion({
            "id": "example",
            "type": "multiquestion",
            "questions": [
                {
                    "id": "example2",
                    "type": "text",
                },
                {
                    "id": "example3",
                    "type": "text",
                }
            ]
        })
        assert question.form_fields == ['example2', 'example3']

    def test_required_form_fields_property(self):
        question = ContentQuestion({
            "id": "example",
            "type": "pricing",
            "fields": {
                "minimum_price": "priceMin",
                "maximum_price": "priceMax",
            }
        })
        assert sorted(question.required_form_fields) == sorted(['priceMin', 'priceMax'])

    def test_required_form_fields_property_when_optional(self):
        question = ContentQuestion({
            "id": "example",
            "type": "pricing",
            "optional": True,
            "fields": {
                "minimum_price": "priceMin",
                "maximum_price": "priceMax",
            }
        })
        assert question.required_form_fields == []

    def test_required_form_fields_property_with_optional_fields(self):
        question = ContentQuestion({
            "id": "example",
            "type": "pricing",
            "fields": {
                "minimum_price": "priceMin",
                "maximum_price": "priceMax",
            },
            "optional_fields": [
                "minimum_price"
            ]
        })
        assert question.required_form_fields == ['priceMax']

    def test_required_form_fields_with_multiquestion(self):
        question = ContentQuestion({
            "id": "example",
            "type": "multiquestion",
            "questions": [
                {
                    "id": "example2",
                    "type": "text",
                    "optional": False,
                },
                {
                    "id": "example3",
                    "type": "text",
                    "optional": True,
                }
            ]
        })
        assert question.required_form_fields == ['example2']


class TestContentQuestionSummary(object):
    def test_question_value_with_no_options(self):
        question = ContentQuestion({
            "id": "example",
            "type": "text",
        }).summary({'example': 'value1'})

        assert question.value == 'value1'

    def test_question_value_returns_matching_option_label(self):
        question = ContentQuestion({
            "id": "example",
            "type": "checkboxes",
            "options": [
                {"label": "Wrong label", "value": "value"},
                {"label": "Option label", "value": "value1"},
                {"label": "Wrong label", "value": "value11"},
            ]
        }).summary({'example': 'value1'})

        assert question.value == 'Option label'


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
        return {"id": "q2", "name": "question2", "depends": [{"on": "lot", "being": "SaaS"}]}

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
                     'name': 'question2', 'id': 'q2'}],
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

    def test_get_question_uses_id_if_available(self, read_yaml_mock):
        read_yaml_mock.return_value = self.question2()

        yaml_loader = ContentLoader("content/")

        assert yaml_loader.get_question('framework-slug', 'question-set', 'question2') == {
            'depends': [{'being': 'SaaS', 'on': 'lot'}],
            'name': 'question2', 'id': 'q2'
        }
        read_yaml_mock.assert_called_with(
            'content/frameworks/framework-slug/questions/question-set/question2.yml')

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

    def test_get_message_with_no_key(self, mock_read_yaml):
        mock_read_yaml.return_value = {
            'field_one': 'value_one',
            'field_two': 'value_two',
        }
        messages = ContentLoader('content/')
        messages.load_messages('g-cloud-7', ['index'])

        assert messages.get_message('g-cloud-7', 'index') == {
            'field_one': 'value_one',
            'field_two': 'value_two',
        }
        assert messages.get_message('g-cloud-7', 'index', 'field_one') == 'value_one'

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

    def test_get_manifest(self, read_yaml_mock):
        self.set_read_yaml_mock_response(read_yaml_mock)

        yaml_loader = ContentLoader('content/')
        yaml_loader.load_manifest('framework-slug', 'question-set', 'manifest')

        builder = yaml_loader.get_manifest('framework-slug', 'manifest')
        assert isinstance(builder, ContentManifest)

        assert [
            section.id for section in builder.sections
        ] == ['section1']

    def test_multple_builders(self, read_yaml_mock):
        self.set_read_yaml_mock_response(read_yaml_mock)

        yaml_loader = ContentLoader('content/')
        yaml_loader.load_manifest('framework-slug', 'question-set', 'manifest')

        builder1 = yaml_loader.get_manifest('framework-slug', 'manifest')
        builder2 = yaml_loader.get_manifest('framework-slug', 'manifest')

        assert builder1 != builder2

    def test_get_manifest_fails_if_manifest_has_not_been_loaded(self, read_yaml_mock):
        with pytest.raises(ContentNotFoundError):
            yaml_loader = ContentLoader('content/')
            yaml_loader.get_manifest('framework-slug', 'manifest')


@pytest.mark.parametrize("title,slug", [
    ("The Title", "the-title"),
    ("This\nAnd\tThat ", "this-and-that"),
    ("This&That?", "this-that"),
])
def test_make_slug(title, slug):
    assert _make_slug(title) == slug
