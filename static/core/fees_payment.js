let selectedStudentId = null;
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
            
            console.log('Search query:', query);  // DEBUG
            
            if (query.length < 2) {
                searchResults.innerHTML = '';
                return;
            }
            
            // Show loading indicator
            searchResults.innerHTML = '<div class="loading">🔍 Searching...</div>';
            
            fetch(`/fees/search-students/?q=${encodeURIComponent(query)}`, {
                method: 'GET',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'Accept': 'application/json'
                }
            })
            .then(response => {
                console.log('Response status:', response.status);  // DEBUG
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                console.log('Search results:', data);  // DEBUG
                
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
                console.error('Search error:', error);  // DEBUG
                searchResults.innerHTML = `<div class="error">❌ Error searching students: ${error.message}</div>`;
            });
        });
    }
    
    // Handle payment form submission
    const paymentForm = document.getElementById('paymentForm');
    if (paymentForm) {
        paymentForm.addEventListener('submit', function(e) {
            e.preventDefault();
            submitPayment();
        });
    }
});

// Select student from search results
function selectStudent(studentId, fullName, course, mobile) {
    console.log('Selecting student:', studentId, fullName);  // DEBUG
    
    selectedStudentId = studentId;
    
    // Hide search results
    document.getElementById('searchResults').innerHTML = '';
    document.getElementById('studentSearch').value = '';
    
    // Show loading indicator
    const detailsSection = document.getElementById('studentDetailsSection');
    if (detailsSection) {
        // Just show the section with loading message, don't replace the whole HTML
        detailsSection.style.display = 'block';
        const studentHeader = detailsSection.querySelector('.student-header');
        if (studentHeader) {
            studentHeader.innerHTML = '<div class="loading">⏳ Loading student details...</div>';
        }
    }
    
    // Load student details
    fetch(`/admission/${studentId}/detail/`, {
        method: 'GET',
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
            'Accept': 'application/json'
        }
    })
    .then(response => {
        console.log('Detail response status:', response.status);  // DEBUG
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        console.log('Student details:', data);  // DEBUG
        
        const detailsSection = document.getElementById('studentDetailsSection');
        if (!detailsSection) return;
        
        // ================= UPDATE STUDENT HEADER SECTION =================
        const studentHeader = detailsSection.querySelector('.student-header');
        if (studentHeader) {
            const displayCourse = data.custom_course || data.course;
            const photoHTML = data.photo 
                ? `<img src="${data.photo}" alt="${data.full_name}" style="max-width: 100%; max-height: 150px; border-radius: 8px;">` 
                : '<div class="no-photo">📷</div>';
            
            studentHeader.innerHTML = `
                <div class="student-photo-large" id="studentPhotoLarge">
                    ${photoHTML}
                </div>
                <div class="student-info-large">
                    <h2 class="student-name-large" id="studentNameDisplay">${data.full_name}</h2>
                    <span class="student-course-large" id="studentCourseDisplay">${displayCourse}</span>
                    <p class="student-mobile-large">📞 <span id="studentMobileDisplay">${data.mobile_own}</span></p>
                </div>
            `;
        }
        
        // ================= UPDATE FEES INFO GRID =================
        const feesGrid = detailsSection.querySelector('.fees-info-grid');
        if (feesGrid) {
            feesGrid.innerHTML = `
                <div class="fees-info-card total">
                    <div class="fees-label">Total Fees</div>
                    <div class="fees-amount total">₹<span id="totalFeesDisplay">${parseFloat(data.total_fees).toFixed(2)}</span></div>
                </div>
                <div class="fees-info-card paid">
                    <div class="fees-label">Paid Fees</div>
                    <div class="fees-amount paid">₹<span id="paidFeesDisplay">${parseFloat(data.paid_fees).toFixed(2)}</span></div>
                </div>
                <div class="fees-info-card remaining">
                    <div class="fees-label">Remaining Fees</div>
                    <div class="fees-amount remaining">₹<span id="remainingFeesDisplay">${parseFloat(data.remaining_fees).toFixed(2)}</span></div>
                </div>
            `;
        }
        
        // ================= UPDATE FORM FIELDS =================
        // Update hidden student ID
        const studentIdInput = document.getElementById('selectedStudentId');
        if (studentIdInput) {
            studentIdInput.value = studentId;
        }
        
        // Update payment amount max value
        const paymentAmountInput = document.getElementById('paymentAmount');
        if (paymentAmountInput) {
            paymentAmountInput.max = parseFloat(data.remaining_fees).toFixed(2);
            paymentAmountInput.value = '';
            paymentAmountInput.placeholder = `Max: ₹${parseFloat(data.remaining_fees).toFixed(2)}`;
        }
        
        // Update max payment display
        const maxPaymentDisplay = document.getElementById('maxPaymentAmount');
        if (maxPaymentDisplay) {
            maxPaymentDisplay.textContent = parseFloat(data.remaining_fees).toFixed(2);
        }
        
        // Show the form section
        const formSection = detailsSection.querySelector('.payment-form-section');
        if (formSection) {
            formSection.style.display = 'block';
        }
        
        // Show details section
        detailsSection.style.display = 'block';
        
        // Auto-focus on payment amount field
        setTimeout(() => {
            if (paymentAmountInput) {
                paymentAmountInput.focus();
            }
        }, 100);
    })
    .catch(error => {
        console.error('Detail loading error:', error);  // DEBUG
        alert('❌ Error loading student details: ' + error.message);
        
        const detailsSection = document.getElementById('studentDetailsSection');
        if (detailsSection) {
            const studentHeader = detailsSection.querySelector('.student-header');
            if (studentHeader) {
                studentHeader.innerHTML = `<div class="error">❌ Error loading details: ${error.message}</div>`;
            }
        }
    });
}

