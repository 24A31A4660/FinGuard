/* ═══════════════════════════════════════════════════════════════════
   FinGuard — Frontend Logic (Fixed Data Isolation)
   Dual Mode: Demo Landing Page ↔ Authenticated Dashboard
   ═══════════════════════════════════════════════════════════════════ */

const API = "";
let pieChart = null, lineChart = null;
let demoPieChart = null, demoLineChart = null;
let currentUser = null;
let _dashboardInitialized = false;  // Prevent duplicate event listeners

/* ═══════════════════════════════════════════════════════════════════
   STATIC DEMO DATA (Frontend only — never touches database)
   ═══════════════════════════════════════════════════════════════════ */
const DEMO_DATA = Object.freeze({
    transactions: [
        { date: "2026-03-28", amount: 1200, category: "Food" },
        { date: "2026-03-28", amount: 450,  category: "Transport" },
        { date: "2026-03-27", amount: 8500, category: "Shopping" },
        { date: "2026-03-27", amount: 2100, category: "Bills" },
        { date: "2026-03-26", amount: 650,  category: "Entertainment" },
        { date: "2026-03-26", amount: 3200, category: "Food" },
        { date: "2026-03-25", amount: 1800, category: "Bills" },
        { date: "2026-03-25", amount: 900,  category: "Transport" },
        { date: "2026-03-24", amount: 4200, category: "Shopping" },
        { date: "2026-03-24", amount: 750,  category: "Food" },
        { date: "2026-03-23", amount: 1100, category: "Entertainment" },
        { date: "2026-03-23", amount: 2800, category: "Others" },
        { date: "2026-03-22", amount: 1500, category: "Food" },
        { date: "2026-03-22", amount: 3200, category: "Bills" },
    ],
    categoryTotals: { Food: 6650, Transport: 1350, Shopping: 12700, Bills: 7100, Entertainment: 1750, Others: 2800 },
    insights: {
        issues: [
            "Shopping spend is 39% of total — highest category",
            "3 transactions above ₹3,000 this week",
            "Weekend spending 42% higher than weekdays",
        ],
        patterns: [
            "Peak spending hours: 2PM–6PM",
            "Food expenses consistent at ₹1,200/day average",
            "Transport costs stable week-over-week",
        ],
        risks: [
            "High-value shopping may push over monthly budget",
            "Bill payments clustering at month-end",
            "Entertainment spend rising 28% vs last month",
        ],
    },
    dailySpending: {
        "03-22": 4700, "03-23": 3900, "03-24": 4950,
        "03-25": 2700, "03-26": 3850, "03-27": 10600, "03-28": 1650,
    },
});

/* ═══════════════════════════════════════════════════════════════════
   INITIALIZATION
   ═══════════════════════════════════════════════════════════════════ */
document.addEventListener("DOMContentLoaded", () => {
    // Setup auth modal (once)
    setupAuthModal();
    setupPasswordToggles();
    setupPasswordStrength();
    
    // Initialize Google Auth once the script loads
    if (window.google) {
        initGoogleAuth();
    } else {
        window.onload = initGoogleAuth;
    }

    // CTA buttons → open auth modal (once)
    document.getElementById("heroGetStarted").addEventListener("click", () => openAuthModal("signup"));
    document.getElementById("heroLogin").addEventListener("click", () => openAuthModal("login"));
    document.getElementById("navLoginBtn").addEventListener("click", () => openAuthModal("login"));
    document.getElementById("navGetStartedBtn").addEventListener("click", () => openAuthModal("signup"));
    document.getElementById("bannerGetStarted").addEventListener("click", () => openAuthModal("signup"));
    document.getElementById("logoutBtn").addEventListener("click", handleLogout);
    
    // Settings Navigation
    document.getElementById("settingsBtn").addEventListener("click", switchToSettings);
    document.getElementById("backToDashBtn").addEventListener("click", switchToDashboard);
    
    document.getElementById("profileForm").addEventListener("submit", handleProfileUpdate);
    document.getElementById("passwordForm").addEventListener("submit", handlePasswordChange);
    document.getElementById("salaryForm").addEventListener("submit", handleUpdateSalary);

    // Check session — decides which view to show
    checkAuthStatus();
});

/* ═══════════════════════════════════════════════════════════════════
   PASSWORD & SETTINGS HELPERS
   ═══════════════════════════════════════════════════════════════════ */
function setupPasswordToggles() {
    document.querySelectorAll(".pwd-toggle").forEach(btn => {
        btn.addEventListener("click", (e) => {
            const targetId = btn.getAttribute("data-target");
            const input = document.getElementById(targetId);
            if (input.type === "password") {
                input.type = "text";
                btn.textContent = "🙈";
            } else {
                input.type = "password";
                btn.textContent = "👁️";
            }
        });
    });
}

