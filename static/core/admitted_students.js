// ===================== FIXED: admitted_students.js =====================

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

// ===================== DUPLICATE DETECTION =====================
function markDuplicateStudents() {
    const studentCards = document.querySelectorAll('.student-card');
    const seenMobiles = {};
    const seenEmails = {};
    const seenFullNames = {};
    const duplicateIds = new Set();
    
    // First pass: identify duplicates
    studentCards.forEach(card => {
        const mobile = card.getAttribute('data-mobile')?.trim();
        const email = card.getAttribute('data-email')?.trim();
        
        // Create full name from surname + student_name + father_name (as displayed)
        const surname = card.getAttribute('data-surname')?.trim() || '';
        const studentName = card.getAttribute('data-studentname')?.trim() || '';
        const fatherName = card.getAttribute('data-fathername')?.trim() || '';
        const fullNameCombo = `${surname} ${studentName} ${fatherName}`.replace(/\s+/g, ' ').trim();
        
        // Check for mobile duplicates
        if (mobile && mobile !== '') {
            if (seenMobiles[mobile]) {
                duplicateIds.add(seenMobiles[mobile]);
                duplicateIds.add(card.getAttribute('data-student-id'));
            } else {
                seenMobiles[mobile] = card.getAttribute('data-student-id');
            }
        }
        
        // Check for email duplicates
        if (email && email !== '') {
            if (seenEmails[email]) {
                duplicateIds.add(seenEmails[email]);
                duplicateIds.add(card.getAttribute('data-student-id'));
            } else {
                seenEmails[email] = card.getAttribute('data-student-id');
            }
        }
        
        // Check for full name duplicates (surname + student_name + father_name)
        if (fullNameCombo && fullNameCombo !== '') {
            if (seenFullNames[fullNameCombo]) {
                duplicateIds.add(seenFullNames[fullNameCombo]);
                duplicateIds.add(card.getAttribute('data-student-id'));
            } else {
                seenFullNames[fullNameCombo] = card.getAttribute('data-student-id');
            }
        }
    });
    
    // Second pass: apply styling to duplicates
    studentCards.forEach(card => {
        const studentId = card.getAttribute('data-student-id');
        if (duplicateIds.has(studentId)) {
            card.classList.add('duplicate-student');
        } else {
            card.classList.remove('duplicate-student');
        }
    });
    
    // Log duplicates for debugging
    if (duplicateIds.size > 0) {
        console.log('⚠️ Duplicate students detected:', Array.from(duplicateIds));
    }
}

// ✅ FIXED: Open student modal with payment history
function openStudentModal(studentId) {
    const modal = document.getElementById('studentModal');
    
    modal.style.display = 'block';
    document.body.style.overflow = 'hidden';
    
    fetch(`/admission/${studentId}/detail/`, {
        method: 'GET',
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
            'Accept': 'application/json'
        }
    })
    .then(response => {
        console.log('Detail response status:', response.status);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        console.log('Student details loaded:', data);
        
        // Populate form fields
        document.getElementById('studentId').value = data.id;
        document.getElementById('studentName').value = data.student_name;
        document.getElementById('fatherName').value = data.father_name;
        document.getElementById('surname').value = data.surname;
        document.getElementById('motherName').value = data.mother_name;
        document.getElementById('fullName').value = data.full_name;
        document.getElementById('dob').value = data.date_of_birth;
        document.getElementById('gender').value = data.gender;
        
        // Set the right-side fields (Marital Status, Mobile, Parent Mobile)
        document.getElementById('maritalStatusRight').value = data.marital_status;
        document.getElementById('mobileOwnRight').value = data.mobile_own;
        document.getElementById('parentMobileRight').value = data.parent_mobile || '';
        
        // Display admission date
        const admissionDateInput = document.getElementById('admissionDateInput');
        if (data.admission_date) {
            admissionDateInput.value = data.admission_date;
        } else {
            admissionDateInput.value = '';
        }
        
        // Photo
        const modalPhoto = document.getElementById('modalPhoto');
        if (data.photo) {
            modalPhoto.src = data.photo;
        } else {
            const firstLetter = (data.student_name || data.full_name || 'S').charAt(0).toUpperCase();
            modalPhoto.src = `data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" width="150" height="150"><rect width="150" height="150" fill="%23667eea"/><text x="50%" y="50%" font-size="60" fill="white" text-anchor="middle" dy=".3em">${firstLetter}</text></svg>`;
        }
        
        // Course info
        document.getElementById('courseSelect').value = data.course;
        document.getElementById('customCourse').value = data.custom_course || '';
        document.getElementById('qualification').value = data.educational_qualification;
        
        // Batch info
        document.getElementById('batchMonth').value = data.batch_month || '';
        document.getElementById('batchYear').value = data.batch_year || '';
        document.getElementById('currentBatchDisplay').textContent = data.batch_display || 'Not Assigned';
        
        // Populate batch years
        const batchYearSelect = document.getElementById('batchYear');
        if (batchYearSelect && batchYearSelect.options.length <= 1) {
            const currentYear = new Date().getFullYear();
            for (let i = -2; i <= 2; i++) {
                const year = currentYear + i;
                const option = document.createElement('option');
                option.value = year;
                option.textContent = year;
                batchYearSelect.appendChild(option);
            }
            // Set the value again after populating
            batchYearSelect.value = data.batch_year || '';
        }
        
        // Address
        document.getElementById('address').value = data.address;
        document.getElementById('city').value = data.city;
        
        // Set district and tehsil (handle select dropdowns)
        const districtSelect = document.getElementById('district');
        const tehsilSelect = document.getElementById('tehsil');
        
        // Set district value
        districtSelect.value = data.district || '';
        
        // Populate tehsil options based on selected district
        if (data.district && maharashtraData[data.district]) {
            tehsilSelect.innerHTML = '<option value="">-- Select Tehsil/Block --</option>';
            const tehsils = maharashtraData[data.district];
            tehsils.forEach(tehsil => {
                const option = document.createElement('option');
                option.value = tehsil;
                option.textContent = tehsil;
                tehsilSelect.appendChild(option);
            });
            // Set tehsil value after populating
            tehsilSelect.value = data.tehsil_block || '';
        }
        
        document.getElementById('pinCode').value = data.pin_code;
        
        // Financial info
        document.getElementById('totalFees').value = data.total_fees || 5000;
        document.getElementById('paidFees').value = data.paid_fees || 0;
        calculateRemainingFees();
        
        // ✅ FIXED: Display payment history
        displayPaymentHistory(data.payment_history || []);
        
        modal.style.display = 'block';
    })
    .catch(error => {
        console.error('Detail loading error:', error);
        alert('❌ Error loading student details:\n\n' + error.message);
        closeModal();
    });
}

