# DermAI frontend rebuild

## Stack and design

- React with JavaScript (no TypeScript), Vite, Tailwind CSS 4, React Router, Axios, and Lucide icons.
- Warm off-white surfaces, muted charcoal typography, restrained terracotta accents, serif display headings, responsive sidebar, and compact data tables.
- Shared API service and authentication context; UI authorization follows the authenticated role, while backend authorization remains authoritative.

## Role workspaces

| Role | Implemented UI | Backend dependency/status |
|---|---|---|
| General user / patient | Overview, own patient profile, case list/create/detail, image upload and preprocessing review | Connected to `/auth`, `/api/v1/patients/me`, `/api/v1/cases`, and image endpoints |
| Clinician | Overview, patient directory/detail, case management, notes, image intake and preprocessing review | Connected to clinician-scoped patient routes and owner-scoped case/image routes |
| Researcher | Role-specific overview and account/session settings | Research datasets, cohort analytics, and exports are not available in backend |
| Data scientist / ML engineer | Role-specific model workspace overview and account/session settings | Model registry, training history, evaluation, and inference monitoring are not available in backend |
| Administrator | Overview, account role/active management, audit log, account/session settings | Connected to `/auth/admin/users` and `/auth/admin/audit` |

## Implemented flows

- Cookie session authentication with `withCredentials`; CSRF token bootstrap through `/auth/csrf` and `X-CSRF-Token` on unsafe methods.
- Role-aware protected routes and side navigation; registration follows the backend contract and creates a general-user account only.
- Patient create/read/update/archive (clinician), own profile lifecycle (general user), case create/list/detail, events, and clinician/admin notes.
- Image upload through gallery, drag/drop, `getUserMedia` live camera, or mobile camera capture. The client checks JPEG/PNG, default configured size, minimum side, and pixel limit; server validation remains final.
- Original image retrieval and stateless preprocessing report via the existing image endpoints. The UI distinguishes preprocessing previews from inference or clinical findings.
- Account profile and session listing/revocation; administrator access changes and audit event pagination.

## Backend capabilities still required

No prediction/inference, quality assessment, segmentation, attention maps, risk classification, report generation, notifications, researcher analytics, dataset management, or model management APIs exist in the inspected backend. Those screens are therefore not represented as working features. Clinical result displays, confidence figures, heat maps, and model performance charts are intentionally absent.

The API does not publish configured upload limits. UI preflight checks use current documented defaults and can be adjusted per deployment; the backend remains authoritative.

## Verification

- `npm run lint` — passed.
- `npm run build` — passed.
- Automated tests were not added or run during this rebuild.
