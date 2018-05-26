from datetime import datetime as dt

from .formats import DATETIME_FORMAT


def lot(lot_id=1, slug="some-lot", name=None, allows_brief=False, one_service_limit=False, unit_singular='service',
        unit_plural='services'):
    if not name:
        name = slug.replace("-", " ").title()

    return {
        "id": lot_id,
        "slug": slug,
        "name": name,
        "allowsBrief": allows_brief,
        "oneServiceLimit": one_service_limit,
        "unitSingular": unit_singular,
        "unitPlural": unit_plural,
    }


def framework_agreement_details(slug='g-cloud-7',
                                framework_agreement_version='RM1557x',
                                framework_variations=None,
                                lots=None):
    if not lots:
        lots = []

    lot_descriptions = {}
    for i, one_lot in enumerate(lots):
        lot_descriptions[one_lot['slug']] = f"Lot {i+1}: {one_lot['name']}"

    lot_order = [one_lot['slug'] for one_lot in lots]

    if not framework_variations:
        framework_variations = {}

    return {
        "contractNoticeNumber": "2010/ABC-DEF",
        "frameworkAgreementVersion": framework_agreement_version,
        "frameworkEndDate": "01 January 2001",
        "frameworkExtensionLength": "12 months",
        "frameworkRefDate": "29-06-2000",
        "frameworkStartDate": "05 January 2000",
        "frameworkURL": f"https://www.gov.uk/government/publications/{slug}",
        "lotDescriptions": lot_descriptions,
        "lotOrder": lot_order,
        "pageTotal": 99,
        "signaturePageNumber": 98,
        "variations": framework_variations
    }


def framework(framework_id=1,
              status="open",
              slug="g-cloud-7",
              name=None,
              clarification_questions_open=True,
              lots=None,
              framework_family=None,
              framework_agreement_version='RM1557x',
              framework_variations=None,
              allow_declaration_reuse=True,
              clarifications_close_at=dt(2000, 1, 1),
              clarifications_publish_at=dt(2000, 1, 2),
              applications_close_at=dt(2000, 1, 3),
              intention_to_award_at=dt(2000, 1, 4),
              framework_live_at=dt(2000, 1, 5),
              framework_expires_at=dt(2000, 1, 6),
              has_direct_award=True,
              has_further_competition=False):
    if name:
        pass
    elif slug.startswith('g-cloud'):
        name = 'G-Cloud {}'.format(slug.split('-')[-1])
    elif slug.startswith("digital-outcomes-and-specialists"):
        name = slug.replace("-", " ").title()
        name = name.replace('And', 'and')
    else:
        name = slug.replace("-", " ").title()

    if framework_family:
        pass
    elif slug.startswith('g-cloud'):
        framework_family = 'g-cloud'
    elif slug.startswith("digital-outcomes-and-specialists"):
        framework_family = 'digital-outcomes-and-specialists'
    else:
        framework_family = slug

    lots = lots or []

    agreement_details = framework_agreement_details(slug=slug,
                                                    framework_agreement_version=framework_agreement_version,
                                                    framework_variations=framework_variations,
                                                    lots=lots)

    def format_datetime(datetime_utc):
        assert isinstance(datetime_utc, dt)
        return datetime_utc.strftime(DATETIME_FORMAT)

    return {
        "frameworks": {
            "id": framework_id,
            "name": name,
            "slug": slug,
            "framework": framework_family,
            "status": status,
            "clarificationQuestionsOpen": clarification_questions_open,
            "lots": lots,
            "allowDeclarationReuse": allow_declaration_reuse,
            "frameworkAgreementDetails": agreement_details,
            "countersignerName": agreement_details.get('countersignerName'),
            "frameworkAgreementVersion": agreement_details.get('frameworkAgreementVersion'),
            "variations": agreement_details.get('variations'),
            'clarificationsCloseAtUTC': format_datetime(clarifications_close_at),
            'clarificationsPublishAtUTC': format_datetime(clarifications_publish_at),
            'applicationsCloseAtUTC': format_datetime(applications_close_at),
            'intentionToAwardAtUTC': format_datetime(intention_to_award_at),
            'frameworkLiveAtUTC': format_datetime(framework_live_at),
            'frameworkExpiresAtUTC': format_datetime(framework_expires_at),
            "hasDirectAward": has_direct_award,
            "hasFurtherCompetition": has_further_competition,
        }
    }


def brief(status="draft",
          framework_slug="digital-outcomes-and-specialists",
          lot_slug="digital-specialists",
          user_id=123,
          framework_name="Digital Outcomes and Specialists",
          framework_family="digital-outcomes-and-specialists",
          clarification_questions=None,
          clarification_questions_closed=False):
    brief = {
        "briefs": {
            "id": 1234,
            "title": "I need a thing to do a thing",
            "frameworkSlug": framework_slug,
            "frameworkName": framework_name,
            "frameworkFramework": framework_family,
            "lotSlug": lot_slug,
            "status": status,
            "users": [{"active": True,
                       "role": "buyer",
                       "emailAddress": "buyer@email.com",
                       "id": user_id,
                       "name": "Buyer User"}],
            "createdAt": "2016-03-29T10:11:12.000000Z",
            "updatedAt": "2016-03-29T10:11:13.000000Z",
            "clarificationQuestions": clarification_questions or [],
        }
    }
    if status in ("live", "closed"):
        brief['briefs']['publishedAt'] = "2016-03-29T10:11:14.000000Z"
        brief['briefs']['applicationsClosedAt'] = "2016-04-07T00:00:00.000000Z"
        brief['briefs']['clarificationQuestionsClosedAt'] = "2016-04-02T00:00:00.000000Z"
        brief['briefs']['clarificationQuestionsAreClosed'] = clarification_questions_closed

    return brief


def supplier(id=1234, contact_id=4321, other_company_registration_number=0, company_details_confirmed=True):
    data = {
        "suppliers": {
            "companiesHouseNumber": "12345678",
            "companyDetailsConfirmed": company_details_confirmed,
            "contactInformation": [
                {
                    "address1": "123 Fake Road",
                    "city": "Madeupolis",
                    "contactName": "Mr E Man",
                    "email": "mre@company.com",
                    "id": contact_id,
                    "links": {
                        "self": "http://localhost:5000/suppliers/{id}/contact-information/{contact_id}".format(
                            id=id, contact_id=contact_id
                        )
                    },
                    "phoneNumber": "01234123123",
                    "postcode": "A11 1AA",
                    "website": "https://www.mre.company"
                }
            ],
            "description": "I'm a supplier.",
            "dunsNumber": "123456789",
            "id": id,
            "links": {
                "self": "http://localhost:5000/suppliers/{id}".format(id=id)
            },
            "name": "My Little Company",
            "organisationSize": "micro",
            "registeredName": "My Little Registered Company",
            "registrationCountry": "country:GB",
            "service_counts": {
                "G-Cloud 9": 109,
                "G-Cloud 8": 108,
                "G-Cloud 7": 107,
                "G-Cloud 6": 106,
                "G-Cloud 5": 105,
            },
            "tradingStatus": "limited company",
            "vatNumber": "111222333"
        }
    }

    if other_company_registration_number:
        data['suppliers']['otherCompanyRegistrationNumber'] = other_company_registration_number
        # We allow one or other of these registration numbers, but not both
        del data['suppliers']['companiesHouseNumber']
        # Companies without a Companies House number aren't necessarily overseas, but they might well be
        data['suppliers']['registrationCountry'] = 'country:NZ'

    return data
