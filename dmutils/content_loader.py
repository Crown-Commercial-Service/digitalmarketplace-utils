import yaml
import inflection
import re
import os


class ContentBuilder(object):

    def __init__(self, manifest, content_directory, yaml_loader):
        self.yaml_loader = yaml_loader
        section_order = yaml_loader.read(manifest)
        self._directory = content_directory

        self._all_sections = [
            self._populate_section(s) for s in section_order
        ]

        self.sections = self._all_sections

    def get_section(self, requested_section):
        for section in self._all_sections:
            if section["id"] == requested_section:
                return section
        return None

    def get_question(self, question):
        return self.yaml_loader.read(self._directory + question + ".yml")

    def filter(self, service_data):
        self.sections = [
            section for section in [
                self._get_section_filtered_by(section["id"], service_data)
                for section in self._all_sections
            ] if section is not None
        ]

    def get_next_section_id(self, section_id):

        previous_section_is_current = False

        for section in self.sections:
            if previous_section_is_current:
                return section["id"]
            if section["id"] == section_id:
                previous_section_is_current = True

        return None

    def _get_section_filtered_by(self, section_id, service_data):

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


class YAMLLoader(object):

    def __init__(self):
        self._cache = {}

    def read(self, yaml_file):
        if yaml_file not in self._cache:
            if not os.path.isfile(yaml_file):
                return None
            with open(yaml_file, "r") as file:
                self._cache[yaml_file] = yaml.load(file)
        return self._cache[yaml_file]
