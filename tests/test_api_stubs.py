from datetime import datetime as dt
from dmutils import api_stubs


class TestLot:
    def test_default_values(self):
        assert api_stubs.lot() == {
            "id": 1,
            "slug": "some-lot",
            "name": "Some Lot",
            "allowsBrief": False,
            "oneServiceLimit": False,
            "unitSingular": "service",
            "unitPlural": "services",
        }

    def test_override_values(self):
        assert api_stubs.lot(lot_id=2, slug="my-special-lot", allows_brief=True, one_service_limit=True,
                             unit_singular='brief', unit_plural='briefs') == {
            "id": 2,
            "slug": "my-special-lot",
            "name": "My Special Lot",
            "allowsBrief": True,
            "oneServiceLimit": True,
            "unitSingular": "brief",
            "unitPlural": "briefs",
        }


class TestFrameworkAgreementDetails:
    def test_default_values(self):
        assert api_stubs.framework_agreement_details() == {
            "contractNoticeNumber": "2010/ABC-DEF",
            "frameworkAgreementVersion": "RM1557x",
            "frameworkEndDate": "01 January 2001",
            "frameworkExtensionLength": "12 months",
            "frameworkRefDate": "29-06-2000",
            "frameworkStartDate": "05 January 2000",
            "frameworkURL": f"https://www.gov.uk/government/publications/g-cloud-7",
            "lotDescriptions": {},
            "lotOrder": [],
            "pageTotal": 99,
            "signaturePageNumber": 98,
            "variations": {}
        }

    def test_override_slug_version_and_variation(self):
        assert api_stubs.framework_agreement_details(slug='my-custom-slug',
                                                     framework_agreement_version='v0.0.1',
                                                     framework_variations={"1": "blah"}) == {
            "contractNoticeNumber": "2010/ABC-DEF",
            "frameworkAgreementVersion": "v0.0.1",
            "frameworkEndDate": "01 January 2001",
            "frameworkExtensionLength": "12 months",
            "frameworkRefDate": "29-06-2000",
            "frameworkStartDate": "05 January 2000",
            "frameworkURL": f"https://www.gov.uk/government/publications/my-custom-slug",
            "lotDescriptions": {},
            "lotOrder": [],
            "pageTotal": 99,
            "signaturePageNumber": 98,
            "variations": {"1": "blah"},
        }

    def test_with_lots(self):
        lots = [api_stubs.lot(slug='cloud-hosting'), api_stubs.lot(slug='cloud-support')]
        assert api_stubs.framework_agreement_details(lots=lots) == {
            "contractNoticeNumber": "2010/ABC-DEF",
            "frameworkAgreementVersion": "RM1557x",
            "frameworkEndDate": "01 January 2001",
            "frameworkExtensionLength": "12 months",
            "frameworkRefDate": "29-06-2000",
            "frameworkStartDate": "05 January 2000",
            "frameworkURL": f"https://www.gov.uk/government/publications/g-cloud-7",
            "lotDescriptions": {"cloud-hosting": "Lot 1: Cloud Hosting",
                                "cloud-support": "Lot 2: Cloud Support"},
            "lotOrder": ["cloud-hosting", "cloud-support"],
            "pageTotal": 99,
            "signaturePageNumber": 98,
            "variations": {}
        }


