# Synthetic example outputs

Everything in this folder is **invented**. "Example Dental Cloud" is not a real product, and every path, owner and finding is fictional. The files show what HIPAA Guardian produces; they are not a real assessment.

| File | What it is |
|---|---|
| [`assessment.json`](assessment.json) | The evidence matrix: 75 controls, 4 confirmed gaps, 3 verified, 1 not applicable, the rest awaiting evidence |
| [`HIPAA-READINESS.pdf`](HIPAA-READINESS.pdf) | Full PDF report (`render_report.py --pdf`) |
| [`HIPAA-READINESS.md`](HIPAA-READINESS.md) | The same report in Markdown |
| [`risk-register.csv`](risk-register.csv) | Owner-oriented backlog |
| [`tasks-jira.csv`](tasks-jira.csv) | Jira CSV import |
| [`tasks-notion.csv`](tasks-notion.csv) | Notion database import |
| [`tasks-slack-list.csv`](tasks-slack-list.csv) | Slack Lists import |
| [`tasks-slack.txt`](tasks-slack.txt) | Slack message to paste |
| [`tasks.md`](tasks.md) | Markdown checklist |

Regenerate after changing the scripts:

```bash
python3 docs/example/make_example.py
```

Real assessments belong in a private, git-ignored folder such as `hipaa-output/`, never in a public repository.
