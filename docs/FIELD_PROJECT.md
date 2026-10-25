# Proposed first field project: Water Point Condition Check

Update, 25 October 2026: this direction was approved and implemented locally.
Project 3 is the empty collection project; project 4 is a separate synthetic
pilot. The current validated, Collect-tested form version is **2026102502**,
with an explicit primary-instance namespace. Use
`outputs/01a169aa-cee9-7832-9577-4d6d6d6607ba/water-point-condition-v2.xlsx`
and `forms/water-point-condition/water-point-condition-v2.xml`.
Both original version-1 files below remain unchanged as historical sources.
The monitor is implemented for reviewed uploads and sealed inbox exports.
See [CONTINUOUS_CHECKS.md](CONTINUOUS_CHECKS.md) for actual evidence and limits.

## Original draft brief (retained history)

Draft prepared on 25 October 2026. This is a proposed operational form, with no
invented visits, respondents, locations or field results. It has not been
published or installed in Collect. Existing Central projects, recovery targets
and sponsor-publication restrictions are unchanged.

## Purpose

Record the condition of a tap, borehole or other water point during one visit.
The coordinator needs a complete server copy of every submitted visit, including
all problem observations and their photos. The form records observed operating
condition; it does not establish drinking-water quality.

This is a useful first project for LastCopy because a visit can contain several
different observations, each with its own attachment. Losing one repeated answer
or one photo matters even if the total number of visits looks correct. No real
organization, community partnership or existing campaign is claimed.

## The form

| Information | Required? | Purpose |
| --- | --- | --- |
| Site code | Yes | Stable site identity. Stored as text to preserve leading zeros. |
| Site name or landmark | Yes | Help the coordinator recognize the place. |
| Visit date | Yes | Identify when the inspection happened. |
| GPS location | No | Locate the site when GPS is available. |
| Working status | Yes | Working, working with a problem, not working, or could not check. |
| Overview photo | No | Show the water point. |
| Problems observed | Yes | Yes/no determines whether problem entries are shown. |
| Repeated problem entry | When entered | Problem type, urgency and description are required per entry. Each entry can have its own photo. |
| Suggested follow-up | No | Describe a useful next visit or repair action. |
| Start/end timestamps and instance ID | Automatic | Collect metadata. Completion still comes from explicit collector/export metadata. |

The form asks for no respondent names, telephone numbers or voice recordings.
Image hints ask the collector to avoid including people. No photos or other
third-party media are packaged.

Editable XLSForm:
`outputs/01a169aa-cee9-7832-9577-4d6d6d6607ba/water-point-condition.xlsx`

Converted original XForm:
`forms/water-point-condition/water-point-condition.xml`

Form ID: `lastcopy_water_point_v1`. Version: `2026102501`.

## Intended first workflow

1. Configure a separate collection project after confirming this project scope.
2. Install its form in the existing Android emulator for a clearly labelled
   test. Do not describe an emulator entry as an actual site inspection.
3. Complete a visit with multiple problem entries and permitted test media.
4. Retain a device snapshot with trustworthy completion metadata.
5. Sync to Central and fetch fresh original XML, version metadata and media.
6. Run LastCopy's unchanged comparator and inspect every retained answer/file.

No completed step is implied by this plan. This follow-up only authored and
validated the form. A real campaign requires actual collectors and visits.

## Continuous checking boundary

For automatic checks, define a device-export inbox and expected-device roster.
Accept a new export only after it is completely transferred and validated, hash
and register it immutably, then queue a bounded comparison against a fresh scoped
server capture. Show the source capture time and any missing devices. Reconnects
must not duplicate finished work. Offline devices cannot be observed before their
evidence arrives. This watcher is a proposed next implementation, not an existing
feature or automatic recovery authorization.

Current assisted publication remains synthetic-only. Recovery Apply remains
reviewed and restricted to the configured dedicated synthetic test target. A
separate production read configuration is still needed before using private
field records. Do not weaken those guards to make this form appear connected.

## Validation and references

The XLSForm has `survey`, `choices` and `settings` worksheets. It was converted
with the already-installed Central pyxform service, with validation enabled, and
completed without errors. Its two advisories recommend max-pixels image settings;
no resizing policy has been imposed in this draft. Each worksheet was visually
reviewed. Collect rendering, real submissions and continuous monitoring have not
been tested with this new form. See the hash/validation receipt in
`verification/water-point-form-20261025.json`.

Sources checked on 25 October 2026:

- [ODK form design](https://docs.getodk.org/form-design-intro/)
- [Official question types](https://docs.getodk.org/form-question-types/)
- [ODK XForms specification](https://getodk.github.io/xforms-spec/)

The project topic and question wording are original proposed content, not an
existing organization's questionnaire or evidence of a community partnership.
