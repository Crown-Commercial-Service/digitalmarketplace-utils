import pytest

from datetime import datetime as dt
from dmutils import api_stubs


class TestLot:
    def test_default_values(self):
        assert api_stubs.lot() == {
            "id": 1,
            "slug": "some-lot",
            "name": "Some lot",
            "allowsBrief": False,
            "oneServiceLimit": False,
            "unitSingular": "service",
            "unitPlural": "services",
        }

    @pytest.mark.parametrize(
        ("kwarg", "key", "value"), (
            ("slug", "slug", "my-special-lot"),
            ("allows_brief", "allowsBrief", True),
            ("one_service_limit", "oneServiceLimit", True),
            ("unit_singular", "unitSingular", "brief"),
            ("unit_plural", "unitPlural", "briefs"),
        )
    )
    def test_returns_mapping_which_can_be_changed_using_kwargs(self, kwarg, key, value):
        assert key in api_stubs.lot()
        assert api_stubs.lot(**{kwarg: value})[key] == value


class TestFrameworkAgreementDetails:
    def test_default_values(self):
        assert api_stubs.framework_agreement_details() == {
            "contractNoticeNumber": "2010/ABC-DEF",
            "frameworkAgreementVersion": "RM1557x",
            "frameworkExtensionLength": "12 months",
            "frameworkRefDate": "29-06-2000",
            "frameworkURL": f"https://www.gov.uk/government/publications/g-cloud-7",
            "lotDescriptions": {},
            "lotOrder": [],
            "pageTotal": 99,
            "signaturePageNumber": 98,
            "variations": {}
        }

    @pytest.mark.parametrize(
        ("kwarg", "key", "value"), (
            ("framework_agreement_version", "frameworkAgreementVersion", "v0.0.1"),
            ("framework_variations", "variations", {"1": "blah"}),
        )
    )
    def test_returns_mapping_which_can_be_changed_using_kwargs(self, kwarg, key, value):
        assert key in api_stubs.framework_agreement_details()
        assert api_stubs.framework_agreement_details(**{kwarg: value})[key] == value

    def test_slug_kwarg_changes_framework_url(self):
        assert api_stubs.framework_agreement_details(slug="my-custom-slug")["frameworkURL"] \
            == "https://www.gov.uk/government/publications/my-custom-slug"

    def test_lots_kwarg_changes_lot_description_and_lot_order(self):
        lots = [api_stubs.lot(slug='cloud-hosting'), api_stubs.lot(slug='cloud-support')]
        framework_agreement_details = api_stubs.framework_agreement_details(lots=lots)

        assert framework_agreement_details["lotDescriptions"] == {
            "cloud-hosting": "Lot 1: Cloud hosting",
            "cloud-support": "Lot 2: Cloud support"
        }
        assert framework_agreement_details["lotOrder"] == [
            "cloud-hosting",
            "cloud-support"
        ]