// Submit payment
function submitPayment() {
    // ================= PREVENT DOUBLE SUBMISSION =================
    if (paymentSubmitting) {
        alert('⏳ Payment is being processed. Please wait...');
        return false;
    }
    
    // ================= PREVENT RAPID SUBMISSIONS =================
    const now = Date.now();
    if (now - lastSubmissionTime < 2000) {
        alert('⏳ Please wait before submitting again');
        return false;
    }
    
    // ================= VALIDATION =================
    if (!selectedStudentId) {
        alert('❌ Please select a student');
        return false;
    }
    
    const amount = document.getElementById('paymentAmount').value.trim();
    const paymentMode = document.getElementById('paymentMode').value.trim();
    
    if (!amount) {
        alert('❌ Please enter payment amount');
        return false;
    }
    
    if (parseFloat(amount) <= 0) {
        alert('❌ Payment amount must be greater than zero');
        return false;
    }
    
    if (!paymentMode) {
        alert('❌ Please select payment mode');
        return false;
    }
    
    // Check if amount exceeds remaining fees
    const remainingFeesText = document.getElementById('remainingFeesDisplay').textContent;
    const remainingFees = parseFloat(remainingFeesText);
    
    if (parseFloat(amount) > remainingFees) {
        alert(`❌ Payment amount cannot exceed remaining fees (₹${remainingFees.toFixed(2)})`);
        return false;
    }
    
    // ================= MARK AS SUBMITTING =================
    paymentSubmitting = true;
    lastSubmissionTime = now;
    
    const submitBtn = document.querySelector('#paymentForm button[type="submit"]');
    const originalText = submitBtn.textContent;
    
    // ================= DISABLE BUTTON =================
    submitBtn.disabled = true;
    submitBtn.textContent = '⏳ Processing...';
    submitBtn.style.opacity = '0.6';
    submitBtn.style.cursor = 'not-allowed';
    
    // ================= DISABLE ALL FORM INPUTS =================
    const paymentForm = document.getElementById('paymentForm');
    const allInputs = paymentForm.querySelectorAll('input, select, textarea');
    allInputs.forEach(input => {
        input.disabled = true;
    });
    
    // ================= SEND PAYMENT DATA =================
    const formData = new FormData();
    formData.append('student_id', selectedStudentId);
    formData.append('amount', amount);
    formData.append('payment_mode', paymentMode);
    formData.append('remarks', document.getElementById('remarks').value || '');
    
    fetch('/fees/submit-payment/', {
        method: 'POST',
        body: formData,
        headers: {
            'X-CSRFToken': getCookie('csrftoken'),
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(response => {
        console.log('Payment response status:', response.status);  // DEBUG
        if (!response.ok) {
            return response.json().then(data => {
                throw new Error(data.error || 'Payment submission failed');
            });
        }
        return response.json();
    })
    .then(data => {
        console.log('Payment response:', data);  // DEBUG
        
        if (data.success) {
            // Show success message
            alert('✅ Payment recorded successfully!');
            
            // Display receipt
            displayReceipt(data.receipt);
            
            // Reset form
            paymentForm.reset();
            
            // Reset state
            paymentSubmitting = false;
            selectedStudentId = null;
            
            // Hide student details section
            document.getElementById('studentDetailsSection').style.display = 'none';
            document.getElementById('studentSearch').value = '';
            document.getElementById('searchResults').innerHTML = '';
            
            // Reset button
            submitBtn.disabled = false;
            submitBtn.textContent = originalText;
            submitBtn.style.opacity = '1';
            submitBtn.style.cursor = 'pointer';
            
            // Re-enable inputs
            allInputs.forEach(input => {
                input.disabled = false;
            });
        } else {
            throw new Error(data.error || 'Unknown error');
        }
    })
    .catch(error => {
        console.error('Payment error:', error);  // DEBUG
        alert('❌ ' + error.message);
        
        // Reset on error
        paymentSubmitting = false;
        submitBtn.disabled = false;
        submitBtn.textContent = originalText;
        submitBtn.style.opacity = '1';
        submitBtn.style.cursor = 'pointer';
        
        // Re-enable inputs
        allInputs.forEach(input => {
            input.disabled = false;
        });
    });
}

// Display receipt
function displayReceipt(receipt) {
    document.getElementById('receiptNo').textContent = receipt.receipt_no;
    document.getElementById('receiptDate').textContent = receipt.date;
    document.getElementById('receiptStudentName').textContent = receipt.student_name;
    document.getElementById('receiptCourse').textContent = receipt.course;
    document.getElementById('receiptMobile').textContent = receipt.mobile;
    document.getElementById('receiptPaymentMode').textContent = receipt.payment_mode;
    
    document.getElementById('receiptTotalFees').textContent = receipt.total_fees;
    document.getElementById('receiptPreviousPaid').textContent = receipt.previous_paid;
    document.getElementById('receiptAmountPaid').textContent = receipt.amount_paid;
    document.getElementById('receiptRemainingFees').textContent = receipt.remaining_fees;
    document.getElementById('receiptAmountWords').textContent = receipt.amount_in_words;
    
    // Show receipt modal
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
                body { 
                    font-family: 'Arial', sans-serif; 
                    margin: 20px; 
                    background: #fff;
                    color: #333;
                }
                .receipt-container { 
                    max-width: 700px; 
                    margin: 0 auto; 
                    background: white;
                    padding: 20px;
                    border: 1px solid #ddd;
                }
                .receipt-header { 
                    text-align: center; 
                    margin-bottom: 20px; 
                    border-bottom: 3px solid #333; 
                    padding-bottom: 15px; 
                }
                .institute-name { 
                    font-size: 18px; 
                    font-weight: bold; 
                    color: #333;
                }
                .institute-details { 
                    font-size: 11px; 
                    color: #666; 
                    margin-top: 5px; 
                    line-height: 1.6;
                }
                .receipt-title { 
                    text-align: center; 
                    font-size: 16px; 
                    margin: 20px 0; 
                    font-weight: bold;
                }
                .receipt-info { 
                    display: grid; 
                    grid-template-columns: 150px 1fr; 
                    gap: 10px; 
                    margin: 20px 0;
                    font-size: 12px;
                }
                .receipt-label { 
                    font-weight: bold;
                    color: #333;
                }
                .receipt-value { 
                    color: #666;
                }
                .amount-section { 
                    margin: 20px 0; 
                    font-size: 12px;
                }
                .amount-row { 
                    display: flex; 
                    justify-content: space-between; 
                    padding: 8px 0;
                    border-bottom: 1px dotted #ddd;
                }
                .amount-row.paid { 
                    background: #e8f5e9; 
                    padding: 10px; 
                    font-weight: bold;
                    border: 1px solid #4caf50;
                    border-bottom: none;
                }
                .amount-in-words { 
                    margin-top: 15px; 
                    padding: 10px; 
                    background: #f5f5f5;
                    border-left: 3px solid #666;
                    font-size: 11px;
                    line-height: 1.5;
                }
                .receipt-footer { 
                    text-align: center; 
                    margin-top: 30px;
                    font-size: 12px;
                }
                .thank-you {
                    margin-bottom: 20px;
                    font-weight: bold;
                }
                .signature-section { 
                    margin-top: 40px; 
                    text-align: center; 
                }
                .signature-line { 
                    border-top: 1px solid #333; 
                    width: 200px; 
                    margin: 0 auto 5px; 
                }
                .signature-label {
                    font-size: 11px;
                    color: #666;
                }
                hr { 
                    border: none; 
                    border-top: 1px solid #ddd; 
                    margin: 15px 0;
                }
                @media print { 
                    body { margin: 0; padding: 0; }
                    .receipt-container { border: none; }
                }
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

// Close modals on ESC key
document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
        if (!paymentSubmitting) {
            closeReceiptModal();
        }
    }
});

// Close modal on outside click
window.addEventListener('click', function(e) {
    const receiptModal = document.getElementById('receiptModal');
    if (e.target === receiptModal && !paymentSubmitting) {
        closeReceiptModal();
    }
});

// Prevent closing modal during payment submission
window.addEventListener('beforeunload', function(e) {
    if (paymentSubmitting) {
        e.preventDefault();
        e.returnValue = '';
    }
});