function setupPasswordStrength() {
    const input = document.getElementById("signupPassword");
    const label = document.getElementById("pwdLabel");
    const bars = document.querySelectorAll(".pwd-bar");
    if (!input || !label || !bars.length) return;
    
    input.addEventListener("input", (e) => {
        const val = e.target.value;
        let score = 0;
        if (val.length >= 8) score++;
        if (/[A-Z]/.test(val) && /[a-z]/.test(val)) score++;
        if (/[0-9]/.test(val)) score++;
        if (/[^A-Za-z0-9]/.test(val)) score++;
        
        bars.forEach(b => b.className = "pwd-bar");
        
        if (val.length === 0) {
            label.textContent = "Weak";
            label.style.color = "var(--muted)";
        } else if (score < 2 || val.length < 6) {
            label.textContent = "Weak";
            label.style.color = "var(--red)";
            bars[0].classList.add("weak-active");
        } else if (score === 2 || score === 3) {
            label.textContent = "Medium";
            label.style.color = "var(--yellow)";
            bars[0].classList.add("med-active");
            bars[1].classList.add("med-active");
        } else {
            label.textContent = "Strong";
            label.style.color = "var(--green)";
            bars.forEach(b => b.classList.add("strong-active"));
        }
    });
}

function switchToSettings() {
    document.getElementById("dashboardView").style.display = "none";
    document.getElementById("landingView").style.display = "none";
    document.getElementById("settingsView").style.display = "block";
    
    document.getElementById("navDemoBadge").style.display = "none";
    document.getElementById("navAuthBtns").style.display = "none";
    document.getElementById("navUserInfo").style.display = "flex";
    
    document.getElementById("profileName").value = currentUser ? currentUser.name : "";
    loadSalaryIntoSettings();
}

async function loadSalaryIntoSettings() {
    try {
        const res = await fetch(`${API}/api/user/salary`);
        const data = await res.json();
        if (data.salary > 0) {
            document.getElementById("monthlySalary").value = data.salary;
            document.getElementById("salaryAlertBanner").style.display = "none";
        } else {
            document.getElementById("monthlySalary").value = "";
            document.getElementById("salaryAlertBanner").style.display = "flex";
        }
    } catch {}
}

async function handleProfileUpdate(e) {
    e.preventDefault();
    const name = document.getElementById("profileName").value;
    const msg = document.getElementById("profileMessage");
    try {
        const res = await fetch(`${API}/api/user/settings`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ name }),
        });
        const data = await res.json();
        if (data.success) {
            currentUser.name = name;
            document.getElementById("userName").textContent = name;
            document.getElementById("userAvatar").textContent = name.charAt(0).toUpperCase();
            msg.textContent = "Profile updated successfully!";
            setTimeout(() => msg.textContent = "", 3000);
        }
    } catch {}
}

async function handlePasswordChange(e) {
    e.preventDefault();
    const oldPassword = document.getElementById("oldPassword").value;
    const newPassword = document.getElementById("newPassword").value;
    const err = document.getElementById("passwordError");
    err.textContent = "";
    
    try {
        const res = await fetch(`${API}/api/user/password`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ oldPassword, newPassword }),
        });
        const data = await res.json();
        if (data.success) {
            err.style.color = "var(--green)";
            err.textContent = "Password changed successfully!";
            document.getElementById("oldPassword").value = "";
            document.getElementById("newPassword").value = "";
            setTimeout(() => { err.textContent = ""; err.style.color = "var(--red)"; }, 3000);
        } else {
            err.style.color = "var(--red)";
            err.textContent = data.error;
        }
    } catch {
        err.style.color = "var(--red)";
        err.textContent = "Connection error";
    }
}

function initGoogleAuth() {
    if (!window.google) return;
    google.accounts.id.initialize({
        client_id: "PLACEHOLDER_GOOGLE_CLIENT_ID", // To be replaced in actual prod deployment
        callback: handleGoogleCredentialResponse
    });
    
    const loginBtn = document.getElementById("googleLoginBtn");
    const signupBtn = document.getElementById("googleSignupBtn");
    if(loginBtn) google.accounts.id.renderButton(loginBtn, { theme: "filled_black", size: "large", width: "100%", text: "continue_with" });
    if(signupBtn) google.accounts.id.renderButton(signupBtn, { theme: "filled_black", size: "large", width: "100%", text: "signup_with" });
}

async function handleGoogleCredentialResponse(response) {
    try {
        const res = await fetch(`${API}/api/auth/google`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ token: response.credential }),
        });
        const data = await res.json();
        if (data.success) {
            currentUser = data.user;
            document.getElementById("authModal").classList.remove("open");
            switchToDashboard();
        } else {
            document.getElementById("loginError").textContent = data.error || "Google auth failed";
            document.getElementById("signupError").textContent = data.error || "Google auth failed";
        }
    } catch (err) {
        document.getElementById("loginError").textContent = "Google auth connection error.";
    }
}


/* ═══════════════════════════════════════════════════════════════════
   AUTH MODAL
   ═══════════════════════════════════════════════════════════════════ */
