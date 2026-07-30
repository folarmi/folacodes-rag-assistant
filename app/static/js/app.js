const questionForm = document.getElementById("questionForm");
const questionInput = document.getElementById("questionInput");
const submitButton = document.getElementById("submitButton");
const chatMessages = document.getElementById("chatMessages");
const errorMessage = document.getElementById("errorMessage");
const characterCount = document.getElementById("characterCount");
const historyList = document.getElementById("historyList");
const refreshHistoryButton = document.getElementById("refreshHistoryButton");
const suggestionButtons = document.querySelectorAll(".suggestion-button");

let isSubmitting = false;

function escapeHtml(value) {
  const element = document.createElement("div");
  element.textContent = String(value ?? "");
  return element.innerHTML;
}

function formatTime(value = new Date()) {
  const date = value instanceof Date ? value : new Date(value);

  if (Number.isNaN(date.getTime())) {
    return "";
  }

  return date.toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit",
  });
}

function scrollToBottom() {
  chatMessages.scrollTo({
    top: chatMessages.scrollHeight,
    behavior: "smooth",
  });
}

function resizeTextarea() {
  questionInput.style.height = "auto";
  questionInput.style.height = `${Math.min(questionInput.scrollHeight, 150)}px`;
}

function updateCharacterCount() {
  characterCount.textContent = questionInput.value.length;
}

function hideError() {
  errorMessage.hidden = true;
  errorMessage.textContent = "";
}

function showError(message) {
  errorMessage.textContent = message;
  errorMessage.hidden = false;
}

function addUserMessage(question, createdAt = new Date()) {
  const message = document.createElement("div");
  message.className = "message user-message";

  message.innerHTML = `
    <div class="message-avatar">You</div>

    <div class="message-content">
      <p class="message-author">You</p>

      <div class="message-bubble">
        <p>${escapeHtml(question)}</p>
      </div>

      <p class="message-time">${formatTime(createdAt)}</p>
    </div>
  `;

  chatMessages.appendChild(message);
  scrollToBottom();
}

function addLoadingMessage() {
  const message = document.createElement("div");
  message.className = "message assistant-message loading-message";
  message.id = "loadingMessage";

  message.innerHTML = `
    <div class="message-avatar">F</div>

    <div class="message-content">
      <p class="message-author">Folacodes Assistant</p>

      <div class="message-bubble loading-bubble">
        <div class="loading-status">
          <div
            class="loading-dots"
            aria-label="Searching company documents"
          >
            <span></span>
            <span></span>
            <span></span>
          </div>

          <p>Searching company documents...</p>
        </div>
      </div>
    </div>
  `;

  chatMessages.appendChild(message);
  scrollToBottom();
}

function removeLoadingMessage() {
  const loadingMessage = document.getElementById("loadingMessage");

  if (loadingMessage) {
    loadingMessage.remove();
  }
}

function buildSourcesMarkup(sources) {
  if (!Array.isArray(sources) || sources.length === 0) {
    return "";
  }

  const sourceCards = sources
    .map((source, index) => {
      const title = escapeHtml(source.title || `Source ${index + 1}`);
      const section = escapeHtml(source.section || "General");
      const sourcePath = escapeHtml(source.source || "");

      return `
        <article class="source-card">
          <h4>${index + 1}. ${title}</h4>
          <p>Section: ${section}</p>
          ${sourcePath ? `<p>File: ${sourcePath}</p>` : ""}
        </article>
      `;
    })
    .join("");

  return `
    <details class="sources">
      <summary>
        Retrieved sources
        <span class="source-count">${sources.length}</span>
      </summary>

      <div class="source-list">
        ${sourceCards}
      </div>
    </details>
  `;
}

function buildFeedbackMarkup(responseId, question, answer) {
  if (!responseId) {
    return "";
  }

  return `
    <div
      class="feedback"
      data-response-id="${escapeHtml(responseId)}"
      data-question="${escapeHtml(question)}"
      data-answer="${escapeHtml(answer)}"
    >
      <span>Was this helpful?</span>

      <button
        class="feedback-button"
        type="button"
        data-rating="helpful"
        aria-label="Mark answer as helpful"
      >
        👍
      </button>

      <button
        class="feedback-button"
        type="button"
        data-rating="not_helpful"
        aria-label="Mark answer as not helpful"
      >
        👎
      </button>

      <span class="feedback-status"></span>
    </div>
  `;
}

function addAssistantMessage({
  answer,
  sources = [],
  responseId = "",
  question = "",
  createdAt = new Date(),
}) {
  const message = document.createElement("div");
  message.className = "message assistant-message";

  message.innerHTML = `
    <div class="message-avatar">F</div>

    <div class="message-content">
      <p class="message-author">Folacodes Assistant</p>

      <div class="message-bubble">
        <p>${escapeHtml(answer)}</p>
      </div>

      ${buildSourcesMarkup(sources)}

      ${buildFeedbackMarkup(responseId, question, answer)}

      <p class="message-time">${formatTime(createdAt)}</p>
    </div>
  `;

  chatMessages.appendChild(message);
  scrollToBottom();
}

