// ===================== GET CSRF TOKEN =====================
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

// ===================== OPEN STUDENT MODAL =====================
// ===================== OPEN STUDENT MODAL =====================
function openStudentModal(studentId) {
    const modal = document.getElementById('studentModal');
    
    // Show loading state
    modal.style.display = 'block';
    document.body.style.overflow = 'hidden';
    
    // Fetch student details
    fetch(`/student-detail-admitted/${studentId}/`)
        .then(response => {
            if (!response.ok) {
                throw new Error('Failed to fetch student details');
            }
            return response.json();
        })
        .then(data => {
            // Set student ID
            document.getElementById('studentId').value = data.id;
            
            // Personal info
            document.getElementById('studentName').value = data.student_name || '';
            document.getElementById('fatherName').value = data.father_name || '';
            document.getElementById('surname').value = data.surname || '';
            document.getElementById('motherName').value = data.mother_name || '';
            document.getElementById('fullName').value = data.full_name || '';
            document.getElementById('dob').value = data.date_of_birth || '';
            document.getElementById('gender').value = data.gender || 'Male';
            document.getElementById('maritalStatus').value = data.marital_status || 'Single';
            
            // Photo
            const modalPhoto = document.getElementById('modalPhoto');
            if (data.photo) {
                modalPhoto.src = data.photo;
            } else {
                const firstLetter = data.student_name ? data.student_name.charAt(0).toUpperCase() : 'S';
                modalPhoto.src = `data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" width="150" height="150"><rect width="150" height="150" fill="%23667eea"/><text x="50%" y="50%" font-size="60" fill="white" text-anchor="middle" dy=".3em">${firstLetter}</text></svg>`;
            }
            
            // Contact info
            document.getElementById('mobileOwn').value = data.mobile_own || '';
            document.getElementById('parentMobile').value = data.parent_mobile || '';
            
            // Course info
            document.getElementById('courseSelect').value = data.course || 'MS-CIT';
            document.getElementById('customCourse').value = data.custom_course || '';
            document.getElementById('qualification').value = data.educational_qualification || '';
            
            // Address
            document.getElementById('address').value = data.address || '';
            document.getElementById('city').value = data.city || '';
            document.getElementById('tehsil').value = data.tehsil_block || '';
            document.getElementById('district').value = data.district || '';
            document.getElementById('pinCode').value = data.pin_code || '';
            
            // Financial info
            document.getElementById('totalFees').value = data.total_fees || 5000;
            document.getElementById('paidFees').value = data.paid_fees || 0;
            calculateRemainingFees();
            
            // ===================== NEW: Display Payment History =====================
            displayPaymentHistory(data.payment_history || []);
        })
        .catch(error => {
            console.error('Error:', error);
            alert('❌ Error loading student details. Please try again.');
            closeModal();
        });
}