class TestFramework:
    def test_default_values(self):
        assert api_stubs.framework() == {
            "frameworks": {
                "id": 1,
                "name": "G-Cloud 7",
                "slug": "g-cloud-7",
                "framework": "g-cloud",
                "status": "open",
                "clarificationQuestionsOpen": True,
                "lots": [],
                "allowDeclarationReuse": True,
                "frameworkAgreementDetails": api_stubs.framework_agreement_details(),
                "countersignerName": None,
                "frameworkAgreementVersion": "RM1557x",
                "variations": {},
                'clarificationsCloseAtUTC': '2000-01-01T00:00:00.000000Z',
                'clarificationsPublishAtUTC': '2000-01-02T00:00:00.000000Z',
                'applicationsCloseAtUTC': '2000-01-03T00:00:00.000000Z',
                'intentionToAwardAtUTC': '2000-01-04T00:00:00.000000Z',
                'frameworkLiveAtUTC': '2000-01-05T00:00:00.000000Z',
            }
        }

    def test_custom_slug_derives_name_and_framework(self):
        framework_agreement_details = api_stubs.framework_agreement_details(slug='digital-outcomes-and-specialists')
        assert api_stubs.framework(slug='digital-outcomes-and-specialists') == {
            "frameworks": {
                "id": 1,
                "name": "Digital Outcomes and Specialists",
                "slug": "digital-outcomes-and-specialists",
                "framework": "digital-outcomes-and-specialists",
                "status": "open",
                "clarificationQuestionsOpen": True,
                "lots": [],
                "allowDeclarationReuse": True,
                "frameworkAgreementDetails": framework_agreement_details,
                "countersignerName": None,
                "frameworkAgreementVersion": "RM1557x",
                "variations": {},
                'clarificationsCloseAtUTC': '2000-01-01T00:00:00.000000Z',
                'clarificationsPublishAtUTC': '2000-01-02T00:00:00.000000Z',
                'applicationsCloseAtUTC': '2000-01-03T00:00:00.000000Z',
                'intentionToAwardAtUTC': '2000-01-04T00:00:00.000000Z',
                'frameworkLiveAtUTC': '2000-01-05T00:00:00.000000Z',
            }
        }

    def test_override_status_slug_name_and_clarification_questions(self):
        assert api_stubs.framework(status='live', slug='my-fake-framework', name='My overriden name',
                                   clarification_questions_open=False) == {
            "frameworks": {
                "id": 1,
                "name": "My overriden name",
                "slug": "my-fake-framework",
                "framework": "my-fake-framework",
                "status": "live",
                "clarificationQuestionsOpen": False,
                "lots": [],
                "allowDeclarationReuse": True,
                "frameworkAgreementDetails": api_stubs.framework_agreement_details(slug='my-fake-framework'),
                "countersignerName": None,
                "frameworkAgreementVersion": "RM1557x",
                "variations": {},
                'clarificationsCloseAtUTC': '2000-01-01T00:00:00.000000Z',
                'clarificationsPublishAtUTC': '2000-01-02T00:00:00.000000Z',
                'applicationsCloseAtUTC': '2000-01-03T00:00:00.000000Z',
                'intentionToAwardAtUTC': '2000-01-04T00:00:00.000000Z',
                'frameworkLiveAtUTC': '2000-01-05T00:00:00.000000Z',
            }
        }

    def test_with_lots(self):
        lots = [api_stubs.lot(slug='cloud-hosting'), api_stubs.lot(slug='cloud-support')]
        assert api_stubs.framework(lots=lots) == {
            "frameworks": {
                "id": 1,
                "name": "G-Cloud 7",
                "slug": "g-cloud-7",
                "framework": "g-cloud",
                "status": "open",
                "clarificationQuestionsOpen": True,
                "lots": lots,
                "allowDeclarationReuse": True,
                "frameworkAgreementDetails": api_stubs.framework_agreement_details(lots=lots),
                "countersignerName": None,
                "frameworkAgreementVersion": "RM1557x",
                "variations": {},
                'clarificationsCloseAtUTC': '2000-01-01T00:00:00.000000Z',
                'clarificationsPublishAtUTC': '2000-01-02T00:00:00.000000Z',
                'applicationsCloseAtUTC': '2000-01-03T00:00:00.000000Z',
                'intentionToAwardAtUTC': '2000-01-04T00:00:00.000000Z',
                'frameworkLiveAtUTC': '2000-01-05T00:00:00.000000Z',
            }
        }

    def test_custom_dates(self):
        assert api_stubs.framework(clarifications_close_at=dt(2010, 1, 1),
                                   clarifications_publish_at=dt(2010, 2, 2),
                                   applications_close_at=dt(2010, 3, 3),
                                   intention_to_award_at=dt(2010, 4, 4),
                                   framework_live_at=dt(2010, 5, 5)) == {
            "frameworks": {
                "id": 1,
                "name": "G-Cloud 7",
                "slug": "g-cloud-7",
                "framework": "g-cloud",
                "status": "open",
                "clarificationQuestionsOpen": True,
                "lots": [],
                "allowDeclarationReuse": True,
                "frameworkAgreementDetails": api_stubs.framework_agreement_details(),
                "countersignerName": None,
                "frameworkAgreementVersion": "RM1557x",
                "variations": {},
                'clarificationsCloseAtUTC': '2010-01-01T00:00:00.000000Z',
                'clarificationsPublishAtUTC': '2010-02-02T00:00:00.000000Z',
                'applicationsCloseAtUTC': '2010-03-03T00:00:00.000000Z',
                'intentionToAwardAtUTC': '2010-04-04T00:00:00.000000Z',
                'frameworkLiveAtUTC': '2010-05-05T00:00:00.000000Z',
            }
        }