function setSubmittingState(submitting) {
  isSubmitting = submitting;
  submitButton.disabled = submitting;
  questionInput.disabled = submitting;

  const buttonText = submitButton.querySelector(".button-text");

  if (buttonText) {
    buttonText.textContent = submitting ? "Sending" : "Send";
  }
}

async function askQuestion(question) {
  hideError();
  addUserMessage(question);
  addLoadingMessage();
  setSubmittingState(true);

  try {
    const response = await fetch("/api/ask", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        question,
      }),
    });

    let data;

    try {
      data = await response.json();
    } catch {
      throw new Error("The server returned an invalid response.");
    }

    if (!response.ok) {
      throw new Error(
        data.error || "The assistant could not process your question.",
      );
    }

    removeLoadingMessage();

    addAssistantMessage({
      answer: data.answer,
      sources: data.sources,
      responseId: data.id,
      question: data.question,
      createdAt: data.created_at,
    });

    await loadHistory();
  } catch (error) {
    removeLoadingMessage();

    const message =
      error instanceof Error
        ? error.message
        : "Something went wrong. Please try again.";

    showError(message);

    addAssistantMessage({
      answer:
        "I could not process your question at this time. Please try again.",
    });
  } finally {
    setSubmittingState(false);
    questionInput.focus();
    scrollToBottom();
  }
}

async function submitFeedback(feedbackElement, rating) {
  const responseId = feedbackElement.dataset.responseId;
  const question = feedbackElement.dataset.question;
  const answer = feedbackElement.dataset.answer;

  const buttons = feedbackElement.querySelectorAll(".feedback-button");
  const status = feedbackElement.querySelector(".feedback-status");

  buttons.forEach((button) => {
    button.disabled = true;
  });

  try {
    const response = await fetch("/api/feedback", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        response_id: responseId,
        rating,
        question,
        answer,
      }),
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.error || "Could not save feedback.");
    }

    buttons.forEach((button) => {
      button.classList.toggle("selected", button.dataset.rating === rating);
    });

    status.textContent = "Thank you";
  } catch (error) {
    status.textContent =
      error instanceof Error ? error.message : "Feedback failed";

    buttons.forEach((button) => {
      button.disabled = false;
    });
  }
}

function renderHistory(history) {
  if (!Array.isArray(history) || history.length === 0) {
    historyList.innerHTML = `
      <p class="history-empty">No recent questions yet.</p>
    `;
    return;
  }

  historyList.innerHTML = history
    .map(
      (item) => `
        <button
          class="history-item"
          type="button"
          data-question="${escapeHtml(item.question)}"
          title="${escapeHtml(item.question)}"
        >
          <span>${escapeHtml(item.question)}</span>
          <small>${formatTime(item.created_at)}</small>
        </button>
      `,
    )
    .join("");
}

async function loadHistory() {
  try {
    const response = await fetch("/api/history");
    const data = await response.json();

    if (!response.ok) {
      throw new Error("Could not load history.");
    }

    renderHistory(data.history);
  } catch {
    historyList.innerHTML = `
      <p class="history-empty">History is unavailable.</p>
    `;
  }
}

questionForm.addEventListener("submit", async (event) => {
  event.preventDefault();

  if (isSubmitting) {
    return;
  }

  const question = questionInput.value.trim();

  if (!question) {
    showError("Please enter a company question.");
    questionInput.focus();
    return;
  }

  questionInput.value = "";
  updateCharacterCount();
  resizeTextarea();

  await askQuestion(question);
});

questionInput.addEventListener("input", () => {
  hideError();
  updateCharacterCount();
  resizeTextarea();
});

questionInput.addEventListener("keydown", (event) => {
  if (event.key === "Enter" && !event.shiftKey && !event.isComposing) {
    event.preventDefault();
    questionForm.requestSubmit();
  }
});

suggestionButtons.forEach((button) => {
  button.addEventListener("click", () => {
    const question = button.dataset.question;

    if (!question || isSubmitting) {
      return;
    }

    questionInput.value = question;
    updateCharacterCount();
    resizeTextarea();
    questionInput.focus();
  });
});

historyList.addEventListener("click", (event) => {
  const historyItem = event.target.closest(".history-item");

  if (!historyItem || isSubmitting) {
    return;
  }

  const question = historyItem.dataset.question;

  if (!question) {
    return;
  }

  questionInput.value = question;
  updateCharacterCount();
  resizeTextarea();
  questionInput.focus();
});

chatMessages.addEventListener("click", (event) => {
  const feedbackButton = event.target.closest(".feedback-button");

  if (!feedbackButton) {
    return;
  }

  const feedbackElement = feedbackButton.closest(".feedback");

  if (!feedbackElement) {
    return;
  }

  submitFeedback(feedbackElement, feedbackButton.dataset.rating);
});

refreshHistoryButton.addEventListener("click", loadHistory);

document.querySelectorAll("[data-current-time]").forEach((element) => {
  element.textContent = formatTime();
});

updateCharacterCount();
resizeTextarea();
loadHistory();
questionInput.focus();
