// Payment Tracking Page JavaScript

// Update cutoff date display when days input changes
document.addEventListener('DOMContentLoaded', function() {
    const daysInput = document.getElementById('daysInput');
    const cutoffDisplay = document.getElementById('cutoffDisplay');
    
    if (daysInput) {
        daysInput.addEventListener('input', function() {
            const days = parseInt(this.value) || 25;
            if (days > 0) {
                // Calculate cutoff date
                const today = new Date();
                const cutoffDate = new Date(today);
                cutoffDate.setDate(cutoffDate.getDate() - days);
                
                // Format date as DD-MM-YYYY
                const day = String(cutoffDate.getDate()).padStart(2, '0');
                const month = String(cutoffDate.getMonth() + 1).padStart(2, '0');
                const year = cutoffDate.getFullYear();
                
                cutoffDisplay.textContent = `${day}-${month}-${year}`;
            }
        });
    }
});

// Open student detail modal
function openPaymentTrackingModal(studentId) {
    const modal = document.getElementById('paymentTrackingModal');
    modal.style.display = 'flex';
    document.body.style.overflow = 'hidden';
    
    // Fetch student details
    fetch(`/payment-tracking/${studentId}/detail/`, {
        method: 'GET',
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
            'Accept': 'application/json'
        }
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        console.log('Student details loaded:', data);
        
        // Populate personal information
        document.getElementById('trackingFullName').textContent = data.full_name || '-';
        document.getElementById('trackingStudentName').textContent = data.student_name || '-';
        document.getElementById('trackingFatherName').textContent = data.father_name || '-';
        document.getElementById('trackingMotherName').textContent = data.mother_name || '-';
        document.getElementById('trackingGender').textContent = data.gender || '-';
        document.getElementById('trackingDOB').textContent = data.date_of_birth || '-';
        
        // Contact information
        document.getElementById('trackingMobileOwn').textContent = data.mobile_own || '-';
        document.getElementById('trackingParentMobile').textContent = data.parent_mobile || '-';
        
        // Address information
        document.getElementById('trackingAddress').textContent = data.address || '-';
        document.getElementById('trackingCity').textContent = data.city || '-';
        document.getElementById('trackingDistrict').textContent = data.district || '-';
        document.getElementById('trackingPinCode').textContent = data.pin_code || '-';
        
        // Course information
        document.getElementById('trackingCourse').textContent = data.course || '-';
        const batch = (data.batch_month || '') + (data.batch_year ? ' ' + data.batch_year : '');
        document.getElementById('trackingBatch').textContent = batch || '-';
        document.getElementById('trackingAdmissionDate').textContent = data.admission_date || '-';
        
        // Payment summary
        document.getElementById('trackingTotalFees').textContent = '₹' + parseFloat(data.total_fees).toFixed(2);
        document.getElementById('trackingTotalPaid').textContent = '₹' + parseFloat(data.total_paid).toFixed(2);
        document.getElementById('trackingRemaining').textContent = '₹' + parseFloat(data.remaining).toFixed(2);
        document.getElementById('trackingPaymentCount').textContent = data.payment_count;
        
        // Photo
        const photoElement = document.getElementById('trackingPhoto');
        if (data.photo) {
            photoElement.src = data.photo;
        } else {
            const firstLetter = (data.full_name || 'S').charAt(0).toUpperCase();
            photoElement.src = `data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" width="300" height="400"><rect width="300" height="400" fill="%23667eea"/><text x="50%" y="50%" font-size="120" fill="white" text-anchor="middle" dy=".3em">${firstLetter}</text></svg>`;
        }
        
        // Payment history
        const historyBody = document.getElementById('paymentHistoryBody');
        historyBody.innerHTML = '';
        
        if (data.payments && data.payments.length > 0) {
            data.payments.forEach((payment, index) => {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>${payment.receipt_no}</td>
                    <td>₹${parseFloat(payment.amount).toFixed(2)}</td>
                    <td>${payment.payment_date}</td>
                    <td><span class="badge badge-success">${payment.payment_mode}</span></td>
                `;
                historyBody.appendChild(row);
            });
        } else {
            const row = document.createElement('tr');
            row.innerHTML = '<td colspan="4" class="text-center">No payments found</td>';
            historyBody.appendChild(row);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('❌ Error loading student details. Please try again.');
    });
}

// Close student detail modal
function closePaymentTrackingModal() {
    const modal = document.getElementById('paymentTrackingModal');
    modal.style.display = 'none';
    document.body.style.overflow = 'auto';
}

// Close modal when clicking outside
window.onclick = function(event) {
    const modal = document.getElementById('paymentTrackingModal');
    if (event.target === modal) {
        closePaymentTrackingModal();
    }
};

// Close modal with Escape key
document.addEventListener('keydown', function(event) {
    if (event.key === 'Escape') {
        closePaymentTrackingModal();
    }
});
