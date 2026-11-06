# SKelo Overview, streak and custom study courses

## Backend update

1. Keep your existing private `.env` file. Add `INITIAL_ADMIN_PASSWORD=Admin@1234` if it is not already present.
2. From the backend folder, run:

   ```bash
   python manage.py migrate
   python manage.py set_admin_password --password "Admin@1234"
   python manage.py check
   ```

   The password command uses Django's `set_password()` method, so the password is stored as a secure Django password hash. It updates the existing `Admin` account (or the first active superuser if the username differs).

3. The Overview page records one streak check-in per local calendar day. XP-awarding actions continue to update the streak too. If a day is missed, the current streak displays as zero and starts again at one on the next check-in; the longest streak is retained.

4. For scheduled in-app study reminders every two days, keep the existing daily Windows Task Scheduler job pointed at:

   ```bash
   python manage.py send_study_reminders
   ```

## Frontend update

From the frontend folder, run:

```bash
npm install
npm run dev
```

The Overview layout uses SKelo's existing dark-purple, lilac and accent palette. Schedule offers a built-in course catalogue plus an open custom-course field. Custom courses are stored on the student's study plan and receive a starter topic roadmap even if the course is not published in the SKelo course library. Existing published courses can still use their own lesson syllabus through the API.
