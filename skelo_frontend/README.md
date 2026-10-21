# SCOTT Student Platform — React Frontend

This is the cleaned source for the SCOTT student platform. The application uses real Django REST APIs and does not include hardcoded module datasets or an API-to-demo-data fallback.

## Included workflows

Authentication, dashboard, calendar, profile, courses, coding arena, assessments, assignments, codeathons, interviews, attendance, achievements, notifications, reports, global search, and authorized faculty/admin management.

## Requirements

- Node.js 20+ recommended
- npm
- Django backend running and reachable from the Vite proxy or `VITE_API_BASE_URL`

## Setup

```bash
npm install
npm run dev
```

For a production build:

```bash
npm run build
npm run preview
```

The repository intentionally does **not** include `node_modules`.

## Environment

Copy `.env.example` to `.env` when an explicit API base URL is needed. The recommended development value is:

```env
VITE_API_BASE_URL=/api
```

The included `vite.config.js` listens on `0.0.0.0` and proxies `/api` to the Django server for LAN-friendly development.

## Data behavior

Pages use loading, empty and error states. When the API is unavailable, the UI shows an error instead of substituting demo records. Profile edits, notification reads, lesson completion, assessment attempts, assignment submissions and other actions are persisted through the backend.


## External coding platforms

Coding Arena supports real external question links for LeetCode, HackerRank, CodeChef, Codeforces and GeeksforGeeks.

Faculty/Admin can open **Management → External Coding** and add an authorized question using:
- the original platform URL
- the real question title
- difficulty/topic metadata
- an optional approved question summary

The student sees that question inside SCOTT and can click **Solve on <platform>**. SCOTT opens the canonical URL in a new browser tab. External submissions are intentionally not executed by SCOTT and therefore do not appear in SCOTT's local submission history.

This design keeps platform judging, accounts, rankings and submissions on the platform that owns the problem. Do not paste or reproduce third-party question content unless you are authorized to do so.
