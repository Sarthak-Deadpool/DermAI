# DermAI frontend

React and JavaScript application for the existing DermAI API. The interface uses Tailwind CSS 4 and a warm, restrained visual language with a responsive role-aware workspace.

## Local setup

Run the backend on `http://localhost:8000` with its database configured. The backend's default development CORS origin is `http://localhost:5173`.

```powershell
cd frontend
Copy-Item .env.example .env
npm install
npm run dev
```

Open `http://localhost:5173`. If the backend uses another origin, set `VITE_API_BASE_URL` in `.env` and add the frontend's exact origin to `CORS_DEVELOPMENT_ORIGINS` in the backend environment. The app uses credentialed, server-managed session cookies and the backend CSRF token flow; keep the UI and API on a compatible same-site configuration.

## Included workflows

- User registration (backend creates general-user accounts only), sign in/out, account profile, and active session revocation.
- Role-specific navigation and dashboards for user, clinician, researcher, data scientist, and administrator roles.
- Patient profile for general users; clinician patient directory, create/edit/archive, and patient detail.
- Case creation and owner-scoped case list/detail with actual events, images, and clinical notes where the backend allows note creation.
- JPEG/PNG image intake from gallery, drag/drop, browser live camera (`getUserMedia`), and mobile camera capture input. The client checks configured default size/dimensions; backend validation remains authoritative.
- Authenticated image retrieval and on-demand preprocessing details and preview.
- Administrator user/role controls and paginated audit events.

## API limitations represented in the UI

The current backend has no inference/prediction, image-quality scoring, lesion segmentation, attention map, risk assessment, report export, notification, researcher analytics, dataset, or model registry endpoints. The interface shows these as unavailable and never inserts sample clinical/model output.

The frontend defaults to the backend's documented upload defaults (10 MiB, 100 px minimum side, 25 megapixels). These server settings are configurable and are not exposed through a public configuration endpoint, so the server remains authoritative and may reject uploads that do not match its deployment settings.

## Scripts

- `npm run dev` — development server
- `npm run lint` — ESLint
- `npm run build` — production bundle
- `npm run preview` — serve the production bundle locally