// ===================== NEW FUNCTION: Display Payment History =====================
function displayPaymentHistory(payments) {
    const paymentHistoryContainer = document.getElementById('paymentHistoryContainer');
    
    if (!paymentHistoryContainer) {
        console.error('Payment history container not found');
        return;
    }
    
    if (payments.length === 0) {
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

// ===================== CLOSE MODAL =====================
function closeModal() {
    const modal = document.getElementById('studentModal');
    modal.style.display = 'none';
    document.body.style.overflow = 'auto';
    
    // Reset form
    const form = document.getElementById('studentForm');
    if (form) {
        form.reset();
    }
}

// ===================== CLOSE MODAL ON OUTSIDE CLICK =====================
window.onclick = function(event) {
    const modal = document.getElementById('studentModal');
    if (event.target === modal) {
        closeModal();
    }
}

// ===================== CLOSE MODAL ON ESC KEY =====================
document.addEventListener('keydown', function(event) {
    if (event.key === 'Escape') {
        closeModal();
    }
});

// ===================== CALCULATE REMAINING FEES =====================
function calculateRemainingFees() {
    const totalFeesInput = document.getElementById('totalFees');
    const paidFeesInput = document.getElementById('paidFees');
    const remainingFeesInput = document.getElementById('remainingFees');
    
    if (totalFeesInput && paidFeesInput && remainingFeesInput) {
        const totalFees = parseFloat(totalFeesInput.value) || 0;
        const paidFees = parseFloat(paidFeesInput.value) || 0;
        const remainingFees = Math.max(0, totalFees - paidFees);
        remainingFeesInput.value = remainingFees.toFixed(2);
        
        // Add visual feedback
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

// ===================== AUTO-GENERATE FULL NAME =====================
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

// ===================== VALIDATE MOBILE NUMBER =====================
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

// ===================== VALIDATE PIN CODE =====================
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

// ===================== DOCUMENT READY =====================
document.addEventListener('DOMContentLoaded', function() {
    
    // ===================== FEES CALCULATION =====================
    const totalFeesInput = document.getElementById('totalFees');
    const paidFeesInput = document.getElementById('paidFees');
    
    if (totalFeesInput) {
        totalFeesInput.addEventListener('input', calculateRemainingFees);
    }
    if (paidFeesInput) {
        paidFeesInput.addEventListener('input', calculateRemainingFees);
    }
    
    // ===================== AUTO-GENERATE FULL NAME =====================
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
    
    // ===================== MOBILE NUMBER VALIDATION =====================
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
    
    // ===================== PIN CODE VALIDATION =====================
    const pinCodeInput = document.getElementById('pinCode');
    if (pinCodeInput) {
        pinCodeInput.addEventListener('input', function() {
            validatePinCode(this);
        });
    }
    
    // ===================== PHOTO PREVIEW =====================
    const photoInput = document.getElementById('photoInput');
    if (photoInput) {
        photoInput.addEventListener('change', function(e) {
            const file = e.target.files[0];
            
            if (file) {
                // Check file size (max 2MB)
                if (file.size > 2 * 1024 * 1024) {
                    alert('⚠️ File size should be less than 2MB');
                    photoInput.value = '';
                    return;
                }
                
                // Check file type
                if (!file.type.startsWith('image/')) {
                    alert('⚠️ Please select an image file');
                    photoInput.value = '';
                    return;
                }
                
                // Show preview
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
    
    // ===================== FORM SUBMISSION =====================
    const studentForm = document.getElementById('studentForm');
    if (studentForm) {
        studentForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const studentId = document.getElementById('studentId').value;
            const formData = new FormData(studentForm);
            
            // Validate required fields
            const mobileOwn = document.getElementById('mobileOwn').value;
            if (mobileOwn.length !== 10) {
                alert('⚠️ Please enter a valid 10-digit mobile number');
                document.getElementById('mobileOwn').focus();
                return;
            }
            
            const pinCode = document.getElementById('pinCode').value;
            if (pinCode && pinCode.length !== 6) {
                alert('⚠️ Please enter a valid 6-digit pin code');
                document.getElementById('pinCode').focus();
                return;
            }
            
            // Show loading state
            const saveBtn = document.querySelector('.save-btn');
            const originalText = saveBtn.textContent;
            saveBtn.textContent = '💾 Saving...';
            saveBtn.disabled = true;
            
            // Submit form
            fetch(`/update-student-admitted/${studentId}/`, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-CSRFToken': getCookie('csrftoken')
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    showNotification('✅ Student details updated successfully!', 'success');
                    closeModal();
                    
                    // Reload page to show updated data
                    setTimeout(() => {
                        window.location.reload();
                    }, 1000);
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
    
    // ===================== FILTER FORM - PREVENT MULTIPLE SUBMISSIONS =====================
    const filterForm = document.getElementById('filterForm');
    if (filterForm) {
        let isSubmitting = false;
        
        filterForm.addEventListener('submit', function(e) {
            if (isSubmitting) {
                e.preventDefault();
                return false;
            }
            
            isSubmitting = true;
            
            // Reset after 2 seconds
            setTimeout(() => {
                isSubmitting = false;
            }, 2000);
        });
    }
    
    // ===================== SMOOTH SCROLL TO TOP ON FILTER =====================
    const applyFilterBtn = document.querySelector('.filter-btn.apply');
    if (applyFilterBtn) {
        applyFilterBtn.addEventListener('click', function() {
            setTimeout(() => {
                window.scrollTo({ top: 0, behavior: 'smooth' });
            }, 100);
        });
    }
});

// ===================== SHOW SUCCESS MESSAGE ON LOAD =====================
window.addEventListener('load', function() {
    // Check if there's a success message in URL parameters
    const urlParams = new URLSearchParams(window.location.search);
    const success = urlParams.get('success');
    
    if (success === 'updated') {
        // Remove the parameter from URL
        const newUrl = window.location.pathname;
        window.history.replaceState({}, document.title, newUrl);
        
        // Show success notification
        showNotification('✅ Student details updated successfully!', 'success');
    }
});

// ===================== NOTIFICATION FUNCTION =====================
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

// ===================== ADD ANIMATION STYLES =====================
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

document.getElementById('batchMonth').value = data.batch_month || '';
document.getElementById('batchYear').value = data.batch_year || '';
document.getElementById('currentBatchDisplay').textContent = data.batch_display || 'Not Assigned';

// Populate batch years
const batchYearSelect = document.getElementById('batchYear');
const currentYear = new Date().getFullYear();
for (let i = -2; i <= 2; i++) {
    const year = currentYear + i;
    const option = document.createElement('option');
    option.value = year;
    option.textContent = year;
    batchYearSelect.appendChild(option);
}