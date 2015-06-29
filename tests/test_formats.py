
from dmutils.formats import get_label_for_lot_param, lot_to_lot_case
import pytest


class TestFormats(object):

    def test_returns_lot_in_lot_case(self):

        cases = [
            ("saas", "SaaS"),
            ("iaas", "IaaS"),
            ("paas", "PaaS"),
            ("scs", "SCS"),
            ("dewdew", None),
        ]

        for example, expected in cases:
            assert lot_to_lot_case(example) == expected

    def test_returns_label_for_lot(self):

        cases = [
            ("saas", "Software as a Service"),
            ("iaas", "Infrastructure as a Service"),
            ("paas", "Platform as a Service"),
            ("scs", "Specialist Cloud Services"),
            ("dewdew", None),
        ]

        for example, expected in cases:
            assert get_label_for_lot_param(example) == expected