// ✅ FIXED: Display payment history function
function displayPaymentHistory(payments) {
    const paymentHistoryContainer = document.getElementById('paymentHistoryContainer');
    
    if (!paymentHistoryContainer) {
        console.error('Payment history container not found');
        return;
    }
    
    console.log('Displaying payment history:', payments);
    
    if (!payments || payments.length === 0) {
        paymentHistoryContainer.innerHTML = `
            <div class="no-payments">
                <div class="no-payments-icon">💸</div>
                <p>No payment history available</p>
                <small>Payments will appear here once recorded</small>
            </div>
        `;
        return;
    }
    
    let html = '<div class="payment-timeline">';
    
    payments.forEach((payment, index) => {
        html += `
            <div class="payment-item">
                <div class="payment-header">
                    <div class="installment-number">
                        <span>📌 Installment ${index + 1}</span>
                    </div>
                    <span class="receipt-badge">${payment.receipt_no}</span>
                </div>
                
                <div class="payment-details">
                    <div class="payment-detail-row">
                        <span class="detail-label">📅 Date:</span>
                        <span class="detail-value">${payment.payment_date}</span>
                    </div>
                    
                    <div class="payment-detail-row">
                        <span class="detail-label">⏰ Time:</span>
                        <span class="detail-value">${payment.payment_time}</span>
                    </div>
                    
                    <div class="payment-detail-row">
                        <span class="detail-label">💳 Mode:</span>
                        <span class="payment-mode-badge">${payment.payment_mode}</span>
                    </div>
                    
                    <div class="payment-detail-row">
                        <span class="detail-label">💰 Amount:</span>
                        <span class="detail-value amount">₹${parseFloat(payment.amount).toFixed(2)}</span>
                    </div>
                    
                    <div class="payment-detail-row highlight">
                        <span class="detail-label">📊 Remaining After:</span>
                        <span class="detail-value remaining">₹${parseFloat(payment.remaining_after).toFixed(2)}</span>
                    </div>
                </div>
            </div>
        `;
    });
    
    html += '</div>';
    paymentHistoryContainer.innerHTML = html;
}

// Close modal
function closeModal() {
    const modal = document.getElementById('studentModal');
    modal.style.display = 'none';
    document.body.style.overflow = 'auto';
    
    const form = document.getElementById('studentForm');
    if (form) {
        form.reset();
    }
}

// Close modal on outside click
window.onclick = function(event) {
    const modal = document.getElementById('studentModal');
    if (event.target === modal) {
        closeModal();
    }
}

// Close modal on ESC key
document.addEventListener('keydown', function(event) {
    if (event.key === 'Escape') {
        closeModal();
    }
});

