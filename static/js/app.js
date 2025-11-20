// Calendar Assistant Frontend
const API_BASE = '';

let isListening = false;
let currentDate = new Date();
let allEvents = [];

// DOM Elements
const queryInput = document.getElementById('queryInput');
const sendBtn = document.getElementById('sendBtn');
const voiceBtn = document.getElementById('voiceBtn');
const responseArea = document.getElementById('responseArea');
const eventsList = document.getElementById('eventsList');
const calendarGrid = document.getElementById('calendarGrid');
const calendarMonth = document.getElementById('calendarMonth');
const prevMonthBtn = document.getElementById('prevMonth');
const nextMonthBtn = document.getElementById('nextMonth');
const testTTSBtn = document.getElementById('testTTSBtn');

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    checkAuthStatus();
    loadEvents();
    renderCalendar();
    
    // Send button click
    sendBtn.addEventListener('click', handleSend);
    
    // Enter key press
    queryInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            handleSend();
        }
    });
    
    // Voice button click
    voiceBtn.addEventListener('click', handleVoice);
    
    // Calendar navigation
    prevMonthBtn.addEventListener('click', () => {
        currentDate.setMonth(currentDate.getMonth() - 1);
        renderCalendar();
    });
    
    nextMonthBtn.addEventListener('click', () => {
        currentDate.setMonth(currentDate.getMonth() + 1);
        renderCalendar();
    });
    
    // Test TTS button
    if (testTTSBtn) {
        testTTSBtn.addEventListener('click', () => {
            playAudioResponse('Hello, this is a test of the text to speech system.');
        });
    }
});

// Load events
async function loadEvents() {
    try {
        const response = await fetch(`${API_BASE}/api/events`);
        const data = await response.json();
        
        if (data.success) {
            allEvents = data.events;
            displayEvents(data.events);
            renderCalendar();
        } else {
            eventsList.innerHTML = '<div class="empty-state">Failed to load events</div>';
        }
    } catch (error) {
        console.error('Error loading events:', error);
        eventsList.innerHTML = '<div class="empty-state">Error loading events</div>';
    }
}

// Display events
function displayEvents(events) {
    if (events.length === 0) {
        eventsList.innerHTML = '<div class="empty-state"><p>No events found</p></div>';
        return;
    }
    
    eventsList.innerHTML = events.map(event => `
        <div class="event-card">
            <div class="event-title">${escapeHtml(event.summary)}</div>
            <div class="event-time">${formatDateTime(event.start)} - ${formatDateTime(event.end)}</div>
            ${event.location ? `<div class="event-location">📍 ${escapeHtml(event.location)}</div>` : ''}
        </div>
    `).join('');
}

// Handle send
async function handleSend() {
    const query = queryInput.value.trim();
    
    if (!query) {
        return;
    }
    
    // Clear input
    queryInput.value = '';
    
    // Add user message
    addMessage(query, 'user');
    
    // Show loading
    const loadingId = addMessage('Thinking...', 'assistant');
    
    try {
        const response = await fetch(`${API_BASE}/api/query`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ query }),
        });
        
        const data = await response.json();
        
        // Remove loading message
        removeMessage(loadingId);
        
        if (data.success) {
            addMessage(data.response, 'assistant');
            
            // Generate and play audio response
            playAudioResponse(data.response);
            
            // Update events if provided
            if (data.events && data.events.length > 0) {
                displayEvents(data.events);
            } else if (data.intent === 'create' || data.intent === 'modify' || data.intent === 'cancel') {
                // Reload all events after modification
                loadEvents();
            } else {
                // Reload events to update calendar
                loadEvents();
            }
        } else {
            addMessage(`Error: ${data.error}`, 'error');
        }
    } catch (error) {
        removeMessage(loadingId);
        addMessage(`Error: ${error.message}`, 'error');
    }
}

