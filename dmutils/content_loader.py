import yaml
import inflection
import re
import os


class ContentLoader(object):

    def __init__(self, manifest, content_directory):

        section_order = self._read_yaml_file(manifest)

        self._directory = content_directory
        self._question_cache = {}
        self.sections = [
            self._populate_section(s) for s in section_order
        ]

    def get_section(self, requested_section):

        for section in self.sections:
            if section["id"] == requested_section:
                return section

    def get_question(self, question):

        if question not in self._question_cache:

            question_file = self._directory + question + ".yml"

            if not self._yaml_file_exists(question_file):
                self._question_cache[question] = {}
                return {}

            question_content = self._read_yaml_file(question_file)
            question_content["id"] = question
            self._question_cache[question] = question_content

        return self._question_cache[question]

    def get_sections_filtered_by(self, service_data):
        return [
            section for section in [
                self.get_section_filtered_by(section["id"], service_data)
                for section in self.sections
            ] if section is not None
        ]

    def get_section_filtered_by(self, section_id, service_data):

        section = self.get_section(section_id)

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

    def get_next_section_id(self, section_id, sections):

        previous_section_is_current = False

        for section in sections:
            if previous_section_is_current:
                return section["id"]
            if section["id"] == section_id:
                previous_section_is_current = True

        return None

    def _yaml_file_exists(self, yaml_file):
        return os.path.isfile(yaml_file)

    def _read_yaml_file(self, yaml_file):
        with open(yaml_file, "r") as file:
            question_content = yaml.load(file)
            return question_content

    def _populate_section(self, section):
        section["questions"] = [
            self.get_question(q) for q in section["questions"]
        ]
        section["id"] = self._make_id(section["name"])
        return section

    def _make_id(self, name):
        return inflection.underscore(
            re.sub("\s", "_", name)
        )

    def _question_should_be_shown(self, dependencies, service_data):
        if dependencies is None:
            return True
        for depends in dependencies:
            if not depends["on"] in service_data:
                return False
            if not service_data[depends["on"]] in depends["being"]:
                return False
        return True
