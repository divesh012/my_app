// --- CALL SUPPORT MODAL ---
const callTrigger = document.getElementById('call-support-trigger');
const callModal = document.getElementById('call-support-modal');
const closeCallModal = document.getElementById('close-call-modal');

callTrigger.addEventListener('click', () => {
  callModal.style.display = 'flex';
});

closeCallModal.addEventListener('click', () => {
  callModal.style.display = 'none';
});

// --- CHATBOT ---
const chatTrigger = document.getElementById('chat-trigger');
const chatBox = document.getElementById('chatbot-box');
const chatClose = document.getElementById('chat-close');
const sendBtn = document.getElementById('send-btn');
const userInput = document.getElementById('user-input');
const chatBody = document.getElementById('chat-body');

// Open chatbot
chatTrigger.addEventListener('click', () => {
  chatBox.style.display = 'block';
});

// Close chatbot button
chatClose.addEventListener('click', () => {
  chatBox.style.display = 'none';
});

// Send message button
sendBtn.addEventListener('click', sendMessage);

// Send message on Enter key
userInput.addEventListener('keypress', (e) => {
  if (e.key === 'Enter') sendMessage();
});

// Minimize chatbot if clicked outside
document.addEventListener('click', (e) => {
  if (!chatBox.contains(e.target) && !chatTrigger.contains(e.target)) {
    chatBox.style.display = 'none';
  }
});

// --- Functions ---

function sendMessage() {
  const text = userInput.value.trim();
  if (!text) return;

  appendMessage(text, 'user-msg');
  userInput.value = '';

  // Bot reply after delay
  setTimeout(() => {
    const reply = generateReply(text);
    appendMessage(reply, 'bot-msg');
  }, 800);
}

function appendMessage(msg, type) {
  const div = document.createElement('div');
  div.className = type;
  div.textContent = msg;
  chatBody.appendChild(div);
  chatBody.scrollTop = chatBody.scrollHeight;
}

function generateReply(userText) {
  const text = userText.toLowerCase();

  // Greetings
  if (/hi|hello|hey/.test(text)) return "Hello 👋! How can I assist you today?";
  if (text.includes("thank")) return "You're most welcome! 😊";

  // Order Related
  if (text.includes("order status") || text.includes("track order")) {
    return "You can track your order by visiting the 'Order Related' section and clicking on 'Track Order'.";
  }
  if (text.includes("cancel order")) {
    return "To cancel your order, go to 'Order Related' > 'Cancel/Return' and select the item.";
  }
  if (text.includes("change address")) {
    return "To update the delivery address, please go to 'Gloora Account' > 'Manage Address'.";
  }

  // Payment
  if (text.includes("payment failed") || text.includes("payment issue")) {
    return "If your payment failed, the amount (if deducted) will be refunded within 3–5 working days.";
  }
  if (text.includes("refund")) {
    return "Refunds are usually processed within 5–7 working days. Check 'Payments' section for status.";
  }

  // Account
  if (text.includes("forgot password")) {
    return "Click 'Sign in' and then 'Forgot Password' to reset your Gloora account password.";
  }
  if (text.includes("change email") || text.includes("update phone")) {
    return "Go to 'Gloora Account' > 'Profile Settings' to update your email or phone number.";
  }

  // Returns
  if (text.includes("return product")) {
    return "You can return items by going to 'Order Related' > 'Returns & Refunds'. Be sure to check the return window.";
  }

  // Delivery
  if (text.includes("delivery delayed") || text.includes("when will it arrive")) {
    return "We’re sorry for the delay. You can track your delivery in the 'Order Related' section.";
  }

  // Technical
  if (text.includes("website not working") || text.includes("page not opening")) {
    return "Please clear your browser cache or try opening the website in incognito mode. Still stuck? Let us know!";
  }

  // Default fallback
  return "I'm here to help! But this query may need a human agent. A support representative will assist you shortly. For urgent issues, please call 📞 9112879562.";
}