// Handle voice input
function handleVoice() {
    if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
        addMessage('Voice input is not supported in your browser', 'error');
        return;
    }
    
    if (isListening) {
        // Stop listening
        isListening = false;
        voiceBtn.style.background = '';
        return;
    }
    
    // Start listening
    isListening = true;
    voiceBtn.style.background = 'var(--error)';
    
    const Recognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    const recognition = new Recognition();
    
    recognition.continuous = false;
    recognition.interimResults = false;
    
    recognition.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        queryInput.value = transcript;
        handleSend();
    };
    
    recognition.onerror = (event) => {
        console.error('Speech recognition error:', event.error);
        addMessage('Voice recognition error', 'error');
        isListening = false;
        voiceBtn.style.background = '';
    };
    
    recognition.onend = () => {
        isListening = false;
        voiceBtn.style.background = '';
    };
    
    recognition.start();
}

// Add message to response area
function addMessage(text, type = 'assistant') {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${type}`;
    messageDiv.textContent = text;
    
    // Clear welcome message if present
    const welcomeMsg = responseArea.querySelector('.welcome-message');
    if (welcomeMsg) {
        welcomeMsg.remove();
    }
    
    // Append to response area (CSS flex-direction: column-reverse will show newest on top)
    responseArea.appendChild(messageDiv);
    
    // Scroll to top to show new message
    responseArea.scrollTop = 0;
    
    return messageDiv;
}

// Remove message
function removeMessage(messageElement) {
    if (messageElement && messageElement.parentNode) {
        messageElement.remove();
    }
}

// Format datetime
function formatDateTime(isoString) {
    if (!isoString) return 'N/A';
    
    const date = new Date(isoString);
    const options = {
        month: 'short',
        day: 'numeric',
        hour: 'numeric',
        minute: '2-digit',
        hour12: true
    };
    
    return date.toLocaleString('en-US', options);
}

// Escape HTML
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Render calendar
function renderCalendar() {
    const year = currentDate.getFullYear();
    const month = currentDate.getMonth();
    
    // Update month header
    const monthNames = ['January', 'February', 'March', 'April', 'May', 'June',
        'July', 'August', 'September', 'October', 'November', 'December'];
    calendarMonth.textContent = `${monthNames[month]} ${year}`;
    
    // Get first day of month and number of days
    const firstDay = new Date(year, month, 1);
    const lastDay = new Date(year, month + 1, 0);
    const daysInMonth = lastDay.getDate();
    const startingDayOfWeek = firstDay.getDay();
    
    // Clear calendar
    calendarGrid.innerHTML = '';
    
    // Add day headers
    const dayHeaders = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
    dayHeaders.forEach(day => {
        const header = document.createElement('div');
        header.className = 'calendar-day-header';
        header.textContent = day;
        calendarGrid.appendChild(header);
    });
    
    // Add empty cells for days before month starts
    for (let i = 0; i < startingDayOfWeek; i++) {
        const emptyDay = document.createElement('div');
        emptyDay.className = 'calendar-day other-month';
        calendarGrid.appendChild(emptyDay);
    }
    
    // Add days of month
    const today = new Date();
    const isCurrentMonth = today.getMonth() === month && today.getFullYear() === year;
    
    for (let day = 1; day <= daysInMonth; day++) {
        const dayElement = document.createElement('div');
        const dayDate = new Date(year, month, day);
        const isToday = isCurrentMonth && day === today.getDate();
        
        dayElement.className = 'calendar-day';
        if (isToday) {
            dayElement.classList.add('today');
        }
        
        // Check if this day has events
        const dayEvents = getEventsForDate(dayDate);
        if (dayEvents.length > 0) {
            dayElement.classList.add('has-events');
            
            const dayNumber = document.createElement('div');
            dayNumber.className = 'calendar-day-number';
            dayNumber.textContent = day;
            dayElement.appendChild(dayNumber);
            
            const eventDots = document.createElement('div');
            eventDots.className = 'calendar-event-dots';
            // Show up to 3 dots
            const dotsToShow = Math.min(dayEvents.length, 3);
            for (let i = 0; i < dotsToShow; i++) {
                const dot = document.createElement('div');
                dot.className = 'calendar-event-dot';
                eventDots.appendChild(dot);
            }
            dayElement.appendChild(eventDots);
            
            // Add title on hover
            dayElement.title = `${dayEvents.length} event(s)`;
        } else {
            dayElement.textContent = day;
        }
        
        calendarGrid.appendChild(dayElement);
    }
    
    // Add empty cells for days after month ends
    const totalCells = startingDayOfWeek + daysInMonth;
    const remainingCells = 42 - totalCells; // 6 rows * 7 days
    for (let i = 0; i < remainingCells && totalCells + i < 42; i++) {
        const emptyDay = document.createElement('div');
        emptyDay.className = 'calendar-day other-month';
        calendarGrid.appendChild(emptyDay);
    }
}

// Check authentication status
async function checkAuthStatus() {
    try {
        const response = await fetch(`${API_BASE}/api/auth/status`);
        const data = await response.json();
        
        const indicator = document.getElementById('authIndicator');
        const logoutLink = document.getElementById('logoutLink');
        
        if (data.authenticated && data.has_calendar_access) {
            indicator.textContent = '✓ Authenticated';
            indicator.style.color = 'var(--success)';
            logoutLink.style.display = 'inline';
        } else {
            indicator.textContent = 'Not authenticated';
            indicator.style.color = 'var(--error)';
            logoutLink.style.display = 'none';
            // Redirect to login if not authenticated
            if (!data.authenticated) {
                window.location.href = '/login';
            }
        }
    } catch (error) {
        console.error('Error checking auth status:', error);
    }
}

// Get events for a specific date
function getEventsForDate(date) {
    if (!allEvents || allEvents.length === 0) return [];
    
    const dateStr = date.toISOString().split('T')[0];
    
    return allEvents.filter(event => {
        if (!event.start) return false;
        const eventDate = new Date(event.start);
        const eventDateStr = eventDate.toISOString().split('T')[0];
        return eventDateStr === dateStr;
    });
}

// Play audio response using ElevenLabs
async function playAudioResponse(text) {
    if (!text || text.trim().length === 0) {
        console.log('No text to speak');
        return;
    }
    
    try {
        console.log('Requesting TTS for:', text.substring(0, 50));
        const response = await fetch(`${API_BASE}/api/tts`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ text }),
        });
        
        console.log('TTS response status:', response.status);
        
        if (response.ok) {
            const audioBlob = await response.blob();
            console.log('Audio blob received:', audioBlob.size, 'bytes');
            
            if (audioBlob.size === 0) {
                console.warn('Empty audio blob received');
                return;
            }
            
            const audioUrl = URL.createObjectURL(audioBlob);
            const audio = new Audio(audioUrl);
            
            // Add event listeners for debugging
            audio.addEventListener('loadstart', () => console.log('Audio loading started'));
            audio.addEventListener('canplay', () => console.log('Audio can play'));
            audio.addEventListener('error', (e) => console.error('Audio error:', e));
            audio.addEventListener('ended', () => {
                console.log('Audio playback ended');
                URL.revokeObjectURL(audioUrl);
            });
            
            // Try to play
            const playPromise = audio.play();
            if (playPromise !== undefined) {
                playPromise
                    .then(() => {
                        console.log('Audio playing successfully');
                    })
                    .catch(error => {
                        console.error('Error playing audio:', error);
                        // User may have blocked autoplay - try with user interaction
                        console.log('Autoplay blocked. Audio will play on next user interaction.');
                    });
            }
        } else {
            const errorData = await response.json().catch(() => ({ error: 'Unknown error' }));
            console.warn('TTS request failed:', response.status, errorData);
        }
    } catch (error) {
        console.error('TTS error:', error);
        // Fail silently - TTS is optional
    }
}

