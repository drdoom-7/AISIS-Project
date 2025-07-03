document.addEventListener('DOMContentLoaded', () => {
    const chatHistory = document.getElementById('chat-history');
    const chatInput = document.getElementById('chat-input');
    const sendButton = document.getElementById('send-button');
    const progressBar = document.getElementById('progress-bar');
    const aisisLogo = document.getElementById('aisis-logo');

    // 1. Smart Scrolling
    let isUserScrolling = false;
    chatHistory.addEventListener('scroll', () => {
        const { scrollTop, scrollHeight, clientHeight } = chatHistory;
        // If user is not at the very bottom, assume they are scrolling up or staying put
        isUserScrolling = (scrollHeight - scrollTop - clientHeight > 1);
    });

    const scrollToBottom = () => {
        if (!isUserScrolling) {
            chatHistory.scrollTop = chatHistory.scrollHeight;
        }
        // Optional: add 'New Messages' indicator logic here if isUserScrolling is true
    };

    // Initial scroll to bottom (for pre-existing messages)
    scrollToBottom();

    // 2. Conditional Shining for Progress Bar
    function setProgressBarActive(isActive) {
        if (isActive) {
            progressBar.classList.add('progress-bar-active');
            progressBar.classList.remove('progress-bar-idle');
            progressBar.textContent = 'Working...';
        } else {
            progressBar.classList.remove('progress-bar-active');
            progressBar.classList.add('progress-bar-idle');
            progressBar.textContent = 'Idle';
        }
    }

    // Example usage: Simulate work
    setProgressBarActive(false); // Initially idle
    setTimeout(() => setProgressBarActive(true), 1000); // Simulate starting work
    setTimeout(() => setProgressBarActive(false), 5000); // Simulate finishing work

    // 3. AISIS Logo load-in animation (CSS handles this via animation property)
    // We can just ensure the animation plays on load.
    // Adding a class to trigger it. The CSS `header` rule or `aisis-logo` can directly have it.
    // For demonstrative purposes, applying it here:
    aisisLogo.style.animation = 'logo-load-in 0.8s ease-out forwards';

    // 4. Right-Panel Interaction Effect (Ripple) & Message Sending
    sendButton.addEventListener('click', sendMessage);
    chatInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    function sendMessage() {
        const messageText = chatInput.value.trim();
        if (messageText) {
            addMessage(messageText, 'user');
            chatInput.value = '';
            // Simulate AI response after a short delay
            setProgressBarActive(true);
            setTimeout(() => {
                addMessage("This is an AI response to your message.", 'ai');
                setProgressBarActive(false);
            }, 1500);
        }
    }

    function addMessage(text, type) {
        const messageDiv = document.createElement('div');
        messageDiv.classList.add('message', `${type}-message`);

        const avatarSrc = type === 'user' ? 'https://via.placeholder.com/40/007bff/ffffff?text=U' : 'https://via.placeholder.com/40/6c757d/ffffff?text=AI';
        const avatarAlt = type === 'user' ? 'User Avatar' : 'AI Avatar';

        messageDiv.innerHTML = `
            <img src="${avatarSrc}" alt="${avatarAlt}" class="avatar">
            <div class="message-content">
                <p>${text}</p>
                <span class="timestamp">${new Date().toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })}</span>
            </div>
        `;

        chatHistory.appendChild(messageDiv);

        // Apply ripple effect to the newly added message
        messageDiv.classList.add('ripple-effect');
        messageDiv.addEventListener('animationend', () => {
            messageDiv.classList.remove('ripple-effect');
        }, { once: true });

        scrollToBottom();
    }

    // Adjust chat input height dynamically
    chatInput.addEventListener('input', () => {
        chatInput.style.height = 'auto';
        chatInput.style.height = chatInput.scrollHeight + 'px';
    });
});
