import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from django.conf import settings
from django.db import transaction

from core.notifications import create_notification
from gamification.services import award_xp
from .models import Problem, Submission, SubmissionResult, TestCase

MAX_CODE_LENGTH = 20000
MAX_TEST_CASES = 20
TIMEOUT_SECONDS = 2.5


def _limits():
    def preexec():
        try:
            import resource
            resource.setrlimit(resource.RLIMIT_CPU, (3, 3))
            memory = 256 * 1024 * 1024
            resource.setrlimit(resource.RLIMIT_AS, (memory, memory))
            resource.setrlimit(resource.RLIMIT_FSIZE, (2 * 1024 * 1024, 2 * 1024 * 1024))
            resource.setrlimit(resource.RLIMIT_NPROC, (20, 20))
        except Exception:
            pass
    return None if os.name == "nt" else preexec


def _command(language, workdir):
    if language == "PYTHON":
        return [sys.executable, "-I", "-S", "main.py"], "main.py"
    if language == "JAVASCRIPT":
        node = shutil.which("node")
        return ([node, "main.js"], "main.js") if node else (None, "main.js")
    if language == "JAVA":
        javac = shutil.which("javac"); java = shutil.which("java")
        if not javac or not java: return None, "Main.java"
        compile_result = subprocess.run([javac, "Main.java"], cwd=workdir, capture_output=True, text=True, timeout=10)
        if compile_result.returncode != 0:
            return ("COMPILE_ERROR", compile_result.stderr[-4000:]), "Main.java"
        return [java, "-cp", workdir, "Main"], "Main.java"
    if language in {"C", "CPP"}:
        compiler = shutil.which("gcc" if language == "C" else "g++") or shutil.which("clang" if language == "C" else "clang++")
        if not compiler: return None, "main.c" if language == "C" else "main.cpp"
        source = "main.c" if language == "C" else "main.cpp"
        exe = "main.exe" if os.name == "nt" else "main.out"
        result = subprocess.run([compiler, source, "-O2", "-o", exe], cwd=workdir, capture_output=True, text=True, timeout=10)
        if result.returncode != 0:
            return ("COMPILE_ERROR", result.stderr[-4000:]), source
        return [str(Path(workdir) / exe)], source
    return None, "main.txt"


def _write_source(workdir, language, code):
    filenames = {"PYTHON": "main.py", "JAVASCRIPT": "main.js", "JAVA": "Main.java", "C": "main.c", "CPP": "main.cpp"}
    filename = filenames[language]
    Path(workdir, filename).write_text(code, encoding="utf-8")


def run_code(language, source_code, test_cases):
    if not getattr(settings, "CODE_EXECUTION_ENABLED", True):
        return "ERROR", "Code execution is disabled by server configuration.", []
    if len(source_code) > MAX_CODE_LENGTH:
        return "ERROR", "Source code exceeds the maximum allowed size.", []
    if len(test_cases) > MAX_TEST_CASES:
        return "ERROR", "This problem has too many test cases for the configured runner.", []
    results = []
    with tempfile.TemporaryDirectory(prefix="skelo-run-") as workdir:
        _write_source(workdir, language, source_code)
        command, filename = _command(language, workdir)
        if isinstance(command, tuple):
            return command[0], command[1], []
        if not command:
            return "ERROR", f"No runtime/compiler is configured for {language}.", []
        for tc in test_cases:
            started = time.perf_counter()
            try:
                proc = subprocess.run(
                    command,
                    cwd=workdir,
                    input=tc.input_data,
                    capture_output=True,
                    text=True,
                    timeout=TIMEOUT_SECONDS,
                    preexec_fn=_limits(),
                )
            except subprocess.TimeoutExpired:
                results.append({"test_case": tc, "passed": False, "actual_output": "", "runtime_ms": int((time.perf_counter()-started)*1000), "error_message": "Time limit exceeded."})
                return "TIME_LIMIT", "Execution timed out.", results
            runtime = int((time.perf_counter() - started) * 1000)
            actual = (proc.stdout or "").strip()
            expected = (tc.expected_output or "").strip()
            if proc.returncode != 0:
                results.append({"test_case": tc, "passed": False, "actual_output": actual, "runtime_ms": runtime, "error_message": (proc.stderr or "Runtime error.")[-4000:]})
                return "RUNTIME_ERROR", (proc.stderr or "Runtime error.")[-4000:], results
            passed = actual == expected
            results.append({"test_case": tc, "passed": passed, "actual_output": actual, "runtime_ms": runtime, "error_message": ""})
        return ("ACCEPTED" if all(r["passed"] for r in results) else "WRONG_ANSWER"), "", results


@transaction.atomic
def evaluate_submission(student, problem, language, source_code):
    submission = Submission.objects.create(
        student=student,
        problem=problem,
        language=language,
        source_code=source_code,
        total_test_cases=problem.test_cases.count(),
        status="PENDING",
    )
    test_cases = list(problem.test_cases.all())[:MAX_TEST_CASES]
    status, error, results = run_code(language, source_code, test_cases)
    submission.status = status
    submission.error_message = error
    submission.passed_test_cases = sum(1 for x in results if x["passed"])
    submission.total_test_cases = len(test_cases)
    submission.runtime_ms = max([x["runtime_ms"] for x in results], default=0)
    submission.save(update_fields=["status", "error_message", "passed_test_cases", "total_test_cases", "runtime_ms"])
    SubmissionResult.objects.bulk_create([
        SubmissionResult(submission=submission, test_case=r["test_case"], passed=r["passed"], actual_output=r["actual_output"], runtime_ms=r["runtime_ms"], error_message=r["error_message"])
        for r in results
    ])
    if status == "ACCEPTED":
        award_xp(student, "PROBLEM", problem.points, f"Solved coding problem: {problem.title}", source_key=f"problem:{problem.id}")
        create_notification(student.user, "Problem accepted", f"Your solution for {problem.title} passed all tests.", "SYSTEM")
    return submission
