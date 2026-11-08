from tests.evals.evals_cases.evals_case_rag_agent import EvalsCaseRagAgent


EVALS_DOCUMENTS_RAG_AGENT: dict[str, str] = {
    "Operations Runbook": (
        "# Operations Runbook\n\n## Error codes\n"
        "Error E1042 means the service could not read the RDS secret from Secrets Manager. It almost always "
        "follows a secret rotation. Fix it by checking that the task role still has "
        "secretsmanager:GetSecretValue on the new secret version, then restart the service.\n\n"
        "Error E2001 means the message queue is full. Scale the consumers up before draining the "
        "dead-letter queue.\n\n## Backups\n"
        "Database backups run every night at 02:00 UTC. Backups are kept for 35 days and then deleted "
        "automatically. Application logs are kept for 14 days.\n\n## Deployments\n"
        "Every deployment goes through the staging cluster first and needs one approval. Deployments are "
        "frozen on Fridays after 15:00."
    ),
    "Employee Handbook": (
        "# Employee Handbook\n\n## Leave\n"
        "Every employee has 25 days of paid annual leave per calendar year. Up to 5 unused days can be "
        "carried over to the next year. Sick leave is separate: 10 paid days per year, with a doctor's "
        "note needed from the third day.\n\n## Office\n"
        "The office is open from 08:00 to 20:00 on weekdays. The Wi-Fi network for guests is called "
        "Vela-Guest.\n\n## Equipment\n"
        "Laptops are replaced every three years. Lost equipment must be reported to IT within 24 hours."
    ),
    "ACME-7 Sensor Manual": (
        "# ACME-7 Sensor Manual\n\n"
        "The ACME-7 measures humidity and temperature in the server room and reports every 60 seconds.\n\n"
        "## Calibration\n"
        "The ACME-7 must be calibrated every six months with the ACME calibration kit. A sensor that "
        "drifts by more than 3 percent between calibrations must be replaced.\n\n## Battery\n"
        "The battery lasts about two years. Replace it when the status light blinks red."
    ),
}

EVALS_CASES_RAG_AGENT: list[EvalsCaseRagAgent] = [
    EvalsCaseRagAgent(
        id = "error_code",
        question = "What does error E1042 mean and how do I fix it?",
        facts = (r"secret", r"GetSecretValue|role|permission"),
        answerable = True,
        language = "en"
    ),
    EvalsCaseRagAgent(
        id = "bulgarian_over_english",
        question = "Колко дни платен годишен отпуск има всеки служител?",
        facts = (r"\b25\b",),
        answerable = True,
        language = "bg"
    ),
    EvalsCaseRagAgent(
        id = "follow_up",
        question = "How often must it be calibrated?",
        facts = (r"six months|6 months",),
        answerable = True,
        language = "en",
        history = (("What does the ACME-7 sensor measure?", "The ACME-7 measures humidity and temperature in the server room [1]."),)
    ),
    EvalsCaseRagAgent(
        id = "two_facts",
        question = "When do database backups run and how long are they kept?",
        facts = (r"02:00|2:00|2 ?a\.?m", r"35 days|35-day"),
        answerable = True,
        language = "en"
    ),
    EvalsCaseRagAgent(
        id = "unanswerable",
        question = "What is the CEO's annual salary?",
        facts = (),
        answerable = False,
        language = "en"
    ),
    EvalsCaseRagAgent(
        id = "unanswerable_in_bulgarian",
        question = "Кога е следващото тиймбилдинг парти на фирмата?",
        facts = (),
        answerable = False,
        language = "bg"
    ),
]
