// ===================== COMPLETE UPDATED fees_payment.js =====================
let selectedStudentId = null;
let selectedStudentData = null;
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
    
    const searchResults = document.getElementById('searchResults');
    if (searchResults) {
        searchResults.innerHTML = '';
        searchResults.style.display = 'none';
    }
    
    const studentSearch = document.getElementById('studentSearch');
    if (studentSearch) {
        studentSearch.value = '';
    }
    
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
        
        selectedStudentData = data;
        
        const detailsSection = document.getElementById('studentDetailsSection');
        if (!detailsSection) {
            throw new Error('Student details section not found');
        }
        
        const studentHeader = detailsSection.querySelector('.student-header');
        if (studentHeader) {
            const displayCourse = data.custom_course || data.course;
            const photoHTML = data.photo 
                ? `<img src="${data.photo}" alt="${data.full_name}">` 
                : '<div class="no-photo">📷</div>';
            
            const batchDisplay = (data.batch_month && data.batch_year) 
                ? `${data.batch_month} ${data.batch_year}` 
                : 'Not Assigned';
            
            studentHeader.innerHTML = `
                <div class="student-photo-large">
                    ${photoHTML}
                </div>
                <div class="student-info-large">
                    <h2 class="student-name-large">${data.full_name}</h2>
                    <span class="student-course-large">${displayCourse}</span>
                    <div style="margin-top: 10px; padding: 8px 16px; background: linear-gradient(135deg, #e0f2fe 0%, #bae6fd 100%); border: 2px solid #0284c7; border-radius: 8px; display: inline-block;">
                        <span style="color: #0c4a6e; font-weight: 700; font-size: 14px;">📅 Batch: ${batchDisplay}</span>
                    </div>
                    <p class="student-mobile-large">📞 ${data.mobile_own}</p>
                </div>
            `;
        }
        
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
        
        const formSection = detailsSection.querySelector('.payment-form-section');
        if (formSection) {
            formSection.style.display = 'block';
        }
        
        detailsSection.style.display = 'block';
        
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

// Submit payment function
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
            // Show receipt immediately
            displayReceipt(data.receipt);
            
            // Reset form after showing receipt
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

// ✅ FIXED: Display receipt function - NO AUTO-PRINT, just show modal
function displayReceipt(receipt) {
    console.log('Displaying receipt:', receipt);
    
    // Generate complete receipt HTML
    const receiptHTML = `
        <!-- INSTITUTE HEADER -->
        <div class="receipt-header">
            <div class="institute-name">Shri Samarth Computer Education Murud</div>
            <div class="institute-details">
                Contact No: 9960638066<br>
                Address: Samarth Road, Behind Bus Stand, Shivaji Nagar, Murud<br>
                TQ. DIST. Latur - 413510<br>
                <strong>MKCL Authorized Center Code: 45210017</strong>
            </div>
        </div>

        <!-- RECEIPT TITLE -->
        <h2 class="receipt-title">🧾 FEE PAYMENT RECEIPT</h2>

        <!-- RECEIPT INFO -->
        <div class="receipt-info">
            <span class="receipt-label">Receipt No:</span>
            <span class="receipt-value">${receipt.receipt_no}</span>

            <span class="receipt-label">Date:</span>
            <span class="receipt-value">${receipt.date} ${receipt.time || ''}</span>

            <span class="receipt-label">Student Name:</span>
            <span class="receipt-value">${receipt.student_name}</span>

            <span class="receipt-label">Course:</span>
            <span class="receipt-value">${receipt.course}</span>

            <span class="receipt-label">Batch:</span>
            <span class="receipt-value" style="font-weight: 700; color: #0284c7;">${receipt.batch_display || 'Not Assigned'}</span>

            <span class="receipt-label">Mobile:</span>
            <span class="receipt-value">${receipt.mobile}</span>

            <span class="receipt-label">Payment Mode:</span>
            <span class="receipt-value">${receipt.payment_mode}</span>
        </div>
        <hr class="receipt-divider">

        <!-- AMOUNT SECTION -->
        <div class="amount-section">
            <div class="amount-row">
                <span>Total Course Fees:</span>
                <strong>₹${receipt.total_fees}</strong>
            </div>
            <div class="amount-row">
                <span>Previous Paid:</span>
                <strong>₹${receipt.previous_paid}</strong>
            </div>
            <div class="amount-row paid">
                <span>Amount Paid Now:</span>
                <strong>₹${receipt.amount_paid}</strong>
            </div>
            <div class="amount-row">
                <span>Remaining Fees:</span>
                <strong>₹${receipt.remaining_fees}</strong>
            </div>
            <div class="amount-in-words">
                <strong>In Words:</strong> ${receipt.amount_in_words}
            </div>
        </div>

        <hr class="receipt-divider">

        <!-- FOOTER -->
        <div class="receipt-footer">
            <div class="thank-you">
                Thank you for your payment!<br>
                <small>This is a computer-generated receipt</small>
            </div>
            <div class="signature-section">
                <div class="signature-line"></div>
                <div class="signature-label">Authorized Signature</div>
            </div>
        </div>
    `;
    
    // Insert receipt HTML into container
    const receiptContent = document.getElementById('receiptContent');
    if (receiptContent) {
        receiptContent.innerHTML = receiptHTML;
    }
    
    // Show modal
    const receiptModal = document.getElementById('receiptModal');
    if (receiptModal) {
        receiptModal.classList.add('active');
        document.body.style.overflow = 'hidden';
        
        console.log('Receipt modal displayed successfully');
        
        // Show success message
        alert('✅ Payment recorded successfully!\n\nReceipt No: ' + receipt.receipt_no + '\n\nClick "Print Receipt" button to print.');
    } else {
        console.error('Receipt modal not found!');
        alert('✅ Payment recorded successfully!\n\nReceipt: ' + receipt.receipt_no);
    }
}

