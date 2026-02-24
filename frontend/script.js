/* =====================
   GLOBAL STATE
===================== */
let hasPin = false;
let isSignup = false;

/* =====================
   AUTH TOGGLE
===================== */
function toggleAuth() {
  isSignup = !isSignup;

  document.getElementById("form-slider").style.transform =
    isSignup ? "translateX(-50%)" : "translateX(0)";

  document.getElementById("toggle-indicator").style.transform =
    isSignup ? "translateX(100%)" : "translateX(0)";
}

/* =====================
   SIGNUP
===================== */
async function signup() {
  const firstName = document.getElementById("signup-firstname").value.trim();
  const lastName = document.getElementById("signup-lastname").value.trim();
  const email = document.getElementById("signup-email").value.trim();
  const password = document.getElementById("signup-password").value;
  const password2 = document.getElementById("signup-password2").value;
  const msg = document.getElementById("signup-message");

  msg.innerText = "";

  if (!firstName || !lastName || !email || !password || !password2) {
    msg.innerText = "All fields are required";
    return;
  }

  if (password !== password2) {
    msg.innerText = "Passwords do not match";
    return;
  }

  const res = await fetch("/api/users/signup/", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-CSRFToken": getCsrfToken()
    },
    credentials: "same-origin",
    body: JSON.stringify({
      first_name: firstName,
      last_name: lastName,
      email:email,
      password:password
    })
  });

  const data = await res.json().catch(() => ({}));

  
  if(res.ok)
  {
    
    document.getElementById("signup-section").reset();
    msg.innerText = "Account created. Please log in.";
  }
  else
  {
    msg.innerText=data.detail || "Signup failed";
  }
}

/* =====================
   LOGIN / LOGOUT
===================== */
async function login() {
  const email = document.getElementById("login-email").value;
  const password = document.getElementById("login-password").value;
  const msg = document.getElementById("login-message");

  msg.innerText = "";

  const res = await fetch("/api/users/login/", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-CSRFToken": getCsrfToken()
    },
    credentials: "same-origin",
    body: JSON.stringify({ email, password })
  });

  const data = await res.json();

  if (!res.ok) {
    msg.innerText = data.detail ||   data.error ||  data.message ||"Login failed";
    return;
  }

  document.getElementById("login-section").reset();
  await loadProfile();
  showApp();
  showSection("balance");
  loadRequests();
}

function logout() {
  fetch("/api/users/logout/", {
    method: "POST",
    headers: { "X-CSRFToken": getCsrfToken() },
    credentials: "same-origin"
  });

  hideApp();
  showLogin();
}

/* =====================
   APP VISIBILITY
===================== */
function showApp() {
  document.getElementById("landing-container").style.display = "none";
  document.getElementById("app-container").style.display = "block";
  document.getElementById("pin-form").classList.remove("active");
  
  const btn = document.getElementById("pin-toggle-btn");

  btn.innerText = (hasPin ? "Change Transaction PIN" : "Set Transaction PIN");
}

function hideApp() {
  resetAppState();
  document.getElementById("app-container").style.display = "none";
  document.getElementById("landing-container").style.display = "flex";
}


