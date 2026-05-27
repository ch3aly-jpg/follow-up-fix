const onboardingForm = document.querySelector("#clientOnboardingForm");

onboardingForm.addEventListener("submit", (event) => {
  event.preventDefault();
  const data = new FormData(onboardingForm);
  const subject = encodeURIComponent("Follow-Up Fix onboarding details");
  const body = encodeURIComponent(
    [
      "Hi Follow-Up Fix,",
      "",
      "Here are my onboarding details.",
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
      "Thanks"
    ].join("\n")
  );
  window.location.href = `mailto:ch3aly@googlemail.com?subject=${subject}&body=${body}`;
});
