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
        document.getElementById('mobileOwn').value = data.mobile_own;
        document.getElementById('parentMobile').value = data.parent_mobile || '';
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
        document.getElementById('tehsil').value = data.tehsil_block;
        document.getElementById('district').value = data.district;
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
    
    // Fees calculation
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
            
            // Validate
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
                if (data.success) {
                    showNotification('✅ Student details updated successfully!', 'success');
                    closeModal();
                    
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
    const count = checkboxes.length;
    const deleteBtn = document.getElementById('deleteSelectedBtn');
    const countSpan = document.getElementById('selectedCount');
    
    if (countSpan) countSpan.textContent = count;
    
    if (deleteBtn) {
        if (count > 0) {
            deleteBtn.style.display = 'inline-flex';
        } else {
            deleteBtn.style.display = 'none';
        }
    }
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
                          `• Student photos and documents\n\n` +
                          `Type "DELETE" to confirm:`;
    
    const userInput = prompt(confirmMessage);
    
    if (userInput !== 'DELETE') {
        if (userInput !== null) {
            alert('❌ Deletion cancelled. You must type "DELETE" to confirm.');
        }
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