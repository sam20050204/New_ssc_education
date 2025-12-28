// ===================== GLOBAL VARIABLES =====================
let selectedStudent = null;
let searchTimeout = null;

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

// ===================== SEARCH STUDENTS =====================
document.addEventListener('DOMContentLoaded', function() {
    const searchInput = document.getElementById('studentSearch');
    const searchResults = document.getElementById('searchResults');
    
    searchInput.addEventListener('input', function(e) {
        const query = e.target.value.trim();
        
        clearTimeout(searchTimeout);
        
        if (query.length < 2) {
            searchResults.classList.remove('active');
            searchResults.innerHTML = '';
            return;
        }
        
        searchTimeout = setTimeout(() => {
            searchStudents(query);
        }, 300);
    });
});

function searchStudents(query) {
    const searchResults = document.getElementById('searchResults');
    
    fetch(`/fees-payment/search/?q=${encodeURIComponent(query)}`)
        .then(response => response.json())
        .then(data => {
            if (data.students && data.students.length > 0) {
                let html = '';
                data.students.forEach(student => {
                    html += `
                        <div class="student-result" onclick="selectStudent(${student.id})">
                            <div class="student-result-name">${student.full_name}</div>
                            <div class="student-result-details">
                                📞 ${student.mobile_own} | 📚 ${student.course}
                            </div>
                        </div>
                    `;
                });
                searchResults.innerHTML = html;
                searchResults.classList.add('active');
            } else {
                searchResults.innerHTML = '<div class="no-results">No students found</div>';
                searchResults.classList.add('active');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            searchResults.innerHTML = '<div class="no-results">Error searching students</div>';
            searchResults.classList.add('active');
        });
}

// ===================== SELECT STUDENT =====================
function selectStudent(studentId) {
    fetch(`/student-detail-admitted/${studentId}/`)
        .then(response => response.json())
        .then(data => {
            selectedStudent = data;
            displayStudentDetails(data);
            
            // Hide search results
            document.getElementById('searchResults').classList.remove('active');
            
            // Clear search input
            document.getElementById('studentSearch').value = data.full_name;
        })
        .catch(error => {
            console.error('Error:', error);
            alert('❌ Error loading student details');
        });
}

// ===================== DISPLAY STUDENT DETAILS =====================
function displayStudentDetails(student) {
    // Show student details section
    document.getElementById('studentDetailsSection').classList.add('active');
    
    // Set student ID
    document.getElementById('selectedStudentId').value = student.id;
    
    // Display photo
    const photoContainer = document.getElementById('studentPhotoLarge');
    if (student.photo) {
        photoContainer.innerHTML = `<img src="${student.photo}" alt="${student.full_name}">`;
    } else {
        const firstLetter = student.student_name ? student.student_name.charAt(0).toUpperCase() : 'S';
        photoContainer.innerHTML = `<div class="photo-placeholder-large">${firstLetter}</div>`;
    }
    
    // Display student info
    document.getElementById('studentNameDisplay').textContent = student.full_name;
    const courseText = student.course === 'Other' && student.custom_course ? 
                       student.custom_course : student.course;
    document.getElementById('studentCourseDisplay').textContent = courseText;
    document.getElementById('studentMobileDisplay').textContent = student.mobile_own;
    
    // Display fees info
    const totalFees = parseFloat(student.total_fees) || 5000;
    const paidFees = parseFloat(student.paid_fees) || 0;
    const remainingFees = totalFees - paidFees;
    
    document.getElementById('totalFeesDisplay').textContent = totalFees.toFixed(2);
    document.getElementById('paidFeesDisplay').textContent = paidFees.toFixed(2);
    document.getElementById('remainingFeesDisplay').textContent = remainingFees.toFixed(2);
    
    // Set max payment amount
    document.getElementById('paymentAmount').max = remainingFees;
    
    // Reset form
    document.getElementById('paymentForm').reset();
    document.getElementById('selectedStudentId').value = student.id;
}

// ===================== HANDLE PAYMENT FORM SUBMISSION =====================
document.addEventListener('DOMContentLoaded', function() {
    const paymentForm = document.getElementById('paymentForm');
    
    if (paymentForm) {
        paymentForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            if (!selectedStudent) {
                alert('⚠️ Please select a student first');
                return;
            }
            
            const paymentAmount = parseFloat(document.getElementById('paymentAmount').value);
            const remainingFees = parseFloat(document.getElementById('remainingFeesDisplay').textContent);
            
            if (paymentAmount <= 0) {
                alert('⚠️ Payment amount must be greater than zero');
                return;
            }
            
            if (paymentAmount > remainingFees) {
                alert('⚠️ Payment amount cannot exceed remaining fees');
                return;
            }
            
            const paymentMode = document.getElementById('paymentMode').value;
            if (!paymentMode) {
                alert('⚠️ Please select payment mode');
                return;
            }
            
            // Show loading
            const submitBtn = paymentForm.querySelector('.btn-submit');
            const originalText = submitBtn.innerHTML;
            submitBtn.innerHTML = '⏳ Processing...';
            submitBtn.disabled = true;
            
            // Prepare form data
            const formData = new FormData(paymentForm);
            
            // Submit payment
            fetch('/fees-payment/submit/', {
                method: 'POST',
                body: formData,
                headers: {
                    'X-CSRFToken': getCookie('csrftoken')
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Show receipt
                    showReceipt(data.receipt);
                    
                    // Update student details
                    selectStudent(selectedStudent.id);
                    
                    // Show success message
                    alert('✅ Payment recorded successfully!');
                } else {
                    alert('❌ Error: ' + (data.error || 'Failed to process payment'));
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('❌ Error processing payment');
            })
            .finally(() => {
                submitBtn.innerHTML = originalText;
                submitBtn.disabled = false;
            });
        });
    }
});

