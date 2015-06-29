import yaml
import inflection
import re
import os


class ContentBuilder(object):
    def __init__(self, sections):
        self.sections = list(sections)

    def __iter__(self):
        return self.sections.__iter__()

    def get_section(self, requested_section):
        for section in self.sections:
            if section["id"] == requested_section:
                return section
        return None

    def get_next_section_id(self, section_id=None, only_editable=False):
        previous_section_is_current = section_id is None

        for section in self.sections:
            if only_editable:
                if (
                    previous_section_is_current and
                    "editable" in section and
                    section["editable"]
                ):
                    return section["id"]
            else:
                if previous_section_is_current:
                    return section["id"]

            if section["id"] == section_id:
                previous_section_is_current = True

        return None

    def get_next_editable_section_id(self, section_id=None):
        return self.get_next_section_id(section_id, True)

    def filter(self, service_data):
        sections = filter(None, [
            self._get_section_filtered_by(section, service_data)
            for section in self.sections
        ])

        return ContentBuilder(sections)

    def _get_section_filtered_by(self, section, service_data):
        section = section.copy()

        filtered_questions = [
            question for question in section["questions"]
            if self._question_should_be_shown(
                question.get("depends"), service_data
            )
        ]

        if len(filtered_questions):
            section["questions"] = filtered_questions
            return section
        else:
            return None

    def _question_should_be_shown(self, dependencies, service_data):
        if dependencies is None:
            return True
        for depends in dependencies:
            if not depends["on"] in service_data:
                return False
            if not service_data[depends["on"]] in depends["being"]:
                return False
        return True


class ContentLoader(object):
    def __init__(self, manifest, content_directory):
        manifest_sections = read_yaml(manifest)

        self._questions = {
            q: _load_question(q, content_directory)
            for section in manifest_sections
            for q in section["questions"]
        }

        self._sections = [
            self._populate_section(s) for s in manifest_sections
        ]

    def get_question(self, question):
        return self._questions.get(question, {}).copy()

    def get_builder(self):
        return ContentBuilder(self._sections)

    def _populate_section(self, section):
        section["id"] = _make_section_id(section["name"])
        section["questions"] = [
            self.get_question(q) for q in section["questions"]
        ]

        return section


def _load_question(question, directory):
    question_content = read_yaml(
        directory + question + ".yml"
    )
    question_content["id"] = _make_question_id(question)

    return question_content


def _make_section_id(name):
    return inflection.underscore(
        re.sub("\s", "_", name)
    )


def _make_question_id(question):
    if re.match('^serviceTypes(SCS|SaaS|PaaS|IaaS)', question):
        return 'serviceTypes'
    return question


def read_yaml(yaml_file):
    if not os.path.isfile(yaml_file):
        return {}
    with open(yaml_file, "r") as file:
        return yaml.load(file)