function setupAuthModal() {
    const modal = document.getElementById("authModal");
    const close = document.getElementById("modalClose");

    close.addEventListener("click", () => modal.classList.remove("open"));
    modal.addEventListener("click", (e) => { if (e.target === modal) modal.classList.remove("open"); });

    // Tab switching
    document.querySelectorAll(".modal-tab").forEach(tab => {
        tab.addEventListener("click", () => {
            document.querySelectorAll(".modal-tab").forEach(t => t.classList.remove("active"));
            tab.classList.add("active");
            const isLogin = tab.dataset.auth === "login";
            document.getElementById("loginForm").style.display = isLogin ? "block" : "none";
            document.getElementById("signupForm").style.display = isLogin ? "none" : "block";
            document.getElementById("loginError").textContent = "";
            document.getElementById("signupError").textContent = "";
        });
    });

    // Login form
    document.getElementById("loginForm").addEventListener("submit", async (e) => {
        e.preventDefault();
        const email = document.getElementById("loginEmail").value.trim();
        const password = document.getElementById("loginPassword").value;
        const errEl = document.getElementById("loginError");
        errEl.textContent = "";

        try {
            const res = await fetch(`${API}/api/auth/login`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ email, password }),
            });
            const data = await res.json();
            if (data.success) {
                currentUser = data.user;
                modal.classList.remove("open");
                // Clear login form
                document.getElementById("loginEmail").value = "";
                document.getElementById("loginPassword").value = "";
                switchToDashboard();
            } else {
                errEl.textContent = data.error || "Login failed";
            }
        } catch (err) {
            errEl.textContent = "Connection error. Is the server running?";
        }
    });

    // Signup form
    document.getElementById("signupForm").addEventListener("submit", async (e) => {
        e.preventDefault();
        const name = document.getElementById("signupName").value.trim();
        const email = document.getElementById("signupEmail").value.trim();
        const password = document.getElementById("signupPassword").value;
        const errEl = document.getElementById("signupError");
        errEl.textContent = "";

        try {
            const res = await fetch(`${API}/api/auth/signup`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ name, email, password }),
            });
            const data = await res.json();
            if (data.success) {
                currentUser = data.user;
                modal.classList.remove("open");
                // Clear signup form
                document.getElementById("signupName").value = "";
                document.getElementById("signupEmail").value = "";
                document.getElementById("signupPassword").value = "";
                switchToDashboard();
            } else {
                errEl.textContent = data.error || "Signup failed";
            }
        } catch (err) {
            errEl.textContent = "Connection error. Is the server running?";
        }
    });
}

function openAuthModal(tab = "login") {
    const modal = document.getElementById("authModal");
    modal.classList.add("open");
    document.querySelectorAll(".modal-tab").forEach(t => {
        t.classList.toggle("active", t.dataset.auth === tab);
    });
    document.getElementById("loginForm").style.display = tab === "login" ? "block" : "none";
    document.getElementById("signupForm").style.display = tab === "signup" ? "block" : "none";
    document.getElementById("loginError").textContent = "";
    document.getElementById("signupError").textContent = "";
}


/* ═══════════════════════════════════════════════════════════════════
   AUTH STATUS & VIEW SWITCHING
   ═══════════════════════════════════════════════════════════════════ */
async function checkAuthStatus() {
    try {
        const res = await fetch(`${API}/api/auth/status`);
        const data = await res.json();
        if (data.authenticated) {
            currentUser = data.user;
            switchToDashboard();
        } else {
            switchToLanding();
        }
    } catch {
        switchToLanding();
    }
}

function switchToDashboard() {
    if (!currentUser) {
        switchToLanding();
        return;
    }

    // 1. Destroy demo charts FIRST (they live inside the landing view)
    destroyDemoCharts();

    // 1.5. Clear dashboard UI explicitly
    resetDashboardUI();

    // 2. Hide landing, hide settings, show dashboard
    document.getElementById("landingView").style.display = "none";
    document.getElementById("settingsView").style.display = "none";
    document.getElementById("dashboardView").style.display = "block";

    // 3. Nav: hide demo badge & auth buttons, show user info
    document.getElementById("navDemoBadge").style.display = "none";
    document.getElementById("navAuthBtns").style.display = "none";
    document.getElementById("navUserInfo").style.display = "flex";

    // 4. Set user info
    if (currentUser) {
        document.getElementById("userName").textContent = currentUser.name;
        document.getElementById("userAvatar").textContent = currentUser.name.charAt(0).toUpperCase();
    }

    // 5. Reset nav score to loading state
    document.getElementById("navScore").textContent = "...";

    // 6. Initialize dashboard (only attach events once)
    initDashboard();
}

function switchToLanding() {
    // 1. Destroy dashboard charts completely
    destroyDashboardCharts();

    // 2. Reset all dashboard UI to defaults
    resetDashboardUI();

    // 3. Show landing, hide dashboard, hide settings
    document.getElementById("landingView").style.display = "block";
    document.getElementById("dashboardView").style.display = "none";
    document.getElementById("settingsView").style.display = "none";

    // 4. Nav: show demo badge & auth buttons, hide user info
    document.getElementById("navDemoBadge").style.display = "flex";
    document.getElementById("navAuthBtns").style.display = "flex";
    document.getElementById("navUserInfo").style.display = "none";

    // 5. Reset nav score for demo mode
    document.getElementById("navScore").textContent = "--";
    const badge = document.getElementById("navHealthBadge");
    badge.style.background = "rgba(34,197,94,0.1)";
    badge.style.borderColor = "rgba(34,197,94,0.2)";
    badge.style.color = "#22c55e";

    // 6. Render demo charts fresh
    renderDemoCharts();
    renderDemoInsights();
}

