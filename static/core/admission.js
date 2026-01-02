/* MODAL CONTROLS - MUST BE OUTSIDE DOMContentLoaded */
function openAddCourseModal() {
    const modal = document.getElementById('addCourseModal');
    if (modal) modal.classList.add('active');
}

function closeAddCourseModal() {
    const modal = document.getElementById('addCourseModal');
    if (modal) {
        modal.classList.remove('active');
        const form = document.getElementById('addCourseForm');
        if (form) form.reset();
    }
}

/* MAIN CODE */
document.addEventListener('DOMContentLoaded', function() {
    
    const studentName = document.getElementById('student_name');
    const fatherName = document.getElementById('father_name');
    const surname = document.getElementById('surname');
    const fullName = document.getElementById('full_name');

    function generateFullName() {
        const parts = [];
        if (studentName && studentName.value) parts.push(studentName.value.trim());
        if (fatherName && fatherName.value) parts.push(fatherName.value.trim());
        if (surname && surname.value) parts.push(surname.value.trim());
        if (fullName) fullName.value = parts.join(' ');
    }

    if (studentName) studentName.addEventListener('input', generateFullName);
    if (fatherName) fatherName.addEventListener('input', generateFullName);
    if (surname) surname.addEventListener('input', generateFullName);

    const courseSelect = document.getElementById('course');
    const customCourseGroup = document.getElementById('customCourseGroup');
    const customCourseInput = document.getElementById('custom_course');

    if (courseSelect) {
        courseSelect.addEventListener('change', function() {
            if (this.value === 'Other') {
                if (customCourseGroup) customCourseGroup.style.display = 'block';
                if (customCourseInput) customCourseInput.required = true;
            } else {
                if (customCourseGroup) customCourseGroup.style.display = 'none';
                if (customCourseInput) {
                    customCourseInput.required = false;
                    customCourseInput.value = '';
                }
            }
        });
    }

    const photoInput = document.getElementById('photo');
    const previewImage = document.getElementById('previewImage');
    const photoPlaceholder = document.querySelector('.photo-placeholder');

    if (photoInput && previewImage && photoPlaceholder) {
        photoInput.addEventListener('change', function(e) {
            const file = e.target.files[0];
            if (!file) return;

            if (file.size > 2 * 1024 * 1024) {
                alert('❌ File size should be less than 2MB');
                photoInput.value = '';
                return;
            }

            if (!file.type.startsWith('image/')) {
                alert('❌ Please select an image file');
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
        });
    }

    const form = document.getElementById('admissionForm');
    if (form) {
        form.addEventListener('submit', function(e) {

            const mobileOwn = document.getElementById('mobile_own')?.value || '';
            const parentMobile = document.getElementById('parent_mobile')?.value || '';
            const pinCode = document.getElementById('pin_code')?.value || '';

            if (mobileOwn && !/^[0-9]{10}$/.test(mobileOwn)) {
                e.preventDefault(); 
                alert('❌ Invalid 10-digit mobile number'); 
                return;
            }
            if (parentMobile && !/^[0-9]{10}$/.test(parentMobile)) {
                e.preventDefault(); 
                alert('❌ Invalid parent mobile number'); 
                return;
            }
            if (pinCode && !/^[0-9]{6}$/.test(pinCode)) {
                e.preventDefault(); 
                alert('❌ Invalid 6-digit pin code'); 
                return;
            }
        });
    }

    const resetBtn = document.querySelector('.btn-reset');
    if (resetBtn && form) {
        resetBtn.addEventListener('click', function(e) {
            e.preventDefault();
            if (confirm('Are you sure you want to reset the form? All data will be cleared.')) {
                
                // CLEAR ALL TEXT INPUTS
                const textInputs = form.querySelectorAll('input[type="text"], input[type="tel"], input[type="email"], input[type="number"], input[type="date"]');
                textInputs.forEach(input => {
                    input.value = '';
                });

                // CLEAR TEXTAREAS
                const textareas = form.querySelectorAll('textarea');
                textareas.forEach(textarea => {
                    textarea.value = '';
                });

                // CLEAR SELECT DROPDOWNS
                const selects = form.querySelectorAll('select');
                selects.forEach(select => {
                    select.selectedIndex = 0;
                    select.value = '';
                });

                // CLEAR FILE INPUTS
                const fileInputs = form.querySelectorAll('input[type="file"]');
                fileInputs.forEach(input => {
                    input.value = '';
                });

                // Clear full name field (readonly)
                if (fullName) fullName.value = '';
                
                // Hide custom course group
                if (customCourseGroup) customCourseGroup.style.display = 'none';
                if (customCourseInput) {
                    customCourseInput.value = '';
                    customCourseInput.required = false;
                }
                
                // Reset course select
                if (courseSelect) {
                    courseSelect.selectedIndex = 0;
                    courseSelect.value = '';
                }
                
                // Reset photo preview
                if (photoInput) photoInput.value = '';
                if (previewImage) {
                    previewImage.src = '';
                    previewImage.style.display = 'none';
                }
                if (photoPlaceholder) photoPlaceholder.style.display = 'flex';
                
                // Remove any error classes
                const errorInputs = form.querySelectorAll('.error');
                errorInputs.forEach(input => {
                    input.classList.remove('error');
                });
                
                // Remove any error messages
                const errorMessages = form.querySelectorAll('.error-message');
                errorMessages.forEach(msg => {
                    msg.style.display = 'none';
                    msg.textContent = '';
                });

                // Show success message
                alert('✅ Form has been reset successfully!');
                
                // Focus on first field
                if (studentName) studentName.focus();
            }
        });
    }

    /* ================= ADD COURSE TO DATABASE ================= */
    const addCourseForm = document.getElementById('addCourseForm');
    
    if (addCourseForm) {
        addCourseForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const courseName = document.getElementById('newCourseName').value.trim();
            const submitBtn = addCourseForm.querySelector('button[type="submit"]');
            const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
            
            // Validation
            if (!courseName) {
                alert('❌ Please enter a course name');
                return;
            }
            
            // Check if course already exists in dropdown
            let alreadyExists = false;
            for (let option of courseSelect.options) {
                if (option.value.toLowerCase() === courseName.toLowerCase()) {
                    alreadyExists = true;
                    break;
                }
            }
            
            if (alreadyExists) {
                alert('⚠️ This course already exists!');
                document.getElementById('newCourseName').focus();
                return;
            }
            
            // Show loading state
            const originalText = submitBtn.innerHTML;
            submitBtn.innerHTML = '⏳ Adding...';
            submitBtn.disabled = true;
            
            // Send to backend
            fetch('/add-course/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                },
                body: JSON.stringify({
                    course_name: courseName
                })
            })
            .then(response => {
                if (!response.ok) {
                    return response.json().then(data => {
                        throw new Error(data.message || 'Failed to add course');
                    });
                }
                return response.json();
            })
            .then(data => {
            if (data.success) {
                    // Show success message
                    alert('✅ ' + data.message + '\n\nPage will reload to show the new course everywhere.');
                    
                    // Reload the page to show new course in all dropdowns
                    window.location.reload();
                } else {
                    alert('❌ ' + data.message);
            }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('❌ ' + error.message);
            })
            .finally(() => {
                submitBtn.innerHTML = originalText;
                submitBtn.disabled = false;
            });
        });
    }
});