// Calculate remaining fees
function calculateRemainingFees() {
    const totalFeesInput = document.getElementById('totalFees');
    const paidFeesInput = document.getElementById('paidFees');
    const remainingFeesInput = document.getElementById('remainingFees');
    
    if (totalFeesInput && paidFeesInput && remainingFeesInput) {
        const totalFees = parseFloat(totalFeesInput.value) || 0;
        const paidFees = parseFloat(paidFeesInput.value) || 0;
        const remainingFees = Math.max(0, totalFees - paidFees);
        remainingFeesInput.value = remainingFees.toFixed(2);
        
        if (remainingFees === 0) {
            remainingFeesInput.style.color = '#10b981';
            remainingFeesInput.style.fontWeight = '700';
        } else if (remainingFees < totalFees * 0.5) {
            remainingFeesInput.style.color = '#f59e0b';
            remainingFeesInput.style.fontWeight = '700';
        } else {
            remainingFeesInput.style.color = '#ef4444';
            remainingFeesInput.style.fontWeight = '700';
        }
    }
}

// Auto-generate full name
function generateFullName() {
    const studentNameInput = document.getElementById('studentName');
    const fatherNameInput = document.getElementById('fatherName');
    const surnameInput = document.getElementById('surname');
    const fullNameInput = document.getElementById('fullName');
    
    if (studentNameInput && fatherNameInput && surnameInput && fullNameInput) {
        const studentName = studentNameInput.value.trim();
        const fatherName = fatherNameInput.value.trim();
        const surname = surnameInput.value.trim();
        
        const parts = [];
        if (studentName) parts.push(studentName);
        if (fatherName) parts.push(fatherName);
        if (surname) parts.push(surname);
        
        fullNameInput.value = parts.join(' ');
    }
}

// Validate mobile number
function validateMobile(input) {
    const value = input.value.replace(/\D/g, '');
    input.value = value.slice(0, 10);
    
    if (value.length === 10) {
        input.style.borderColor = '#10b981';
    } else if (value.length > 0) {
        input.style.borderColor = '#ef4444';
    } else {
        input.style.borderColor = '#e8e8e8';
    }
}

// Validate pin code
function validatePinCode(input) {
    const value = input.value.replace(/\D/g, '');
    input.value = value.slice(0, 6);
    
    if (value.length === 6) {
        input.style.borderColor = '#10b981';
    } else if (value.length > 0) {
        input.style.borderColor = '#ef4444';
    } else {
        input.style.borderColor = '#e8e8e8';
    }
}