async function handleLogout() {
    // 1. Call server logout
    try {
        await fetch(`${API}/api/auth/logout`, { method: "POST" });
    } catch {}

    // 2. Clear user state
    currentUser = null;

    // 3. Switch to landing (this handles all cleanup)
    switchToLanding();
}


/* ═══════════════════════════════════════════════════════════════════
   CHART CLEANUP HELPERS
   ═══════════════════════════════════════════════════════════════════ */
function destroyDemoCharts() {
    if (demoPieChart) { demoPieChart.destroy(); demoPieChart = null; }
    if (demoLineChart) { demoLineChart.destroy(); demoLineChart = null; }
}

function destroyDashboardCharts() {
    if (pieChart) { pieChart.destroy(); pieChart = null; }
    if (lineChart) { lineChart.destroy(); lineChart = null; }
}

function resetDashboardUI() {
    // Reset stat cards
    document.getElementById("totalSpent").textContent = "₹0";
    document.getElementById("healthScore").textContent = "0";
    document.getElementById("riskLevel").textContent = "--";
    document.getElementById("riskLevel").style.color = "";
    document.getElementById("personalityType").textContent = "--";
    document.getElementById("predictedMonthly").textContent = "₹0";
    document.getElementById("trendDirection").textContent = "--";
    document.getElementById("trendDirection").style.color = "";
    document.getElementById("scoreBar").style.width = "0%";

    // Reset insights
    document.getElementById("keyIssues").innerHTML = '<li class="placeholder">Add transactions to see insights</li>';
    document.getElementById("behaviorPatterns").innerHTML = '<li class="placeholder">Add transactions to see patterns</li>';
    document.getElementById("riskFactors").innerHTML = '<li class="placeholder">Add transactions to see risks</li>';

    // Reset recommendations
    document.getElementById("recommendations").innerHTML = '<div class="placeholder-msg">Add transactions to get personalized recommendations.</div>';

    // Reset trend details
    document.getElementById("trendLast7").textContent = "--";
    document.getElementById("trendPrev7").textContent = "--";
    document.getElementById("trendChange").textContent = "--";
    document.getElementById("trendChange").className = "dv";
    document.getElementById("trendWeekend").textContent = "--";
    document.getElementById("trendWeekend").className = "dv";
    document.getElementById("trendAvgWeekday").textContent = "--";
    document.getElementById("trendAvgWeekend").textContent = "--";
    document.getElementById("spikeSection").style.display = "none";

    // Reset payment list
    document.getElementById("paymentList").innerHTML = '<div class="placeholder-msg">No transactions yet. Start by adding your first expense.</div>';
    document.getElementById("txnCount").textContent = "0 payments";

    // Reset decision result
    document.getElementById("decisionResult").style.display = "none";
    document.getElementById("decisionResult").innerHTML = "";

    // Reset what-if result
    document.getElementById("simResult").style.display = "none";

    // Reset alert banner
    document.getElementById("alertBanner").style.display = "none";

    // Reset tabs to first tab
    document.querySelectorAll(".tab").forEach(t => t.classList.remove("active"));
    document.querySelectorAll(".tab-content").forEach(c => c.classList.remove("active"));
    const firstTab = document.querySelector('.tab[data-tab="insights"]');
    if (firstTab) firstTab.classList.add("active");
    const firstContent = document.getElementById("tab-insights");
    if (firstContent) firstContent.classList.add("active");
}


/* ═══════════════════════════════════════════════════════════════════
   DEMO MODE — Landing Page (Static frontend data only)
   ═══════════════════════════════════════════════════════════════════ */
function renderDemoCharts() {
    const colors = {
        Food: "#6366f1", Transport: "#06b6d4", Shopping: "#a855f7",
        Bills: "#f59e0b", Entertainment: "#ec4899", Others: "#64748b"
    };

    // Demo Pie
    const pCtx = document.getElementById("demoPieChart");
    if (pCtx) {
        // Ensure clean canvas
        if (demoPieChart) { demoPieChart.destroy(); demoPieChart = null; }
        const cats = Object.keys(DEMO_DATA.categoryTotals);
        const vals = Object.values(DEMO_DATA.categoryTotals);
        demoPieChart = new Chart(pCtx.getContext("2d"), {
            type: "doughnut",
            data: {
                labels: cats,
                datasets: [{ data: vals, backgroundColor: cats.map(c => colors[c]), borderWidth: 0, hoverOffset: 6 }],
            },
            options: {
                responsive: true, maintainAspectRatio: false, cutout: "62%",
                plugins: { legend: { position: "bottom", labels: { color: "#94a3b8", boxWidth: 10, padding: 12, font: { size: 11, family: "'Inter'" } } } },
            },
        });
    }

    // Demo Line
    const lCtx = document.getElementById("demoLineChart");
    if (lCtx) {
        if (demoLineChart) { demoLineChart.destroy(); demoLineChart = null; }
        const dates = Object.keys(DEMO_DATA.dailySpending);
        const vals = Object.values(DEMO_DATA.dailySpending);
        demoLineChart = new Chart(lCtx.getContext("2d"), {
            type: "line",
            data: {
                labels: dates,
                datasets: [{
                    label: "Daily Spending",
                    data: vals,
                    borderColor: "#6366f1",
                    backgroundColor: "rgba(99,102,241,0.06)",
                    borderWidth: 2.5, fill: true, tension: 0.3,
                    pointRadius: 4, pointBackgroundColor: "#6366f1", pointBorderWidth: 0,
                }],
            },
            options: {
                responsive: true, maintainAspectRatio: false,
                scales: {
                    x: { grid: { color: "rgba(30,41,59,0.4)" }, ticks: { color: "#64748b", font: { size: 10 } } },
                    y: { grid: { color: "rgba(30,41,59,0.4)" }, ticks: { color: "#64748b", font: { size: 10 }, callback: v => "₹" + v.toLocaleString() } },
                },
                plugins: { legend: { display: false } },
            },
        });
    }
}