// ===================== SHOW RECEIPT =====================
function showReceipt(receiptData) {
    // Set receipt details
    document.getElementById('receiptNo').textContent = receiptData.receipt_no;
    document.getElementById('receiptDate').textContent = receiptData.date;
    document.getElementById('receiptStudentName').textContent = receiptData.student_name;
    document.getElementById('receiptCourse').textContent = receiptData.course;
    document.getElementById('receiptMobile').textContent = receiptData.mobile;
    document.getElementById('receiptPaymentMode').textContent = receiptData.payment_mode;
    
    document.getElementById('receiptTotalFees').textContent = receiptData.total_fees;
    document.getElementById('receiptPreviousPaid').textContent = receiptData.previous_paid;
    document.getElementById('receiptAmountPaid').textContent = receiptData.amount_paid;
    document.getElementById('receiptRemainingFees').textContent = receiptData.remaining_fees;
    
    document.getElementById('receiptAmountWords').textContent = receiptData.amount_in_words;
    
    // Show modal
    document.getElementById('receiptModal').classList.add('active');
    document.body.style.overflow = 'hidden';
}

// ===================== CLOSE RECEIPT MODAL =====================
function closeReceiptModal() {
    document.getElementById('receiptModal').classList.remove('active');
    document.body.style.overflow = 'auto';
}

// ===================== PRINT RECEIPT =====================
function printReceipt() {
    window.print();
}

// ===================== NUMBER TO WORDS =====================
function numberToWords(num) {
    const ones = ['', 'One', 'Two', 'Three', 'Four', 'Five', 'Six', 'Seven', 'Eight', 'Nine'];
    const tens = ['', '', 'Twenty', 'Thirty', 'Forty', 'Fifty', 'Sixty', 'Seventy', 'Eighty', 'Ninety'];
    const teens = ['Ten', 'Eleven', 'Twelve', 'Thirteen', 'Fourteen', 'Fifteen', 'Sixteen', 'Seventeen', 'Eighteen', 'Nineteen'];
    
    if (num === 0) return 'Zero';
    
    function convertLessThanThousand(n) {
        if (n === 0) return '';
        
        let result = '';
        
        if (n >= 100) {
            result += ones[Math.floor(n / 100)] + ' Hundred ';
            n %= 100;
        }
        
        if (n >= 20) {
            result += tens[Math.floor(n / 10)] + ' ';
            n %= 10;
        } else if (n >= 10) {
            result += teens[n - 10] + ' ';
            return result;
        }
        
        if (n > 0) {
            result += ones[n] + ' ';
        }
        
        return result;
    }
    
    if (num >= 10000000) {
        return convertLessThanThousand(Math.floor(num / 10000000)) + 'Crore ' + numberToWords(num % 10000000);
    } else if (num >= 100000) {
        return convertLessThanThousand(Math.floor(num / 100000)) + 'Lakh ' + numberToWords(num % 100000);
    } else if (num >= 1000) {
        return convertLessThanThousand(Math.floor(num / 1000)) + 'Thousand ' + numberToWords(num % 1000);
    } else {
        return convertLessThanThousand(num);
    }
}

// ===================== VALIDATE PAYMENT AMOUNT =====================
document.addEventListener('DOMContentLoaded', function() {
    const paymentAmount = document.getElementById('paymentAmount');
    
    if (paymentAmount) {
        paymentAmount.addEventListener('input', function() {
            const value = parseFloat(this.value);
            const remaining = parseFloat(document.getElementById('remainingFeesDisplay').textContent);
            
            if (value > remaining) {
                this.style.borderColor = '#ef4444';
                this.style.color = '#ef4444';
            } else if (value > 0) {
                this.style.borderColor = '#10b981';
                this.style.color = '#10b981';
            } else {
                this.style.borderColor = '#e8e8e8';
                this.style.color = '#495057';
            }
        });
    }
});