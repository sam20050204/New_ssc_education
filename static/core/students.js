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

// Open student modal
function openStudentModal(studentId) {
    const modal = document.getElementById('studentModal');
    
    fetch(`/admission/student-detail-admitted/${studentId}/`)
        .then(response => response.json())
        .then(data => {
            // Set student ID
            document.getElementById('studentId').value = data.id;
            
            // Personal info
            document.getElementById('studentName').value = data.student_name;
            document.getElementById('fatherName').value = data.father_name;
            document.getElementById('surname').value = data.surname;
            document.getElementById('motherName').value = data.mother_name;
            document.getElementById('fullName').value = data.full_name;
            document.getElementById('dob').value = data.date_of_birth;
            document.getElementById('gender').value = data.gender;
            document.getElementById('maritalStatus').value = data.marital_status;
            
            // Photo
            const modalPhoto = document.getElementById('modalPhoto');
            if (data.photo) {
                modalPhoto.src = data.photo;
            } else {
                const firstLetter = data.student_name.charAt(0).toUpperCase();
                modalPhoto.src = `data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" width="150" height="150"><rect width="150" height="150" fill="%23667eea"/><text x="50%" y="50%" font-size="60" fill="white" text-anchor="middle" dy=".3em">${firstLetter}</text></svg>`;
            }
            
            // Contact info
            document.getElementById('mobileOwn').value = data.mobile_own;
            document.getElementById('parentMobile').value = data.parent_mobile || '';
            
            // Course info
            document.getElementById('courseSelect').value = data.course;
            document.getElementById('customCourse').value = data.custom_course || '';
            document.getElementById('qualification').value = data.educational_qualification;
            
            // Address
            document.getElementById('address').value = data.address;
            document.getElementById('city').value = data.city;
            document.getElementById('tehsil').value = data.tehsil_block;
            document.getElementById('district').value = data.district;
            document.getElementById('pinCode').value = data.pin_code;
            
            // Financial info
            document.getElementById('totalFees').value = data.total_fees || 5000;
            document.getElementById('paidFees').value = data.paid_fees || 0;
            calculateRemainingFees();
            
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
    const totalFees = parseFloat(document.getElementById('totalFees').value) || 0;
    const paidFees = parseFloat(document.getElementById('paidFees').value) || 0;
    const remainingFees = totalFees - paidFees;
    document.getElementById('remainingFees').value = remainingFees.toFixed(2);
}

// Auto-generate full name
function generateFullName() {
    const studentName = document.getElementById('studentName').value.trim();
    const fatherName = document.getElementById('fatherName').value.trim();
    const surname = document.getElementById('surname').value.trim();
    
    const parts = [];
    if (studentName) parts.push(studentName);
    if (fatherName) parts.push(fatherName);
    if (surname) parts.push(surname);
    
    document.getElementById('fullName').value = parts.join(' ');
}

// Add event listeners
document.addEventListener('DOMContentLoaded', function() {
    const totalFeesInput = document.getElementById('totalFees');
    const paidFeesInput = document.getElementById('paidFees');
    
    if (totalFeesInput) {
        totalFeesInput.addEventListener('input', calculateRemainingFees);
    }
    if (paidFeesInput) {
        paidFeesInput.addEventListener('input', calculateRemainingFees);
    }
    
    // Auto-generate full name
    const studentNameInput = document.getElementById('studentName');
    const fatherNameInput = document.getElementById('fatherName');
    const surnameInput = document.getElementById('surname');
    
    if (studentNameInput) studentNameInput.addEventListener('input', generateFullName);
    if (fatherNameInput) fatherNameInput.addEventListener('input', generateFullName);
    if (surnameInput) surnameInput.addEventListener('input', generateFullName);
    
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
            saveBtn.textContent = '💾 Saving...';
            saveBtn.disabled = true;
            
            fetch(`/admission/update-student-admitted/${studentId}/`, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-CSRFToken': getCookie('csrftoken')
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    alert('✅ Student details updated successfully!');
                    closeModal();
                    location.reload();
                } else {
                    alert('❌ Error: ' + (data.error || 'Unknown error'));
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('❌ Error updating student details');
            })
            .finally(() => {
                saveBtn.textContent = originalText;
                saveBtn.disabled = false;
            });
        });
    }
});