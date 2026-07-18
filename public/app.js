// Initialize Firebase Configuration
let db;
try {
  const firebaseConfig = {
    apiKey: "AIzaSyD-EE4pIw9rD4tZmz9tKnzsd6VQzhC3ck0",
    authDomain: "cngpi-edu.firebaseapp.com",
    projectId: "cngpi-edu",
    storageBucket: "cngpi-edu.firebasestorage.app",
    messagingSenderId: "889275125335",
    appId: "1:889275125335:web:a3e8a944d1a2d429501d12"
  };

  if (typeof firebase !== 'undefined') {
    firebase.initializeApp(firebaseConfig);
    db = firebase.firestore();
  } else {
    console.warn("Firebase SDK not loaded. App will run in offline fallback mode.");
  }
} catch (e) {
  console.error("Firebase initialization failed:", e);
}

// App State
let availableGroups = [];

// DOM Elements
const groupSelectorOverlay = document.getElementById("group-selector-overlay");
const groupCodeInput = document.getElementById("group-code-input");
const groupSuggestions = document.getElementById("group-suggestions");
const btnSelectGroupSubmit = document.getElementById("btn-select-group-submit");
const headerGroupPill = document.getElementById("header-group-pill");
const headerGroupLabel = document.getElementById("header-group-label");

// Navigation Links
const cardRoutine = document.getElementById("card-routine");

// Toast Notification
const toastContainer = document.getElementById("toast-container");
function showToast(title, message, type = "success") {
  const toast = document.createElement("div");
  toast.className = `toast ${type}`;
  
  let iconName = "check-circle";
  if (type === "error") iconName = "alert-circle";
  if (type === "info") iconName = "info";

  toast.innerHTML = `
    <div class="toast-icon"><i data-lucide="${iconName}"></i></div>
    <div class="toast-content">
      <div class="toast-title">${title}</div>
      <div class="toast-message">${message}</div>
    </div>
  `;
  
  toastContainer.appendChild(toast);
  lucide.createIcons();
  
  setTimeout(() => {
    toast.style.transform = "translateY(-50px) scale(0.9)";
    toast.style.opacity = "0";
    setTimeout(() => toast.remove(), 300);
  }, 4000);
}

// Fetch Group codes from Firestore
function fetchGroups() {
  if (typeof db === 'undefined' || !db) {
    console.warn("Database offline. Using offline group codes.");
    availableGroups = ["CST 3/1", "ET 3/1"]; // fallback group codes
    return;
  }
  db.collection("routines").get().then((snapshot) => {
    availableGroups = [];
    snapshot.forEach((doc) => {
      const data = doc.data();
      availableGroups.push(data.group_short_code || doc.id);
    });
    console.log("Loaded groups:", availableGroups);
  }).catch((err) => {
    console.error("Error fetching group codes:", err);
    availableGroups = ["CST 3/1", "ET 3/1"];
  });
}

// Handle Auto-suggestions popup
function filterSuggestions() {
  const filter = groupCodeInput.value.trim().toUpperCase();
  groupSuggestions.innerHTML = "";

  if (availableGroups.length === 0) {
    groupSuggestions.classList.add("hidden");
    return;
  }

  // Filter groups matching current text input
  const matches = availableGroups.filter(g => g.toUpperCase().includes(filter));

  if (matches.length === 0) {
    groupSuggestions.classList.add("hidden");
    return;
  }

  matches.forEach(match => {
    const item = document.createElement("div");
    item.className = "suggestion-item";
    item.textContent = match;
    item.addEventListener("click", () => {
      groupCodeInput.value = match;
      groupSuggestions.classList.add("hidden");
    });
    groupSuggestions.appendChild(item);
  });

  groupSuggestions.classList.remove("hidden");
}



// Quick Group Select Cards interactive logic
const quickCardCst = document.getElementById("quick-card-cst");
const quickCardEt = document.getElementById("quick-card-et");

