// script.js
import { apiConfig } from './config.js';

class ProjectManager {
    constructor() {
        this.projects = [];
        this.isLoading = false;
        this.initialize();
    }

    async initialize() {
        try {
            await this.loadProjects();
            this.setupEventListeners();
            this.renderProjects();
        } catch (error) {
            this.handleError('Initialization failed', error);
        }
    }

    async loadProjects() {
        if (this.isLoading) return;
        
        this.isLoading = true;
        this.showLoadingState();
        
        try {
            const response = await fetch(apiConfig.projectsEndpoint, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${apiConfig.token}`
                }
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();
            this.projects = Array.isArray(data) ? data : [];
            
        } catch (error) {
            this.handleError('Failed to load projects', error);
            this.projects = [];
        } finally {
            this.isLoading = false;
            this.hideLoadingState();
        }
    }

    async createProject(projectData) {
        try {
            const response = await fetch(apiConfig.projectsEndpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${apiConfig.token}`
                },
                body: JSON.stringify(projectData)
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const newProject = await response.json();
            this.projects.push(newProject);
            this.renderProjects();
            
            return newProject;
        } catch (error) {
            this.handleError('Failed to create project', error);
            throw error;
        }
    }

    async updateProject(id, updates) {
        try {
            const response = await fetch(`${apiConfig.projectsEndpoint}/${id}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${apiConfig.token}`
                },
                body: JSON.stringify(updates)
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const updatedProject = await response.json();
            const index = this.projects.findIndex(p => p.id === id);
            
            if (index !== -1) {
                this.projects[index] = updatedProject;
                this.renderProjects();
            }
            
            return updatedProject;
        } catch (error) {
            this.handleError('Failed to update project', error);
            throw error;
        }
    }

    async deleteProject(id) {
        try {
            const response = await fetch(`${apiConfig.projectsEndpoint}/${id}`, {
                method: 'DELETE',
                headers: {
                    'Authorization': `Bearer ${apiConfig.token}`
                }
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            this.projects = this.projects.filter(project => project.id !== id);
            this.renderProjects();
            
            return true;
        } catch (error) {
            this.handleError('Failed to delete project', error);
            throw error;
        }
    }

    renderProjects() {
        const container = document.getElementById('projects-container');
        if (!container) return;

        if (this.projects.length === 0) {
            container.innerHTML = '<div class="empty-state">No projects found</div>';
            return;
        }

        container.innerHTML = this.projects.map(project => `
            <div class="project-card" data-id="${project.id}">
                <h3>${this.escapeHtml(project.name)}</h3>
                <p>${this.escapeHtml(project.description || 'No description')}</p>
                <div class="project-actions">
                    <button class="btn-edit" data-id="${project.id}">Edit</button>
                    <button class="btn-delete" data-id="${project.id}">Delete</button>
                </div>
            </div>
        `).join('');
    }

    setupEventListeners() {
        document.addEventListener('click', async (event) => {
            try {
                if (event.target.classList.contains('btn-delete')) {
                    const id = event.target.dataset.id;
                    if (id && confirm('Are you sure you want to delete this project?')) {
                        await this.deleteProject(id);
                    }
                }

                if (event.target.classList.contains('btn-edit')) {
                    const id = event.target.dataset.id;
                    this.handleEditProject(id);
                }

                if (event.target.id === 'create-project-btn') {
                    this.handleCreateProject();
                }

                if (event.target.id === 'refresh-btn') {
                    await this.loadProjects();
                }
            } catch (error) {
                this.handleError('Action failed', error);
            }
        });

        const searchInput = document.getElementById('project-search');
        if (searchInput) {
            searchInput.addEventListener('input', debounce(() => {
                this.filterProjects(searchInput.value);
            }, 300));
        }
    }

    handleEditProject(id) {
        const project = this.projects.find(p => p.id === id);
        if (!project) return;

        const name = prompt('Enter new project name:', project.name);
        if (name && name !== project.name) {
            this.updateProject(id, { name });
        }
    }

    async handleCreateProject() {
        const name = prompt('Enter project name:');
        if (!name) return;

        const description = prompt('Enter project description (optional):');
        
        try {
            await this.createProject({
                name: name.trim(),
                description: description?.trim() || ''
            });
        } catch (error) {
            console.error('Create project failed:', error);
        }
    }

    filterProjects(searchTerm) {
        if (!searchTerm) {
            this.renderProjects();
            return;
        }

        const filtered = this.projects.filter(project =>
            project.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
            (project.description && project.description.toLowerCase().includes(searchTerm.toLowerCase()))
        );

        const container = document.getElementById('projects-container');
        if (!container) return;

        if (filtered.length === 0) {
            container.innerHTML = '<div class="empty-state">No matching projects</div>';
            return;
        }

        container.innerHTML = filtered.map(project => `
            <div class="project-card" data-id="${project.id}">
                <h3>${this.escapeHtml(project.name)}</h3>
                <p>${this.escapeHtml(project.description || 'No description')}</p>
            </div>
        `).join('');
    }

    showLoadingState() {
        const container = document.getElementById('projects-container');
        if (container) {
            container.innerHTML = '<div class="loading">Loading projects...</div>';
        }
    }

    hideLoadingState() {
        // Loading state is automatically removed by renderProjects
    }

    handleError(context, error) {
        console.error(`${context}:`, error);
        
        const errorContainer = document.getElementById('error-container');
        if (errorContainer) {
            errorContainer.innerHTML = `
                <div class="error-message">
                    ${context}: ${error.message}
                </div>
            `;
            
            setTimeout(() => {
                errorContainer.innerHTML = '';
            }, 5000);
        }
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Utility function for debouncing
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    const projectManager = new ProjectManager();
    
    // Make available globally for debugging if needed
    window.projectManager = projectManager;
});

// Export for module usage if needed
export default ProjectManager;