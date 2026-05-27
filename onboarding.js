const onboardingForm = document.querySelector("#clientOnboardingForm");
const contactEmail = "ch3aly@gmail.com";

function buildOnboardingMailto(data) {
  const subject = encodeURIComponent("Follow-Up Fix Proof Trial details");
  const body = encodeURIComponent(
    [
      "Hi Follow-Up Fix,",
      "",
      "Here are my Proof Trial onboarding details.",
      "",
      `Business: ${data.get("business")}`,
      `Contact: ${data.get("name")}`,
      `Email: ${data.get("email")}`,
      `Trade and town: ${data.get("trade")}`,
      `Main enquiry channels: ${data.get("channels")}`,
      `Preferred check-in day: ${data.get("checkin")}`,
      `Google review link: ${data.get("reviewLink")}`,
      `Number of open quotes: ${data.get("quoteCount")}`,
      "",
      "Open quotes:",
      data.get("quotes"),
      "",
      "Words or tone to avoid:",
      data.get("tone"),
      "",
      "I saw the instant setup note on the website.",
      "",
      "Thanks"
    ].join("\n")
  );
  return `mailto:${contactEmail}?subject=${subject}&body=${body}`;
}

window.FollowUpFix = {
  ...(window.FollowUpFix || {}),
  buildOnboardingMailto
};

onboardingForm.addEventListener("submit", (event) => {
  event.preventDefault();
  window.location.href = buildOnboardingMailto(new FormData(onboardingForm));
});
