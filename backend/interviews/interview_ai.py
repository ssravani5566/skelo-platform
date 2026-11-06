"""Server-side AI helpers for SCOTT interview practice.

The OpenAI API key is read only from the backend environment. When it is absent
or the provider is temporarily unavailable, deterministic practice prompts and
clearly-labelled heuristic feedback keep the interview workflow usable.
"""
import json
import logging
import os
import re
import urllib.error
import urllib.request

logger = logging.getLogger(__name__)


def ai_configured():
    return bool(os.getenv("OPENAI_API_KEY", "").strip())


def _openai_json(system_prompt, user_prompt, max_tokens=650):
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        return None
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini").strip() or "gpt-4o-mini"
    body = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt + " Return valid JSON only."},
            {"role": "user", "content": user_prompt},
        ],
        "response_format": {"type": "json_object"},
        "max_tokens": max_tokens,
        "temperature": 0.5,
    }
    request = urllib.request.Request(
        "https://api.openai.com/v1/chat/completions",
        data=json.dumps(body).encode("utf-8"),
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        timeout = max(5, min(45, int(os.getenv("OPENAI_TIMEOUT_SECONDS", "20"))))
        with urllib.request.urlopen(request, timeout=timeout) as response:
            payload = json.loads(response.read().decode("utf-8"))
        content = payload["choices"][0]["message"]["content"]
        if isinstance(content, list):
            content = "".join(part.get("text", "") for part in content if isinstance(part, dict))
        content = str(content or "").strip()
        content = re.sub(r"^```(?:json)?\s*|\s*```$", "", content, flags=re.IGNORECASE)
        parsed = json.loads(content)
        return parsed if isinstance(parsed, dict) else None
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        # Never log the API key, student answer, or complete provider response.
        logger.warning("Interview AI request failed (%s). Falling back to practice mode.", type(exc).__name__)
        return None
    except Exception as exc:  # Keep a transient provider error from breaking an interview.
        logger.warning("Unexpected interview AI error (%s). Falling back to practice mode.", type(exc).__name__)
        return None


QUESTION_BANK = {
    "HR": [
        ("Tell me about yourself and the experience most relevant to this role.", "HR"),
        ("What is one strength you would bring to this team, and how have you demonstrated it?", "Behavioral"),
        ("Tell me about a time you received difficult feedback. What did you do next?", "Behavioral"),
        ("Why are you interested in this role and this company?", "HR"),
        ("Describe a disagreement with a teammate and how you worked through it.", "Behavioral"),
        ("What skill are you actively improving, and how are you practising it?", "HR"),
        ("Tell me about a time you had to meet a challenging deadline.", "Behavioral"),
        ("What questions would you ask the interviewer before deciding whether this role is right for you?", "HR"),
    ],
    "TECHNICAL": [
        ("Explain an important technical concept related to your selected role, using a practical example.", "Technical"),
        ("How would you investigate a bug that you cannot reproduce consistently? Walk me through your approach.", "Technical"),
        ("Describe a trade-off you would consider when choosing a data structure for a feature.", "Technical"),
        ("Which concept from your selected topics is easiest to misunderstand, and how would you explain it to a junior developer?", "Technical"),
        ("How would you test a change before releasing it to users?", "Technical"),
        ("Explain the time and space complexity of a solution you have implemented.", "DSA"),
        ("Tell me about a technical decision you made on a project and what you would do differently now.", "Project"),
        ("If a service became slow after a release, what information would you check first and why?", "Technical"),
    ],
    "SYSTEM_DESIGN": [
        ("Design a URL-shortening service. Describe the main components and data model.", "System Design"),
        ("How would you handle a sudden tenfold increase in traffic to a service?", "System Design"),
        ("How would you design reliable retries without creating duplicate operations?", "System Design"),
        ("What would you monitor in production, and how would those signals help you diagnose failures?", "System Design"),
        ("Describe the trade-offs between a relational database and a document database for this use case.", "System Design"),
        ("How would you protect private user data in the system you designed?", "System Design"),
    ],
    "CODING": [
        ("Talk through your approach before coding a solution for finding the first non-repeating character in a string.", "Coding"),
        ("How would you test edge cases for a function that merges two sorted arrays?", "Coding"),
        ("Explain how you would compare two solutions with different time and space complexity.", "Coding"),
        ("A coding solution passes samples but fails hidden tests. How would you investigate?", "Coding"),
        ("How would you explain your code to an interviewer while implementing it?", "Coding"),
    ],
    "DSA": [
        ("When would you use a hash map instead of sorting and scanning an array? Explain the trade-offs.", "DSA"),
        ("Explain how a stack and a queue differ, and give a practical use case for each.", "DSA"),
        ("How would you detect a cycle in a linked list? Describe the reasoning.", "DSA"),
        ("What is the difference between breadth-first search and depth-first search?", "DSA"),
        ("How would you estimate the time and space complexity of a recursive algorithm?", "DSA"),
    ],
    "BEHAVIORAL": [
        ("Tell me about a time you worked with someone whose approach differed from yours.", "Behavioral"),
        ("Describe a mistake you made and how you changed your process afterward.", "Behavioral"),
        ("How do you decide what to do first when several deadlines conflict?", "Behavioral"),
        ("Tell me about a time you took initiative without being asked.", "Behavioral"),
    ],
    "PROJECT": [
        ("Explain the architecture of a project you have built and why you chose those components.", "Project"),
        ("What was the hardest technical issue in your project and how did you solve it?", "Project"),
        ("If you had another week to improve your project, what would you prioritize and why?", "Project"),
        ("How did you test your project and decide it was ready to demonstrate?", "Project"),
    ],
    "RESUME_BASED": [
        ("Choose one skill or project from the resume context you entered and explain how you used it in practice.", "Resume"),
        ("Which project or achievement best demonstrates your fit for this role? Explain your contribution.", "Resume"),
        ("Pick one technical skill you listed and describe a difficult problem you solved with it.", "Resume"),
    ],
    "COMPANY_SPECIFIC": [
        ("For this company-specific practice simulation, explain how you would approach a role-related problem and justify your choices.", "Company Practice"),
        ("Which part of this role would require the most learning from you, and how would you prepare?", "Company Practice"),
        ("Describe a technical project that demonstrates the skills relevant to this company's selected role.", "Company Practice"),
    ],
    "MIXED": [
        ("Tell me about yourself and one project you are proud of.", "HR / Project"),
        ("Explain a core technical concept relevant to your role and give a real-world example.", "Technical"),
        ("How would you approach a coding problem you have never seen before?", "Coding"),
        ("Describe a teamwork challenge and how you helped resolve it.", "Behavioral"),
        ("Explain how you would debug a SQL query or application that is returning the wrong results.", "Technical"),
        ("What was the hardest trade-off in one of your projects?", "Project"),
        ("How would you explain your solution's time complexity to an interviewer?", "DSA"),
        ("What would you learn or improve first if you joined this team?", "HR"),
    ],
}


def _type_key(interview):
    return interview.interview_type if interview.interview_type in QUESTION_BANK else "MIXED"


def question_limit(interview):
    try:
        minutes = int(interview.duration_minutes or 30)
    except (TypeError, ValueError):
        minutes = 30
    return max(3, min(10, (minutes + 4) // 5))


def make_question(interview, question_number=1, previous_question="", previous_answer="", evaluation=None):
    """Generate an opening/follow-up question, using a safe fallback when needed."""
    topics = (interview.technical_topics or "general role fundamentals").strip()
    if previous_question:
        user_prompt = (
            f"Interview context: company={interview.company}; role={interview.role}; "
            f"type={interview.interview_type}; difficulty={interview.difficulty}; topics={topics}.\n"
            f"Previous question: {previous_question}\nStudent answer: {previous_answer[:6000]}\n"
            f"Evaluation: {json.dumps(evaluation or {}, ensure_ascii=False)[:2500]}\n"
            "Write the next single interview question. React naturally to the answer: if it is vague, ask a useful follow-up; "
            "otherwise move to a related but distinct topic. Do not reveal the answer. Keep it concise. "
            'Return JSON with keys "question_text" and "category".'
        )
    else:
        user_prompt = (
            f"Create the opening question for a practice interview. company={interview.company}; role={interview.role}; "
            f"type={interview.interview_type}; difficulty={interview.difficulty}; topics={topics}. "
            "Make it appropriate for the chosen interview type and difficulty, concise, and conversational. "
            "Company-specific material is a practice simulation, not an official or guaranteed hiring question. "
            'Return JSON with keys "question_text" and "category".'
        )
    result = _openai_json(
        "You are a fair, supportive interview coach. Ask one question at a time. Avoid evaluating appearance, accent, facial expressions, or inferred emotions.",
        user_prompt,
        max_tokens=260,
    )
    if result:
        text = str(result.get("question_text") or "").strip()
        if text and len(text) <= 1400:
            return {"question_text": text, "category": str(result.get("category") or interview.interview_type.title())[:100]}, True
    bank = QUESTION_BANK[_type_key(interview)]
    index = max(0, int(question_number or 1) - 1) % len(bank)
    qtext, category = bank[index]
    if topics and topics.lower() not in {"java, sql, dsa", "general role fundamentals"} and not previous_question and "technical" in category.lower():
        qtext = f"For {topics}, " + qtext[0].lower() + qtext[1:]
    return {"question_text": qtext, "category": category}, False


def _bounded_score(value, default=50):
    try:
        return round(max(0.0, min(100.0, float(value))), 2)
    except (TypeError, ValueError):
        return float(default)


def evaluate_answer(interview, question_text, answer_text):
    topics = (interview.technical_topics or "the role").strip()
    result = _openai_json(
        "You are a careful interview evaluator. Evaluate only the content of the answer against the question. Do not infer confidence, personality, honesty, or hiring success from appearance, accent, or emotion. Be specific, constructive, and appropriately cautious. Return valid JSON.",
        (
            f"Evaluate this practice answer. Interview type={interview.interview_type}; role={interview.role}; "
            f"difficulty={interview.difficulty}; topics={topics}.\nQUESTION: {question_text}\nANSWER: {answer_text[:8000]}\n"
            "Return JSON keys: score (0-100), strengths (short string), missing_concepts (short string), "
            "technical_mistakes (short string), expected_answer (short model answer or rubric), "
            "improvement_advice (specific next action), communication_score (0-100). "
            "Score answer relevance, correctness where assessable, completeness, and reasoning; do not reward length alone."
        ),
        max_tokens=650,
    )
    if result:
        evaluation = {
            "score": _bounded_score(result.get("score")),
            "strengths": str(result.get("strengths") or "The answer was reviewed against the interview question.")[:2000],
            "missing_concepts": str(result.get("missing_concepts") or "No specific missing concept was identified.")[:2000],
            "technical_mistakes": str(result.get("technical_mistakes") or "No specific technical mistake was identified.")[:2000],
            "expected_answer": str(result.get("expected_answer") or "A strong answer should address the question directly and support the explanation with a concrete example.")[:4000],
            "improvement_advice": str(result.get("improvement_advice") or "Practise giving a concise explanation followed by an example.")[:2000],
            "communication_score": _bounded_score(result.get("communication_score"), 60),
            "evaluation_method": "AI feedback; use as a practice indicator, not a validated hiring prediction.",
        }
        return evaluation, True

    word_count = len((answer_text or "").split())
    punctuation_bonus = 8 if any(mark in answer_text for mark in ".!?;:—-" ) else 0
    score = _bounded_score(25 + min(52, word_count * 1.15) + punctuation_bonus, 25)
    evaluation = {
        "score": score,
        "strengths": "You submitted an answer and have a concrete starting point to improve.",
        "missing_concepts": "Review the question and add the key concepts, reasoning, and a practical example that directly support your answer.",
        "technical_mistakes": "Offline fallback mode cannot fact-check technical statements. Configure OPENAI_API_KEY for AI-based content evaluation.",
        "expected_answer": "A strong answer directly addresses the question, explains the reasoning step by step, and uses an accurate example. This is guidance, not a verified model answer.",
        "improvement_advice": "Try a simple structure: direct answer, reasoning, concrete example, and trade-off or conclusion.",
        "communication_score": _bounded_score(30 + min(60, word_count * 1.2) + punctuation_bonus, 30),
        "evaluation_method": "Offline heuristic only; it does not validate answer correctness.",
    }
    return evaluation, False


def make_final_report(interview, answer_rows):
    records = []
    for question, answer in answer_rows:
        try:
            analysis = json.loads(answer.feedback) if answer.feedback else {}
        except (TypeError, json.JSONDecodeError):
            analysis = {}
        records.append({
            "question": question.question_text[:1000],
            "answer": answer.answer_text[:2500],
            "score": _bounded_score(answer.score, 0),
            "analysis": analysis if isinstance(analysis, dict) else {},
        })
    result = _openai_json(
        "You are a constructive interview coach generating a final practice report. Judge answer content only; never score appearance, accent, facial expressions, or inferred emotions. Return valid JSON.",
        (
            f"Generate a final report for a {interview.interview_type} practice interview for role {interview.role} "
            f"at {interview.company}, difficulty={interview.difficulty}, topics={interview.technical_topics}. "
            f"Questions and answer-level reviews: {json.dumps(records, ensure_ascii=False)[:12000]}. "
            "Return JSON keys: technical_score (0-100), communication_score (0-100), confidence_score (0-100), "
            "strengths (short paragraph), improvement_areas (short paragraph), overall_feedback (short paragraph), "
            "next_steps (array of 2-4 concrete actions). Keep scores as practice indicators, not hiring predictions."
        ),
        max_tokens=700,
    )
    if result:
        next_steps = result.get("next_steps", [])
        if not isinstance(next_steps, list):
            next_steps = [str(next_steps)]
        return {
            "technical_score": _bounded_score(result.get("technical_score")),
            "communication_score": _bounded_score(result.get("communication_score")),
            "confidence_score": _bounded_score(result.get("confidence_score")),
            "strengths": str(result.get("strengths") or "Review your answer-level feedback for strengths.")[:3000],
            "improvement_areas": (str(result.get("improvement_areas") or "Review the missing concepts identified in each answer.") + ("\nNext steps: " + "; ".join(str(x) for x in next_steps[:4]) if next_steps else ""))[:4000],
            "overall_feedback": str(result.get("overall_feedback") or "Use this report to guide your next practice attempt.")[:4000],
        }, True

    scores = [row[1].score for row in answer_rows]
    average = round(sum(float(x or 0) for x in scores) / len(scores), 2) if scores else 0
    return {
        "technical_score": average,
        "communication_score": average,
        "confidence_score": average,
        "strengths": "You completed a practice attempt. Review the question-by-question feedback to identify which explanations were clear and complete.",
        "improvement_areas": "The offline fallback cannot reliably judge technical correctness. Add an OpenAI API key to receive AI-generated content feedback and personalized next steps.",
        "overall_feedback": f"Practice score average: {average}/100 across {len(answer_rows)} answered question(s). This is a heuristic practice indicator, not a validated prediction of hiring success.",
    }, False
