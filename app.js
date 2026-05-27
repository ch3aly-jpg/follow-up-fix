const cleanSiteOrigin = "https://followupfix.vercel.app";

if (window.location.hostname === "ch3aly-jpg.github.io") {
  const cleanPath = window.location.pathname.replace(/^\/follow-up-fix\/?/, "/");
  window.location.replace(`${cleanSiteOrigin}${cleanPath}${window.location.search}${window.location.hash}`);
}

const templates = {
  quote:
    "Hi {first_name}, just checking in on the quote I sent over for {job}. Happy to answer any questions. Shall we pencil you in?",
  enquiry:
    "Hi {first_name}, thanks for getting in touch about {job}. I can help with that. What is the best time today for a quick call?",
  review:
    "Hi {first_name}, thanks again for choosing us for {job}. If you were happy with the work, would you mind leaving a quick Google review? It really helps a small local business."
};

const messageSelect = document.querySelector("#messageSelect");
const messageOutput = document.querySelector("#messageOutput");
const copyButton = document.querySelector("#copyMessage");
const copyStatus = document.querySelector("#copyStatus");
const toggleRows = document.querySelector("#toggleRows");
const demoRows = document.querySelector("#demoRows");
const leadForm = document.querySelector("#leadForm");

function setMessage() {
  messageOutput.value = templates[messageSelect.value];
  copyStatus.textContent = "";
}

messageSelect.addEventListener("change", setMessage);
setMessage();

copyButton.addEventListener("click", async () => {
  try {
    await navigator.clipboard.writeText(messageOutput.value);
    copyStatus.textContent = "Copied.";
  } catch {
    messageOutput.select();
    document.execCommand("copy");
    copyStatus.textContent = "Copied.";
  }
});

let overdueOnly = false;
toggleRows.addEventListener("click", () => {
  overdueOnly = !overdueOnly;
  toggleRows.textContent = overdueOnly ? "Show all rows" : "Show overdue only";
  [...demoRows.querySelectorAll("tr")].forEach((row) => {
    row.hidden = overdueOnly && row.dataset.status !== "overdue";
  });
});

leadForm.addEventListener("submit", (event) => {
  event.preventDefault();
  const data = new FormData(leadForm);
  const subject = encodeURIComponent("Follow-Up Fix 7-day Proof Trial");
  const body = encodeURIComponent(
    [
      "Hi Follow-Up Fix,",
      "",
      "I want to try the 7-day Proof Trial.",
      "",
      `Name: ${data.get("name")}`,
      `Business: ${data.get("business")}`,
      `Email: ${data.get("email")}`,
      `Trade and town: ${data.get("trade")}`,
      "",
      "Current quote follow-up process:",
      "",
      "I can send 3-5 open quotes in rough format to get started.",
      "",
      "Thanks"
    ].join("\n")
  );
  window.location.href = `mailto:ch3aly@googlemail.com?subject=${subject}&body=${body}`;
});