function resetAppState() {

  /* =========================
     1️⃣ Reset Landing Forms
  ========================== */

  document.getElementById("login-section")?.reset();
  document.getElementById("signup-section")?.reset();

  document.getElementById("login-message").innerText = "";
  document.getElementById("signup-message").innerText = "";

  // Reset auth slider to Login position
  document.getElementById("form-slider").style.transform = "translateX(0%)";
  document.getElementById("toggle-indicator").style.left = "0%";


  /* =========================
     2️⃣ Clear Profile Info
  ========================== */

  document.getElementById("welcome-text").innerText = "";
  document.getElementById("profile-email").innerText = "";
  document.getElementById("profile-wallet").innerText = "";

  document.getElementById("profile-bar").style.display = "none";


  /* =========================
     3️⃣ Clear PIN Section
  ========================== */

  document.getElementById("pin-1").value = "";
  document.getElementById("pin-2").value = "";
  document.getElementById("pin-message").innerText = "";
  document.getElementById("pin-form").classList.remove("show");


  /* =========================
     4️⃣ Clear All Inputs Inside App
  ========================== */

  const inputsToClear = [
    "search-query",
    "credit-amount",
    "transfer-to",
    "transfer-amount",
    "transfer-pin",
    "request-to",
    "request-amount",
    "request-note"
  ];

  inputsToClear.forEach(id => {
    const el = document.getElementById(id);
    if (el) el.value = "";
  });


  /* =========================
     5️⃣ Clear Messages
  ========================== */

  const messageIds = [
    "balance-display",
    "credit-message",
    "transfer-message",
    "request-msg"
  ];

  messageIds.forEach(id => {
    const el = document.getElementById(id);
    if (el) el.innerText = "";
  });


  /* =========================
     6️⃣ Clear Lists
  ========================== */

  const listIds = [
    "search-results",
    "incoming-requests",
    "outgoing-requests",
    "history-list"
  ];

  listIds.forEach(id => {
    const el = document.getElementById(id);
    if (el) el.innerHTML = "";
  });


  /* =========================
     7️⃣ Hide All Sections
  ========================== */

  document.querySelectorAll(".section").forEach(sec => {
  sec.classList.remove("active");
});


  /* =========================
     8️⃣ Reset Nav Active State
  ========================== */

  document.querySelectorAll("#nav-bar button").forEach(btn => {
    btn.classList.remove("active");
  });
}

function showLogin() {
  isSignup = false;
  toggleAuth();
  toggleAuth();
}

/* =====================
   NAVIGATION
===================== */


function showSection(section) {
  document.querySelectorAll(".section").forEach(s =>
    s.classList.remove("active")
  );

  document.querySelectorAll("#nav-bar button").forEach(b =>
    b.classList.remove("active")
  );

  const map = {
    balance: "balance-section",
    transfer: "transfer-section",
    search: "search-section",
    request: "request-section",
    requests: "requests-section",
    history: "history-section",
    credit: "credit-section"
  };

  const el = document.getElementById(map[section]);
  if (!el) {
    console.error("Section not found:", map[section]);
    return;
  }

  el.classList.add("active");

  if (section === "balance") loadBalance();
  if (section === "history") loadTransactions();
  if (section === "requests") loadRequests();
}


function clearSectionUI() {
  document.getElementById("balance-display").innerText = "";
  document.getElementById("search-results").innerHTML = "";
  document.getElementById("transfer-message").innerText = "";
  document.getElementById("credit-message").innerText = "";
  document.getElementById("history-list").innerHTML = "";
}


/* =====================
   PROFILE
===================== */
async function loadProfile() {
  const res = await fetch("/api/users/balance/", {
    credentials: "same-origin"
  });

  if (!res.ok) return;

  const data = await res.json();

  document.getElementById("profile-bar").style.display = "flex";
  document.getElementById("welcome-text").innerText =
    `Hi ${data.first_name || "there"} 👋`;

  document.getElementById("profile-email").innerText =
    `email: ${data.email}`;

  document.getElementById("profile-wallet").innerText =
    `walletId: ${data.walletId}`;

  hasPin = data.has_pin;
}

/* =====================
   PIN
===================== */
function togglePinForm() {
  const form = document.getElementById("pin-form");
  const btn = document.getElementById("pin-toggle-btn");

  const open = form.classList.toggle("active");
  btn.innerText = open
    ? "Close PIN Form"
    : (hasPin ? "Change Transaction PIN" : "Set Transaction PIN");
}

async function submitPin() {
  const p1 = document.getElementById("pin-1").value;
  const p2 = document.getElementById("pin-2").value;
  const msg = document.getElementById("pin-message");
  const btn = document.getElementById("pin-toggle-btn");
  const form = document.getElementById("pin-form");

  msg.innerText = "";

  if (!p1 || p1 !== p2) {
    msg.innerText = "PINs must match";
    return;
  }

  const res = await fetch("/api/users/set-pin/", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-CSRFToken": getCsrfToken()
    },
    credentials: "same-origin",
    body: JSON.stringify({ pin: p1 })
  });

  if (res.ok) {
    hasPin = true;
    msg.innerText = "PIN updated successfully";

    form.classList.remove("active");
    btn.innerText = "Change Transaction PIN";

    document.getElementById("pin-1").value = "";
    document.getElementById("pin-2").value = "";
  } else {
    msg.innerText = "Failed to update PIN";
  }
}