function renderDemoInsights() {
    fillDemoList("demoIssues", DEMO_DATA.insights.issues, "#ef4444");
    fillDemoList("demoPatterns", DEMO_DATA.insights.patterns, "#a855f7");
    fillDemoList("demoRisks", DEMO_DATA.insights.risks, "#f59e0b");
}

function fillDemoList(id, items, color) {
    const ul = document.getElementById(id);
    if (!ul) return;
    ul.innerHTML = "";
    items.forEach(text => {
        const li = document.createElement("li");
        li.textContent = text;
        li.style.borderLeftColor = color;
        ul.appendChild(li);
    });
}


/* ═══════════════════════════════════════════════════════════════════
   DASHBOARD MODE — Authenticated User (Real data only)
   ═══════════════════════════════════════════════════════════════════ */
function initDashboard() {
    document.getElementById("txnDate").valueAsDate = new Date();

    // Only attach event listeners ONCE
    if (!_dashboardInitialized) {
        initTabs();
        document.getElementById("txnForm").addEventListener("submit", handleAddTransaction);
        document.getElementById("simBtn").addEventListener("click", runSimulation);
        document.getElementById("decisionForm").addEventListener("submit", handleDecisionCheck);
        _dashboardInitialized = true;
    }

    // Always fetch fresh data on dashboard entry
    loadAnalysis();
}

async function handleUpdateSalary(e) {
    e.preventDefault();
    const btn = document.getElementById("updateSalaryBtn");
    btn.disabled = true;
    btn.textContent = "Updating...";

    const salaryElem = document.getElementById("monthlySalary");
    if (!salaryElem) return;
    const salary = parseFloat(salaryElem.value);

    try {
        const res = await fetch(`${API}/api/user/salary`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ salary }),
        });
        const data = await res.json();
        if (data.success) {
            document.getElementById("salaryAlertBanner").style.display = "none";
            btn.textContent = "Saved";
            setTimeout(() => { btn.textContent = "Update Income" }, 2000);
        } else {
             btn.textContent = "Update Income";
        }
    } catch (err) {
        console.error("Salary update error:", err);
        btn.textContent = "Update Income";
    }
    btn.disabled = false;
}

function initTabs() {
    document.querySelectorAll(".tab").forEach(btn => {
        btn.addEventListener("click", () => {
            document.querySelectorAll(".tab").forEach(t => t.classList.remove("active"));
            document.querySelectorAll(".tab-content").forEach(c => c.classList.remove("active"));
            btn.classList.add("active");
            document.getElementById("tab-" + btn.dataset.tab).classList.add("active");
        });
    });
}

async function loadAnalysis() {
    try {
        const [txnRes, analysisRes] = await Promise.all([
            fetch(`${API}/api/transactions`),
            fetch(`${API}/api/analysis`),
        ]);
        const txnData = await txnRes.json();
        const analysis = await analysisRes.json();

        if (analysis.error) {
            // Show empty state
            document.getElementById("totalSpent").textContent = "₹0";
            document.getElementById("healthScore").textContent = "N/A";
            document.getElementById("navScore").textContent = "N/A";
            
            if (analysis.error.includes("Configuration required")) {
                document.getElementById("salaryAlertBanner").style.display = "flex";
            }
            if (txnData && txnData.transactions) {
                renderTable(txnData.transactions);
            }
            return;
        }

        renderStats(analysis);
        renderInsights(analysis.insights);
        renderRecommendations(analysis.recommendations);
        renderTrend(analysis.trend_analysis);
        renderTable(txnData.transactions);
        renderCharts(analysis, txnData.transactions);
        renderAlerts(analysis);
    } catch (err) {
        console.error("Load error:", err);
    }
}

async function handleAddTransaction(e) {
    e.preventDefault();
    const btn = document.getElementById("submitBtn");
    btn.disabled = true;
    btn.textContent = "Processing...";

    const body = {
        date: document.getElementById("txnDate").value,
        amount: parseFloat(document.getElementById("txnAmount").value),
        category: document.getElementById("txnCategory").value,
    };

    try {
        const res = await fetch(`${API}/api/add_transaction`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(body),
        });
        const data = await res.json();
        if (data.success) {
            document.getElementById("txnAmount").value = "";
            document.getElementById("txnCategory").value = "";
            loadAnalysis();
        }
    } catch (err) {
        console.error("Add error:", err);
    }
    btn.disabled = false;
    btn.textContent = "Add & Analyze";
}

