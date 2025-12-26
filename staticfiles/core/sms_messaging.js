// Global variables
let allStudents = [];
let selectedStudentIds = new Set();

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    setupEventListeners();
});

// Setup event listeners
function setupEventListeners() {
    // Apply filter button
    document.getElementById('applyFilterBtn').addEventListener('click', loadStudents);
    
    // Select all checkbox
    document.getElementById('selectAllCheckbox').addEventListener('change', toggleSelectAll);
    
    // Message textarea character count
    const messageTextarea = document.getElementById('messageText');
    messageTextarea.addEventListener('input', updateCharCount);
    
    // Send message button
    document.getElementById('sendMessageBtn').addEventListener('click', sendMessage);
    
    // Clear message button
    document.getElementById('clearMessageBtn').addEventListener('click', clearMessage);
}

// Load students based on filters
async function loadStudents() {
    try {
        showLoading(true, 'Loading students...');
        
        const month = document.getElementById('monthFilter').value;
        const year = document.getElementById('yearFilter').value;
        
        // Build query parameters
        const params = new URLSearchParams();
        if (month) params.append('month', month);
        if (year) params.append('year', year);
        
        const response = await fetch(`/api/sms/get-students/?${params.toString()}`);
        const data = await response.json();
        
        if (data.success) {
            allStudents = data.students;
            renderStudents(allStudents);
            updateSelectedCount();
            
            if (allStudents.length > 0) {
                showNotification(`Loaded ${allStudents.length} student(s)`, 'success');
            } else {
                showNotification('No students found for selected filters', 'info');
            }
        } else {
            throw new Error(data.error || 'Failed to load students');
        }
        
        showLoading(false);
    } catch (error) {
        console.error('Error:', error);
        showNotification('Failed to load students. Please try again.', 'error');
        showLoading(false);
    }
}

