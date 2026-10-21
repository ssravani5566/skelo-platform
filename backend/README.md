# SCOTT Student Platform — Django Backend

This is the live Django REST backend for the SCOTT student learning platform. Feature data is persisted in PostgreSQL (or SQLite for local development) and there is no frontend demo-data fallback.

## Modules

- Authentication: register, JWT login/refresh, logout blacklist, profile, forgot/reset password, email verification
- Students: profile, skills, skill catalog, authorized student directory
- Courses: courses, modules, lessons, course progress, lesson completion
- Coding: published problems, sample tests, submissions, isolated local execution, submission history
- Assessments: published assessments, attempts, answer saving, submission and scoring, faculty/admin question management
- Assignments: published assignments, file/text submission, evaluation and feedback
- Codeathons: events, registration, problems, submissions and live leaderboard
- Interviews: scheduling, questions, answers and feedback
- Attendance: training sessions, student attendance and summary
- Gamification: XP, streaks and badges triggered by verified activities
- Notifications: persistent read/unread state
- Dashboard: live aggregation from persisted activity
- Reports: live formula-based metrics and CSV export
- Search: real cross-module search

## API root

All REST endpoints are under `/api/`.

## Configuration

1. Create a Python virtual environment.
2. Install `requirements.txt`.
3. Copy `.env.example` to `.env` and supply the PostgreSQL and email settings you actually use.
4. Run `python manage.py migrate`.
5. Create an admin account with `python manage.py createsuperuser`.
6. Run `python manage.py runserver`.

For local SQLite verification, set:

```env
DB_ENGINE=django.db.backends.sqlite3
DB_NAME=db.sqlite3
```

Never commit or distribute `.env` containing real credentials. The repository should contain `.env.example` only.

## Frontend connection

Set the React app's `VITE_API_BASE_URL`. During Vite development the included proxy maps `/api` to Django, so `VITE_API_BASE_URL=/api` is recommended.

## Code execution note

The coding service executes submissions in a temporary working directory with size, CPU-time and memory limits where supported by the host OS. For a public multi-tenant deployment, move the runner behind a dedicated container/sandbox boundary with stronger network and process isolation instead of running arbitrary student code in the web host.

## Testing

Run:

```bash
python manage.py check
python manage.py test
```

The integration tests cover registration/profile persistence, course completion and reporting, coding evaluation/XP de-duplication, assessment answer protection and scoring, and assignment evaluation/ownership isolation.


## External coding platforms

The Coding module supports external question records without adding a second database table. External metadata is stored in the existing `Problem.tags` JSON field with a reserved format (`external`, `platform:<KEY>`, `url:<HTTPS URL>`, optional `external_id:<ID>`).

Supported platforms:
- LeetCode
- HackerRank
- CodeChef
- Codeforces
- GeeksforGeeks

Endpoints:
- `GET /api/coding/platforms/` — official platform home links
- `GET /api/coding/problems/?source=external` — published external questions
- `GET /api/coding/problems/?platform=LEETCODE` — filter by platform
- `POST /api/coding/external/` — Faculty/Admin only; add a real external question
- `GET /api/coding/problems/<id>/` — view question details
- `POST /api/coding/problems/<id>/submit/` — local SCOTT problems only; external problems return a clear error directing the student to the original platform

The frontend never sends a student's code to an external platform on the student's behalf. The platform link is opened directly in a new tab, preserving the platform's own login, editor, judging and submission flow.

## External Coding Catalog

Use `Management → External Coding → Sync live` to populate the Coding Arena with real public question metadata from supported platforms. The backend also provides `python manage.py sync_external_problems --platform <PLATFORM> --limit <N>` for controlled imports. Students always solve external questions on the original platform; SCOTT records only their local progress state.

## Coding Arena live catalog

The Coding Arena automatically bootstraps the external question catalog on the first authenticated visit when the requested platform has no imported records. It stores live public metadata and the canonical problem URL in PostgreSQL; it does not create a hardcoded question list. Set `SCOTT_AUTO_SYNC=0` in `.env` to disable this behavior. You can also run `python manage.py sync_external_problems --platform LEETCODE --limit 5000` (and the equivalent platform commands) for an explicit refresh.
