# SCOTT Codeathons update

This update is scoped to the Codeathons student pages, the Codeathons tab inside the existing admin Management page, and the Django `codeathons` app. Other student pages, routes, dashboard components, and shared styling files were not intentionally changed.

## Frontend changes
- `src/pages/codeathons/Codeathons.jsx` and `Codeathons.css`: event stats from API records, tabs, search and event type/difficulty/mode filters, responsive event cards, registered state, and empty state.
- `src/pages/codeathons/CodeathonDetail.jsx`: event schedule, registration windows, rules, problems, prizes and registration/withdrawal controls.
- `src/pages/management/CodeathonManager.jsx` and `CodeathonManager.css`: admin event create/edit/publish/unpublish/delete workflow and attaching existing published Coding Arena problems to an event.
- `src/pages/management/Management.jsx`: renders the new manager only for the existing Codeathons admin tab.

## Backend changes
- `backend/codeathons/models.py`: adds event configuration fields for type, category, difficulty, participation type, mode, registration window, venue, instructions and prizes.
- `backend/codeathons/serializers.py`: exposes these fields and derives event status from publication and event/registration timestamps.
- `backend/codeathons/views.py`: enforces registration opening/closing times, event start time, and withdrawal restrictions on the server.
- `backend/codeathons/migrations/0002_codeathon_event_configuration.py`: schema migration for the added fields.

## Apply the update
1. Back up your project and database.
2. Copy the updated frontend and backend files into their matching project locations.
3. From the backend directory, run:
   ```bash
   python manage.py migrate
   python manage.py check
   ```
4. From the frontend directory, install dependencies using your normal project setup, then run your normal Vite development/build command.
5. Log in as an admin, open Admin Management → Codeathons, create an event, attach published Coding Arena problems, and publish it. Student events appear only when published.

## Current scope and production notes
This update builds on the existing codeathon participant/submission/leaderboard models and the existing coding evaluation service. The form captures team participation as event metadata, but it does **not** implement a complete team invitation/membership subsystem, a hackathon project-file submission/revision workflow, judge assignment/rubrics, certificate generation/verification, websocket live updates, or a new isolated code-execution service. Those require additional models, endpoints, workers/infrastructure, and tests before the platform can be described as production-ready. Existing evaluation execution is only as isolated as the current Coding Arena service. Review and harden that service (for example, with a properly isolated Judge0 deployment) before accepting untrusted code in production.

The current backend's admin/faculty permission model is preserved. The new migration must be applied before using the new form fields.
