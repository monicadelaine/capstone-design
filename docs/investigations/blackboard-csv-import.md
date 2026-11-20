# Blackboard Roster CSV Import (PBI-06, #66)

**Date:** 2026-11-14 · **Author:** Jayden White · **Related:** #66 (PBI-06), ADR-002, `v1-reference.md` section 2
**Question:** The Django admin already has a student import that maps the Blackboard columns. Does it meet #66's four criteria (columns, re-import by CWID, bad rows reported with good rows kept, admin only), and what has to change?
**Answer:** Only the column mapping works as shipped. Three small changes in `StudentResource` (match on CWID, turn on model validation, normalize emails and headers) fix re-import and bad-row reporting. One setting, `IMPORT_EXPORT_IMPORT_PERMISSION_CODE = 'add'`, fixes the admin-only criterion, and the gap it closes is larger than #66: every import page in the admin is open to any staff login. Keeping the good rows when some rows are bad needs a design choice (see "Partial import").
**Status:** Every behaviour below was run on the dev stack with django-import-export 4.4.3, inside transactions that were rolled back. **No real Blackboard export is available** (none is in the repository, and a search for the column names found nothing), so file-format assumptions come from #66 and the v1 column mapping. Items marked **TODO** need the instructor or a real file.

## What exists today

| Area | Finding | Where |
|---|---|---|
| Resource | `StudentResource` maps the eight columns (`EMAIL`, `FIRST_NAME`, `MIDDLE_NAME`, `LAST_NAME`, `PREF_NAME`, `CWID`, `STU_CLASS_CODE`, `MAJR_1_CODE`) and converts class names (Freshman to Graduate) to codes. It sets no `import_id_fields`, does no model validation and does not clean emails. | `backend/user/resources.py` |
| Admin | `StudentAdmin` is an `ImportExportModelAdmin`, so the import button exists. The import permission is the library default. | `backend/user/admin.py` |
| Model | `cwid` is unique and must be 8 digits; `email` is **not** unique; `major_code` holds at most 3 characters; `class_code` has fixed choices. | `backend/user/models.py` |
| Login | A student is recognized by an exact match of the Auth0 email against `Student.email` (ADR-002). A student who is not in the table sees "not registered". | `backend/user/views.py` |
| Tests, docs | No tests for the import and no instructor documentation of it. | `backend/user/tests`, `docs/user-guide` |
| Roster vs semester | The Student table has no link to a semester, so students from earlier semesters stay in it. | `backend/user/models.py` |

## What was tested

"Current" is the code as it is today. "Proposed" adds to `StudentResource.Meta`: `import_id_fields = ('cwid',)`, `clean_model_instances = True`, `skip_unchanged = True`, `report_skipped = True`.

| Scenario | Current | Proposed |
|---|---|---|
| Valid 2-row file | 2 created, class names mapped to codes | same |
| Same file imported again, one last name changed | Every row fails with a duplicate-CWID database error; nothing updates | 1 updated, 1 skipped, no duplicates. A third unchanged import skips both rows. |
| 7-row file, 5 bad rows (`12AB` and a 9-digit CWID, an email of `notanemail`, class "Super Senior", major `COMP`) | Four bad values are saved without complaint; only the 9-digit CWID fails, and that failure rolls back the whole import, so 0 rows land | All 5 reported with the reason and row number (for example "CWID must be exactly 8 digits", "Value 'Super Senior' is not a valid choice", "at most 3 characters"); the 2 good rows land |
| CWID column missing | A student with a blank CWID is created, then the next row fails | Nothing created, but each row says only "This field cannot be blank"; the message never names the missing column |
| Same email with a different CWID | A second Student with that email is created | Same: a second Student with that email is created |
| Email `Ann.Lee@CRIMSON.UA.EDU ` | Stored exactly as given (capitals and trailing space); the exact-match login lookup for the lowercase Auth0 email finds nothing | not tested with the proposed options |

Row numbers count data rows only: the header is not row 1.

**File format** (uploaded through the real admin page). "Before" is the first run for this investigation; "Now" was re-run after the `StudentResource` and admin changes on this branch, with the confirmed import checked in the database.

