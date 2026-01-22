// Beginner note: The frontend sends the textarea content to /redact and shows what was scrubbed.

const input = document.getElementById("inputText");
const output = document.getElementById("outputText");
const redactBtn = document.getElementById("redactBtn");
const summary = document.getElementById("summary");
const closeSummary = document.getElementById("closeSummary");
const countEmails = document.getElementById("countEmails");
const countIps = document.getElementById("countIps");
const countSecrets = document.getElementById("countSecrets");
const countUrls = document.getElementById("countUrls");
const countAws = document.getElementById("countAws");
const countJwts = document.getElementById("countJwts");
const countPhones = document.getElementById("countPhones");
const totalRedacted = document.getElementById("totalRedacted");
const themeToggle = document.getElementById("themeToggle");
const toast = document.getElementById("toast-notification");
const copyButtons = document.querySelectorAll(".copy-output-btn");
const exportButtons = document.querySelectorAll(".export-output-btn");
const charCount = document.getElementById("charCount");
const wordCount = document.getElementById("wordCount");
const piiScoreFill = document.getElementById("piiScoreFill");
const piiScoreText = document.getElementById("piiScoreText");
const CHAR_LIMIT = 10000;
const WORD_LIMIT = 2000;

// Update input stats
function updateInputStats() {
  const text = input.value;
  const chars = text.length;
  const words = text.trim() ? text.trim().split(/\s+/).length : 0;
  
  charCount.textContent = chars.toLocaleString();
  wordCount.textContent = words.toLocaleString();
  
  // Character status
  if (chars > CHAR_LIMIT) {
    charCount.className = "stat-compact exceeded";
  } else if (chars > CHAR_LIMIT * 0.9) {
    charCount.className = "stat-compact warning";
  } else {
    charCount.className = "stat-compact";
  }
  
  // Word status
  if (words > WORD_LIMIT) {
    wordCount.className = "stat-compact exceeded";
  } else if (words > WORD_LIMIT * 0.9) {
    wordCount.className = "stat-compact warning";
  } else {
    wordCount.className = "stat-compact";
  }
}

// Listen to input changes
if (input) {
  input.addEventListener("input", updateInputStats);
  updateInputStats(); // Initialize on load
}

// Initialize theme from localStorage
function initTheme() {
  const savedTheme = localStorage.getItem("theme") || "dark";
  if (savedTheme === "light") {
    document.body.classList.add("light-mode");
  } else {
    document.body.classList.remove("light-mode");
  }
}

// Theme toggle handler
themeToggle.addEventListener("click", () => {
  document.body.classList.toggle("light-mode");
  const isLightMode = document.body.classList.contains("light-mode");
  localStorage.setItem("theme", isLightMode ? "light" : "dark");
  showToast(isLightMode ? "Light theme enabled" : "Dark theme enabled");
});

// Redaction handler
redactBtn.addEventListener("click", async () => {
    const text = input.value;
    if (!text.trim()) {
        output.textContent = "Please paste some text first.";
        return;
    }

    try {
        const res = await fetch("/redact", {
            method: "POST",
            headers: { "Content-Type": "text/plain" },
            body: text,
        });

        if (!res.ok) {
            const errorText = await res.text();
            throw new Error(`Server returned ${res.status}: ${errorText}`);
        }

        const data = await res.json();
        output.textContent = data.redacted;

        countEmails.textContent = data.counts.emails;
        countIps.textContent = data.counts.ips;
        countSecrets.textContent = data.counts.secrets;
        if (countUrls) countUrls.textContent = data.counts.urls ?? 0;
        if (countAws) countAws.textContent = data.counts.aws_keys ?? 0;
        if (countJwts) countJwts.textContent = data.counts.jwts ?? 0;
        if (countPhones) countPhones.textContent = data.counts.phones ?? 0;
        
        const total = (data.counts.emails || 0)
          + (data.counts.ips || 0)
          + (data.counts.secrets || 0)
          + (data.counts.urls || 0)
          + (data.counts.aws_keys || 0)
          + (data.counts.jwts || 0)
          + (data.counts.phones || 0);
        totalRedacted.textContent = total;
        showToast(`Redaction complete: ${total} items`);
        
        // Update PII score
        if (piiScoreFill && piiScoreText && data.pii_score !== undefined) {
          const score = data.pii_score;
          piiScoreFill.style.width = `${Math.min(score, 100)}%`;
          piiScoreText.textContent = `${score}/100 Risk`;
          piiScoreText.dataset.score = score;
          
          // Color code: green (0-30), amber (31-70), red (71-100)
          if (score <= 30) {
            piiScoreText.style.color = "#10b981";
          } else if (score <= 70) {
            piiScoreText.style.color = "#f59e0b";
          } else {
            piiScoreText.style.color = "#ef4444";
          }
        }
        
        // Enable AI analysis buttons - always keep enabled
        // (Removed: they will check for output when clicked)
        
        summary.classList.add("show");
        summary.classList.remove("hidden");
    } catch (err) {
        output.textContent = `Error: ${err.message}`;
        showToast("Redaction failed");
    }
});

closeSummary.addEventListener("click", () => {
    summary.classList.remove("show");
    summary.classList.add("hidden");
});

// Initialize theme on page load
initTheme();

// Show toast helper
function showToast(message) {
  if (!toast) return;
  toast.textContent = message;
  toast.classList.remove("toast-hidden");
  toast.classList.add("toast-show");
  setTimeout(() => {
    toast.classList.remove("toast-show");
    toast.classList.add("toast-hidden");
    toast.textContent = "";
  }, 2500);
}

// Copy Output handler (supports multiple buttons)
copyButtons.forEach((btn) => {
  btn.addEventListener("click", async () => {
    try {
      const text = output?.textContent || "";
      if (!text.trim()) {
        showToast("⚠️ No output to copy yet");
        return;
      }
      await navigator.clipboard.writeText(text);
      
      // Visual feedback: change button text
      const originalText = btn.innerHTML;
      btn.innerHTML = '<span class="btn-icon" aria-hidden="true"><svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor"><path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41L9 16.17z"/></svg></span><span>Copied!</span>';
      btn.style.borderColor = "var(--accent-emerald)";
      btn.style.color = "var(--accent-emerald)";
      
      showToast("✅ Copied to clipboard!");
      
      // Reset after 2 seconds
      setTimeout(() => {
        btn.innerHTML = originalText;
        btn.style.borderColor = "";
        btn.style.color = "";
      }, 2000);
    } catch (e) {
      showToast("❌ Copy failed - try Ctrl+C");
    }
  });
});

// Export File handler (supports multiple buttons)
exportButtons.forEach((btn) => {
  btn.addEventListener("click", () => {
    try {
      const text = output?.textContent || "";
      if (!text.trim()) {
        showToast("No output to export yet");
        return;
      }
      const blob = new Blob([text], { type: "text/plain;charset=utf-8" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "code-ghost-redacted.txt";
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
      showToast("Exported redacted output as file");
    } catch (e) {
      showToast("Export failed. Try again.");
    }
  });
});

