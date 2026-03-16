/**
 * Student Timetable JavaScript
 * Handles modal interactions, form submissions, and UI interactions
 */

/**
 * Open student details modal
 */
function openStudentModal(event, name, mobile, email, address, course, batch) {
    event.preventDefault();
    document.getElementById('modalName').textContent = name;
    document.getElementById('modalMobile').textContent = mobile;
    document.getElementById('modalEmail').textContent = email;
    document.getElementById('modalAddress').textContent = address;
    document.getElementById('modalCourse').textContent = course;
    document.getElementById('modalBatch').textContent = batch;
    document.getElementById('studentModal').classList.add('show');
}

/**
 * Close student details modal
 */
function closeStudentModal() {
    document.getElementById('studentModal').classList.remove('show');
}

/**
 * Submit time slot form when dropdown changes
 */
function submitSlotForm(selectElement) {
    const form = selectElement.closest('.inline-form');
    if (form && selectElement.value) {
        form.submit();
    }
}

/**
 * Close modal when clicking outside of it
 */
window.onclick = function(event) {
    const modal = document.getElementById('studentModal');
    if (event.target == modal) {
        modal.classList.remove('show');
    }
}

/**
 * Initialize on document load
 */
document.addEventListener('DOMContentLoaded', function() {
    // Auto-dismiss alerts after 4 seconds
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 4000);
    });
});
