let selectedStudentId = null;
let selectedStudentData = null; // Store student data
let lastSubmissionTime = 0;
let paymentSubmitting = false;

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

// Search students
document.addEventListener('DOMContentLoaded', function() {
    const studentSearch = document.getElementById('studentSearch');
    
    if (studentSearch) {
        studentSearch.addEventListener('input', function() {
            const query = this.value.trim();
            const searchResults = document.getElementById('searchResults');
            
            console.log('Search query:', query);
            
            if (query.length < 2) {
                searchResults.innerHTML = '';
                searchResults.style.display = 'none';
                return;
            }
            
            searchResults.style.display = 'block';
            searchResults.innerHTML = '<div class="loading">🔍 Searching...</div>';
            
            fetch(`/fees/search-students/?q=${encodeURIComponent(query)}`, {
                method: 'GET',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'Accept': 'application/json'
                }
            })
            .then(response => {
                console.log('Search response status:', response.status);
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                console.log('Search results:', data);
                
                if (!data.students || data.students.length === 0) {
                    searchResults.innerHTML = '<div class="no-results">❌ No students found</div>';
                    return;
                }
                
                searchResults.innerHTML = data.students.map(student => `
                    <div class="search-result-item" onclick="selectStudent(${student.id}, '${student.full_name.replace(/'/g, "\\'")}', '${student.course.replace(/'/g, "\\'")}', '${student.mobile_own}')">
                        <div class="result-name">👤 ${student.full_name}</div>
                        <div class="result-details">📱 ${student.mobile_own} | 📚 ${student.course}</div>
                    </div>
                `).join('');
            })
            .catch(error => {
                console.error('Search error:', error);
                searchResults.innerHTML = `<div class="error">❌ Error: ${error.message}</div>`;
            });
        });
    }
    
    // Handle payment form submission
    const paymentForm = document.getElementById('paymentForm');
    if (paymentForm) {
        paymentForm.addEventListener('submit', function(e) {
            e.preventDefault();
            console.log('Payment form submitted!');
            submitPayment();
        });
    }
});

// Select student from search results
function selectStudent(studentId, fullName, course, mobile) {
    console.log('Selecting student:', studentId, fullName);
    
    selectedStudentId = studentId;
    
    // Hide search results
    const searchResults = document.getElementById('searchResults');
    if (searchResults) {
        searchResults.innerHTML = '';
        searchResults.style.display = 'none';
    }
    
    const studentSearch = document.getElementById('studentSearch');
    if (studentSearch) {
        studentSearch.value = '';
    }
    
    // Show loading indicator
    const detailsSection = document.getElementById('studentDetailsSection');
    if (!detailsSection) {
        console.error('Student details section not found!');
        alert('❌ Error: Student details section not found');
        return;
    }
    
    detailsSection.style.display = 'block';
    const studentHeader = detailsSection.querySelector('.student-header');
    if (studentHeader) {
        studentHeader.innerHTML = '<div class="loading">⏳ Loading student details...</div>';
    }
    
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
        
        // Store student data globally
        selectedStudentData = data;
        
        const detailsSection = document.getElementById('studentDetailsSection');
        if (!detailsSection) {
            throw new Error('Student details section not found');
        }
        
        // Update student header
        const studentHeader = detailsSection.querySelector('.student-header');
        if (studentHeader) {
            const displayCourse = data.custom_course || data.course;
            const photoHTML = data.photo 
                ? `<img src="${data.photo}" alt="${data.full_name}">` 
                : '<div class="no-photo">📷</div>';
            
            studentHeader.innerHTML = `
                <div class="student-photo-large">
                    ${photoHTML}
                </div>
                <div class="student-info-large">
                    <h2 class="student-name-large">${data.full_name}</h2>
                    <span class="student-course-large">${displayCourse}</span>
                    <p class="student-mobile-large">📞 ${data.mobile_own}</p>
                </div>
            `;
        }
        
        // Update fees info grid
        const feesGrid = detailsSection.querySelector('.fees-info-grid');
        if (feesGrid) {
            feesGrid.innerHTML = `
                <div class="fees-info-card total">
                    <div class="fees-label">Total Fees</div>
                    <div class="fees-amount total">₹${parseFloat(data.total_fees).toFixed(2)}</div>
                </div>
                <div class="fees-info-card paid">
                    <div class="fees-label">Paid Fees</div>
                    <div class="fees-amount paid">₹${parseFloat(data.paid_fees).toFixed(2)}</div>
                </div>
                <div class="fees-info-card remaining">
                    <div class="fees-label">Remaining Fees</div>
                    <div class="fees-amount remaining">₹${parseFloat(data.remaining_fees).toFixed(2)}</div>
                </div>
            `;
        }
        
        // Update form fields with null checks
        const selectedStudentIdInput = document.getElementById('selectedStudentId');
        if (selectedStudentIdInput) {
            selectedStudentIdInput.value = studentId;
        }
        
        const paymentAmountInput = document.getElementById('paymentAmount');
        if (paymentAmountInput) {
            paymentAmountInput.max = parseFloat(data.remaining_fees).toFixed(2);
            paymentAmountInput.value = '';
            paymentAmountInput.placeholder = `Max: ₹${parseFloat(data.remaining_fees).toFixed(2)}`;
        }
        
        const maxPaymentDisplay = document.getElementById('maxPaymentAmount');
        if (maxPaymentDisplay) {
            maxPaymentDisplay.textContent = parseFloat(data.remaining_fees).toFixed(2);
        }
        
        // Show form section
        const formSection = detailsSection.querySelector('.payment-form-section');
        if (formSection) {
            formSection.style.display = 'block';
        }
        
        // Show details section
        detailsSection.style.display = 'block';
        
        // Auto-focus on payment amount
        setTimeout(() => {
            if (paymentAmountInput) {
                paymentAmountInput.focus();
            }
        }, 100);
    })
    .catch(error => {
        console.error('Detail loading error:', error);
        alert('❌ Error loading student details:\n\n' + error.message);
        
        const detailsSection = document.getElementById('studentDetailsSection');
        if (detailsSection) {
            detailsSection.style.display = 'none';
        }
    });
}