// Print receipt - Uses new window method like receipts page
function printReceipt() {
    const receiptContent = document.getElementById('receiptContent');
    if (!receiptContent) {
        alert('❌ Receipt not found');
        return;
    }
    
    // Create new window for printing
    const printWindow = window.open('', '', 'width=800,height=600');
    
    if (!printWindow) {
        alert('❌ Please allow popups to print the receipt');
        return;
    }
    
    printWindow.document.write(`
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Fee Payment Receipt</title>
            <style>
                * { margin: 0; padding: 0; box-sizing: border-box; }
                body { 
                    font-family: Arial, sans-serif; 
                    padding: 20px; 
                    background: white; 
                    color: #333; 
                }
                .receipt-container { 
                    max-width: 700px; 
                    margin: 0 auto; 
                    background: white; 
                    padding: 20px; 
                }
                .receipt-header { 
                    text-align: center; 
                    margin-bottom: 20px; 
                    border-bottom: 3px solid #333; 
                    padding-bottom: 15px; 
                }
                .institute-name { 
                    font-size: 20px; 
                    font-weight: bold; 
                    color: #333; 
                    margin-bottom: 8px;
                }
                .institute-details { 
                    font-size: 11px; 
                    color: #666; 
                    line-height: 1.6; 
                }
                .receipt-title { 
                    text-align: center; 
                    font-size: 18px; 
                    margin: 20px 0; 
                    font-weight: bold; 
                    color: #333;
                }
                .receipt-info { 
                    display: grid; 
                    grid-template-columns: 150px 1fr; 
                    gap: 10px; 
                    margin: 20px 0; 
                    font-size: 13px; 
                }
                .receipt-label { 
                    font-weight: bold; 
                    color: #333; 
                }
                .receipt-value { 
                    color: #666; 
                }
                .receipt-divider { 
                    border: none; 
                    border-top: 2px dashed #999; 
                    margin: 15px 0; 
                }
                .amount-section { 
                    margin: 20px 0; 
                    font-size: 13px; 
                }
                .amount-row { 
                    display: flex; 
                    justify-content: space-between; 
                    padding: 8px 0; 
                    border-bottom: 1px dotted #ddd; 
                }
                .amount-row.paid { 
                    background: #e8f5e9; 
                    padding: 12px; 
                    font-weight: bold; 
                    border: 2px solid #4caf50; 
                    margin: 10px 0; 
                    border-radius: 4px;
                }
                .amount-in-words { 
                    margin-top: 15px; 
                    padding: 12px; 
                    background: #f5f5f5; 
                    border-left: 3px solid #666; 
                    font-size: 12px; 
                }
                .receipt-footer { 
                    margin-top: 30px; 
                    font-size: 12px; 
                }
                .thank-you { 
                    text-align: center; 
                    margin-bottom: 30px; 
                }
                .signature-section { 
                    text-align: right; 
                    margin-top: 50px; 
                    padding-right: 50px; 
                }
                .signature-line { 
                    border-top: 2px solid #333; 
                    width: 200px; 
                    margin: 0 0 5px auto; 
                }
                .signature-label { 
                    font-weight: bold; 
                    color: #333; 
                }
                @media print { 
                    body { margin: 0; padding: 0; } 
                    @page { margin: 1cm; }
                    .receipt-container { padding: 0; }
                }
            </style>
        </head>
        <body>
            ${receiptContent.innerHTML}
            <script>
                window.onload = function() {
                    window.print();
                    setTimeout(function() {
                        window.close();
                    }, 100);
                };
            </script>
        </body>
        </html>
    `);
    
    printWindow.document.close();
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