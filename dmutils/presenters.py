import re


class Presenters(object):

    def __init__(self):
        return None

    def present(self, value, question_content):

        if question_content is None:
            return value

        if "type" in question_content:
            field_type = question_content["type"]
        else:
            return value

        if hasattr(self, "_" + field_type):
            return getattr(self, "_" + field_type)(value)
        else:
            return value

    def present_all(self, service_data, content):
        return {
            key: self.present(value, content.get_question(key))
            for key, value in service_data.items()
        }

    def _service_id(self, value):
        if re.findall("[a-zA-Z]", str(value)):
            return [value]
        else:
            return re.findall("....", str(value))

    def _upload(self, value):
        return {
            "url": value or "",
            "filename": value.split("/")[-1] or ""
        }

    def _boolean(self, value):
        if value is True:
            return "Yes"
        if value is False:
            return "No"
        return ""
