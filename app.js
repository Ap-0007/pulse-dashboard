class PulseHUD {
    constructor() {
        this.projects = [];
        this.selectedProject = null;
        this.init();
    }

    async init() {
        this.log('Initializing neural link to workspace...');
        await this.refreshData();
        this.render();
        this.startAutoRefresh();
    }

    async refreshData() {
        try {
            const res = await fetch('/api/pulse');
            this.projects = await res.json();
            this.log(`Pulse detected: ${this.projects.length} systems active.`);
            this.updateTotalMetrics();
        } catch (err) {
            this.log('Signal lost. Retrying link...', 'red');
        }
    }

    updateTotalMetrics() {
        const total = this.projects.reduce((acc, p) => acc + p.todo_count, 0);
        document.getElementById('total-todos').innerText = total;
        document.getElementById('active-threads').innerText = this.projects.length;
    }

    log(msg, color = 'var(--green)') {
        const log = document.getElementById('system-log');
        const entry = document.createElement('div');
        const time = new Date().toLocaleTimeString([], { hour12: false });
        entry.style.color = color;
        entry.innerHTML = `<span style="opacity:0.5">[${time}]</span> ${msg}`;
        log.prepend(entry);
    }

    render() {
        this.renderProjectList();
        this.renderTodoList();
    }

    renderProjectList() {
        const list = document.getElementById('project-list');
        list.innerHTML = '';

        this.projects.sort((a, b) => b.vitality - a.vitality).forEach(proj => {
            const card = document.createElement('div');
            card.className = 'project-vital';
            
            const vitalityClass = proj.vitality > 70 ? '' : (proj.vitality > 30 ? 'med' : 'low');
            
            card.innerHTML = `
                <div class="vital-header">
                    <span class="project-name">${proj.name.toUpperCase()}</span>
                    <span class="vitality-badge ${vitalityClass}">${proj.vitality}%</span>
                </div>
                <div class="vital-stats">
                    <span>${proj.stats.recent_commits} COMMITS/MO</span>
                    <span>${proj.todo_count} TASKS_PENDING</span>
                </div>
            `;

            card.onclick = () => this.selectProject(proj);
            list.appendChild(card);
        });
    }

    renderTodoList() {
        const list = document.getElementById('todo-list');
        list.innerHTML = '';

        // Flatten all todos and sort by project vitality (showing todos from most "at risk" projects first)
        const allTodos = this.projects
            .flatMap(p => p.todos.map(t => ({ ...t, projectName: p.name, vitality: p.vitality })))
            .sort((a, b) => a.vitality - b.vitality);

        allTodos.forEach(todo => {
            const item = document.createElement('div');
            item.className = 'task-item';
            item.innerHTML = `
                <div class="task-tag">${todo.projectName.slice(0, 3)}</div>
                <div style="flex-grow: 1;">
                    <div class="task-text">${todo.text}</div>
                    <div class="task-meta">${todo.file}:${todo.line}</div>
                </div>
            `;
            list.appendChild(item);
        });
    }

    selectProject(proj) {
        this.selectedProject = proj;
        document.getElementById('focused-project').innerText = proj.name.toUpperCase();
        document.getElementById('stat-commits').innerText = proj.stats.recent_commits;
        document.getElementById('stat-last').innerText = proj.stats.last_activity ? proj.stats.last_activity.split(' ')[0] : 'NEVER';
        
        const meta = document.getElementById('project-meta');
        meta.innerText = `LATEST_HEARTBEAT DETECTED AT ${proj.stats.last_activity || '---'}`;

        this.log(`Accessing system: ${proj.name}...`);
        this.drawActivityPulse(proj);
    }

    drawActivityPulse(proj) {
        // Simple SVG-based pulse visualization for the focused project
        const chart = document.getElementById('activity-chart');
        chart.innerHTML = '';
        const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
        svg.setAttribute("width", "100%");
        svg.setAttribute("height", "100%");
        
        let pathData = "M 0 150";
        for(let i=0; i<30; i++) {
            const peak = Math.random() * (proj.vitality / 2);
            pathData += ` L ${i*30} ${150 - peak} L ${i*30 + 15} ${150 + peak}`;
        }

        const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
        path.setAttribute("d", pathData);
        path.setAttribute("stroke", "var(--green)");
        path.setAttribute("fill", "none");
        path.setAttribute("stroke-width", "2");
        path.style.opacity = "0.5";
        
        svg.appendChild(path);
        chart.appendChild(svg);
    }

    startAutoRefresh() {
        setInterval(() => this.refreshData().then(() => this.render()), 15000);
    }
}

window.onload = () => new PulseHUD();