| File | Before | Now |
|---|---|---|
| Plain UTF-8, UTF-8 with BOM (Excel "CSV UTF-8"), CRLF line endings, blank lines at the end, a quoted comma in a name | read correctly | read correctly, and the stored values are right (`Test, Jr.` stays one name) |
| Header names with spaces around them, or in lower case | The preview showed one "New" row with every value blank and still offered **Confirm**. Confirming created a Student with a blank CWID, email and name. | Headers are cleaned before they are matched, so both variants import correctly. Tests: `test_header_case_spacing_and_a_byte_order_mark_are_tolerated`; manual file `06-header-variants.csv`. |
| UTF-8 file with accented names (José, Zoë) | not tested | imports, and the characters are stored correctly. Tests: `test_the_same_names_saved_as_utf8_import_correctly`; manual file `07a-accents-utf8.csv`. |
| Windows-1252 file with one accented name (what Excel's plain "CSV (Comma delimited)" saves on Windows) | Refused with only "'UnicodeDecodeError' encountered while trying to read file. Ensure you have chosen the correct format for the file." | **Still refused**, with no Confirm and nothing imported, but the message now says the file is not saved as UTF-8 and how to save it as "CSV UTF-8 (Comma delimited)". Reading Windows-1252 files is not implemented (see Options, Encoding). Other read failures keep the library's message. Tests: `TestFileEncodingMessage`; manual file `07b-accents-windows-1252.csv`. The admin still decodes uploads with a fixed `from_encoding = "utf-8-sig"`. |

**Permissions:**

| Test | Result |
|---|---|
| Import page of all eight import-enabled admins (Assignment, Attachment, Feedback, Preference, Project, Semester, Sponsor, Student) for a staff account with **no permissions** | 200 for every one |
| That account uploads a roster and confirms it | A Student row is created |
| With `IMPORT_EXPORT_IMPORT_PERMISSION_CODE = 'add'` (Student import): no permissions, view only, add plus view, superuser | 403, 403, 200, 200 |

The library's `has_import_permission` returns True when the setting is unset (checked in its source), and the setting is read by every import admin.

**The admin preview with validation on:** it names the bad row and the reason, writes nothing during the preview, and **does not offer Confirm** when any row is invalid. The gate is in the admin's `import_action` (`not result.has_errors() and not result.has_validation_errors()`). With validation errors alone the resource itself keeps the good rows, because `rollback_on_validation_errors` defaults to False; a database error rolls everything back.

## Options

Status as of this branch: what was built, and in which commit, is marked **Done**.

**Matching and validation. Done (`7fb1d7c`).** The four `Meta` options above. Matching on CWID makes re-import safe and repeatable, which also makes it cheap to fix a bad file and upload it again. Matching on CWID means a CWID repeated within one file would silently overwrite the earlier row, so a repeat is reported as a row error instead.

**Partial import ("good rows still import").**
- **A. All-or-nothing in the admin, no custom code.** Not chosen: it does not meet the letter of #66.
- **B. Offer Confirm when only validation errors remain. Done (`e3b95d0`).** `StudentAdmin.import_action` adds the confirm form when the only problems are invalid rows (not database errors, which roll everything back) and at least one row would be created or updated, with a warning that names the rows that will be skipped (shortened after ten). After the import a second warning lists them, so the instructor knows what to correct; the corrected file can be imported whole, because rows already imported are skipped as unchanged. Confirm is still withheld when every row is bad, when nothing would change, and for hard errors such as a missing column. Tested through the real admin pages (`TestPartialImportThroughTheAdmin`). It relies on library internals (version pinned at 4.4.3).
- **C. Skip the preview** (`IMPORT_EXPORT_SKIP_ADMIN_CONFIRM`). Not used: the instructor would lose the chance to look first.

**Permission.**
- **Override `has_import_permission` on `StudentAdmin`. Done (`e83f873`).** Importing needs both the add and the change permission on Student. One override covers the upload page, the confirm step and the Import button, and a confirm step replayed by an account without the permission is refused. Tested (`TestImportPermission`).
- **Setting `IMPORT_EXPORT_IMPORT_PERMISSION_CODE = 'add'`. Not applied.** It would close all eight import pages with one line (tested on the Student import), but it also changes the other seven, which is beyond #66. Those seven (Assignment, Attachment, Feedback, Preference, Project, Semester, Sponsor) are still open to a staff account with no permissions. **Open:** decide whether to set it.

**Encoding.**
- **A clearer error message. Done (`e3b95d0`).** A file that is not UTF-8 is refused with a message saying so and how to save it as "CSV UTF-8 (Comma delimited)". Every other read failure keeps the library's message. Tested (`TestFileEncodingMessage`).
- **"Save as CSV UTF-8" in the instructor documentation. Not written yet.**
- **Fall back to Windows-1252 when UTF-8 fails. Not implemented, and not recommended unless the real roster turns out to be Windows-1252.** It would turn a loud failure into a possible silent one (a Mac Roman file would decode without an error, as the wrong characters), and it cannot recover characters Excel already replaced with `?` when saving.

**Headers and emails. Done (`7fb1d7c`).** `before_import` strips and upper-cases header names (and a leading BOM) and checks that `EMAIL`, `FIRST_NAME`, `LAST_NAME` and `CWID` exist, naming any that are missing; the other four columns may be absent, and an absent column no longer blanks existing values on re-import. `before_import_row` trims every value and lower-cases the email. A row whose email already belongs to a different CWID is reported as an error, not allowed to create a second Student. Email uniqueness as a database constraint is still on the planned list in `development-guide/data-model.md`; the import check is a stopgap, and emails stored before this change are not cleaned up.

## Risks and open questions

- **No real export.** The instructor needs to supply a redacted sample: the exact header names, the values in `STU_CLASS_CODE` (words or codes), the length of the `MAJR_1_CODE` values (anything over 3 characters is rejected), how CWIDs look (a leading zero lost by Excel makes a 7-digit CWID, which is rejected), and the file encoding. **TODO**
- **The roster is not per semester.** An import adds and updates students but never removes them, so last semester's students can still log in and receive the PBI-05 reminder. Whether to mark students inactive, or link them to a semester, is a separate decision.
- **Who is "an admin" for this?** Importing happens in the Django admin, so the instructor needs a staff account with the add permission (ADR-002 says admin is granted only by an existing admin in our database).
- **Library pinned at 4.4.3.** Option B and the encoding fallback rely on its internals.
- The library's docs say validation errors roll the transaction back; on the default admin path of the installed version the valid rows stayed. This document reports what was observed.

## Recommendation

1. **Done (`7fb1d7c`).** In `StudentResource`: the four `Meta` options, header normalization with a clear missing-column error, email strip and lower-case, a row error for an email that belongs to another CWID, and a row error for a CWID repeated in the file.
2. **Done for Student (`e83f873`)** as an override of `has_import_permission`. **Open:** whether to set `IMPORT_EXPORT_IMPORT_PERMISSION_CODE = 'add'` to close the other seven import pages, with a test per admin that a non-admin gets 403.
3. **Done (`e3b95d0`)** as option B. **TODO:** confirm with the instructor that skipping bad rows is what she wants.
4. **Done.** 42 tests in `user/tests/test_resources.py` cover the issue's list (valid file, duplicate CWID, missing column, non-admin 403) plus re-import, bad rows with row numbers, header variants, email normalization, partial import through the real admin pages and the encoding message.
5. **Not done.** A short instructor section in the user guide: save as CSV UTF-8, the expected header names, and how to read the preview and the skipped-rows warnings.
6. **Open.** Get a redacted real export from the instructor and check it against the assumptions in "Risks and open questions". Add the Windows-1252 fallback only if it turns out to be needed.

## Sources

- django-import-export settings (`IMPORT_EXPORT_IMPORT_PERMISSION_CODE`, `IMPORT_EXPORT_USE_TRANSACTIONS`, `IMPORT_EXPORT_SKIP_ADMIN_CONFIRM`): https://django-import-export.readthedocs.io/en/latest/installation.html
- django-import-export 4.4.3 source (installed copy): `admin.py` (`has_import_permission`, `import_action`, `from_encoding`), `resources.py` (`import_data`, `rollback_on_validation_errors`)
- ADR-002: `docs/decisions/ADR-002-auth.md`
- v1 import description: `docs/investigations/v1-reference.md`, section 2

Drafted with Claude Code; Research, testing, validation, and revisions were done by me.
