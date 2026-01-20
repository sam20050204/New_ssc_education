// Global flag to prevent double form submission
let formSubmitted = false;

function confirmDelete(id){
    if(confirm("Are you sure you want to delete this enquiry?")){
        window.location.href = `/enquiry/${id}/delete/`;
    }
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

// Course selection - show/hide other course field
document.addEventListener('DOMContentLoaded', function() {
    const courseEnquiry = document.getElementById('courseEnquiry');
    if (courseEnquiry) {
        courseEnquiry.addEventListener('change', function() {
            const otherCourseField = document.getElementById('otherCourseEnquiry');
            if (this.value === 'Other') {
                otherCourseField.style.display = 'block';
                otherCourseField.required = true;
            } else {
                otherCourseField.style.display = 'none';
                otherCourseField.required = false;
                otherCourseField.value = '';
            }
        });
    }
});

// View Enquiry Details
function viewEnquiry(enquiryId) {
    fetch(`/enquiry/${enquiryId}/`)
        .then(response => response.json())
        .then(data => {
            // Determine display course
            let displayCourse = data.course;
            // Note: Since Enquiry model doesn't have custom_course field,
            // we just show "Other" if that's the course
            
            const content = `
                <div class="detail-section">
                    <h3>👤 Personal Information</h3>
                    <div class="detail-row">
                        <span class="detail-label">Name:</span>
                        <span class="detail-value">${data.name}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Mobile:</span>
                        <span class="detail-value">${data.mobile}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Education:</span>
                        <span class="detail-value">${data.education}</span>
                    </div>
                </div>

                <div class="detail-section">
                    <h3>📚 Course Information</h3>
                    <div class="detail-row">
                        <span class="detail-label">Course:</span>
                        <span class="course-badge-modal">${displayCourse}</span>
                    </div>
                </div>

                <div class="detail-section">
                    <h3>🏠 Address Information</h3>
                    <div class="detail-row">
                        <span class="detail-label">Address:</span>
                        <span class="detail-value ${!data.address ? 'empty' : ''}">${data.address || 'Not provided'}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">City:</span>
                        <span class="detail-value ${!data.city ? 'empty' : ''}">${data.city || 'Not provided'}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Taluka:</span>
                        <span class="detail-value ${!data.taluka ? 'empty' : ''}">${data.taluka || 'Not provided'}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">District:</span>
                        <span class="detail-value ${!data.district ? 'empty' : ''}">${data.district || 'Not provided'}</span>
                    </div>
                </div>

                <div class="detail-section">
                    <h3>📅 Date Information</h3>
                    <div class="detail-row">
                        <span class="detail-label">Enquiry Date:</span>
                        <span class="detail-value">${data.created_at}</span>
                    </div>
                </div>

                <div class="modal-actions" style="margin-top: 20px; padding-top: 20px; border-top: 2px solid #e8e8e8;">
                    <a href="/enquiries/convert/${enquiryId}/" class="btn-submit">
                        🎓 Convert to Admission
                    </a>
                    <button type="button" class="btn-cancel" onclick="closeViewModal()">
                        ❌ Close
                    </button>
                </div>
            `;
            
            document.getElementById('enquiryDetailsContent').innerHTML = content;
            document.getElementById('viewEnquiryModal').classList.add('active');
            document.body.style.overflow = 'hidden';
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Error loading enquiry details');
        });
}

// Close View Modal
function closeViewModal() {
    document.getElementById('viewEnquiryModal').classList.remove('active');
    document.body.style.overflow = 'auto';
}

// Open New Enquiry Modal
function openNewEnquiryModal() {
    document.getElementById('newEnquiryModal').classList.add('active');
    document.body.style.overflow = 'hidden';
}

// Close New Enquiry Modal
function closeNewEnquiryModal() {
    document.getElementById('newEnquiryModal').classList.remove('active');
    document.body.style.overflow = 'auto';
    document.getElementById('newEnquiryForm').reset();
    document.getElementById('successMessageEnquiry').classList.remove('show');
    // Hide "Other" course field if shown
    const otherField = document.getElementById('otherCourseEnquiry');
    if (otherField) {
        otherField.style.display = 'none';
        otherField.required = false;
    }
}

// Handle New Enquiry Form Submission with AJAX
document.addEventListener('DOMContentLoaded', function() {
    const newEnquiryForm = document.getElementById('newEnquiryForm');
    if (newEnquiryForm) {
        newEnquiryForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            // ================= PREVENT DOUBLE SUBMISSION =================
            if (formSubmitted) {
                alert('⏳ Form is being submitted. Please wait...');
                return false;
            }
            
            // ================= VALIDATE FORM DATA =================
            const nameInput = document.getElementById('nameEnquiry');
            const mobileInput = document.getElementById('mobileEnquiry');
            const educationInput = document.getElementById('educationEnquiry');
            const courseInput = document.getElementById('courseEnquiry');
            const otherCourseInput = document.getElementById('otherCourseEnquiry');
            
            // Validate name
            const name = nameInput ? nameInput.value.trim() : '';
            if (!name) {
                alert('❌ Please enter your name');
                return false;
            }
            
            // Validate mobile
            const mobile = mobileInput ? mobileInput.value.trim() : '';
            if (!mobile) {
                alert('❌ Please enter mobile number');
                return false;
            }
            if (!/^[0-9]{10}$/.test(mobile)) {
                alert('❌ Please enter a valid 10-digit mobile number');
                return false;
            }
            
            // Validate education
            const education = educationInput ? educationInput.value.trim() : '';
            if (!education) {
                alert('❌ Please enter education qualification');
                return false;
            }
            
            // Validate course
            const course = courseInput ? courseInput.value.trim() : '';
            if (!course) {
                alert('❌ Please select a course');
                return false;
            }
            
            // Validate custom course if "Other" selected
            if (course === 'Other') {
                const customCourse = otherCourseInput ? otherCourseInput.value.trim() : '';
                if (!customCourse) {
                    alert('❌ Please specify the course name');
                    return false;
                }
            }
            
            // ================= MARK AS SUBMITTED =================
            formSubmitted = true;
            
            const formData = new FormData(this);
            const submitBtn = this.querySelector('.btn-submit');
            const originalText = submitBtn.textContent;
            
            // ================= DISABLE SUBMIT BUTTON =================
            submitBtn.textContent = '⏳ Submitting...';
            submitBtn.disabled = true;
            submitBtn.style.opacity = '0.6';
            submitBtn.style.cursor = 'not-allowed';
            
            // ================= DISABLE ALL FORM INPUTS =================
            const allInputs = newEnquiryForm.querySelectorAll('input, textarea, select');
            allInputs.forEach(input => {
                input.disabled = true;
            });
            
            fetch(window.location.href, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-CSRFToken': getCookie('csrftoken'),
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
            .then(response => {
                if (response.ok) {
                    // Show success message
                    const successMsg = document.getElementById('successMessageEnquiry');
                    successMsg.textContent = '✅ Enquiry added successfully!';
                    successMsg.classList.add('show');
                    
                    // Clear form fields
                    newEnquiryForm.reset();
                    
                    // Hide "Other" course field if shown
                    const otherField = document.getElementById('otherCourseEnquiry');
                    if (otherField) {
                        otherField.style.display = 'none';
                        otherField.required = false;
                    }
                    
                    // Hide success message after 3 seconds
                    setTimeout(() => {
                        successMsg.classList.remove('show');
                    }, 3000);
                    
                    // Reset form state for next entry
                    formSubmitted = false;
                    submitBtn.textContent = originalText;
                    submitBtn.disabled = false;
                    submitBtn.style.opacity = '1';
                    submitBtn.style.cursor = 'pointer';
                    
                    // Re-enable form inputs
                    allInputs.forEach(input => {
                        input.disabled = false;
                    });
                    
                    // Note: Modal stays open for next entry
                } else {
                    throw new Error('Submission failed');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('❌ Error adding enquiry. Please try again.');
                
                // Reset on error
                formSubmitted = false;
                submitBtn.textContent = originalText;
                submitBtn.disabled = false;
                submitBtn.style.opacity = '1';
                submitBtn.style.cursor = 'pointer';
                
                // Re-enable form inputs
                allInputs.forEach(input => {
                    input.disabled = false;
                });
            });
        });
    }
});

// ================= PREVENT RE-SUBMISSION ON PAGE REFRESH =================
window.addEventListener('beforeunload', function() {
    if (formSubmitted) {
        formSubmitted = true;  // Keep flag true
    }
});
// Close modals on ESC key
document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
        closeViewModal();
        closeNewEnquiryModal();
    }
});

// Close modals on outside click
window.addEventListener('click', function(e) {
    const viewModal = document.getElementById('viewEnquiryModal');
    const newModal = document.getElementById('newEnquiryModal');
    
    if (e.target === viewModal) {
        closeViewModal();
    }
    if (e.target === newModal) {
        closeNewEnquiryModal();
    }
});