class TestFramework:
    def setup(self):
        self.g7_lots = api_stubs.g_cloud_7_lots()
        self.dos_lots = api_stubs.dos_lots()

    def test_default_values(self):
        assert api_stubs.framework() == {
            "frameworks": {
                "id": 1,
                "name": "G-Cloud 7",
                "slug": "g-cloud-7",
                "framework": "g-cloud",
                "family": "g-cloud",
                "status": "open",
                "clarificationQuestionsOpen": True,
                "lots": self.g7_lots,
                "allowDeclarationReuse": True,
                "frameworkAgreementDetails": api_stubs.framework_agreement_details(lots=self.g7_lots),
                "countersignerName": None,
                "frameworkAgreementVersion": "RM1557x",
                "variations": {},
                'clarificationsCloseAtUTC': '2000-01-01T00:00:00.000000Z',
                'clarificationsPublishAtUTC': '2000-01-02T00:00:00.000000Z',
                'applicationsCloseAtUTC': '2000-01-03T00:00:00.000000Z',
                'intentionToAwardAtUTC': '2000-01-04T00:00:00.000000Z',
                'frameworkLiveAtUTC': '2000-01-05T00:00:00.000000Z',
                'frameworkExpiresAtUTC': '2000-01-06T00:00:00.000000Z',
                'hasDirectAward': True,
                'hasFurtherCompetition': False,
            }
        }

    @pytest.mark.parametrize(
        ("kwarg", "key", "value"), (
            ("status", "status", "live"),
            ("name", "name", "My overridden name"),
            ("clarification_questions_open", "clarificationQuestionsOpen", False),
            ("has_direct_award", "hasDirectAward", False),
            ("has_further_competition", "hasFurtherCompetition", True),
        )
    )
    def test_returns_mapping_which_can_be_changed_using_kwargs(self, kwarg, key, value):
        assert key in api_stubs.framework()["frameworks"]
        assert api_stubs.framework(**{kwarg: value})["frameworks"][key] == value

    def test_includes_lots(self):
        assert api_stubs.framework()["frameworks"]["lots"] == self.g7_lots

    def test_includes_framework_agreement_details(self):
        assert api_stubs.framework()["frameworks"]["frameworkAgreementDetails"] \
            == api_stubs.framework_agreement_details(lots=self.g7_lots)

    @pytest.mark.parametrize(
        ("slug", "family"), (
            ("my-fake-framework", "my-fake-framework"),
            ("digital-outcomes-and-specialists", "digital-outcomes-and-specialists"),
            ("digital-outcomes-and-specialists-2", "digital-outcomes-and-specialists"),
            ("g-cloud-10", "g-cloud"),
        )
    )
    def test_slug_kwarg_changes_framework_name_slug_family(self, slug, family):
        framework = api_stubs.framework(slug=slug)

        assert framework["frameworks"]["slug"] == slug
        assert framework["frameworks"]["framework"] == family
        assert framework["frameworks"]["family"] == family

    def test_dos_slug_kwarg_changes_all_related_framework_details(self):
        expected = api_stubs.framework()
        expected["frameworks"].update({
            "name": "Digital Outcomes and Specialists",
            "slug": "digital-outcomes-and-specialists",
            "framework": "digital-outcomes-and-specialists",
            "family": "digital-outcomes-and-specialists",
            "lots": self.dos_lots,
            "frameworkAgreementDetails": api_stubs.framework_agreement_details(slug='digital-outcomes-and-specialists',
                                                                               lots=self.dos_lots),
            "hasDirectAward": False,
            "hasFurtherCompetition": True,
        })

        assert api_stubs.framework(slug='digital-outcomes-and-specialists') \
            == expected

    def test_lots_kwarg_changes_lots_and_framework_agreement_details(self):
        lots = [api_stubs.lot(slug='cloud-hosting'), api_stubs.lot(slug='cloud-support')]

        expected = api_stubs.framework()
        expected["frameworks"]["lots"] = lots
        expected["frameworks"]["frameworkAgreementDetails"]["lotOrder"] = ["cloud-hosting", "cloud-support"]
        expected["frameworks"]["frameworkAgreementDetails"]["lotDescriptions"] = {
            "cloud-hosting": "Lot 1: Cloud hosting",
            "cloud-support": "Lot 2: Cloud support",
        }

        assert api_stubs.framework(lots=lots) == expected

    @pytest.mark.parametrize(
        ("kwarg", "datetime", "key", "value"), (
            ("clarifications_close_at", dt(2010, 1, 1), "clarificationsCloseAtUTC", "2010-01-01T00:00:00.000000Z"),
            ("clarifications_publish_at", dt(2010, 2, 2), "clarificationsPublishAtUTC", "2010-02-02T00:00:00.000000Z"),
            ("applications_close_at", dt(2010, 3, 3), "applicationsCloseAtUTC", "2010-03-03T00:00:00.000000Z"),
            ("intention_to_award_at", dt(2010, 4, 4), "intentionToAwardAtUTC", "2010-04-04T00:00:00.000000Z"),
            ("framework_live_at", dt(2010, 5, 5), "frameworkLiveAtUTC", "2010-05-05T00:00:00.000000Z"),
            ("framework_expires_at", dt(2010, 6, 6), "frameworkExpiresAtUTC", "2010-06-06T00:00:00.000000Z"),
        )
    )
    def test_date_kwargs_can_be_datetime(self, kwarg, datetime, key, value):
        assert key in api_stubs.framework()["frameworks"]
        assert api_stubs.framework(**{kwarg: datetime})["frameworks"][key] == value