function renderStats(a) {
    const sa = a.spending_analysis;
    const hs = a.financial_health_score;
    const fp = a.financial_personality;
    const sp = a.spending_prediction;
    const ta = a.trend_analysis;

    document.getElementById("totalSpent").textContent = "₹" + sa.total_spending.toLocaleString();
    document.getElementById("healthScore").textContent = hs.score + "/100";
    document.getElementById("navScore").textContent = hs.score;
    document.getElementById("predictedMonthly").textContent = "₹" + sp.predicted_monthly_spending.toLocaleString();
    document.getElementById("personalityType").textContent = fp.type;

    const riskEl = document.getElementById("riskLevel");
    riskEl.textContent = hs.risk_level;
    riskEl.style.color = hs.risk_level === "HIGH" ? "#ef4444" : hs.risk_level === "MEDIUM" ? "#f59e0b" : "#22c55e";

    const trendEl = document.getElementById("trendDirection");
    const label = ta.trend.charAt(0).toUpperCase() + ta.trend.slice(1);
    const sign = ta.change_percent > 0 ? "+" : "";
    trendEl.textContent = `${label} (${sign}${ta.change_percent}%)`;
    trendEl.style.color = ta.trend === "increasing" ? "#ef4444" : ta.trend === "decreasing" ? "#22c55e" : "#06b6d4";

    document.getElementById("scoreBar").style.width = hs.score + "%";

    const badge = document.getElementById("navHealthBadge");
    if (hs.score >= 75) { badge.style.background="rgba(34,197,94,0.1)"; badge.style.borderColor="rgba(34,197,94,0.2)"; badge.style.color="#22c55e"; }
    else if (hs.score >= 50) { badge.style.background="rgba(245,158,11,0.1)"; badge.style.borderColor="rgba(245,158,11,0.2)"; badge.style.color="#f59e0b"; }
    else { badge.style.background="rgba(239,68,68,0.1)"; badge.style.borderColor="rgba(239,68,68,0.2)"; badge.style.color="#ef4444"; }
}

function renderInsights(ins) {
    fillList("keyIssues", ins.key_issues, "#ef4444");
    fillList("behaviorPatterns", ins.behavior_patterns, "#a855f7");
    fillList("riskFactors", ins.risk_factors, "#f59e0b");
}
function fillList(id, items, color) {
    const ul = document.getElementById(id);
    if (!ul) return;
    ul.innerHTML = "";
    items.forEach(text => {
        const li = document.createElement("li");
        li.textContent = text;
        li.style.borderLeftColor = color;
        ul.appendChild(li);
    });
}

function renderRecommendations(recs) {
    const panel = document.getElementById("recommendations");
    panel.innerHTML = "";
    recs.forEach(r => {
        const div = document.createElement("div");
        div.className = `rec-card p-${r.priority}`;
        div.innerHTML = `
            <span class="rec-badge ${r.priority}">${r.priority}</span>
            <div class="rec-cat">${r.category}</div>
            <div class="rec-action">${r.action}</div>
            <div class="rec-impact">${r.impact}</div>
        `;
        panel.appendChild(div);
    });
}

function renderTrend(t) {
    document.getElementById("trendLast7").textContent = "₹" + t.last_7_days_total.toLocaleString();
    document.getElementById("trendPrev7").textContent = "₹" + t.prev_7_days_total.toLocaleString();

    const changeEl = document.getElementById("trendChange");
    changeEl.textContent = (t.change_percent > 0 ? "+" : "") + t.change_percent + "%";
    changeEl.className = "dv " + (t.change_percent > 15 ? "up" : t.change_percent < -15 ? "down" : "stable");

    const weekendEl = document.getElementById("trendWeekend");
    weekendEl.textContent = t.weekend_spending_spike ? "Yes ⚠️" : "No ✓";
    weekendEl.className = "dv " + (t.weekend_spending_spike ? "up" : "stable");

    document.getElementById("trendAvgWeekday").textContent = "₹" + t.avg_weekday_spending.toLocaleString();
    document.getElementById("trendAvgWeekend").textContent = "₹" + t.avg_weekend_spending.toLocaleString();

    if (t.irregular_spikes && t.irregular_spikes.length > 0) {
        document.getElementById("spikeSection").style.display = "block";
        document.getElementById("spikeList").innerHTML = t.irregular_spikes
            .map(s => `<span class="spike-item">${s.date}: ₹${s.amount.toLocaleString()}</span>`)
            .join("");
    }
}

function renderTable(txns) {
    const list = document.getElementById("paymentList");
    list.innerHTML = "";
    document.getElementById("txnCount").textContent = txns.length + " payments";

    if (txns.length === 0) {
        list.innerHTML = '<div class="placeholder-msg">No transactions yet. Start by adding your first expense.</div>';
        return;
    }

    const emoji = { Food:"🍕", Transport:"🚗", Shopping:"🛍️", Bills:"📄", Entertainment:"🎬", Others:"📦" };
    const sorted = [...txns].sort((a, b) => b.date.localeCompare(a.date));

    let currentDate = "";
    sorted.forEach(t => {
        if (t.date !== currentDate) {
            currentDate = t.date;
            const header = document.createElement("div");
            header.className = "payment-date-group";
            header.textContent = formatDateLabel(t.date);
            list.appendChild(header);
        }

        const item = document.createElement("div");
        item.className = "payment-item";
        item.innerHTML = `
            <div class="pay-icon ${t.category}">${emoji[t.category] || "📦"}</div>
            <div class="pay-info">
                <div class="pay-name">${t.category}</div>
                <div class="pay-date">${t.date}</div>
            </div>
            <div class="pay-amount">- ₹${parseFloat(t.amount).toLocaleString()}</div>
        `;
        list.appendChild(item);
    });
}

