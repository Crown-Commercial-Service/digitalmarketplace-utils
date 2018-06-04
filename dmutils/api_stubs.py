from datetime import datetime as dt

from .formats import DATETIME_FORMAT


def _derive_framework_family(slug):
    if slug.startswith('g-cloud'):
        return 'g-cloud'
    elif slug.startswith("digital-outcomes-and-specialists"):
        return 'digital-outcomes-and-specialists'
    else:
        return slug


def lot(lot_id=1, slug="some-lot", name=None, allows_brief=False, one_service_limit=False, unit_singular='service',
        unit_plural='services'):
    if not name:
        name = slug.replace("-", " ")
        name = name[:1].upper() + name[1:]

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
              has_direct_award=None,
              has_further_competition=None):
    framework_family = framework_family or _derive_framework_family(slug)

    if slug.startswith('g-cloud'):
        name = name or 'G-Cloud {}'.format(slug.split('-')[-1])
        has_direct_award = has_direct_award if has_direct_award is not None else True
        has_further_competition = has_further_competition if has_further_competition is not None else False

    elif slug.startswith('digital-outcomes-and-specialists'):
        name = name or slug.replace("-", " ").title().replace('And', 'and')
        has_direct_award = has_direct_award if has_direct_award is not None else False
        has_further_competition = has_further_competition if has_further_competition is not None else True

    else:
        name = name or slug.replace("-", " ").title()
        has_direct_award = has_direct_award if has_direct_award is not None else True
        has_further_competition = has_further_competition if has_further_competition is not None else True

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


def supplier_framework(
    agreed_variations=True,
    supplier_id=1234,
    framework_slug='g-cloud-7',
    framework_family=None,
    on_framework=True,
    prefill_declaration_from_slug='g-cloud-6',
    with_declaration=True,
    declaration_status='complete',
    with_agreement=True,
    with_users=True,
):
    framework_family = _derive_framework_family(framework_slug) if not framework_family else framework_family

    data = {
        "frameworkInterest": {
            "agreedVariations": {},
            "agreementDetails": None,
            "agreementId": None,
            "agreementPath": None,
            "agreementReturned": False,
            "agreementReturnedAt": None,
            "agreementStatus": None,
            "countersigned": False,
            "countersignedAt": None,
            "countersignedDetails": None,
            "countersignedPath": None,
            "frameworkFramework": framework_family,
            "frameworkSlug": framework_slug,
            "onFramework": on_framework,
            "prefillDeclarationFromFrameworkSlug": prefill_declaration_from_slug,
            "supplierId": supplier_id,
            "supplierName": "My Little Company"
        }
    }
    if agreed_variations:
        data['frameworkInterest']['agreedVariations'].update({
            "1": {
                "agreedAt": "2018-05-04T16:58:52.362855Z",
                "agreedUserEmail": "stub@example.com",
                "agreedUserId": 123,
                "agreedUserName": "Test user"
            }
        })
    if with_declaration:
        data['frameworkInterest']['declaration'] = {
            "nameOfOrganisation": "My Little Company",
            "organisationSize": "micro",
            "primaryContactEmail": "supplier@example.com",
            "status": declaration_status,
        }
    if with_agreement:
        agreement_data = {
            'agreementId': 9876,
            "agreementReturned": True,
            "agreementReturnedAt": "2017-05-17T14:31:27.118905Z",
            "agreementDetails": {
                "frameworkAgreementVersion": "RM1557ix",
                "signerName": "A. Nonymous",
                "signerRole": "The Boss",
                "uploaderUserId": 123,
            },
            "agreementPath": "not/the/real/path.pdf",
            "countersigned": True,
            "countersignedAt": "2017-06-15T08:41:46.390992Z",
            "countersignedDetails": {
                "approvedByUserId": 123,
            },
            "agreementStatus": "countersigned",
        }
        if with_users:
            agreement_data['agreementDetails'].update({
                "uploaderUserEmail": "stub@example.com",
                "uploaderUserName": "Test user",
            })
            agreement_data['countersignedDetails'].update({
                "approvedByUserEmail": "stub@example.com",
                "approvedByUserName": "Test user",
            })
        data['frameworkInterest'].update(agreement_data)

    return data
