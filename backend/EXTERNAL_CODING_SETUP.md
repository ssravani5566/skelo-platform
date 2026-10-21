# SCOTT External Coding Catalog

SCOTT Coding Arena can display **real coding-question metadata** from external platforms while sending the student to the original website for the actual problem statement, editor, execution and submission.

## Student experience

1. Open **Coding Arena**.
2. Search/filter by platform, difficulty, solved state or question number.
3. Click the question title or **Solve**.
4. SCOTT opens the official question URL in a new tab.
5. Solve and submit on the original platform.
6. Return to SCOTT and use **Solved / To do** to track local practice progress.

The local Solved checkbox is SCOTT's own progress record. It does **not** claim that SCOTT can read the student's private accepted-submission state from another platform.

## Live catalog sync

Faculty/Admin can open **Management → External Coding** and use **Sync live** for:

- LeetCode
- HackerRank
- CodeChef
- Codeforces

GeeksforGeeks remains manual-link based because this build does not depend on an undocumented live catalog endpoint for it.

The same sync can be run from the backend command line:

```powershell
python manage.py sync_external_problems --platform LEETCODE --limit 5000
python manage.py sync_external_problems --platform HACKERRANK --limit 1000
python manage.py sync_external_problems --platform CODECHEF --limit 5000
python manage.py sync_external_problems --platform CODEFORCES --limit 5000

# Or sync all live catalogs in one command
python manage.py sync_external_problems --platform ALL --limit 5000
```

The sync saves only metadata such as title, difficulty, platform ID/number, public acceptance or success rate when available, topics, and the official URL. It does not copy complete third-party problem statements or hidden test cases into SCOTT.

## Platform notes

LeetCode's problemset is the source of the question metadata used for its catalog. The current implementation uses its public problemset GraphQL data when available and expects the site to remain reachable from the Django server.

HackerRank exposes coding challenges through its public practice domains; enterprise HackerRank for Work APIs are separately authenticated and should only be connected server-side with authorized credentials.

CodeChef provides a public Practice catalog.

Codeforces exposes an official `problemset.problems` API, which is used by the sync service.

## Security

- Only Faculty/Admin can sync or manually add external questions.
- The backend validates the selected platform against its approved HTTPS hostnames.
- Student code is never submitted to SCOTT for an external problem.
- External progress belongs only to the logged-in student.
- Third-party problem statements and hidden tests are not copied into SCOTT by this feature.