// Submit payment - FIXED VERSION
function submitPayment() {
    console.log('submitPayment function called!');
    
    if (paymentSubmitting) {
        alert('⏳ Payment is being processed. Please wait...');
        return false;
    }
    
    const now = Date.now();
    if (now - lastSubmissionTime < 2000) {
        alert('⏳ Please wait before submitting again');
        return false;
    }
    
    if (!selectedStudentId || !selectedStudentData) {
        alert('❌ Please select a student first');
        return false;
    }
    
    const amountInput = document.getElementById('paymentAmount');
    const paymentModeSelect = document.getElementById('paymentMode');
    
    if (!amountInput || !paymentModeSelect) {
        alert('❌ Error: Form elements not found');
        return false;
    }
    
    const amount = amountInput.value.trim();
    const paymentMode = paymentModeSelect.value.trim();
    
    console.log('Payment data:', { selectedStudentId, amount, paymentMode });
    
    if (!amount) {
        alert('❌ Please enter payment amount');
        amountInput.focus();
        return false;
    }
    
    if (parseFloat(amount) <= 0) {
        alert('❌ Payment amount must be greater than zero');
        amountInput.focus();
        return false;
    }
    
    if (!paymentMode) {
        alert('❌ Please select payment mode');
        paymentModeSelect.focus();
        return false;
    }
    
    // Get remaining fees from stored data
    const remainingFees = parseFloat(selectedStudentData.remaining_fees);
    
    if (parseFloat(amount) > remainingFees) {
        alert(`❌ Payment amount (₹${parseFloat(amount).toFixed(2)}) cannot exceed remaining fees (₹${remainingFees.toFixed(2)})`);
        return false;
    }
    
    paymentSubmitting = true;
    lastSubmissionTime = now;
    
    const submitBtn = document.querySelector('#paymentForm button[type="submit"]');
    if (!submitBtn) {
        console.error('Submit button not found!');
        paymentSubmitting = false;
        return false;
    }
    
    const originalText = submitBtn.textContent;
    
    submitBtn.disabled = true;
    submitBtn.textContent = '⏳ Processing...';
    submitBtn.style.opacity = '0.6';
    submitBtn.style.cursor = 'not-allowed';
    
    const paymentForm = document.getElementById('paymentForm');
    const allInputs = paymentForm.querySelectorAll('input, select, textarea');
    allInputs.forEach(input => {
        input.disabled = true;
    });
    
    const formData = new FormData();
    formData.append('student_id', selectedStudentId);
    formData.append('amount', amount);
    formData.append('payment_mode', paymentMode);
    
    const remarksInput = document.getElementById('remarks');
    if (remarksInput) {
        formData.append('remarks', remarksInput.value || '');
    }
    
    console.log('Sending payment request...');
    
    fetch('/fees/submit-payment/', {
        method: 'POST',
        body: formData,
        headers: {
            'X-CSRFToken': getCookie('csrftoken'),
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(response => {
        console.log('Payment response status:', response.status);
        return response.json().then(data => {
            if (!response.ok) {
                throw new Error(data.error || 'Payment submission failed');
            }
            return data;
        });
    })
    .then(data => {
        console.log('Payment successful:', data);
        
        if (data.success) {
            alert('✅ Payment recorded successfully!');
            displayReceipt(data.receipt);
            
            paymentForm.reset();
            paymentSubmitting = false;
            selectedStudentId = null;
            selectedStudentData = null;
            
            const detailsSection = document.getElementById('studentDetailsSection');
            if (detailsSection) {
                detailsSection.style.display = 'none';
            }
            
            const studentSearch = document.getElementById('studentSearch');
            if (studentSearch) {
                studentSearch.value = '';
            }
            
            const searchResults = document.getElementById('searchResults');
            if (searchResults) {
                searchResults.innerHTML = '';
            }
            
            submitBtn.disabled = false;
            submitBtn.textContent = originalText;
            submitBtn.style.opacity = '1';
            submitBtn.style.cursor = 'pointer';
            
            allInputs.forEach(input => {
                input.disabled = false;
            });
        } else {
            throw new Error(data.error || 'Unknown error');
        }
    })
    .catch(error => {
        console.error('Payment error:', error);
        alert('❌ ' + error.message);
        
        paymentSubmitting = false;
        submitBtn.disabled = false;
        submitBtn.textContent = originalText;
        submitBtn.style.opacity = '1';
        submitBtn.style.cursor = 'pointer';
        
        allInputs.forEach(input => {
            input.disabled = false;
        });
    });
}

// Display receipt
function displayReceipt(receipt) {
    console.log('Displaying receipt:', receipt);
    
    // Use safe element access
    const setTextContent = (id, value) => {
        const element = document.getElementById(id);
        if (element) {
            element.textContent = value;
        } else {
            console.warn(`Element not found: ${id}`);
        }
    };
    
    setTextContent('receiptNo', receipt.receipt_no);
    setTextContent('receiptDate', receipt.date);
    setTextContent('receiptStudentName', receipt.student_name);
    setTextContent('receiptCourse', receipt.course);
    setTextContent('receiptMobile', receipt.mobile);
    setTextContent('receiptPaymentMode', receipt.payment_mode);
    setTextContent('receiptTotalFees', receipt.total_fees);
    setTextContent('receiptPreviousPaid', receipt.previous_paid);
    setTextContent('receiptAmountPaid', receipt.amount_paid);
    setTextContent('receiptRemainingFees', receipt.remaining_fees);
    setTextContent('receiptAmountWords', receipt.amount_in_words);
    
    const receiptModal = document.getElementById('receiptModal');
    if (receiptModal) {
        receiptModal.classList.add('active');
        document.body.style.overflow = 'hidden';
    }
}

// Print receipt
function printReceipt() {
    const receiptContent = document.getElementById('receiptContent');
    if (!receiptContent) {
        alert('❌ Receipt not found');
        return;
    }
    
    const printWindow = window.open('', '', 'width=900,height=700');
    
    printWindow.document.write(`
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Fee Payment Receipt</title>
            <style>
                * { margin: 0; padding: 0; box-sizing: border-box; }
                body { font-family: Arial, sans-serif; margin: 20px; background: #fff; color: #333; }
                .receipt-container { max-width: 700px; margin: 0 auto; background: white; padding: 20px; border: 1px solid #ddd; }
                .receipt-header { text-align: center; margin-bottom: 20px; border-bottom: 3px solid #333; padding-bottom: 15px; }
                .institute-name { font-size: 18px; font-weight: bold; color: #333; }
                .institute-details { font-size: 11px; color: #666; margin-top: 5px; line-height: 1.6; }
                .receipt-title { text-align: center; font-size: 16px; margin: 20px 0; font-weight: bold; }
                .receipt-info { display: grid; grid-template-columns: 150px 1fr; gap: 10px; margin: 20px 0; font-size: 12px; }
                .receipt-label { font-weight: bold; color: #333; }
                .receipt-value { color: #666; }
                .amount-section { margin: 20px 0; font-size: 12px; }
                .amount-row { display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px dotted #ddd; }
                .amount-row.paid { background: #e8f5e9; padding: 10px; font-weight: bold; border: 1px solid #4caf50; }
                .amount-in-words { margin-top: 15px; padding: 10px; background: #f5f5f5; border-left: 3px solid #666; font-size: 11px; }
                .receipt-footer { text-align: center; margin-top: 30px; font-size: 12px; }
                .signature-section { margin-top: 40px; text-align: center; }
                .signature-line { border-top: 1px solid #333; width: 200px; margin: 0 auto 5px; }
                @media print { body { margin: 0; padding: 0; } }
            </style>
        </head>
        <body>
            ${receiptContent.innerHTML}
        </body>
        </html>
    `);
    
    printWindow.document.close();
    setTimeout(() => {
        printWindow.focus();
        printWindow.print();
    }, 250);
}

// Close receipt modal
function closeReceiptModal() {
    const receiptModal = document.getElementById('receiptModal');
    if (receiptModal) {
        receiptModal.classList.remove('active');
        document.body.style.overflow = 'auto';
    }
}

// Close on ESC
document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
        if (!paymentSubmitting) {
            closeReceiptModal();
        }
    }
});

// Close on outside click
window.addEventListener('click', function(e) {
    const receiptModal = document.getElementById('receiptModal');
    if (e.target === receiptModal && !paymentSubmitting) {
        closeReceiptModal();
    }
});

// Prevent closing during payment
window.addEventListener('beforeunload', function(e) {
    if (paymentSubmitting) {
        e.preventDefault();
        e.returnValue = '';
    }
});