/* =====================
   WALLET ACTIONS
===================== */
async function checkBalance() {
  const res = await fetch("/api/users/balance/", { credentials: "same-origin" });
  const data = await res.json();

  document.getElementById("balance-display").innerText =
    res.ok ? `₹ ${data.balance}` : "Error";
}

async function creditWallet() {
  const amount = Number(document.getElementById("credit-amount").value);
  const msg = document.getElementById("credit-message");

  if (!amount) return;

  const res = await fetch("/api/wallets/credit/", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-CSRFToken": getCsrfToken()
    },
    credentials: "same-origin",
    body: JSON.stringify({
      amount: amount * 100,
      idempotency_key: `credit-${Date.now()}`
    })
  });

  const data = await res.json();
  if(res.ok)
  {
    document.getElementById("credit-amount").value="";
    msg.innerText=data.message;
  }
  else{
    msg.innerText=data.detail ||data.error ||data.message ||"Something went wrong";
  }
}

async function transferMoney() {
  const to = document.getElementById("transfer-to").value;
  const amount = Number(document.getElementById("transfer-amount").value);
  const pin = document.getElementById("transfer-pin").value;
  const msg = document.getElementById("transfer-message");

  if (!to || isNaN(amount)  || !pin) return;

  const res = await fetch("/api/wallets/transfer/", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-CSRFToken": getCsrfToken()
    },
    credentials: "same-origin",
    body: JSON.stringify({
      to,
      amount: amount * 100,
      pin,
      idempotency_key: `transfer-${Date.now()}`
    })
  });

  const data = await res.json();
  if(res.ok)
  {
    document.getElementById("transfer-to").value="";
    document.getElementById("transfer-amount").value="";
    document.getElementById("transfer-pin").value="";
    document.getElementById("transfer-message").value="";
    msg.innerText =data.message;
  }
  else
  {
    msg.innerText =
  data.detail ||
  data.error ||
  data.message ||
  "Something went wrong";
  }
}

/* =====================
   SEARCH & REQUESTS
===================== */
async function searchUsers() {
  const q = document.getElementById("search-query").value.trim();
  const ul = document.getElementById("search-results");

  ul.innerHTML = "";

  if (!q) {
    ul.innerHTML = "<li>Enter email or wallet ID</li>";
    return;
  }

  const res = await fetch(`/api/users/search-users/?q=${encodeURIComponent(q)}`, {
    credentials: "same-origin"
  });

  if (!res.ok) {
    ul.innerHTML = "<li>Search failed</li>";
    return;
  }

  const data = await res.json();
  const users = Array.isArray(data) ? data : (data.results || []);

  if (users.length === 0) {
    ul.innerHTML = "<li>No users found</li>";
    return;
  }

  users.forEach(u => {
    const li = document.createElement("li");
    li.innerText = `${u.email} (${u.wallet_id})`;
    ul.appendChild(li);
  });
  document.getElementById("search-query").value=""
}


async function loadRequests() {

  const incomingEl = document.getElementById("incoming-requests");
  const outgoingEl = document.getElementById("outgoing-requests");

  if (!incomingEl || !outgoingEl) {
    console.error("Request UL missing");
    return;
  }

  incomingEl.innerHTML = "";
  outgoingEl.innerHTML = "";

  try {
    const res = await fetch("/api/wallets/requests/", {
      credentials: "same-origin",
    });

    if (!res.ok) throw new Error("Request API failed");

    const data = await res.json();
    console.log("Requests data:", data);

    // Incoming
    if (!data.incoming || data.incoming.length === 0) {
      incomingEl.innerHTML = "<li>No incoming requests</li>";
    } else 
    {
        incomingEl.innerHTML = "";

        data.incoming.forEach(r => {
          const li = document.createElement("li");
          li.innerHTML = `
            <div class="request-item">
              <div class="request-info">
                <strong>From:</strong> ${r.from}<br>
                <strong>Amount:</strong> ₹${r.amount}
              </div>
              <div class="request-actions">
                <button class="accept-btn"
                  onclick="respondRequest('${r.request_id}', 'ACCEPT')">
                  Accept
                </button>
                <button class="reject-btn"
                  onclick="respondRequest('${r.request_id}', 'REJECT')">
                  Reject
                </button>
              </div>
            </div>
          `;
          incomingEl.appendChild(li);
        });

    }

    // Outgoing
    if (!data.outgoing || data.outgoing.length === 0) {
      outgoingEl.innerHTML = "<li>No outgoing requests</li>";
    } else {
      data.outgoing.forEach(r => {
        const li = document.createElement("li");
        li.innerText = `To ${r.to} — ₹${r.amount}`;
        outgoingEl.appendChild(li);
      });
    }

  } catch (err) {
    console.error("loadRequests error:", err);
  }
}



