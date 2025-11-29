// Main client-side logic for VideoTranscript Pro

function isValidYouTubeUrl(url) {
  const patterns = [
    /^https?:\/\/(www\.)?youtube\.com\/watch\?v=[\w-]+/,
    /^https?:\/\/youtu\.be\/[\w-]+/,
    /^https?:\/\/(www\.)?youtube\.com\/embed\/[\w-]+/,
  ];
  return patterns.some((p) => p.test(url));
}

function escapeHtml(text) {
  const div = document.createElement("div");
  div.textContent = text;
  return div.innerHTML;
}

function showAlert(message, type) {
  const alertDiv = document.createElement("div");
  alertDiv.className = `alert alert-${type}`;
  alertDiv.textContent = message;

  const inputSection = document.querySelector(".input-section");
  if (!inputSection) return;

  inputSection.insertBefore(alertDiv, inputSection.firstChild);

  setTimeout(() => alertDiv.remove(), 4000);
}

function hideResults() {
  const resultsSection = document.getElementById("results-section");
  if (resultsSection) {
    resultsSection.classList.add("hidden");
    resultsSection.innerHTML = "";
  }
}

window.showTranscript = function (transcript, sessionId) {
  const resultsSection = document.getElementById("results-section");
  if (!resultsSection) return;

  resultsSection.innerHTML = `
        <div class="result-card">
            <h2>📝 Transcript</h2>
            <div class="transcript-content" style="max-height: 400px; overflow-y: auto; padding: 1rem; background: #f9fafb; border-radius: 0.5rem; margin: 1rem 0;">
                <p style="white-space: pre-wrap; line-height: 1.8;">${escapeHtml(
                  transcript
                )}</p>
            </div>
            <div class="result-actions">
                <button class="btn btn-primary" onclick="window.copyTranscript()">Copy Transcript</button>
                <button class="btn btn-secondary" onclick="window.downloadTranscript()">Download Transcript</button>
                <button class="btn btn-secondary" onclick="window.generateSummary(window.currentSessionId)">Generate Summary</button>
                <button class="btn btn-secondary" onclick="window.showPodcastOptions(window.currentSessionId)">Generate Podcast</button>
            </div>
        </div>
    `;

  window.currentTranscript = transcript;
  window.currentSessionId = sessionId;
  resultsSection.classList.remove("hidden");
  resultsSection.scrollIntoView({ behavior: "smooth", block: "start" });
};

window.generateSummary = async function (sessionId) {
  const resultsSection = document.getElementById("results-section");
  if (!resultsSection || !window.currentTranscript) return;

  resultsSection.innerHTML = `
        <div class="result-card">
            <h2>Generating Summary...</h2>
            <div class="spinner"></div>
            <p class="text-center">This may take a few moments...</p>
        </div>
    `;

  try {
    const response = await fetch("/generate-summary", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        transcript: window.currentTranscript,
        session_id: sessionId,
        url: document.getElementById("youtube-url").value,
      }),
    });

    const data = await response.json();

    if (data.success) {
      resultsSection.innerHTML = `
                <div class="result-card">
                    <h2>📄 Summary</h2>
                    <h3 style="margin: 1rem 0; color: #6366f1;">${escapeHtml(
                      data.title
                    )}</h3>
                    <div style="max-height: 500px; overflow-y: auto; padding: 1rem; background: #f9fafb; border-radius: 0.5rem; margin: 1rem 0;">
                        <p style="white-space: pre-wrap; line-height: 1.8;">${escapeHtml(
                          data.summary
                        )}</p>
                    </div>
                </div>
            `;

      window.currentSummary = data.summary;
      window.currentSummaryTitle = data.title;
      showAlert("Summary generated successfully!", "success");
    } else {
      showAlert(data.error || "Failed to generate summary", "error");
      window.showTranscript(window.currentTranscript, sessionId);
    }
  } catch (err) {
    showAlert("Error generating summary", "error");
    window.showTranscript(window.currentTranscript, sessionId);
  }
};

window.showPodcastOptions = function (sessionId) {
  const resultsSection = document.getElementById("results-section");
  if (!resultsSection) return;

  resultsSection.innerHTML = `
        <div class="result-card">
            <h2>🎙️ Generate Podcast</h2>
            <p>Select a voice style for your generated podcast audio.</p>
            <div style="display: flex; gap: 1rem; margin: 1.5rem 0; flex-wrap: wrap;">
                <button class="btn btn-primary" onclick="window.generatePodcast('${sessionId}', 'male')">Male Voice</button>
                <button class="btn btn-primary" onclick="window.generatePodcast('${sessionId}', 'female')">Female Voice</button>
            </div>
        </div>
    `;
};