function formatDateLabel(dateStr) {
    const d = new Date(dateStr + "T00:00:00");
    const today = new Date();
    today.setHours(0,0,0,0);
    const diff = Math.floor((today - d) / 86400000);
    if (diff === 0) return "Today";
    if (diff === 1) return "Yesterday";
    if (diff < 7) return d.toLocaleDateString("en-IN", { weekday: "long" });
    return d.toLocaleDateString("en-IN", { day: "numeric", month: "short", year: "numeric" });
}

function renderCharts(analysis, transactions) {
    const sa = analysis.spending_analysis;
    const colors = {
        Food: "#6366f1", Transport: "#06b6d4", Shopping: "#a855f7",
        Bills: "#f59e0b", Entertainment: "#ec4899", Others: "#64748b"
    };
    const cats = Object.keys(sa.category_totals);
    const vals = Object.values(sa.category_totals);

    // Destroy existing dashboard charts before re-creating
    destroyDashboardCharts();

    const pCtx = document.getElementById("pieChart").getContext("2d");
    pieChart = new Chart(pCtx, {
        type: "doughnut",
        data: {
            labels: cats,
            datasets: [{ data: vals, backgroundColor: cats.map(c => colors[c] || "#6366f1"), borderWidth: 0, hoverOffset: 6 }],
        },
        options: {
            responsive: true, maintainAspectRatio: false, cutout: "62%",
            plugins: { legend: { position: "bottom", labels: { color: "#94a3b8", boxWidth: 10, padding: 12, font: { size: 11, family: "'Inter'" } } } },
        },
    });

    const lCtx = document.getElementById("lineChart").getContext("2d");
    const dailyMap = {};
    transactions.forEach(t => { dailyMap[t.date] = (dailyMap[t.date] || 0) + parseFloat(t.amount); });
    const dates = Object.keys(dailyMap).sort();
    const dailyVals = dates.map(d => dailyMap[d]);

    lineChart = new Chart(lCtx, {
        type: "line",
        data: {
            labels: dates.map(d => d.slice(5)),
            datasets: [{
                label: "Daily Spending",
                data: dailyVals,
                borderColor: "#6366f1",
                backgroundColor: "rgba(99,102,241,0.06)",
                borderWidth: 2.5, fill: true, tension: 0.3,
                pointRadius: 3, pointBackgroundColor: "#6366f1", pointBorderWidth: 0,
            }],
        },
        options: {
            responsive: true, maintainAspectRatio: false,
            scales: {
                x: { grid: { color: "rgba(30,41,59,0.4)" }, ticks: { color: "#64748b", font: { size: 10 } } },
                y: { grid: { color: "rgba(30,41,59,0.4)" }, ticks: { color: "#64748b", font: { size: 10 }, callback: v => "₹" + v.toLocaleString() } },
            },
            plugins: { legend: { display: false }, tooltip: { callbacks: { label: ctx => "₹" + ctx.parsed.y.toLocaleString() } } },
        },
    });
}

function renderAlerts(a) {
    const banner = document.getElementById("alertBanner");
    const ta = a.trend_analysis;
    if (ta.change_percent > 25) {
        document.getElementById("alertText").textContent = `⚡ Spending increased by ${ta.change_percent}% this week compared to last week`;
        banner.style.display = "flex";
        banner.style.background = "rgba(245,158,11,0.1)";
        banner.style.borderColor = "rgba(245,158,11,0.25)";
        banner.style.color = "#f59e0b";
    } else if (a.financial_health_score.risk_level === "HIGH") {
        document.getElementById("alertText").textContent = `🔴 Financial health score is critically low (${a.financial_health_score.score}/100)`;
        banner.style.display = "flex";
        banner.style.background = "rgba(239,68,68,0.1)";
        banner.style.borderColor = "rgba(239,68,68,0.25)";
        banner.style.color = "#ef4444";
    } else {
        banner.style.display = "none";
    }
}

async function runSimulation() {
    const cat = document.getElementById("wifCategory").value;
    const pct = parseFloat(document.getElementById("wifPercent").value);
    try {
        const res = await fetch(`${API}/api/whatif`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ category: cat, percent: pct }),
        });
        const data = await res.json();
        const div = document.getElementById("simResult");
        div.style.display = "block";
        const sc = data.score_change > 0 ? "positive" : data.score_change < 0 ? "negative" : "";
        div.innerHTML = `
            <div class="sim-row"><span class="sim-label">Category</span><span class="sim-val">${data.category_adjusted}</span></div>
            <div class="sim-row"><span class="sim-label">Adjustment</span><span class="sim-val">${data.adjustment_percent>0?"+":""}${data.adjustment_percent}%</span></div>
            <div class="sim-row"><span class="sim-label">Score Change</span><span class="sim-val ${sc}">${data.score_change>0?"+":""}${data.score_change}</span></div>
            <div class="sim-row"><span class="sim-label">New Score</span><span class="sim-val">${data.new_score}/100</span></div>
            <div class="sim-row"><span class="sim-label">Monthly Impact</span><span class="sim-val ${data.new_monthly<data.original_monthly?"positive":"negative"}">₹${Math.abs(data.new_monthly-data.original_monthly).toLocaleString()}</span></div>
        `;
    } catch (err) { console.error("Sim error:", err); }
}

