const projects = JSON.parse(document.getElementById('serialized-projects').textContent);
let currentProjectId = null;

// Open Project Details Panel
function openProjectDetails(projectId) {
    currentProjectId = projectId;
    const panel = document.getElementById('project-details-panel');
    const title = document.getElementById('project-details-title');
    const tasksList = document.getElementById('project-tasks-list');
    const addTaskLink = document.getElementById('add-task-link');

    // Find the selected project
    const selectedProject = projects.find(p => p.id === projectId);

    // Update the panel content
    title.textContent = selectedProject.name;
    tasksList.innerHTML = '';
    selectedProject.tasks.forEach(task => {
        const li = document.createElement('li');
        li.className = 'list-group-item';
        li.innerHTML = `
            <div class="d-flex justify-content-between align-items-center">
                <span>${task.title}</span>
                <div>
                    <input type="checkbox" class="form-check-input me-2" ${task.status === 'Done' ? 'checked' : ''} onclick="markTaskComplete(${task.id}, ${projectId})">
                    <a href="/edit_task/${task.id}" class="text-primary me-2" title="Edit Task">
                        <i class="bi bi-pencil-square"></i>
                    </a>
                    <i class="bi bi-trash text-danger" title="Delete Task" style="cursor: pointer;" onclick="deleteTask(${task.id})"></i>
                </div>
            </div>
        `;
        tasksList.appendChild(li);
    });

    // Set the Add Task link
    addTaskLink.href = `/add_task?project_id=${projectId}`;

    // Open the panel
    panel.classList.add('open');
}

// Close Project Details Panel
function closeProjectDetails() {
    const panel = document.getElementById('project-details-panel');
    panel.classList.remove('open');
}

// Mark Task as Complete
function markTaskComplete(taskId, projectId) {
    fetch(`/complete_task/${taskId}`, {
        method: 'POST',
    })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                openProjectDetails(projectId); // Refresh the task list
            } else {
                alert('Failed to mark task as complete.');
            }
        });
}

// Delete Task
function deleteTask(taskId) {
    if (!confirm('Are you sure you want to delete this task?')) {
        return;
    }

    fetch(`/delete_task/${taskId}`, {
        method: 'POST',
    })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert('Task deleted successfully!');
                openProjectDetails(currentProjectId); // Refresh the task list
            } else {
                alert(data.message || 'Failed to delete task.');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('An error occurred while deleting the task.');
        });
}

// Delete Project
function deleteProject() {
    if (!confirm('Are you sure you want to delete this project? This will delete all associated tasks.')) {
        return;
    }

    fetch(`/delete_project/${currentProjectId}`, {
        method: 'POST',
    })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert('Project deleted successfully!');
                closeProjectDetails();
                location.reload(); // Reload the page to refresh the project list
            } else {
                alert(data.message || 'Failed to delete project.');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('An error occurred while deleting the project.');
        });
}



// AI INTEGRATION
// AI INTEGRATION - IMPROVED VERSION
function createTaskNLP() {
    const inputElement = document.getElementById('nlp-task-input');
    const button = document.getElementById('nlp-task-button');
    const btnText = document.getElementById('btn-text');
    const btnSpinner = document.getElementById('btn-spinner');
    const input = inputElement.value.trim();
    const projectId = document.getElementById('project-select').value;

    if (!input) {
        showAlert('Please enter a task description.', 'danger');
        inputElement.focus();
        return;
    }

    button.disabled = true;
    btnText.classList.add('d-none');
    btnSpinner.classList.remove('d-none');

    fetch('/create_task_nlp', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ input, project_id: projectId })
    })
    .then(response => response.json())
    .then(data => {
        button.disabled = false;
        btnText.classList.remove('d-none');
        btnSpinner.classList.add('d-none');

        if (data.success) {
            showAlert('Task created!', 'success');
            inputElement.value = '';
        } else {
            showAlert(data.message || 'Failed to create task.', 'danger');
            if (data.ai_response) {
                console.log('AI raw response:', data.ai_response);
            }
        }
    })
    .catch(error => {
        button.disabled = false;
        btnText.classList.remove('d-none');
        btnSpinner.classList.add('d-none');
        showAlert('An error occurred while creating the task.', 'danger');
        console.error(error);
    });
}