// Document ready
document.addEventListener('DOMContentLoaded', function() {
    
    // Fees calculation - only on totalFees change (paidFees is readonly)
    const totalFeesInput = document.getElementById('totalFees');
    
    if (totalFeesInput) {
        totalFeesInput.addEventListener('input', calculateRemainingFees);
    }
    
    // Auto-generate full name
    const studentNameInput = document.getElementById('studentName');
    const fatherNameInput = document.getElementById('fatherName');
    const surnameInput = document.getElementById('surname');
    
    if (studentNameInput) {
        studentNameInput.addEventListener('input', generateFullName);
    }
    if (fatherNameInput) {
        fatherNameInput.addEventListener('input', generateFullName);
    }
    if (surnameInput) {
        surnameInput.addEventListener('input', generateFullName);
    }
    
    // Mobile number validation
    const mobileOwnInput = document.getElementById('mobileOwn');
    const parentMobileInput = document.getElementById('parentMobile');
    
    if (mobileOwnInput) {
        mobileOwnInput.addEventListener('input', function() {
            validateMobile(this);
        });
    }
    if (parentMobileInput) {
        parentMobileInput.addEventListener('input', function() {
            validateMobile(this);
        });
    }
    
    // Pin code validation
    const pinCodeInput = document.getElementById('pinCode');
    if (pinCodeInput) {
        pinCodeInput.addEventListener('input', function() {
            validatePinCode(this);
        });
    }
    
    // Photo preview
    const photoInput = document.getElementById('photoInput');
    if (photoInput) {
        photoInput.addEventListener('change', function(e) {
            const file = e.target.files[0];
            
            if (file) {
                if (file.size > 2 * 1024 * 1024) {
                    alert('⚠️ File size should be less than 2MB');
                    photoInput.value = '';
                    return;
                }
                
                if (!file.type.startsWith('image/')) {
                    alert('⚠️ Please select an image file');
                    photoInput.value = '';
                    return;
                }
                
                const reader = new FileReader();
                reader.onload = function(e) {
                    const modalPhoto = document.getElementById('modalPhoto');
                    if (modalPhoto) {
                        modalPhoto.src = e.target.result;
                    }
                };
                reader.readAsDataURL(file);
            }
        });
    }
    
    // Form submission
    const studentForm = document.getElementById('studentForm');
    if (studentForm) {
        studentForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const studentId = document.getElementById('studentId').value;
            const formData = new FormData(studentForm);
            
            // Debug: log what's in the formData
            console.log('Form submission debug:');
            for (let [key, value] of formData.entries()) {
                if (value instanceof File) {
                    console.log(`  ${key}: File - ${value.name} (${value.size} bytes)`);
                } else {
                    console.log(`  ${key}: ${value}`);
                }
            }
            
            // Validate mobile from the right-side field
            const mobileOwnRight = document.getElementById('mobileOwnRight').value;
            if (mobileOwnRight.length !== 10) {
                alert('⚠️ Please enter a valid 10-digit mobile number');
                document.getElementById('mobileOwnRight').focus();
                return;
            }
            
            const pinCode = document.getElementById('pinCode').value;
            if (pinCode && pinCode.length !== 6) {
                alert('⚠️ Please enter a valid 6-digit pin code');
                document.getElementById('pinCode').focus();
                return;
            }
            
            const saveBtn = document.querySelector('.save-btn');
            const originalText = saveBtn.textContent;
            saveBtn.textContent = '💾 Saving...';
            saveBtn.disabled = true;
            
            fetch(`/admission/${studentId}/update/`, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-CSRFToken': getCookie('csrftoken')
                }
            })
            .then(response => response.json())
            .then(data => {
                console.log('Update response:', data);
                if (data.success) {
                    showNotification('✅ Student details updated successfully!', 'success');
                    closeModal();
                    
                    // Refresh the student table without reloading the page
                    setTimeout(() => {
                        refreshStudentTable();
                    }, 500);
                } else {
                    alert('❌ Error: ' + (data.error || 'Failed to update student details'));
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('❌ Error updating student details. Please try again.');
            })
            .finally(() => {
                saveBtn.textContent = originalText;
                saveBtn.disabled = false;
            });
        });
    }
    
    // Filter form - prevent multiple submissions
    const filterForm = document.getElementById('filterForm');
    if (filterForm) {
        let isSubmitting = false;
        
        filterForm.addEventListener('submit', function(e) {
            if (isSubmitting) {
                e.preventDefault();
                return false;
            }
            
            isSubmitting = true;
            
            setTimeout(() => {
                isSubmitting = false;
            }, 2000);
        });
    }
    
    // Smooth scroll to top on filter
    const applyFilterBtn = document.querySelector('.filter-btn.apply');
    if (applyFilterBtn) {
        applyFilterBtn.addEventListener('click', function() {
            setTimeout(() => {
                window.scrollTo({ top: 0, behavior: 'smooth' });
            }, 100);
        });
    }
    
    // Mark duplicate students on page load
    markDuplicateStudents();
});

// Show success message on load
window.addEventListener('load', function() {
    const urlParams = new URLSearchParams(window.location.search);
    const success = urlParams.get('success');
    
    if (success === 'updated') {
        const newUrl = window.location.pathname;
        window.history.replaceState({}, document.title, newUrl);
        
        showNotification('✅ Student details updated successfully!', 'success');
    }
});

// Notification function
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

// Add animation styles
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    
    @keyframes fadeOut {
        to {
            opacity: 0;
            transform: translateX(100%);
        }
    }
