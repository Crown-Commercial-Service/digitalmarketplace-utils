import yaml
import inflection
import re
import os


class ContentLoader(object):

    def __init__(self, manifest, content_directory):

        section_order = self._read_yaml_file(manifest)

        self._directory = content_directory
        self._question_cache = {}
        self._all_sections = [
            self.__populate_section__(s) for s in section_order
        ]
        self.sections = self._all_sections

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

    def filter(self, service_data):

        self.sections = self._all_sections
        filtered_sections = []

        for section in self.sections:
            filtered_questions = []
            for question in section["questions"]:
                if self._question_should_be_shown(
                    question.get("depends"), service_data
                ):
                    filtered_questions.append(question)
            if len(filtered_questions):
                section["questions"] = filtered_questions
                filtered_sections.append(section)

        self.sections = filtered_sections

    def _yaml_file_exists(self, yaml_file):
        return os.path.isfile(yaml_file)

    def _read_yaml_file(self, yaml_file):
        with open(yaml_file, "r") as file:
            question_content = yaml.load(file)
            return question_content

    def __populate_section__(self, section):
        section["questions"] = [
            self.get_question(q) for q in section["questions"]
        ]
        section["id"] = self.__make_id__(section["name"])
        return section

    def __make_id__(self, name):
        return inflection.underscore(
            re.sub("\s", "_", name)
        )

    def _question_should_be_shown(self, dependencies, service_data):
        for depends in dependencies:
            if not service_data[depends["on"]] in depends["being"]:
                return False
        return True
