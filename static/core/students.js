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

// Reset filters
function resetFilters() {
    window.location.href = window.location.pathname;
}

// Export to Excel
function exportToExcel() {
    const form = document.getElementById('filterForm');
    const params = new URLSearchParams(new FormData(form));
    window.location.href = '/export-students/?' + params.toString();
}

// Open student modal
function openStudentModal(studentId) {
    const modal = document.getElementById('studentModal');
    
    fetch(`/student-detail/${studentId}/`)
        .then(response => response.json())
        .then(data => {
            // Set student ID
            document.getElementById('studentId').value = data.id;
            
            // Personal info
            document.getElementById('studentName').value = data.name;
            document.getElementById('studentPhone').value = data.phone;
            document.getElementById('studentEmail').value = data.email;
            document.getElementById('studentDOB').value = data.date_of_birth;
            document.getElementById('studentQualification').value = data.qualification;
            
            // Photo
            const modalPhoto = document.getElementById('modalPhoto');
            if (data.photo) {
                modalPhoto.src = data.photo;
            } else {
                modalPhoto.src = 'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" width="150" height="150"><rect width="150" height="150" fill="%23667eea"/><text x="50%" y="50%" font-size="60" fill="white" text-anchor="middle" dy=".3em">' + data.name.charAt(0) + '</text></svg>';
            }
            
            // Course info
            document.getElementById('studentCourse').value = data.course_id;
            document.getElementById('studentAdmissionDate').value = data.admission_date;
            
            // Address
            document.getElementById('studentAddress').value = data.address;
            document.getElementById('studentCity').value = data.city;
            document.getElementById('studentState').value = data.state;
            document.getElementById('studentPincode').value = data.pincode;
            
            // Parent info
            document.getElementById('studentParentName').value = data.parent_name;
            document.getElementById('studentParentPhone').value = data.parent_phone;
            
            // Financial info
            document.getElementById('studentTotalFees').value = data.total_fees;
            document.getElementById('studentPaidFees').value = data.paid_fees;
            document.getElementById('studentRemainingFees').value = data.remaining_fees;
            
            modal.style.display = 'block';
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Error loading student details');
        });
}

// Close modal
function closeModal() {
    document.getElementById('studentModal').style.display = 'none';
}

// Close modal when clicking outside
window.onclick = function(event) {
    const modal = document.getElementById('studentModal');
    if (event.target == modal) {
        modal.style.display = 'none';
    }
}

// Calculate remaining fees
function calculateRemainingFees() {
    const totalFees = parseFloat(document.getElementById('studentTotalFees').value) || 0;
    const paidFees = parseFloat(document.getElementById('studentPaidFees').value) || 0;
    const remainingFees = totalFees - paidFees;
    document.getElementById('studentRemainingFees').value = remainingFees.toFixed(2);
}

// Add event listeners for fee calculations
document.addEventListener('DOMContentLoaded', function() {
    const totalFeesInput = document.getElementById('studentTotalFees');
    const paidFeesInput = document.getElementById('studentPaidFees');
    
    if (totalFeesInput) {
        totalFeesInput.addEventListener('input', calculateRemainingFees);
    }
    if (paidFeesInput) {
        paidFeesInput.addEventListener('input', calculateRemainingFees);
    }
    
    // Handle photo preview
    const photoInput = document.getElementById('photoInput');
    if (photoInput) {
        photoInput.addEventListener('change', function(e) {
            if (e.target.files && e.target.files[0]) {
                const reader = new FileReader();
                reader.onload = function(e) {
                    document.getElementById('modalPhoto').src = e.target.result;
                };
                reader.readAsDataURL(e.target.files[0]);
            }
        });
    }
    
    // Handle form submission
    const studentForm = document.getElementById('studentForm');
    if (studentForm) {
        studentForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const studentId = document.getElementById('studentId').value;
            const formData = new FormData(studentForm);
            
            // Show loading state
            const saveBtn = document.querySelector('.save-btn');
            const originalText = saveBtn.textContent;
            saveBtn.textContent = 'Saving...';
            saveBtn.disabled = true;
            
            fetch(`/update-student/${studentId}/`, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-CSRFToken': getCookie('csrftoken')
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    alert('Student details updated successfully!');
                    closeModal();
                    location.reload();
                } else {
                    alert('Error updating student details: ' + (data.error || 'Unknown error'));
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('Error updating student details');
            })
            .finally(() => {
                saveBtn.textContent = originalText;
                saveBtn.disabled = false;
            });
        });
    }
});