# SCOTT AI Interview Setup

The interview practice flow works in offline practice mode without an AI key. To enable model-generated opening/follow-up questions, answer evaluation, and a final report:

1. Create or edit `backend/.env` (the same directory as `manage.py`).
2. Add:

   ```dotenv
   OPENAI_API_KEY=your_private_api_key
   OPENAI_MODEL=gpt-4o-mini
   OPENAI_TIMEOUT_SECONDS=20
   ```

3. Restart Django. Do not add this key to the React `.env` or any `VITE_` variable. The browser must never receive the permanent API key.
4. Run migrations after applying this backend update:

   ```bash
   python manage.py migrate
   ```

5. Sign in as a student, open Interviews, configure a session, then click **Start practice session**. Submit an answer to receive feedback and the next question. Finish the round to generate the saved report.

The AI service sends interview context and student-entered answers to the configured OpenAI API. Only enable it in accordance with your organization's privacy requirements. Company-named interviews are practice simulations, not official or guaranteed interview questions. AI scores are learning indicators, not validated hiring predictions. If the key is absent or the provider is temporarily unavailable, the workflow uses clearly labelled offline fallback prompts and heuristic feedback; this fallback does not fact-check technical correctness.