async function handleDecisionCheck(e) {
    e.preventDefault();
    const btn = document.getElementById("decButton");
    btn.disabled = true;
    btn.textContent = "Analyzing...";
    
    const body = {
        amount: parseFloat(document.getElementById("decAmount").value),
        category: document.getElementById("decCategory").value,
    };
    
    try {
        const res = await fetch(`${API}/api/check_affordability`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(body),
        });
        const data = await res.json();
        
        const div = document.getElementById("decisionResult");
        div.style.display = "block";
        
        if (data.error) {
            div.innerHTML = `<div style="color: #ef4444; font-weight: bold; margin-bottom: 10px;">❌ Error</div><div style="color:#cbd5e1">${data.error}</div>`;
            btn.disabled = false;
            btn.textContent = "Check Affordability";
            return;
        }

        const rl = data.risk_level;
        let color = rl === "HIGH" ? "#ef4444" : rl === "MEDIUM" ? "#f59e0b" : "#22c55e";
        
        div.innerHTML = `
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:15px; padding-bottom:15px; border-bottom:1px solid rgba(255,255,255,0.1)">
                <div>
                    <div style="font-size:12px; color:#94a3b8; text-transform:uppercase; margin-bottom:4px;">Risk Level</div>
                    <div style="font-size:24px; font-weight:bold; color:${color}; margin-top:0">${rl}</div>
                    <div style="font-size:12px; color:#64748b; margin-top:2px;">Necessity: <strong>${data.necessity}</strong></div>
                </div>
                <!-- Risk Bar Visualization -->
                <div style="width: 140px;">
                    <div style="font-size:12px; color:#94a3b8; margin-bottom:4px; text-align:right;">Risk Score: ${data.risk_score}%</div>
                    <div style="width:100%; height:8px; border-radius:4px; background:rgba(0,0,0,0.4); overflow:hidden;">
                        <div style="height:100%; width:${data.risk_score}%; background:${color};"></div>
                    </div>
                </div>
            </div>
            
            <div style="display:grid; gap: 12px;">
                <div style="background:rgba(0,0,0,0.2); padding:12px; border-radius:6px; border-left:3px solid ${color};">
                    <span style="font-size:16px;">${rl==="HIGH"?"⚠️":rl==="MEDIUM"?"⚡":"✅"}</span>
                    <span style="color:#e2e8f0; font-weight:500; font-size:14px; margin-left:6px;">${data.affordability_check}</span>
                </div>
                
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-top: 5px;">
                    <div style="padding:10px; background:rgba(0,0,0,0.15); border-radius:6px;">
                        <div style="font-size:11px; color:#94a3b8; text-transform:uppercase;">Insights</div>
                        <div style="font-size:13px; color:#cbd5e1; margin-top:4px;">${data.insight}</div>
                    </div>
                    <div style="padding:10px; background:rgba(0,0,0,0.15); border-radius:6px;">
                        <div style="font-size:11px; color:#94a3b8; text-transform:uppercase;">Budget Impact</div>
                        <div style="font-size:13px; color:#cbd5e1; margin-top:4px;">${data.impact}</div>
                    </div>
                    <div style="padding:10px; background:rgba(0,0,0,0.15); border-radius:6px;">
                        <div style="font-size:11px; color:#94a3b8; text-transform:uppercase;">Goal Impact</div>
                        <div style="font-size:13px; color:#cbd5e1; margin-top:4px;">${data.goal_impact}</div>
                    </div>
                    <div style="padding:10px; background:rgba(0,0,0,0.15); border-radius:6px;">
                        <div style="font-size:11px; color:#94a3b8; text-transform:uppercase;">Future Prediction</div>
                        <div style="font-size:13px; color:#cbd5e1; margin-top:4px;">${data.future_prediction}</div>
                    </div>
                </div>
                
                <div style="margin-top: 8px; padding-top: 15px; border-top: 1px solid rgba(255,255,255,0.05); font-size: 13px; color: #94a3b8;">
                    <strong>Smart Suggestion:</strong><br>
                    <span style="color: #06b6d4;">${data.smart_suggestion.replace(/\n/g, '<br>')}</span>
                </div>
            </div>
        `;
    } catch (err) {
        const div = document.getElementById("decisionResult");
        div.style.display = "block";
        div.innerHTML = `<div style="color: #ef4444; font-weight: bold; margin-bottom: 10px;">❌ Error</div><div style="color:#cbd5e1">${err.message}</div>`;
    }
    
    btn.disabled = false;
    btn.textContent = "Check Affordability";
}
