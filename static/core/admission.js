// REPLACE the entire static/core/admission.js file with this:

document.addEventListener('DOMContentLoaded', function() {
    
    // ===================== AUTO-GENERATE FULL NAME =====================
    const studentName = document.getElementById('student_name');
    const fatherName = document.getElementById('father_name');
    const surname = document.getElementById('surname');
    const fullName = document.getElementById('full_name');
    
    function generateFullName() {
        const sName = studentName.value.trim();
        const fName = fatherName.value.trim();
        const surnameVal = surname.value.trim();
        
        const parts = [];
        if (sName) parts.push(sName);
        if (fName) parts.push(fName);
        if (surnameVal) parts.push(surnameVal);
        
        fullName.value = parts.join(' ');
    }
    
    studentName.addEventListener('input', generateFullName);
    fatherName.addEventListener('input', generateFullName);
    surname.addEventListener('input', generateFullName);
    
    
    // ===================== COURSE SELECTION - SHOW/HIDE CUSTOM FIELD =====================
    const courseSelect = document.getElementById('course');
    const customCourseGroup = document.getElementById('customCourseGroup');
    const customCourseInput = document.getElementById('custom_course');
    
    courseSelect.addEventListener('change', function() {
        if (this.value === 'Other') {
            customCourseGroup.style.display = 'block';
            customCourseInput.required = true;
        } else {
            customCourseGroup.style.display = 'none';
            customCourseInput.required = false;
            customCourseInput.value = '';
        }
    });
    
    
    // ===================== PHOTO PREVIEW =====================
    const photoInput = document.getElementById('photo');
    const photoPreview = document.getElementById('photoPreview');
    const previewImage = document.getElementById('previewImage');
    const photoPlaceholder = document.querySelector('.photo-placeholder');
    
    photoInput.addEventListener('change', function(e) {
        const file = e.target.files[0];
        
        if (file) {
            // Check file size (max 2MB)
            if (file.size > 2 * 1024 * 1024) {
                alert('File size should be less than 2MB');
                photoInput.value = '';
                return;
            }
            
            // Check file type
            if (!file.type.startsWith('image/')) {
                alert('Please select an image file');
                photoInput.value = '';
                return;
            }
            
            const reader = new FileReader();
            
            reader.onload = function(event) {
                previewImage.src = event.target.result;
                previewImage.style.display = 'block';
                photoPlaceholder.style.display = 'none';
            };
            
            reader.readAsDataURL(file);
        }
    });
    
    
    // ===================== FORM VALIDATION =====================
    const form = document.getElementById('admissionForm');
    
    form.addEventListener('submit', function(e) {
        // Validate mobile numbers
        const mobileOwn = document.getElementById('mobile_own').value;
        const parentMobile = document.getElementById('parent_mobile').value;
        
        if (mobileOwn && !/^[0-9]{10}$/.test(mobileOwn)) {
            e.preventDefault();
            alert('Please enter a valid 10-digit mobile number');
            document.getElementById('mobile_own').focus();
            return false;
        }
        
        if (parentMobile && !/^[0-9]{10}$/.test(parentMobile)) {
            e.preventDefault();
            alert('Please enter a valid 10-digit parent mobile number');
            document.getElementById('parent_mobile').focus();
            return false;
        }
        
        // Validate pin code
        const pinCode = document.getElementById('pin_code').value;
        if (pinCode && !/^[0-9]{6}$/.test(pinCode)) {
            e.preventDefault();
            alert('Please enter a valid 6-digit pin code');
            document.getElementById('pin_code').focus();
            return false;
        }
        
        // Validate date of birth
        const dob = new Date(document.getElementById('date_of_birth').value);
        const today = new Date();
        const age = today.getFullYear() - dob.getFullYear();
        
        if (age < 5 || age > 100) {
            e.preventDefault();
            alert('Please enter a valid date of birth');
            document.getElementById('date_of_birth').focus();
            return false;
        }
    });
    
    
    // ===================== RESET FORM - COMPLETE CLEAR =====================
    const resetBtn = document.querySelector('.btn-reset');
    if (resetBtn) {
        resetBtn.addEventListener('click', function(e) {
            e.preventDefault();
            
            if (confirm('⚠️ Are you sure you want to reset the form?\n\nAll entered data will be cleared.')) {
                // Reset the form
                form.reset();
                
                // Clear photo preview
                previewImage.src = '';
                previewImage.style.display = 'none';
                photoPlaceholder.style.display = 'flex';
                
                // Hide custom course field
                customCourseGroup.style.display = 'none';
                customCourseInput.required = false;
                
                // Clear full name
                fullName.value = '';
                
                // Reset to first field
                courseSelect.focus();
                
                // Show success message
                showNotification('✅ Form cleared successfully!', 'success');
            }
        });
    }
    
    
    // ===================== AUTO-FOCUS FIRST FIELD =====================
    setTimeout(function() {
        courseSelect.focus();
    }, 100);
});

// ===================== NOTIFICATION FUNCTION =====================
function showNotification(message, type = 'success') {
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.style.cssText = `
        position: fixed;
        top: 90px;
        right: 20px;
        padding: 15px 25px;
        border-radius: 8px;
        font-weight: 600;
        z-index: 10000;
        animation: slideIn 0.5s ease;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
    `;
    
    if (type === 'success') {
        notification.style.background = '#10b981';
        notification.style.color = 'white';
    } else {
        notification.style.background = '#ef4444';
        notification.style.color = 'white';
    }
    
    notification.textContent = message;
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.style.animation = 'fadeOut 0.5s ease';
        setTimeout(() => {
            notification.remove();
        }, 500);
    }, 3000);
}

