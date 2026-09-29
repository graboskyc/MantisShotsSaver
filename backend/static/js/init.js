function init() {
    return {
        sessions: [],
        currentIndex: 0,
        skip: 0,
        limit: 5,

        async loadList() {
            console.log('Loading List');
            await this.fetchSessions();
        },

        async fetchSessions() {
            const response = await fetch(`/api/sessions?skip=${this.skip}&limit=${this.limit}`);
            this.sessions = await response.json();
            this.currentIndex = 0;
            console.log('Sessions loaded:', this.sessions);
        },

        get currentSession() {
            return this.sessions[this.currentIndex] || null;
        },

        nextSession() {
            if (this.currentIndex < this.sessions.length - 1) {
                this.currentIndex++;
            } else {
                this.skip += this.limit;
                this.fetchSessions();
            }
        },

        prevSession() {
            if (this.currentIndex > 0) {
                this.currentIndex--;
            } else if (this.skip >= this.limit) {
                this.skip -= this.limit;
                this.fetchSessions();
            }
        },

        delay(ms) {
            return new Promise(resolve => setTimeout(resolve, ms))
        }
    }
}