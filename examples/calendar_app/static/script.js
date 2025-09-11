// Calendar Application JavaScript

class CalendarApp {
    constructor() {
        this.currentDate = new Date();
        this.events = [];
        this.currentEventId = null;
        this.init();
    }

    async init() {
        this.setupEventListeners();
        await this.loadEvents();
        this.renderCalendar();
        this.renderUpcomingEvents();
    }

    setupEventListeners() {
        // Navigation buttons
        document.getElementById('prevMonth').addEventListener('click', () => {
            this.currentDate.setMonth(this.currentDate.getMonth() - 1);
            this.renderCalendar();
        });

        document.getElementById('nextMonth').addEventListener('click', () => {
            this.currentDate.setMonth(this.currentDate.getMonth() + 1);
            this.renderCalendar();
        });

        // Modal controls
        const modal = document.getElementById('eventModal');
        const closeBtn = document.querySelector('.close');
        const cancelBtn = document.querySelector('.cancel-btn');

        closeBtn.addEventListener('click', () => this.closeModal());
        cancelBtn.addEventListener('click', () => this.closeModal());

        window.addEventListener('click', (e) => {
            if (e.target === modal) {
                this.closeModal();
            }
        });

        // Event form submission
        document.getElementById('eventForm').addEventListener('submit', (e) => {
            e.preventDefault();
            this.saveEvent();
        });

        // Delete button
        document.getElementById('deleteBtn').addEventListener('click', () => {
            this.deleteEvent();
        });
    }

    async loadEvents() {
        try {
            const response = await fetch('/api/events');
            if (response.ok) {
                this.events = await response.json();
            }
        } catch (error) {
            console.error('Error loading events:', error);
        }
    }

    renderCalendar() {
        const grid = document.getElementById('calendarGrid');
        const monthTitle = document.getElementById('currentMonth');

        // Clear existing calendar days (keep headers)
        const days = grid.querySelectorAll('.calendar-day');
        days.forEach(day => day.remove());

        // Set month title
        const monthNames = [
            'January', 'February', 'March', 'April', 'May', 'June',
            'July', 'August', 'September', 'October', 'November', 'December'
        ];
        monthTitle.textContent = `${monthNames[this.currentDate.getMonth()]} ${this.currentDate.getFullYear()}`;

        // Calculate calendar dates
        const year = this.currentDate.getFullYear();
        const month = this.currentDate.getMonth();
        const firstDay = new Date(year, month, 1);
        const lastDay = new Date(year, month + 1, 0);
        const startDate = new Date(firstDay);
        startDate.setDate(startDate.getDate() - firstDay.getDay());

        const today = new Date();
        today.setHours(0, 0, 0, 0);

        // Generate calendar days
        for (let i = 0; i < 42; i++) {
            const currentDay = new Date(startDate);
            currentDay.setDate(startDate.getDate() + i);

            const dayElement = this.createDayElement(currentDay, month, today);
            grid.appendChild(dayElement);
        }
    }

    createDayElement(date, currentMonth, today) {
        const dayElement = document.createElement('div');
        dayElement.className = 'calendar-day';
        
        if (date.getMonth() !== currentMonth) {
            dayElement.classList.add('other-month');
        }
        
        if (date.getTime() === today.getTime()) {
            dayElement.classList.add('today');
        }

        const dayNumber = document.createElement('div');
        dayNumber.className = 'day-number';
        dayNumber.textContent = date.getDate();

        const dayEvents = document.createElement('div');
        dayEvents.className = 'day-events';

        // Add events for this day
        const dayString = this.formatDate(date);
        const dayEventsData = this.events.filter(event => event.date === dayString);
        
        dayEventsData.forEach(event => {
            const eventElement = document.createElement('div');
            eventElement.className = 'event-item';
            eventElement.textContent = event.title;
            eventElement.addEventListener('click', (e) => {
                e.stopPropagation();
                this.editEvent(event);
            });
            dayEvents.appendChild(eventElement);
        });

        dayElement.appendChild(dayNumber);
        dayElement.appendChild(dayEvents);

        // Click handler for adding new events
        dayElement.addEventListener('click', () => {
            this.openModal(date);
        });

        return dayElement;
    }