window.generatePodcast = async function (sessionId, gender) {
  const resultsSection = document.getElementById("results-section");
  if (!resultsSection || !window.currentTranscript) return;

  resultsSection.innerHTML = `
        <div class="result-card">
            <h2>Generating Podcast...</h2>
            <div class="spinner"></div>
            <p class="text-center">Generating conversation and audio...</p>
        </div>
    `;

  try {
    const response = await fetch("/generate-podcast", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        transcript: window.currentTranscript,
        session_id: sessionId,
        gender,
        url: document.getElementById("youtube-url").value,
      }),
    });

    const data = await response.json();

    if (data.success) {
      resultsSection.innerHTML = `
                <div class="result-card">
                    <h2>🎧 Podcast Generated</h2>
                    <h3 style="margin: 1rem 0; color: #6366f1;">${escapeHtml(
                      data.title
                    )}</h3>
                    <audio controls style="width: 100%; margin: 1.5rem 0;">
                        <source src="${data.audio_url}" type="audio/mpeg" />
                        Your browser does not support the audio element.
                    </audio>
                    <div style="max-height: 400px; overflow-y: auto; padding: 1rem; background: #f9fafb; border-radius: 0.5rem; margin: 1.5rem 0;">
                        <h4>Conversation Script</h4>
                        <p style="white-space: pre-wrap; line-height: 1.8;">${escapeHtml(
                          data.conversation
                        )}</p>
                    </div>
                </div>
            `;

      window.currentConversation = data.conversation;
      showAlert("Podcast generated successfully!", "success");
    } else {
      showAlert(data.error || "Failed to generate podcast", "error");
      window.showPodcastOptions(sessionId);
    }
  } catch (err) {
    showAlert("Error generating podcast", "error");
    window.showPodcastOptions(sessionId);
  }
};

window.copyTranscript = function () {
  if (!window.currentTranscript) {
    showAlert("No transcript available to copy", "error");
    return;
  }
  navigator.clipboard.writeText(window.currentTranscript).then(() => {
    showAlert("Transcript copied to clipboard", "success");
  }).catch(err => {
    console.error("Copy error:", err);
    showAlert("Failed to copy transcript", "error");
  });
};

window.downloadTranscript = function() {
  if (!window.currentTranscript) {
    showAlert("No transcript available to download", "error");
    return;
  }
  const blob = new Blob([window.currentTranscript], { type: 'text/plain' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `transcript_${Date.now()}.txt`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
  showAlert("Transcript downloaded", "success");
};

window.extractTranscript = async function() {
  const urlInput = document.getElementById("youtube-url");
  if (!urlInput) {
    console.error("YouTube URL input not found");
    return;
  }
  
  const url = urlInput.value.trim();

  if (!url) {
    showAlert("Please enter a YouTube URL", "error");
    return;
  }

  if (!isValidYouTubeUrl(url)) {
    showAlert("Please enter a valid YouTube URL", "error");
    return;
  }

  hideResults();

  const extractBtn = document.getElementById("extract-btn");
  const originalText = extractBtn ? extractBtn.textContent : "Extract Transcript";
  if (extractBtn) {
    extractBtn.disabled = true;
    extractBtn.textContent = "Extracting...";
  }

  try {
    const response = await fetch("/extract", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url }),
    });

    const data = await response.json();

    if (data.success) {
      window.showTranscript(data.transcript, data.session_id);
      showAlert("Transcript extracted successfully!", "success");
    } else {
      showAlert(data.error || "Failed to extract transcript", "error");
    }
  } catch (err) {
    console.error("Extract transcript error:", err);
    showAlert("Error extracting transcript: " + (err.message || "Network error"), "error");
  } finally {
    if (extractBtn) {
      extractBtn.disabled = false;
      extractBtn.textContent = originalText;
    }
  }
}

document.addEventListener("DOMContentLoaded", () => {
  const urlInput = document.getElementById("youtube-url");
  const extractBtn = document.getElementById("extract-btn");

  if (extractBtn) {
    extractBtn.addEventListener("click", window.extractTranscript);
  }

  if (urlInput) {
    urlInput.addEventListener("keypress", (e) => {
      if (e.key === "Enter") {
        window.extractTranscript();
      }
    });
  }

  const mobileToggle = document.querySelector(".mobile-menu-toggle");
  const navMenu = document.querySelector(".nav-menu");
  if (mobileToggle && navMenu) {
    mobileToggle.addEventListener("click", () => {
      navMenu.classList.toggle("active");
    });
  }
  
    // Initialize theme toggle
    initThemeToggle();
});

// Logout handler - make globally accessible
window.handleLogout = async function() {
    try {
        const response = await fetch('/auth/logout', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        const data = await response.json();
        if (data.success) {
            window.location.href = data.redirect || '/';
        } else {
            // Still redirect even if response indicates failure
            window.location.href = '/';
        }
    } catch (error) {
        console.error('Logout error:', error);
        // Redirect anyway
        window.location.href = '/';
    }
}

// Dark/Light Mode Toggle
function initThemeToggle() {
  const themeToggle = document.getElementById("theme-toggle");
  if (!themeToggle) return;
  
  const prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
  const savedTheme = localStorage.getItem("theme");
  const theme = savedTheme || (prefersDark ? "dark" : "light");
  
  document.documentElement.setAttribute("data-theme", theme);
  themeToggle.textContent = theme === "dark" ? "☀️" : "🌙";
  
  themeToggle.addEventListener("click", () => {
    const currentTheme = document.documentElement.getAttribute("data-theme");
    const newTheme = currentTheme === "dark" ? "light" : "dark";
    document.documentElement.setAttribute("data-theme", newTheme);
    localStorage.setItem("theme", newTheme);
    themeToggle.textContent = newTheme === "dark" ? "☀️" : "🌙";
  });
}