function renderList(id, list, actionable) {
  const ul = document.getElementById(id);
  ul.innerHTML = "";

  if (!list || list.length === 0) {
    ul.innerHTML = "<li>None</li>";
    return;
  }

  list.forEach(r => {
    const li = document.createElement("li");
    li.innerHTML = actionable
      ? `${r.from} — ₹${r.amount}
         <button onclick="respondRequest('${r.request_id}','ACCEPT')">Accept</button>
         <button onclick="respondRequest('${r.request_id}','REJECT')">Reject</button>`
      : `${r.to} — ₹${r.amount} (Pending)`;
    ul.appendChild(li);
  });
}

async function respondRequest(id, action) {
  const payload = { action };
  if (action === "ACCEPT") {
    payload.pin = prompt("Enter PIN");
    if (!payload.pin) return;
  }

  const res=await fetch(`/api/wallets/request/${id}/respond/`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-CSRFToken": getCsrfToken()
    },
    credentials: "same-origin",
    body: JSON.stringify(payload)
  });

  if (res.ok) {
    loadRequests();
  } else {
    alert("Action failed");
  }
}

/* =====================
   UTIL
===================== */
function getCsrfToken() {
  return document.cookie
    .split(";")
    .find(c => c.trim().startsWith("csrftoken="))
    ?.split("=")[1] || "";
}

window.addEventListener("DOMContentLoaded", () => {
  document.getElementById("landing-container").style.display = "flex";
  document.getElementById("app-container").style.display = "none";
});


async function loadTransactions() {
  const listEl = document.getElementById("history-list");
  listEl.innerHTML = "<li>Loading...</li>";

  const res = await fetch("/api/wallets/transactions/", {
    credentials: "same-origin",
  });

  if (!res.ok) {
    listEl.innerHTML = "<li>Failed to load transactions</li>";
    return;
  }

  const data = await res.json();
  listEl.innerHTML = "";

  if (!Array.isArray(data) || data.length === 0) {
    listEl.innerHTML = "<li>No transactions</li>";
    return;
  }

  data.forEach(tx => {
    const li = document.createElement("li");
    const direction = tx.type.toUpperCase() === "CREDIT" ? "Received from" : "Sent to";
    li.innerText = `${tx.timestamp} | ${tx.type.toUpperCase()} | ₹${tx.amount} | ${direction}: ${tx.counterparty_email} | Txn ID: ${tx.reference}`;

    listEl.appendChild(li);
  });
}
async function loadBalance() {
  const el = document.getElementById("balance-display");
  if (!el) return;

  // reset state every time
  el.innerText = "Loading...";

  try {
    const res = await fetch("/api/users/balance/", {
      credentials: "same-origin",
    });

    if (!res.ok) throw new Error("HTTP error");

    const data = await res.json();
    el.innerText = `₹ ${data.balance}`;
  } catch (err) {
    console.error("Balance load failed", err);
    el.innerText = "";
  }
}

async function createRequest() {
  const to = document.getElementById("request-to").value.trim();
  const amount = document.getElementById("request-amount").value;
  const note = document.getElementById("request-note").value;
  const msg = document.getElementById("request-msg");

  msg.innerText = "";

  if (!to || !amount) {
    msg.innerText = "Recipient and amount required";
    return;
  }

  const res = await fetch("/api/wallets/request/", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-CSRFToken": getCsrfToken()
    },
    credentials: "same-origin",
    body: JSON.stringify({
      to,
      amount: Math.floor(amount * 100),
      note
    })
  });

  const data = await res.json();

  if (res.ok) {
    document.getElementById("request-to").value="";
  document.getElementById("request-amount").value="";
  document.getElementById("request-note").value="";
    msg.innerText = "Request sent";
    loadRequests();
  } else {
    msg.innerText = msg.innerText =
  data.detail ||
  data.error ||
  data.message ||
  "Something went wrong" || "Request failed";
  }
}


