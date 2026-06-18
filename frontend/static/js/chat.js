const chatMessages   = document.getElementById('chat-messages');
const chatInput      = document.getElementById('chat-input');
const sendBtn        = document.getElementById('send-btn');
const typingIndicator = document.getElementById('typing-indicator');

function appendMessage(sender, text) {
  const isUser = sender === 'user';

  const wrapper = document.createElement('div');
  wrapper.className = 'd-flex mb-3 ' + (isUser ? 'justify-content-end' : 'justify-content-start');

  const bubble = document.createElement('div');
  bubble.className = 'chat-bubble ' + (isUser ? 'user-bubble' : 'bot-bubble');
  bubble.textContent = text;

  wrapper.appendChild(bubble);
  chatMessages.appendChild(wrapper);
  chatMessages.scrollTop = chatMessages.scrollHeight;
}

function setInputState(disabled) {
  chatInput.disabled = disabled;
  sendBtn.disabled   = disabled;
  if (!disabled) chatInput.focus();
}

async function sendMessage() {
  const text = chatInput.value.trim();
  if (!text) return;

  appendMessage('user', text);
  chatInput.value = '';

  setInputState(true);
  typingIndicator.classList.remove('d-none');

  try {
    const data = await apiFetch('/api/v1/chat', {
      method: 'POST',
      body: JSON.stringify({ user_message: text }),
    });
    appendMessage('bot', data.response);
  } catch (err) {
    if (err.message !== 'Session expired') {
      appendMessage('bot', 'Sorry, something went wrong. Please try again.');
    }
  } finally {
    typingIndicator.classList.add('d-none');
    setInputState(false);
  }
}

/* ── Init ── */
document.addEventListener('DOMContentLoaded', function () {
  if (!requireAuth()) return;

  const user = getUser();
  const nameEl = document.getElementById('chat-user-name');
  if (nameEl && user) nameEl.textContent = user.name;

  sendBtn.addEventListener('click', sendMessage);

  chatInput.addEventListener('keydown', function (e) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  });

  appendMessage('bot', 'Hello' + (user ? ', ' + user.name : '') + '! I\'m your LMS assistant. You can ask me about your leave balance, apply for leave, check holidays, and more.');

  chatInput.focus();
});
