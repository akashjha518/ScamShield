
const API_URL = "http://127.0.0.1:8000/analyze";

const form = document.querySelector("#analysis-form");
const messageInput = document.querySelector("#message-input");
const analyzeButton = document.querySelector("#analyze-button");
const buttonLabel = document.querySelector("#button-label");
const clearButton = document.querySelector("#clear-button");
const characterCount = document.querySelector("#character-count");
const formError = document.querySelector("#form-error");

const resultsSection = document.querySelector("#results");
const riskCard = document.querySelector("#risk-card");
const riskLevel = document.querySelector("#risk-level");
const riskScore = document.querySelector("#risk-score");
const riskSummary = document.querySelector("#risk-summary");
const findingsList = document.querySelector("#findings-list");
const findingCount = document.querySelector("#finding-count");
const recommendationsList = document.querySelector("#recommendations-list");
const missingList = document.querySelector("#missing-list");
const limitationsList = document.querySelector("#limitations-list");

const examples = {
    fee: "You must pay a registration fee before starting work.",

    legitimate:
        "We are hiring a freelance data-entry assistant for 10 hours per week at an agreed hourly rate. No registration fee is required. Please review the contract and company details before accepting.",

    ambiguous:
        "We have a freelance opportunity available.",
};

function createElement(tag, className, text) {
    const element = document.createElement(tag);

    if (className) {
        element.className = className;
    }

    if (text !== undefined && text !== null) {
        // Use textContent rather than innerHTML for untrusted message data.
        element.textContent = String(text);
    }

    return element;
}

function showError(message) {
    formError.textContent = message;
    formError.hidden = false;
}

function clearError() {
    formError.textContent = "";
    formError.hidden = true;
}

function updateCharacterCount() {
    characterCount.textContent = `${messageInput.value.length} / 10000`;
}

function setLoading(isLoading) {
    analyzeButton.disabled = isLoading;
    buttonLabel.textContent = isLoading ? "Analyzing..." : "Analyze message";
    analyzeButton.setAttribute("aria-busy", String(isLoading));
}

function renderList(container, items, emptyMessage) {
    container.replaceChildren();

    if (!Array.isArray(items) || items.length === 0) {
        if (emptyMessage) {
            container.appendChild(
                createElement("li", "", emptyMessage)
            );
        }
        return;
    }

    for (const item of items) {
        container.appendChild(createElement("li", "", item));
    }
}

function renderFindings(findings, aiExplanations = {}) {
    findingsList.replaceChildren();
    findingCount.textContent = String(findings.length);

    if (findings.length === 0) {
        findingsList.appendChild(
            createElement(
                "div",
                "empty-findings",
                "No warning signs covered by the current rules were detected. " +
                "This does not prove that the offer is legitimate or safe."
            )
        );
        return;
    }

    for (const finding of findings) {
        const card = createElement("article", "finding-card");
        const titleRow = createElement("div", "finding-title-row");

        titleRow.appendChild(
            createElement("h4", "", finding.title)
        );

        const severity = String(finding.severity || "LOW").toLowerCase();

        titleRow.appendChild(
            createElement(
                "span",
                `severity-badge severity-${severity}`,
                finding.severity || "LOW"
            )
        );

        card.appendChild(titleRow);

        card.appendChild(
            createElement("p", "evidence-label", "SUPPORTING EVIDENCE")
        );

        card.appendChild(
            createElement(
                "blockquote",
                "evidence-text",
                finding.evidence || "No excerpt supplied."
            )
        );

        card.appendChild(
            createElement(
                "p",
                "finding-explanation",
                finding.explanation || "No rule explanation available."
            )
        );

        // AI explanation supplements, but never replaces, rule evidence.
        const aiExplanation = aiExplanations?.[finding.rule_id];

        if (typeof aiExplanation === "string" && aiExplanation.trim()) {
            const aiSection = createElement("section", "ai-explanation");
            const aiTitle = createElement(
                "h5",
                "ai-explanation-title",
                "AI explanation"
            );

            aiSection.appendChild(aiTitle);
            aiSection.appendChild(
                createElement("p", "ai-explanation-text", aiExplanation)
            );

            card.appendChild(aiSection);
        }

        card.appendChild(
            createElement(
                "p",
                "finding-points",
                `Rule: ${finding.rule_id} · Score contribution: ${finding.points}`
            )
        );

        findingsList.appendChild(card);
    }
}


