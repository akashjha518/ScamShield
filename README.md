# ScamShield 🛡️
### Protect Your Freelance Journey. Spot Scams Before They Strike.

ScamShield is an open-source, AI-assisted screening tool that helps freelancers assess suspicious job offers, client messages, and payment requests before responding. It looks for warning signs, shows the evidence behind its assessment, and suggests practical next steps.

> **Important:** ScamShield is a decision-support tool, not a guarantee that a message is safe or fraudulent. Always verify clients and companies independently.

## Contents
- [Why ScamShield?](#why-scamshield)
- [Features](#features)
- [How It Works](#how-it-works)
- [Technology Stack](#technology-stack)
- [Project Structure](#project-structure)
- [Requirements](#requirements)
- [Installation and Setup](#installation-and-setup)
- [Run the Application](#run-the-application)
- [Run the Tests](#run-the-tests)
- [Example Scenarios](#example-scenarios)
- [AI, Privacy, and Limitations](#ai-privacy-and-limitations)
- [Roadmap](#roadmap)
- [Contributing](#contributing)
- [License](#license)

## Why ScamShield?

Freelancers and people starting their careers can encounter fake job offers, upfront registration fees, suspicious payment requests, impersonation, and pressure to share sensitive information. These messages can be difficult to evaluate, especially for people who are new to freelance work.

ScamShield makes the assessment more understandable by surfacing specific warning signs and explaining why they matter, instead of returning only a vague verdict.

## Features

- **Message analysis:** Check pasted freelance job offers, client messages, and payment-related messages.
- **Risk assessment:** Returns a risk level (`LOW`, `MEDIUM`, `HIGH`, or `CRITICAL`) and a numeric score.
- **Evidence-based findings:** Shows detected warning signs, associated evidence, and explanations.
- **Recommended next steps:** Provides practical actions to help users verify a client or avoid a risky transaction.
- **Missing-information checks:** Highlights details that may need verification before proceeding.
- **Local AI explanations:** Can use a local Ollama model to explain already-detected findings in plain language.
- **Web interface:** HTML, CSS, and JavaScript frontend connected to a FastAPI API.
- **Automated tests:** Includes tests for analyzer behavior and API functionality.

## How It Works

1. The user pastes a message into the ScamShield interface.
2. The frontend sends the message to the FastAPI backend.
3. Deterministic analysis rules inspect the message for known warning signs.
4. ScamShield calculates a risk score and assigns a risk level.
5. If local Ollama is configured and available, AI can explain detected findings. It is not intended to create new findings or change the rule-based score.
6. The interface displays the result, evidence, missing information, recommendations, and available AI explanations.

### Risk levels

The current analyzer uses these score thresholds:

| Risk level | Score |
|---|---:|
| `LOW` | 0–9 |
| `MEDIUM` | 10–24 |
| `HIGH` | 25–44 |
| `CRITICAL` | 45–100 |

These are implementation-specific heuristics, not statistically validated fraud probabilities. A score is not a percentage chance that a message is a scam.

## Technology Stack

| Component | Technology |
|---|---|
| Backend API | Python, FastAPI |
| Request/response validation | Pydantic |
| Frontend | HTML, CSS, vanilla JavaScript |
| Local AI integration | Ollama |
| Tested local model | `qwen3:4b-q4_K_M` |
| Automated tests | pytest |

## Project Structure

The exact files in your checkout may evolve. The main components are organized approximately as follows:

```text
ScamShield/
├── backend/
│   ├── app/
│   │   ├── main.py             # FastAPI application and endpoints
│   │   ├── analyzer.py         # Deterministic risk analysis rules
│   │   ├── schemas.py          # Request and response schemas
│   │   └── ollama_client.py    # Optional local AI explanation client
│   ├── tests/                  # Automated tests
│   └── requirements.txt        # Python dependencies
├── frontend/
│   ├── index.html              # User interface
│   ├── style.css               # Interface styling
│   └── script.js               # API requests and result rendering
├── .gitignore
└── README.md
```

If your repository uses different filenames or locations, update this tree to match the committed files.

## Requirements

- Python 3.10 or newer (use the version supported by your installed dependencies).
- `pip` and Python virtual-environment support.
- A modern browser.
- **Optional AI explanations:** [Ollama](https://ollama.com/) installed and running locally, with a compatible model downloaded.
- A frontend static server. Python's built-in HTTP server is sufficient for local development.

## Installation and Setup

### 1. Clone the repository

Replace the example URL with your public repository URL:

```bash
git clone <YOUR_PUBLIC_REPOSITORY_URL>
cd ScamShield
```

### 2. Create and activate a virtual environment

From the project root, run:

**Windows PowerShell**
```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**Windows Command Prompt**
```bat
cd backend
python -m venv .venv
.venv\Scripts\activate.bat
```

**Linux / macOS**
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install backend dependencies

With the virtual environment activated and the current directory set to `backend`:

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

If `backend/requirements.txt` is not in your repository, create it from the project's actual dependencies before publishing. Do not add packages that the application does not use.

### 4. Configure the local AI (optional)

Install Ollama from [ollama.com](https://ollama.com/) and download the model used by your configuration:

```bash
ollama pull qwen3:4b-q4_K_M
```

Start Ollama if it is not already running, then verify the model is available:

```bash
ollama list
```

The current implementation uses `qwen3:4b-q4_K_M` by default. If your code supports environment configuration, set the model and timeout variables to match the names used in `backend/app/ollama_client.py`. For example, if supported by your checkout:

**Windows PowerShell**
```powershell
$env:OLLAMA_MODEL = "qwen3:4b-q4_K_M"
$env:OLLAMA_TIMEOUT = "20"
```

**Linux / macOS**
```bash
export OLLAMA_MODEL="qwen3:4b-q4_K_M"
export OLLAMA_TIMEOUT="20"
```

AI explanations require a running local Ollama service and a compatible model. If AI is unavailable, check the API response and application logs to see how your version handles the failure.

## Run the Application

Open **two terminals** from the project root.

### Terminal 1 — Start the backend

```bash
cd backend
```

Activate your virtual environment if needed, then run:

```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

The API should be available at:
- API base: `http://127.0.0.1:8000`
- Interactive API documentation: `http://127.0.0.1:8000/docs`

### Terminal 2 — Start the frontend

From the project root:

```bash
python -m http.server 3000
```

Then open:

`http://127.0.0.1:3000/frontend/index.html`

The frontend is configured to communicate with `http://127.0.0.1:8000`. If you change the frontend or backend ports, update the API URL and FastAPI CORS allowed origins accordingly.

> **Local development only:** The commands above bind the API to loopback. Do not expose this development server directly to the public internet. Before deploying, configure production hosting, security controls, logging, and appropriate CORS origins.

## Run the Tests

From the `backend` directory with the virtual environment activated:

```bash
python -m pytest -v
```

The project reached **29 passing tests** in the development environment when this README was prepared. Run the tests on your current checkout before relying on that result, and update this statement if the result changes.

## Example Scenarios

Use fictional messages when testing. Do not paste real private conversations, credentials, payment details, or personal information into a demo.

### Scenario A — Upfront fee request

> You must pay a registration fee before starting work.

Expected behavior: the analyzer should flag the upfront-fee warning sign and explain why a request for payment before work begins deserves scrutiny. The precise risk result depends on the current rules.

### Scenario B — Offer with details to verify

> We are hiring a freelance data-entry assistant for 10 hours per week at an agreed hourly rate. No registration fee is required. Please review the contract and company details before accepting.

Expected behavior: the analyzer should assess the wording and show relevant findings or missing details. A low-risk result does **not** prove that the offer or sender is legitimate.

### Scenario C — Ambiguous message

Try a message that lacks company information, a clear scope of work, or a verifiable payment arrangement. Review the missing-information and recommendation sections before making a decision.

## AI, Privacy, and Limitations

- **Rules are the basis of risk scoring.** AI explanations are intended to explain existing findings, not determine the score.
- **Local model option.** When configured for local Ollama, the explanation model runs on the user's machine. This does not mean every possible deployment is automatically private; review the code and your local setup.
- **No external verification.** ScamShield does not independently confirm company registration, website ownership, sender identity, or whether a job offer is genuine.
- **Heuristic detection.** Rule-based checks can miss sophisticated scams and can flag legitimate messages that use suspicious wording.
- **No guarantee of safety.** A `LOW` result is not proof that a message is safe, and a `CRITICAL` result is not a legal determination.
- **Protect sensitive data.** Test with fictional or redacted messages. Never submit passwords, authentication codes, banking details, or other secrets.
- **AI output can be wrong.** Review the original evidence and verify claims independently. Do not treat a model explanation as authoritative advice.

## Roadmap

Potential improvements include:

- Add more documented detection rules and regression tests.
- Improve handling of AI service timeouts and unavailable models.
- Add representative, anonymized test fixtures for common freelance scam patterns.
- Improve accessibility and mobile layout.
- Add clearer API error messages and health checks.
- Provide a reproducible demo and more detailed architecture documentation.
- Evaluate false positives and false negatives against a carefully curated test set.

These are possible next steps, not claims that the features are already implemented.

## Contributing

Contributions and constructive feedback are welcome.

1. Fork the repository.
2. Create a feature branch.
3. Make a focused change and add or update tests.
4. Run the test suite with `python -m pytest -v`.
5. Open a pull request describing the change, test results, and limitations.

Please do not include private messages, real client data, credentials, API keys, or other sensitive information in issues, commits, or test fixtures.

## License

Choose and add an open-source license before inviting reuse or contributions. If the repository does not yet contain a license, it is currently **not explicitly licensed for reuse**. Add the appropriate license file (for example, an MIT license only if you choose those terms) and update this section to match.

## Project Links

- **GitHub repository:** `[Add your public repository URL]`
- **Demo video:** `[Add a public demo link, if available]`
- **Challenge:** [Hacktoberfest Week 2 — Side Hustle](https://dev.to/challenges/hacktoberfest-week2-2026-10-12)

---

Built as an open-source AI project for freelancers and independent workers. Stay cautious, verify independently, and never let a risk score replace your own judgment.