    openModal(date) {
        const modal = document.getElementById('eventModal');
        const modalTitle = document.getElementById('modalTitle');
        const eventForm = document.getElementById('eventForm');
        const deleteBtn = document.getElementById('deleteBtn');

        modalTitle.textContent = 'Add Event';
        eventForm.reset();
        deleteBtn.style.display = 'none';
        this.currentEventId = null;

        if (date) {
            document.getElementById('eventDate').value = this.formatDate(date);
        }

        modal.style.display = 'block';
    }

    editEvent(event) {
        const modal = document.getElementById('eventModal');
        const modalTitle = document.getElementById('modalTitle');
        const deleteBtn = document.getElementById('deleteBtn');

        modalTitle.textContent = 'Edit Event';
        deleteBtn.style.display = 'inline-block';
        this.currentEventId = event.id;

        document.getElementById('eventTitle').value = event.title;
        document.getElementById('eventDescription').value = event.description;
        document.getElementById('eventDate').value = event.date;
        document.getElementById('eventTime').value = event.time;

        modal.style.display = 'block';
    }

    closeModal() {
        const modal = document.getElementById('eventModal');
        modal.style.display = 'none';
        this.currentEventId = null;
    }

    async saveEvent() {
        const title = document.getElementById('eventTitle').value;
        const description = document.getElementById('eventDescription').value;
        const date = document.getElementById('eventDate').value;
        const time = document.getElementById('eventTime').value;

        if (!title || !date || !time) {
            alert('Please fill in all required fields');
            return;
        }

        const eventData = { title, description, date, time };

        try {
            let response;
            if (this.currentEventId) {
                // Update existing event
                response = await fetch(`/api/events/${this.currentEventId}`, {
                    method: 'PUT',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(eventData),
                });
            } else {
                // Create new event
                response = await fetch('/api/events', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(eventData),
                });
            }

            if (response.ok) {
                await this.loadEvents();
                this.renderCalendar();
                this.renderUpcomingEvents();
                this.closeModal();
            } else {
                alert('Error saving event');
            }
        } catch (error) {
            console.error('Error saving event:', error);
            alert('Error saving event');
        }
    }

    async deleteEvent() {
        if (!this.currentEventId) return;

        if (!confirm('Are you sure you want to delete this event?')) {
            return;
        }

        try {
            const response = await fetch(`/api/events/${this.currentEventId}`, {
                method: 'DELETE',
            });

            if (response.ok) {
                await this.loadEvents();
                this.renderCalendar();
                this.renderUpcomingEvents();
                this.closeModal();
            } else {
                alert('Error deleting event');
            }
        } catch (error) {
            console.error('Error deleting event:', error);
            alert('Error deleting event');
        }
    }

    renderUpcomingEvents() {
        const eventsList = document.getElementById('eventsList');
        eventsList.innerHTML = '';

        // Sort events by date and time
        const sortedEvents = [...this.events].sort((a, b) => {
            const dateA = new Date(`${a.date}T${a.time}`);
            const dateB = new Date(`${b.date}T${b.time}`);
            return dateA - dateB;
        });

        // Show only upcoming events (next 10)
        const upcomingEvents = sortedEvents.filter(event => {
            const eventDate = new Date(`${event.date}T${event.time}`);
            return eventDate >= new Date();
        }).slice(0, 10);

        if (upcomingEvents.length === 0) {
            eventsList.innerHTML = '<p>No upcoming events</p>';
            return;
        }

        upcomingEvents.forEach(event => {
            const eventElement = document.createElement('div');
            eventElement.className = 'event-list-item';
            eventElement.innerHTML = `
                <h4>${event.title}</h4>
                <div class="event-date-time">
                    ${this.formatDisplayDate(event.date)} at ${this.formatTime(event.time)}
                </div>
                <div class="event-description">${event.description || 'No description'}</div>
            `;
            eventElement.addEventListener('click', () => this.editEvent(event));
            eventsList.appendChild(eventElement);
        });
    }

    formatDate(date) {
        return date.toISOString().split('T')[0];
    }

    formatDisplayDate(dateString) {
        const date = new Date(dateString);
        return date.toLocaleDateString('en-US', {
            weekday: 'short',
            year: 'numeric',
            month: 'short',
            day: 'numeric'
        });
    }

    formatTime(timeString) {
        const [hours, minutes] = timeString.split(':');
        const hour12 = hours % 12 || 12;
        const ampm = hours >= 12 ? 'PM' : 'AM';
        return `${hour12}:${minutes} ${ampm}`;
    }
}

// Initialize the calendar app when the page loads
document.addEventListener('DOMContentLoaded', () => {
    new CalendarApp();
});