class TestSupplierFramework:
    @pytest.mark.parametrize(
        ("kwarg", "key", "value"), (
            ("supplier_id", "supplierId", 4444244),
            ("prefill_declaration_from_slug", "prefillDeclarationFromFrameworkSlug",
                                              "digital-outcomes-and-specialists"),
            ("application_company_details_confirmed", "applicationCompanyDetailsConfirmed", False),
            ("on_framework", "onFramework", False),
        )
    )
    def test_returns_mapping_which_can_be_changed_using_kwargs(self, kwarg, key, value):
        assert key in api_stubs.supplier_framework()["frameworkInterest"]
        assert api_stubs.supplier_framework(**{kwarg: value})["frameworkInterest"][key] == value

    def test_agreed_variations(self):
        assert api_stubs.supplier_framework(agreed_variations=False)['frameworkInterest']['agreedVariations'] == {}

    def test_with_declaration(self):
        assert 'declaration' not in api_stubs.supplier_framework(with_declaration=False)['frameworkInterest'].keys()

    def test_with_agreement(self):
        expected = api_stubs.supplier_framework()
        expected["frameworkInterest"].update({
            'agreementDetails': None,
            'agreementId': None,
            'agreementPath': None,
            'agreementReturned': False,
            'agreementReturnedAt': None,
            'agreementStatus': None,
            'countersigned': False,
            'countersignedAt': None,
            'countersignedDetails': None,
            'countersignedPath': None,
        })

        assert api_stubs.supplier_framework(with_agreement=False)['frameworkInterest'] \
            == expected["frameworkInterest"]

    def test_with_users(self):
        supplier_framework = api_stubs.supplier_framework(with_users=False)['frameworkInterest']
        assert set(supplier_framework['agreementDetails'].keys()) == {
            'frameworkAgreementVersion', 'signerName', 'signerRole', 'uploaderUserId'
        }
        assert set(supplier_framework['countersignedDetails'].keys()) == {'approvedByUserId'}


class TestBrief:
    def test_brief_defaults(self):
        assert api_stubs.brief() \
            == {
            "briefs": {
                "id": 1234,
                "title": "I need a thing to do a thing",
                "frameworkSlug": "digital-outcomes-and-specialists",
                "frameworkStatus": "live",
                "frameworkName": "Digital Outcomes and Specialists",
                "frameworkFramework": "digital-outcomes-and-specialists",
                "framework": {
                    "family": "digital-outcomes-and-specialists",
                    "name": "Digital Outcomes and Specialists",
                    "slug": "digital-outcomes-and-specialists",
                    "status": "live"
                },
                "isACopy": False,
                "lotName": "Digital Specialists",
                "lotSlug": "digital-specialists",
                "status": "draft",
                "users": [{"active": True,
                           "role": "buyer",
                           "emailAddress": "buyer@email.com",
                           "id": 123,
                           "name": "Buyer User"}],
                "createdAt": "2016-03-29T10:11:12.000000Z",
                "updatedAt": "2016-03-29T10:11:13.000000Z",
                "clarificationQuestions": [],
            }
        }

    @pytest.mark.parametrize(
        ("kwarg", "key", "value"), (
            ("status", "status", "live"),
            ("lot_name", "lotName", "A Lot Slug"),
            ("lot_slug", "lotSlug", "a-lot-slug"),
            ("clarification_questions", "clarificationQuestions", [{"question": "Why?", "answer": "Because"}]),
        )
    )
    def test_returns_mapping_which_can_be_changed_using_kwargs(self, kwarg, key, value):
        assert key in api_stubs.brief()["briefs"]
        assert api_stubs.brief(**{kwarg: value})["briefs"][key] == value

    @pytest.mark.parametrize(
        ("kwarg", "key", "inner_key", "value"), (
            ("framework_slug", "frameworkSlug", "slug", "a-framework-slug"),
            ("framework_name", "frameworkName", "name", "A Framework Name"),
            ("framework_family", "frameworkFramework", "family", "a framework framework"),
            ("framework_status", "frameworkStatus", "status", "status"),
        )
    )
    def test_framework_kwarg_changes_framework_value_and_framework_dictionary(self, kwarg, key, inner_key, value):
        brief = api_stubs.brief(**{kwarg: value})
        assert brief["briefs"][key] == value
        assert brief["briefs"]["framework"][inner_key] == value

    def test_user_id_kwarg(self):
        assert api_stubs.brief(user_id=234)["briefs"]["users"][0]["id"] == 234

    def test_brief_clarification_questions_closed(self):
        brief = api_stubs.brief(status='live', clarification_questions_closed=True)
        assert brief["briefs"]["clarificationQuestionsAreClosed"] is True

    def test_if_status_is_closed_brief_contains_milestone_dates(self):
        brief = api_stubs.brief(status="closed")
        assert brief["briefs"]["createdAt"] == "2016-03-29T10:11:12.000000Z"
        assert brief["briefs"]["updatedAt"] == "2016-03-29T10:11:13.000000Z"
        assert brief["briefs"]["publishedAt"] == "2016-03-29T10:11:14.000000Z"
        assert brief["briefs"]["applicationsClosedAt"] == "2016-04-07T00:00:00.000000Z"
        assert brief["briefs"]["clarificationQuestionsClosedAt"] == "2016-04-02T00:00:00.000000Z"
        assert brief["briefs"]["clarificationQuestionsPublishedBy"] == "2016-04-02T00:00:00.000000Z"