`;
document.head.appendChild(style);

// ✅ SELECTION AND DELETION FUNCTIONS
function updateSelectedCount() {
    const checkboxes = document.querySelectorAll('.student-checkbox:checked');
    const totalCheckboxes = document.querySelectorAll('.student-checkbox');
    const count = checkboxes.length;
    const deleteBtn = document.getElementById('deleteSelectedBtn');
    const selectAllBtn = document.getElementById('selectAllBtn');
    const deselectAllBtn = document.getElementById('deselectAllBtn');
    const countSpan = document.getElementById('selectedCount');
    
    if (countSpan) countSpan.textContent = count;
    
    // Show/hide delete button when any student is selected
    if (deleteBtn) {
        if (count > 0) {
            deleteBtn.style.display = 'inline-flex';
        } else {
            deleteBtn.style.display = 'none';
        }
    }
    
    // Show/hide select all and deselect all buttons based on selection
    if (count > 0) {
        // At least one student is selected
        if (count === totalCheckboxes.length) {
            // All students are selected - show deselect all
            if (selectAllBtn) selectAllBtn.style.display = 'none';
            if (deselectAllBtn) deselectAllBtn.style.display = 'inline-flex';
        } else {
            // Some but not all students selected - show select all
            if (selectAllBtn) selectAllBtn.style.display = 'inline-flex';
            if (deselectAllBtn) deselectAllBtn.style.display = 'none';
        }
    } else {
        // No students selected - hide both buttons
        if (selectAllBtn) selectAllBtn.style.display = 'none';
        if (deselectAllBtn) deselectAllBtn.style.display = 'none';
    }
}

function selectAllStudents() {
    const checkboxes = document.querySelectorAll('.student-checkbox');
    checkboxes.forEach(checkbox => {
        checkbox.checked = true;
    });
    updateSelectedCount();
}

function deselectAllStudents() {
    const checkboxes = document.querySelectorAll('.student-checkbox');
    checkboxes.forEach(checkbox => {
        checkbox.checked = false;
    });
    updateSelectedCount();
}

function deleteSelectedStudents() {
    const checkboxes = document.querySelectorAll('.student-checkbox:checked');
    const studentIds = Array.from(checkboxes).map(cb => cb.value);
    
    if (studentIds.length === 0) {
        alert('⚠️ Please select at least one student to delete');
        return;
    }
    
    const confirmMessage = `⚠️ Are you sure you want to delete ${studentIds.length} student${studentIds.length > 1 ? 's' : ''}?\n\n` +
                          `This action cannot be undone and will also delete:\n` +
                          `• All fee payment records\n` +
                          `• Student photos and documents`;
    
    const isConfirmed = confirm(confirmMessage);
    
    if (!isConfirmed) {
        return;
    }
    
    const deleteBtn = document.getElementById('deleteSelectedBtn');
    const originalText = deleteBtn.innerHTML;
    deleteBtn.innerHTML = '<span>⏳</span> Deleting...';
    deleteBtn.disabled = true;
    
    fetch('/admission/delete/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify({
            student_ids: studentIds
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNotification(`✅ Successfully deleted ${data.deleted_count} student${data.deleted_count > 1 ? 's' : ''}!`, 'success');
            
            setTimeout(() => {
                window.location.reload();
            }, 1000);
        } else {
            alert('❌ Error: ' + (data.error || 'Failed to delete students'));
            deleteBtn.innerHTML = originalText;
            deleteBtn.disabled = false;
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('❌ Error deleting students. Please try again.');
        deleteBtn.innerHTML = originalText;
        deleteBtn.disabled = false;
    });
}

// ===================== CAMERA FUNCTIONALITY FOR ADMITTED STUDENTS =====================
let cameraStreamModal = null;

function openCameraModal() {
    const cameraBtnModal = document.getElementById('cameraBtnModal');
    const cameraControlsModal = document.getElementById('cameraControlsModal');
    const cameraVideoModal = document.getElementById('cameraVideoModal');
    const modalPhoto = document.getElementById('modalPhoto');
    
    cameraBtnModal.style.display = 'none';
    cameraControlsModal.style.display = 'flex';
    cameraVideoModal.style.display = 'block';
    modalPhoto.style.display = 'none';
    
    navigator.mediaDevices.getUserMedia({
        video: { 
            facingMode: 'user',
            width: { min: 320, ideal: 640, max: 1280 },
            height: { min: 240, ideal: 480, max: 720 }
        }
    }).then(stream => {
        cameraStreamModal = stream;
        cameraVideoModal.srcObject = stream;
        cameraVideoModal.onloadedmetadata = function() {
            cameraVideoModal.play();
        };
        console.log('Camera opened successfully');
    }).catch(error => {
        console.error('Camera error:', error);
        alert('❌ Unable to access camera. Please check permissions.\n\n' + error.message);
        cameraBtnModal.style.display = 'block';
        cameraControlsModal.style.display = 'none';
        cameraVideoModal.style.display = 'none';
        modalPhoto.style.display = 'block';
    });
}

function capturePhotoModal() {
    const cameraVideoModal = document.getElementById('cameraVideoModal');
    const photoCameraCanvas = document.getElementById('photoCameraCanvas');
    const photoInput = document.getElementById('photoInput');
    const modalPhoto = document.getElementById('modalPhoto');
    const cameraBtnModal = document.getElementById('cameraBtnModal');
    const cameraControlsModal = document.getElementById('cameraControlsModal');
    
    // Draw video frame to canvas
    const context = photoCameraCanvas.getContext('2d');
    photoCameraCanvas.width = cameraVideoModal.videoWidth;
    photoCameraCanvas.height = cameraVideoModal.videoHeight;
    context.drawImage(cameraVideoModal, 0, 0);
    
    // Stop camera stream
    if (cameraStreamModal) {
        cameraStreamModal.getTracks().forEach(track => track.stop());
        cameraStreamModal = null;
    }
    
    // Resize and optimize captured photo
    const maxWidth = 600;
    const maxHeight = 800;
    let newWidth = photoCameraCanvas.width;
    let newHeight = photoCameraCanvas.height;
    
    if (newWidth > maxWidth || newHeight > maxHeight) {
        const aspectRatio = photoCameraCanvas.width / photoCameraCanvas.height;
        if (newWidth > maxWidth) {
            newWidth = maxWidth;
            newHeight = newWidth / aspectRatio;
        }
        if (newHeight > maxHeight) {
            newHeight = maxHeight;
            newWidth = newHeight * aspectRatio;
        }
    }
    
    // Create resized canvas
    const resizeCanvas = document.createElement('canvas');
    resizeCanvas.width = newWidth;
    resizeCanvas.height = newHeight;
    const resizeContext = resizeCanvas.getContext('2d');
    resizeContext.drawImage(photoCameraCanvas, 0, 0, newWidth, newHeight);
    
    // Convert to blob and create file
    resizeCanvas.toBlob(function(blob) {
        const file = new File([blob], 'camera_photo.jpg', { type: 'image/jpeg' });
        const dataTransfer = new DataTransfer();
        dataTransfer.items.add(file);
        photoInput.files = dataTransfer.files;
        
        // Show preview
        const reader = new FileReader();
        reader.onload = function(e) {
            modalPhoto.src = e.target.result;
            modalPhoto.style.display = 'block';
        };
        reader.readAsDataURL(blob);
        
        // Reset UI
        cameraVideoModal.style.display = 'none';
        cameraControlsModal.style.display = 'none';
        cameraBtnModal.style.display = 'block';
        
        alert('✅ Photo captured successfully!');
    }, 'image/jpeg', 0.95);
}

function cancelCameraModal() {
    const cameraVideoModal = document.getElementById('cameraVideoModal');
    const cameraBtnModal = document.getElementById('cameraBtnModal');
    const cameraControlsModal = document.getElementById('cameraControlsModal');
    const modalPhoto = document.getElementById('modalPhoto');
    
    if (cameraStreamModal) {
        cameraStreamModal.getTracks().forEach(track => track.stop());
        cameraStreamModal = null;
    }
    
    cameraVideoModal.srcObject = null;
    cameraVideoModal.style.display = 'none';
    cameraControlsModal.style.display = 'none';
    cameraBtnModal.style.display = 'block';
    modalPhoto.style.display = 'block';
}

// ===================== REFRESH TABLE WITHOUT RELOAD =====================
// Function to refresh the student table without reloading the page
function refreshStudentTable() {
    // Get current filter values from the form
    const filterForm = document.getElementById('filterForm');
    if (!filterForm) return;
    
    const searchValue = document.getElementById('search').value || '';
    const monthValue = document.getElementById('month').value || '';
    const yearValue = document.getElementById('year').value || '';
    const courseValue = document.getElementById('course').value || '';
    
    // Build query string
    const params = new URLSearchParams({
        search: searchValue,
        month: monthValue,
        year: yearValue,
        course: courseValue
    });
    
    // Fetch the updated table HTML
    fetch(`/admitted-students/?${params}`, {
        method: 'GET',
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
            'Accept': 'text/html'
        }
    })
    .then(response => response.text())
    .then(html => {
        // Parse the HTML to extract just the table body
        const parser = new DOMParser();
        const newDoc = parser.parseFromString(html, 'text/html');
        const newTableBody = newDoc.querySelector('table tbody');
        const currentTableBody = document.querySelector('table tbody');
        
        if (newTableBody && currentTableBody) {
            // Replace the table body with the new one
            currentTableBody.innerHTML = newTableBody.innerHTML;
            showNotification('📋 Table updated instantly!', 'info');
            
            // Mark duplicate students after table refresh
            markDuplicateStudents();
        }
    })
    .catch(error => {
        console.error('Error refreshing table:', error);
        // Fallback to page reload if refresh fails
        window.location.reload();
    });
}

// ===================== FIELD SYNC FUNCTIONS =====================
// Initialize field event listeners when document loads
document.addEventListener('DOMContentLoaded', function() {
    const maritalStatusRight = document.getElementById('maritalStatusRight');
    const mobileOwnRight = document.getElementById('mobileOwnRight');
    const parentMobileRight = document.getElementById('parentMobileRight');
    
    // Add change event listeners for form submission
    if (maritalStatusRight) {
        maritalStatusRight.addEventListener('change', function() {
            console.log('Marital Status changed to:', this.value);
        });
    }
    
    if (mobileOwnRight) {
        mobileOwnRight.addEventListener('input', function() {
            console.log('Mobile changed to:', this.value);
        });
    }
    
    if (parentMobileRight) {
        parentMobileRight.addEventListener('input', function() {
            console.log('Parent Mobile changed to:', this.value);
        });
    }
});

// ===================== REMOVE PHOTO FUNCTION =====================
function removeStudentPhoto() {
    // Get the current student ID
    const studentId = document.getElementById('studentId').value;
    
    if (!studentId) {
        alert('Please select a student first');
        return;
    }
    
    if (!confirm('Are you sure you want to remove this student\'s photo?')) {
        return;
    }
    
    // Clear the photo input
    const photoInput = document.getElementById('photoInput');
    photoInput.value = '';
    
    // Set a flag to indicate photo should be removed
    let removePhotoFlag = document.getElementById('removePhotoFlag');
    if (!removePhotoFlag) {
        removePhotoFlag = document.createElement('input');
        removePhotoFlag.type = 'hidden';
        removePhotoFlag.id = 'removePhotoFlag';
        removePhotoFlag.name = 'remove_photo';
        removePhotoFlag.value = 'true';
        document.getElementById('studentForm').appendChild(removePhotoFlag);
    } else {
        removePhotoFlag.value = 'true';
    }
    
    // Show a placeholder in the modal
    const modalPhoto = document.getElementById('modalPhoto');
    const studentName = document.getElementById('studentName').value;
    const firstLetter = (studentName || 'S').charAt(0).toUpperCase();
    modalPhoto.src = `data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" width="150" height="150"><rect width="150" height="150" fill="%23667eea"/><text x="50%" y="50%" font-size="60" fill="white" text-anchor="middle" dy=".3em">${firstLetter}</text></svg>`;
    
    // Show success notification
    showNotification('✅ Photo marked for removal - Click Save to confirm', 'success');
}