function selectQuickCard(selectedCode) {
  if (!quickCardCst || !quickCardEt) return;
  
  if (selectedCode === "CST 3/1") {
    quickCardCst.style.borderColor = "#5c3dff";
    quickCardCst.style.backgroundColor = "rgba(92, 61, 255, 0.04)";
    
    quickCardEt.style.borderColor = "#e2e8f0";
    quickCardEt.style.backgroundColor = "#f8fafc";
  } else if (selectedCode === "ET 3/1") {
    quickCardEt.style.borderColor = "#5c3dff";
    quickCardEt.style.backgroundColor = "rgba(92, 61, 255, 0.04)";
    
    quickCardCst.style.borderColor = "#e2e8f0";
    quickCardCst.style.backgroundColor = "#f8fafc";
  } else {
    // Clear highlights for manual selections
    quickCardCst.style.borderColor = "#e2e8f0";
    quickCardCst.style.backgroundColor = "#f8fafc";
    quickCardEt.style.borderColor = "#e2e8f0";
    quickCardEt.style.backgroundColor = "#f8fafc";
  }
}

if (quickCardCst && quickCardEt) {
  quickCardCst.addEventListener("click", () => {
    groupCodeInput.value = "CST 3/1";
    selectQuickCard("CST 3/1");
  });
  quickCardEt.addEventListener("click", () => {
    groupCodeInput.value = "ET 3/1";
    selectQuickCard("ET 3/1");
  });
}

// Check if group code cookie/localStorage exists
function checkGroupSelection() {
  const selectedGroup = localStorage.getItem("selectedGroupCode");
  
  if (selectedGroup) {
    headerGroupLabel.textContent = selectedGroup;
    groupSelectorOverlay.classList.add("hidden");
  } else {
    groupSelectorOverlay.classList.remove("hidden");
    groupCodeInput.value = "";
    selectQuickCard("");
    groupCodeInput.focus();
  }
}

// Event bindings
groupCodeInput.addEventListener("input", () => {
  filterSuggestions();
  selectQuickCard(groupCodeInput.value.trim());
});
groupCodeInput.addEventListener("focus", filterSuggestions);

// Close suggestions dropdown when clicking outside
document.addEventListener("click", (e) => {
  if (e.target !== groupCodeInput && e.target !== groupSuggestions) {
    groupSuggestions.classList.add("hidden");
  }
});

// Select group code submission
btnSelectGroupSubmit.addEventListener("click", () => {
  const code = groupCodeInput.value.trim();
  if (!code) {
    showToast("Input Required", "Please enter or select a group code.", "error");
    return;
  }

  localStorage.setItem("selectedGroupCode", code);
  showToast("Group Selected", `Routine loaded for ${code}.`, "success");
  checkGroupSelection();
});

// Change selection pill trigger
headerGroupPill.addEventListener("click", () => {
  groupSelectorOverlay.classList.remove("hidden");
  const activeCode = localStorage.getItem("selectedGroupCode") || "";
  groupCodeInput.value = activeCode;
  selectQuickCard(activeCode);
  groupCodeInput.focus();
  filterSuggestions();
});

// Direct Routine link switches
cardRoutine.addEventListener("click", () => {
  window.location.href = "routine.html";
});


const cardCalculator = document.getElementById("card-calculator");
if (cardCalculator) {
  cardCalculator.addEventListener("click", () => {
    window.location.href = "calculator.html";
  });
}

const cardBooks = document.getElementById("card-books");
if (cardBooks) {
  cardBooks.addEventListener("click", () => {
    window.location.href = "books.html";
  });
}

document.getElementById("btn-hamburger").addEventListener("click", () => {
  showToast("Settings Drawer", "Portal configuration settings is coming soon.", "info");
});

document.getElementById("card-notice").addEventListener("click", () => {
  showToast("Coming Soon", "Notice Board announcements are coming soon.", "info");
});

document.getElementById("card-result").addEventListener("click", () => {
  showToast("Coming Soon", "Semester Exam results display is coming soon.", "info");
});



// Initialization lifecycle
document.addEventListener("DOMContentLoaded", () => {
  // Set date
  const today = new Date();
  const formattedDate = today.toLocaleDateString("en-US", {
    weekday: "long",
    month: "long",
    day: "numeric"
  });
  document.getElementById("greeting-date").textContent = formattedDate;

  // Retrieve data
  fetchGroups();
  checkGroupSelection();

  lucide.createIcons();
});