function renderRecommendations(recommendations) {
    recommendationsList.replaceChildren();

    if (!Array.isArray(recommendations) || recommendations.length === 0) {
        renderList(
            recommendationsList,
            [],
            "Verify the client and payment terms independently."
        );
        return;
    }

    for (const recommendation of recommendations) {
        const item = createElement("li");
        const priority = createElement(
            "strong",
            "",
            `${recommendation.priority}: `
        );

        item.appendChild(priority);
        item.appendChild(
            document.createTextNode(recommendation.action)
        );

        recommendationsList.appendChild(item);
    }
}

function renderResults(data) {
    const allowedLevels = ["LOW", "MEDIUM", "HIGH", "CRITICAL"];

    if (
        !data ||
        !allowedLevels.includes(data.risk_level) ||
        !Number.isInteger(data.risk_score) ||
        data.risk_score < 0 ||
        data.risk_score > 100 ||
        !Array.isArray(data.findings)
    ) {
        throw new Error("The API returned an unexpected response.");
    }

    riskCard.classList.remove(
        "risk-low",
        "risk-medium",
        "risk-high",
        "risk-critical"
    );
    riskCard.classList.add(`risk-${data.risk_level.toLowerCase()}`);

    riskLevel.textContent = data.risk_level;
    riskScore.textContent = String(data.risk_score);
    riskSummary.textContent = data.summary || "Analysis completed.";

    renderFindings(
    data.findings,
    data.ai_explanations || {}
);

    renderRecommendations(
        Array.isArray(data.recommendations) ? data.recommendations : []
    );

    renderList(
        missingList,
        data.missing_information,
        "No additional verification gaps were identified by the current checks."
    );

    renderList(
        limitationsList,
        data.limitations,
        "This screening tool cannot guarantee that an offer is safe."
    );

    resultsSection.hidden = false;
    resultsSection.scrollIntoView({
        behavior: window.matchMedia("(prefers-reduced-motion: reduce)").matches
            ? "auto"
            : "smooth",
        block: "start",
    });
}

form.addEventListener("submit", async (event) => {
    event.preventDefault();
    clearError();

    const message = messageInput.value.trim();

    if (!message) {
        showError("Please enter a message to analyze.");
        messageInput.focus();
        return;
    }

    if (message.length > 10000) {
        showError("The message must contain no more than 10,000 characters.");
        return;
    }

    setLoading(true);

    try {
        const response = await fetch(API_URL, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({ message }),
            signal: AbortSignal.timeout(120000),
        });

        if (!response.ok) {
            if (response.status === 422) {
                throw new Error(
                    "The message was rejected by input validation. Check its length and content."
                );
            }

            if (response.status >= 500) {
                throw new Error(
                    "The local analysis service encountered an error. Please try again."
                );
            }

            throw new Error(`Analysis failed (HTTP ${response.status}).`);
        }

        const data = await response.json();
        renderResults(data);
    } catch (error) {
        if (error.name === "TimeoutError") {
            showError("The analysis request timed out. Please try again.");
        } else if (error instanceof TypeError) {
            showError(
                "Could not connect to ScamShield. Make sure the FastAPI server is running."
            );
        } else {
            showError(error.message || "An unexpected error occurred.");
        }
    } finally {
        setLoading(false);
    }
});

messageInput.addEventListener("input", updateCharacterCount);

clearButton.addEventListener("click", () => {
    form.reset();
    updateCharacterCount();
    clearError();
    resultsSection.hidden = true;
    messageInput.focus();
});

document.querySelectorAll("[data-example]").forEach((button) => {
    button.addEventListener("click", () => {
        const example = examples[button.dataset.example];

        if (example) {
            messageInput.value = example;
            updateCharacterCount();
            clearError();
            messageInput.focus();
        }
    });
});

updateCharacterCount();