class TestSupplier:
    def test_default_values(self):
        assert api_stubs.supplier() == {
            'suppliers': {
                'companyDetailsConfirmed': True,
                'companiesHouseNumber': '12345678',
                'contactInformation': [{
                    'address1': '123 Fake Road',
                    'city': 'Madeupolis',
                    'contactName': 'Mr E Man',
                    'email': 'mre@company.com',
                    'id': 4321,
                    'links': {
                        'self': 'http://localhost:5000/suppliers/1234/contact-information/4321'
                    },
                    'phoneNumber': '01234123123',
                    'postcode': 'A11 1AA',
                    "website": "https://www.mre.company"
                }],
                'description': "I'm a supplier.",
                'dunsNumber': '123456789',
                'id': 1234,
                'links': {
                    'self': 'http://localhost:5000/suppliers/1234'
                },
                'name': 'My Little Company',
                'organisationSize': 'micro',
                'registeredName': 'My Little Registered Company',
                'registrationCountry': 'country:GB',
                'service_counts': {
                    "G-Cloud 9": 109,
                    "G-Cloud 8": 108,
                    "G-Cloud 7": 107,
                    "G-Cloud 6": 106,
                    "G-Cloud 5": 105,
                },
                'tradingStatus': 'limited company',
                'vatNumber': '111222333'
            }
        }

    @pytest.mark.parametrize(
        ("kwarg", "key", "value"), (
            ("company_details_confirmed", "companyDetailsConfirmed", False),
        )
    )
    def test_returns_mapping_which_can_be_changed_using_kwargs(self, kwarg, key, value):
        assert key in api_stubs.supplier()["suppliers"]
        assert api_stubs.supplier(**{kwarg: value})["suppliers"][key] == value

    def test_id_kwarg_changes_id_and_self_link(self):
        supplier = api_stubs.supplier(id=9999)
        assert supplier["suppliers"]["id"] == 9999
        assert supplier["suppliers"]["links"]["self"].endswith("9999")

    def test_other_company_registration_number_kwarg(self):
        assert "otherCompanyRegistrationNumber" not in api_stubs.supplier()["suppliers"]

        supplier = api_stubs.supplier(other_company_registration_number=123456)
        assert supplier["suppliers"]["otherCompanyRegistrationNumber"] == 123456
        assert "companiesHouseNumber" not in supplier["suppliers"]

    def test_contact_id_kwarg_changes_contact_dictionary(self):
        brief = api_stubs.supplier(contact_id=9999)
        assert brief["suppliers"]["contactInformation"][0]["id"] == 9999
        assert brief["suppliers"]["contactInformation"][0]["links"]["self"].endswith("9999")