// ===================== MAHARASHTRA DISTRICT & TEHSIL DATA =====================
// Extracted from official Maharashtra Civil Service PDF
const maharashtraData = {
    "Ahmednagar": ["Akole", "Jamkhed", "Karjat", "Kopargaon", "Nagar", "Parner", "Pathardi", "Rahata", "Rahuri", "Sangamner", "Shevgaon", "Shrigonda", "Shrirampur"],
    "Akola": ["Akola", "Akot", "Balapur", "Barshitakli", "Murtajapur", "Patur", "Telhara"],
    "Amravati": ["Achalpur", "Amravati", "Anjangaon Surji", "Bhatukali", "Chandur", "Chandurbazar", "Chikhaldara", "Daryapur", "Dhamangaon", "Dharni", "Morshi", "Nandgaon Khandeshwar", "Tiosa", "Warud"],
    "Beed": ["Ambejogai", "Ashti", "Beed", "Dharur", "Georai", "Kaij", "Manjalgaon", "Parli", "Patoda", "Shirur Kasar", "Wadwani"],
    "Bhandara": ["Bhandara", "Lakhandur", "Lakhni", "Mohadi", "Pauni", "Sakoli", "Tumsar"],
    "Buldhana": ["Buldhana", "Chikhli", "Deulgaon Raja", "Jalgaon Jamod", "Khamgaon", "Lonar", "Malkapur", "Mehkar", "Motala", "Nandura", "Sangrampur", "Shegaon", "Sindkhed Raja"],
    "Chandrapur": ["Ballarpur", "Bhadravati", "Brahmapuri", "Chandrapur", "Chimur", "Gondpimpri", "Jivati", "Korpana", "Mul", "Nagbhid", "Pombhurna", "Rajura", "Saoli", "Sindewahi", "Warora"],
    "Chhatrapati Sambhajinagar": ["Aurangabad", "Gangapur", "Kannad", "Khuldabad", "Paithan", "Phulambri", "Sillod", "Soegaon", "Vaijapur"],
    "Dharashiv": ["Bhum", "Kalamb", "Lohara", "Dharashiv", "Paranda", "Tuljapur", "Umarga", "Washi"],
    "Dhule": ["Dhule", "Sakri", "Shirpur", "Sindkheda"],
    "Gadchiroli": ["Aheri", "Armori", "Bhamragad", "Chamorshi", "Desaiganj", "Dhanora", "Etapalli", "Gadchiroli", "Korchi", "Kurkheda", "Mulchera", "Sironcha"],
    "Gondia": ["Amgaon", "Arjuni Morgaon", "Deori", "Gondia", "Goregaon", "Sadak Arjuni", "Salekasa", "Tirora"],
    "Hingoli": ["Aundha Nagnath", "Basmath", "Hingoli", "Kalamnuri", "Sengaon"],
    "Jalgaon": ["Amalner", "Bhadgaon", "Bhusawal", "Bodwad", "Chalisgaon", "Chopda", "Dharangaon", "Erandol", "Jalgaon", "Jamner", "Muktainagar", "Pachora", "Parola", "Raver", "Yawal"],
    "Jalna": ["Ambad", "Badnapur", "Bhokardan", "Ghansawangi", "Jafrabad", "Jalna", "Mantha", "Partur"],
    "Kolhapur": ["Ajra", "Bhudargad", "Chandgad", "Gadhinglaj", "Gaganbawada", "Hatkanangale", "Kagal", "Karvir", "Panhala", "Radhanagari", "Shahuwadi", "Shirol"],
    "Latur": ["Ahmadpur", "Ausa", "Chakur", "Deoni", "Jalkot", "Latur", "Nilanga", "Renapur", "Shirur Anantpal", "Udgir"],
    "Mumbai City": ["Andheri", "Borivali", "Kurla"],
    "Mumbai Suburban": ["Andheri", "Borivali", "Kurla"],
    "Nagpur": ["Bhiwapur", "Hingna", "Kalameshwar", "Kamptee", "Katol", "Kuhi", "Mouda", "Nagpur Rural", "Nagpur Urban", "Narkhed", "Parseoni", "Ramtek", "Savner", "Umred"],
    "Nanded": ["Ardhapur", "Bhokar", "Biloli", "Deglur", "Dharmabad", "Hadgaon", "Himayatnagar", "Kandhar", "Kinwat", "Loha", "Mahur", "Mudkhed", "Mukhed", "Naigaon", "Nanded", "Umri"],
    "Nandurbar": ["Akkalkuwa", "Akrani", "Nandurbar", "Navapur", "Shahada", "Talode"],
    "Nashik": ["Baglan", "Chandwad", "Deola", "Dindori", "Igatpuri", "Kalwan", "Malegaon", "Nandgaon", "Nashik", "Niphad", "Peint", "Sinnar", "Surgana", "Trimbakeshwar", "Yeola"],
    "Parbhani": ["Gangakhed", "Jintur", "Manwath", "Paalam", "Parbhani", "Pathri", "Purna", "Sailu", "Sonpeth"],
    "Pune": ["Ambegaon", "Baramati", "Bhor", "Daund", "Haveli", "Indapur", "Junnar", "Khed", "Maval", "Mulshi", "Pune City", "Purandhar", "Shirur", "Velhe"],
    "Raigad": ["Alibag", "Karjat", "Khalapur", "Mahad", "Mangaon", "Mhasla", "Murud", "Panvel", "Pen", "Poladpur", "Roha", "Shrivardhan", "Sudhagad", "Tala", "Uran"],
    "Ratnagiri": ["Chiplun", "Dapoli", "Guhagar", "Khed", "Lanja", "Mandangad", "Rajapur", "Ratnagiri", "Sangameshwar"],
    "Sangli": ["Atpadi", "Islampur", "Jat", "Kadegaon", "Kavathe-Mahankal", "Khanapur", "Miraj", "Palus", "Shirala", "Tasgaon", "Vita", "Walwa"],
    "Satara": ["Jaoli", "Karad", "Khandala", "Khatav", "Koregaon", "Maan", "Mahabaleshwar", "Patan", "Phaltan", "Satara", "Wai"],
    "Sindhudurg": ["Devgad", "Dodamarg", "Kankavli", "Kudal", "Malwan", "Sawantwadi", "Vaibhavwadi", "Vengurla"],
    "Solapur": ["Akkalkot", "Barshi", "Karmala", "Madha", "Malshiras", "Mangalvedhe", "Mohol", "Pandharpur", "Sangole", "Solapur North", "Solapur South"],
    "Thane": ["Ambarnath", "Bhiwandi", "Dahanu", "Jawhar", "Kalyan", "Mokhada", "Murbad", "Palghar", "Shahapur", "Talasari", "Thane", "Ulhasnagar", "Vada", "Vasai", "Vikramgad"],
    "Wardha": ["Arvi", "Ashti", "Deoli", "Hinganghat", "Karanja", "Samudrapur", "Seloo", "Wardha"],
    "Washim": ["Karanja", "Malegaon", "Mangrulpir", "Manora", "Risod", "Washim"],
    "Yavatmal": ["Arni", "Babhulgaon", "Darwha", "Digras", "Ghatanji", "Kalamb", "Kelapur", "Mahagaon", "Maregaon", "Ner", "Pusad", "Ralegaon", "Umarkhed", "Wani", "Yavatmal", "Zari Jamani"],
};

// Update tehsil options based on selected district
function updateTehsilOptions() {
    const districtSelect = document.getElementById('district');
    const tehsilSelect = document.getElementById('tehsil');
    const selectedDistrict = districtSelect.value;
    
    // Clear existing options
    tehsilSelect.innerHTML = '<option value="">-- Select Tehsil/Block --</option>';
    
    // Populate with tehsils for selected district
    if (selectedDistrict && maharashtraData[selectedDistrict]) {
        const tehsils = maharashtraData[selectedDistrict];
        tehsils.forEach(tehsil => {
            const option = document.createElement('option');
            option.value = tehsil;
            option.textContent = tehsil;
            tehsilSelect.appendChild(option);
        });
    }
}

// Initialize district/tehsil selects when page loads
document.addEventListener('DOMContentLoaded', function() {
    const districtSelect = document.getElementById('district');
    if (districtSelect && districtSelect.value) {
        updateTehsilOptions();
    }
    
    // Initialize button visibility on page load
    updateSelectedCount();
});