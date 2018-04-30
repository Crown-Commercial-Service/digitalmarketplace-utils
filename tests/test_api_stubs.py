from datetime import datetime as dt
from dmutils import api_stubs


def test_framework():
    assert api_stubs.framework() == {
        "frameworks": {
            "clarificationQuestionsOpen": True,
            "lots": [],
            "name": "G-Cloud 7",
            "slug": "g-cloud-7",
            "framework": "g-cloud",
            "status": "open",
            'clarificationsCloseAtUTC': '2000-01-01T00:00:00.000000Z',
            'clarificationsPublishAtUTC': '2000-01-02T00:00:00.000000Z',
            'applicationsCloseAtUTC': '2000-01-03T00:00:00.000000Z',
            'intentionToAwardAtUTC': '2000-01-04T00:00:00.000000Z',
            'frameworkLiveAtUTC': '2000-01-05T00:00:00.000000Z',
        }
    }

    assert api_stubs.framework(slug='digital-outcomes-and-specialists') == {
        "frameworks": {
            "clarificationQuestionsOpen": True,
            "lots": [],
            "name": "Digital Outcomes and Specialists",
            "slug": "digital-outcomes-and-specialists",
            "framework": "digital-outcomes-and-specialists",
            "status": "open",
            'clarificationsCloseAtUTC': '2000-01-01T00:00:00.000000Z',
            'clarificationsPublishAtUTC': '2000-01-02T00:00:00.000000Z',
            'applicationsCloseAtUTC': '2000-01-03T00:00:00.000000Z',
            'intentionToAwardAtUTC': '2000-01-04T00:00:00.000000Z',
            'frameworkLiveAtUTC': '2000-01-05T00:00:00.000000Z',
        }
    }

    assert api_stubs.framework(status='live', clarification_questions_open=False,
                               name='My overriden name', slug='my-fake-framework') == {
        "frameworks": {
            "clarificationQuestionsOpen": False,
            "lots": [],
            "name": "My overriden name",
            "slug": "my-fake-framework",
            "framework": "my-fake-framework",
            "status": "live",
            'clarificationsCloseAtUTC': '2000-01-01T00:00:00.000000Z',
            'clarificationsPublishAtUTC': '2000-01-02T00:00:00.000000Z',
            'applicationsCloseAtUTC': '2000-01-03T00:00:00.000000Z',
            'intentionToAwardAtUTC': '2000-01-04T00:00:00.000000Z',
            'frameworkLiveAtUTC': '2000-01-05T00:00:00.000000Z',
        }
    }

    assert api_stubs.framework(lots=['cloud-hosting', 'cloud-support']) == {
        "frameworks": {
            "clarificationQuestionsOpen": True,
            "lots": ['cloud-hosting', 'cloud-support'],
            "name": "G-Cloud 7",
            "slug": "g-cloud-7",
            "framework": "g-cloud",
            "status": "open",
            'clarificationsCloseAtUTC': '2000-01-01T00:00:00.000000Z',
            'clarificationsPublishAtUTC': '2000-01-02T00:00:00.000000Z',
            'applicationsCloseAtUTC': '2000-01-03T00:00:00.000000Z',
            'intentionToAwardAtUTC': '2000-01-04T00:00:00.000000Z',
            'frameworkLiveAtUTC': '2000-01-05T00:00:00.000000Z',
        }
    }

    assert api_stubs.framework(clarifications_close_at=dt(2010, 1, 1),
                               clarifications_publish_at=dt(2010, 2, 2),
                               applications_close_at=dt(2010, 3, 3),
                               intention_to_award_at=dt(2010, 4, 4),
                               framework_live_at=dt(2010, 5, 5)) == {
        "frameworks": {
            "clarificationQuestionsOpen": True,
            "lots": [],
            "name": "G-Cloud 7",
            "slug": "g-cloud-7",
            "framework": "g-cloud",
            "status": "open",
            'clarificationsCloseAtUTC': '2010-01-01T00:00:00.000000Z',
            'clarificationsPublishAtUTC': '2010-02-02T00:00:00.000000Z',
            'applicationsCloseAtUTC': '2010-03-03T00:00:00.000000Z',
            'intentionToAwardAtUTC': '2010-04-04T00:00:00.000000Z',
            'frameworkLiveAtUTC': '2010-05-05T00:00:00.000000Z',
        }
    }


def test_framework_name_changes_with_slug():
    assert api_stubs.framework(slug='digital-outcomes-and-specialists')["frameworks"]["name"] == \
        "Digital Outcomes and Specialists"
    assert api_stubs.framework(slug="my-framework")["frameworks"]["name"] == "My Framework"


def test_lot_name_default_is_made_from_slug():
    assert api_stubs.lot(slug="my-lot")["name"] == "My Lot"


def test_lot():
    assert api_stubs.lot(slug="foo") == {
        "id": 1,
        "slug": "foo",
        "name": "Foo",
        "allowsBrief": False,
        "oneServiceLimit": False,
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
