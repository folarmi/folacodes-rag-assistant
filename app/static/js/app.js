const questionForm = document.getElementById("questionForm");
const questionInput = document.getElementById("questionInput");
const submitButton = document.getElementById("submitButton");
const chatMessages = document.getElementById("chatMessages");
const errorMessage = document.getElementById("errorMessage");
const characterCount = document.getElementById("characterCount");
const suggestionButtons = document.querySelectorAll(".suggestion-button");

let isSubmitting = false;

function escapeHtml(value) {
  const element = document.createElement("div");
  element.textContent = String(value ?? "");
  return element.innerHTML;
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

function addUserMessage(question) {
  const message = document.createElement("div");
  message.className = "message user-message";

  message.innerHTML = `
    <div class="message-avatar">You</div>

    <div class="message-content">
      <p class="message-author">You</p>

      <div class="message-bubble">
        <p>${escapeHtml(question)}</p>
      </div>
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

      <div class="message-bubble">
        <div class="loading-dots" aria-label="Generating answer">
          <span></span>
          <span></span>
          <span></span>
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
    <div class="sources">
      <p class="sources-title">Retrieved sources</p>
      <div class="source-list">
        ${sourceCards}
      </div>
    </div>
  `;
}

function addAssistantMessage(answer, sources = []) {
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
    </div>
  `;

  chatMessages.appendChild(message);
  scrollToBottom();
}

function setSubmittingState(submitting) {
  isSubmitting = submitting;
  submitButton.disabled = submitting;
  questionInput.disabled = submitting;

  submitButton.querySelector(".button-text").textContent = submitting
    ? "Sending"
    : "Send";
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
    addAssistantMessage(data.answer, data.sources);
  } catch (error) {
    removeLoadingMessage();

    const message =
      error instanceof Error
        ? error.message
        : "Something went wrong. Please try again.";

    showError(message);

    addAssistantMessage(
      "I could not process your question at this time. Please try again.",
    );
  } finally {
    setSubmittingState(false);
    questionInput.focus();
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

updateCharacterCount();
resizeTextarea();
questionInput.focus();
