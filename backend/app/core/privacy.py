"""Best-effort checks for obvious identifiers in development text fields.

Pattern checks are not a de-identification guarantee. They supplement, and do
not replace, the requirement to use synthetic or approved de-identified data.
"""

import re


OBVIOUS_IDENTIFIER_PATTERN = re.compile(
    r"(?:\b[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}\b|(?:\+?\d[\d .()-]{7,}\d))"
)


def reject_obvious_identifiers(value: str | None) -> str | None:
    if value is not None and OBVIOUS_IDENTIFIER_PATTERN.search(value):
        raise ValueError(
            "Do not include names, email addresses, or phone numbers; "
            "use synthetic or de-identified information."
        )
    return value