def test_brief():
    assert api_stubs.brief() \
        == {
        "briefs": {
            "id": 1234,
            "title": "I need a thing to do a thing",
            "frameworkSlug": "digital-outcomes-and-specialists",
            "frameworkName": "Digital Outcomes and Specialists",
            "frameworkFramework": "digital-outcomes-and-specialists",
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

    assert api_stubs.brief(
        status='live',
        framework_slug='a-framework-slug',
        lot_slug='a-lot-slug', user_id=234,
        framework_name='A Framework Name',
        framework_framework='a framework framework') \
        == {
        "briefs": {
            "id": 1234,
            "title": "I need a thing to do a thing",
            "frameworkSlug": "a-framework-slug",
            "frameworkName": "A Framework Name",
            "frameworkFramework": "a framework framework",
            "lotSlug": "a-lot-slug",
            "status": "live",
            "users": [{"active": True,
                       "role": "buyer",
                       "emailAddress": "buyer@email.com",
                       "id": 234,
                       "name": "Buyer User"}],
            "createdAt": "2016-03-29T10:11:12.000000Z",
            "updatedAt": "2016-03-29T10:11:13.000000Z",
            "publishedAt": "2016-03-29T10:11:14.000000Z",
            "applicationsClosedAt": "2016-04-07T00:00:00.000000Z",
            "clarificationQuestionsClosedAt": "2016-04-02T00:00:00.000000Z",
            "clarificationQuestionsAreClosed": False,
            "clarificationQuestions": [],
        }
    }

    assert api_stubs.brief(clarification_questions=[{"question": "Why?", "answer": "Because"}]) \
        == {
        "briefs": {
            "id": 1234,
            "title": "I need a thing to do a thing",
            "frameworkSlug": "digital-outcomes-and-specialists",
            "frameworkName": "Digital Outcomes and Specialists",
            "frameworkFramework": "digital-outcomes-and-specialists",
            "lotSlug": "digital-specialists",
            "status": "draft",
            "users": [{"active": True,
                       "role": "buyer",
                       "emailAddress": "buyer@email.com",
                       "id": 123,
                       "name": "Buyer User"}],
            "createdAt": "2016-03-29T10:11:12.000000Z",
            "updatedAt": "2016-03-29T10:11:13.000000Z",
            "clarificationQuestions": [{
                "question": "Why?",
                "answer": "Because"
            }],
        }
    }

    assert api_stubs.brief(status='live', clarification_questions_closed=True) \
        == {
        "briefs": {
            "id": 1234,
            "title": "I need a thing to do a thing",
            "frameworkSlug": "digital-outcomes-and-specialists",
            "frameworkName": "Digital Outcomes and Specialists",
            "frameworkFramework": "digital-outcomes-and-specialists",
            "lotSlug": "digital-specialists",
            "status": "live",
            "users": [{"active": True,
                       "role": "buyer",
                       "emailAddress": "buyer@email.com",
                       "id": 123,
                       "name": "Buyer User"}],
            "createdAt": "2016-03-29T10:11:12.000000Z",
            "updatedAt": "2016-03-29T10:11:13.000000Z",
            "publishedAt": "2016-03-29T10:11:14.000000Z",
            "applicationsClosedAt": "2016-04-07T00:00:00.000000Z",
            "clarificationQuestionsClosedAt": "2016-04-02T00:00:00.000000Z",
            "clarificationQuestionsAreClosed": True,
            "clarificationQuestions": [],
        }
    }

    assert api_stubs.brief(
        status='closed',
        framework_slug='a-framework-slug',
        lot_slug='a-lot-slug', user_id=234,
        framework_name='A Framework Name') \
        == {
        "briefs": {
            "id": 1234,
            "title": "I need a thing to do a thing",
            "frameworkSlug": "a-framework-slug",
            "frameworkName": "A Framework Name",
            "frameworkFramework": "digital-outcomes-and-specialists",
            "lotSlug": "a-lot-slug",
            "status": "closed",
            "users": [{"active": True,
                       "role": "buyer",
                       "emailAddress": "buyer@email.com",
                       "id": 234,
                       "name": "Buyer User"}],
            "createdAt": "2016-03-29T10:11:12.000000Z",
            "updatedAt": "2016-03-29T10:11:13.000000Z",
            "publishedAt": "2016-03-29T10:11:14.000000Z",
            "applicationsClosedAt": "2016-04-07T00:00:00.000000Z",
            "clarificationQuestionsClosedAt": "2016-04-02T00:00:00.000000Z",
            "clarificationQuestionsAreClosed": False,
            "clarificationQuestions": [],
        }
    }


def test_supplier():
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

    assert api_stubs.supplier(id=9999) == {
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
                    'self': 'http://localhost:5000/suppliers/9999/contact-information/4321'
                },
                'phoneNumber': '01234123123',
                'postcode': 'A11 1AA',
                "website": "https://www.mre.company"
            }],
            'description': "I'm a supplier.",
            'dunsNumber': '123456789',
            'id': 9999,
            'links': {
                'self': 'http://localhost:5000/suppliers/9999'
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

    assert api_stubs.supplier(contact_id=9999) == {
        'suppliers': {
            'companyDetailsConfirmed': True,
            'companiesHouseNumber': '12345678',
            'contactInformation': [{
                'address1': '123 Fake Road',
                'city': 'Madeupolis',
                'contactName': 'Mr E Man',
                'email': 'mre@company.com',
                'id': 9999,
                'links': {
                    'self': 'http://localhost:5000/suppliers/1234/contact-information/9999'
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

    assert api_stubs.supplier(other_company_registration_number=123456) == {
        'suppliers': {
            'companyDetailsConfirmed': True,
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
            'otherCompanyRegistrationNumber': 123456,
            'organisationSize': 'micro',
            'registeredName': 'My Little Registered Company',
            'registrationCountry': 'country:NZ',
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

    assert api_stubs.supplier(company_details_confirmed=False) == {
        'suppliers': {
            'companyDetailsConfirmed': False,
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