// Render students grid
function renderStudents(students) {
    const grid = document.getElementById('studentsGrid');
    const emptyState = document.getElementById('emptyState');
    const selectionHeader = document.getElementById('selectionHeader');
    
    // Clear previous selections
    selectedStudentIds.clear();
    document.getElementById('selectAllCheckbox').checked = false;
    
    if (students.length === 0) {
        grid.innerHTML = '';
        emptyState.style.display = 'block';
        selectionHeader.style.display = 'none';
        return;
    }
    
    emptyState.style.display = 'none';
    selectionHeader.style.display = 'flex';
    
    let html = '';
    students.forEach(student => {
        const firstLetter = student.full_name.charAt(0).toUpperCase();
        const photoHtml = student.photo_url 
            ? `<img src="${student.photo_url}" alt="${student.full_name}">`
            : `<div class="avatar-placeholder">${firstLetter}</div>`;
        
        html += `
            <div class="student-card" data-student-id="${student.id}" onclick="toggleStudentSelection(${student.id})">
                <div class="student-checkbox-container">
                    <input type="checkbox" class="student-checkbox" data-student-id="${student.id}" onclick="event.stopPropagation();">
                </div>
                
                <div class="student-info-card">
                    <div class="student-avatar">
                        ${photoHtml}
                    </div>
                    
                    <div class="student-details-card">
                        <div class="student-name-card">${student.full_name}</div>
                        
                        <div class="student-meta">
                            <div class="meta-item">
                                <span class="meta-icon">📞</span>
                                <span>${student.mobile_own}</span>
                            </div>
                            
                            <div class="meta-item">
                                <span class="meta-icon">📚</span>
                                <span class="course-badge-small">${student.course}</span>
                            </div>
                            
                            <div class="meta-item">
                                <span class="meta-icon">💰</span>
                                <span>Remaining: ₹${student.remaining_fees.toFixed(2)}</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    });
    
    grid.innerHTML = html;
    
    // Add event listeners to checkboxes
    document.querySelectorAll('.student-checkbox').forEach(checkbox => {
        checkbox.addEventListener('change', function(e) {
            e.stopPropagation();
            const studentId = parseInt(this.dataset.studentId);
            if (this.checked) {
                selectedStudentIds.add(studentId);
            } else {
                selectedStudentIds.delete(studentId);
            }
            updateSelectedCount();
            updateCardAppearance(studentId);
        });
    });
}

// Toggle student selection when clicking card
function toggleStudentSelection(studentId) {
    const checkbox = document.querySelector(`.student-checkbox[data-student-id="${studentId}"]`);
    checkbox.checked = !checkbox.checked;
    checkbox.dispatchEvent(new Event('change'));
}

// Update card appearance based on selection
function updateCardAppearance(studentId) {
    const card = document.querySelector(`.student-card[data-student-id="${studentId}"]`);
    const checkbox = document.querySelector(`.student-checkbox[data-student-id="${studentId}"]`);
    
    if (checkbox.checked) {
        card.classList.add('selected');
    } else {
        card.classList.remove('selected');
    }
}

// Toggle select all
function toggleSelectAll() {
    const selectAllCheckbox = document.getElementById('selectAllCheckbox');
    const studentCheckboxes = document.querySelectorAll('.student-checkbox');
    
    selectedStudentIds.clear();
    
    studentCheckboxes.forEach(checkbox => {
        checkbox.checked = selectAllCheckbox.checked;
        const studentId = parseInt(checkbox.dataset.studentId);
        if (selectAllCheckbox.checked) {
            selectedStudentIds.add(studentId);
        }
        updateCardAppearance(studentId);
    });
    
    updateSelectedCount();
}

// Update selected count
function updateSelectedCount() {
    const count = selectedStudentIds.size;
    document.getElementById('selectedCount').textContent = count;
    
    // Update select all checkbox state
    const selectAllCheckbox = document.getElementById('selectAllCheckbox');
    const totalStudents = allStudents.length;
    
    if (count === 0) {
        selectAllCheckbox.checked = false;
        selectAllCheckbox.indeterminate = false;
    } else if (count === totalStudents) {
        selectAllCheckbox.checked = true;
        selectAllCheckbox.indeterminate = false;
    } else {
        selectAllCheckbox.checked = false;
        selectAllCheckbox.indeterminate = true;
    }
}

// Update character count
function updateCharCount() {
    const textarea = document.getElementById('messageText');
    const charCountSpan = document.getElementById('charCount');
    const count = textarea.value.length;
    const maxLength = 160;
    
    charCountSpan.textContent = `${count}/${maxLength}`;
    
    // Update color based on count
    charCountSpan.classList.remove('warning', 'error');
    if (count > maxLength) {
        charCountSpan.classList.add('error');
    } else if (count > maxLength * 0.8) {
        charCountSpan.classList.add('warning');
    }
}

// Clear message
function clearMessage() {
    document.getElementById('messageText').value = '';
    updateCharCount();
}

// Send message
async function sendMessage() {
    try {
        // Validate selection
        if (selectedStudentIds.size === 0) {
            showNotification('Please select at least one student', 'error');
            return;
        }
        
        // Validate message
        const message = document.getElementById('messageText').value.trim();
        if (!message) {
            showNotification('Please enter a message', 'error');
            return;
        }
        
        if (message.length > 160) {
            showNotification('Message is too long (max 160 characters)', 'error');
            return;
        }
        
        // Confirm sending
        const confirmMessage = `Send SMS to ${selectedStudentIds.size} student(s)?`;
        if (!confirm(confirmMessage)) {
            return;
        }
        
        showLoading(true, 'Sending SMS...');
        
        // Send request
        const response = await fetch('/api/sms/send/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({
                student_ids: Array.from(selectedStudentIds),
                message: message
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showNotification(data.message, 'success');
            
            // Clear message and selections
            clearMessage();
            selectedStudentIds.clear();
            updateSelectedCount();
            
            // Deselect all checkboxes
            document.querySelectorAll('.student-checkbox').forEach(checkbox => {
                checkbox.checked = false;
            });
            document.querySelectorAll('.student-card').forEach(card => {
                card.classList.remove('selected');
            });
            document.getElementById('selectAllCheckbox').checked = false;
        } else {
            showNotification(data.error || 'Failed to send SMS', 'error');
        }
        
        showLoading(false);
    } catch (error) {
        console.error('Error:', error);
        showNotification('An error occurred while sending SMS', 'error');
        showLoading(false);
    }
}

// Show/hide loading overlay
function showLoading(show, message = 'Loading...') {
    const overlay = document.getElementById('loadingOverlay');
    const loadingMessage = document.getElementById('loadingMessage');
    
    if (show) {
        loadingMessage.textContent = message;
        overlay.classList.add('active');
    } else {
        overlay.classList.remove('active');
    }
}

// Show notification
function showNotification(message, type = 'success') {
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.textContent = message;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.style.animation = 'fadeOut 0.5s ease';
        setTimeout(() => {
            notification.remove();
        }, 500);
    }, 3000);
}

// Get CSRF token
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}