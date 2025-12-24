// Global variables
let allReceipts = [];
let filteredReceipts = [];

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    console.log('Receipts page loaded'); // Debug log
    initializePage();
    loadReceipts();
    setupEventListeners();
});

// Initialize page
function initializePage() {
    // Populate year dropdown
    const yearFilter = document.getElementById('yearFilter');
    const currentYear = new Date().getFullYear();
    for (let year = currentYear; year >= currentYear - 5; year--) {
        const option = document.createElement('option');
        option.value = year;
        option.textContent = year;
        yearFilter.appendChild(option);
    }
}

// Setup event listeners
function setupEventListeners() {
    // Search input - real-time search
    document.getElementById('searchInput').addEventListener('input', debounce(applyFilters, 300));
    
    // Apply filter button
    document.getElementById('applyFilterBtn').addEventListener('click', applyFilters);
    
    // Clear filter button
    document.getElementById('clearFilterBtn').addEventListener('click', clearFilters);
    
    // Export button
    document.getElementById('exportBtn').addEventListener('click', exportToExcel);
    
    // Edit form submit
    document.getElementById('editForm').addEventListener('submit', handleEditSubmit);
}

// Debounce function for search
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Load receipts from backend
async function loadReceipts() {
    try {
        console.log('Loading receipts...'); // Debug log
        showLoading(true);
        
        const response = await fetch('/api/receipts/');
        console.log('Response status:', response.status); // Debug log
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        console.log('Received data:', data); // Debug log
        
        if (data.success) {
            allReceipts = data.receipts || [];
            filteredReceipts = [...allReceipts];
            
            console.log('Total receipts loaded:', allReceipts.length); // Debug log
            
            renderReceipts(filteredReceipts);
            updateSummary(filteredReceipts);
        } else {
            throw new Error(data.error || 'Failed to load receipts');
        }
        
        showLoading(false);
    } catch (error) {
        console.error('Error loading receipts:', error);
        showError('Failed to load receipts. Please refresh the page or contact support.');
        showLoading(false);
    }
}

// Apply filters
function applyFilters() {
    const searchTerm = document.getElementById('searchInput').value.toLowerCase();
    const dateFilter = document.getElementById('dateFilter').value;
    const monthFilter = document.getElementById('monthFilter').value;
    const yearFilter = document.getElementById('yearFilter').value;
    
    console.log('Applying filters:', { searchTerm, dateFilter, monthFilter, yearFilter }); // Debug log
    
    filteredReceipts = allReceipts.filter(receipt => {
        // Search filter
        if (searchTerm && !receipt.student_name.toLowerCase().includes(searchTerm) && !receipt.receipt_no.toLowerCase().includes(searchTerm)) {
            return false;
        }
        
        // Date filter
        if (dateFilter && receipt.payment_date !== dateFilter) {
            return false;
        }
        
        // Month and Year filter
        if (monthFilter || yearFilter) {
            const receiptDate = new Date(receipt.payment_date);
            const receiptMonth = String(receiptDate.getMonth() + 1).padStart(2, '0');
            const receiptYear = String(receiptDate.getFullYear());
            
            if (monthFilter && receiptMonth !== monthFilter) {
                return false;
            }
            
            if (yearFilter && receiptYear !== yearFilter) {
                return false;
            }
        }
        
        return true;
    });
    
    console.log('Filtered receipts:', filteredReceipts.length); // Debug log
    renderReceipts(filteredReceipts);
    updateSummary(filteredReceipts);
}

// Clear all filters
function clearFilters() {
    document.getElementById('searchInput').value = '';
    document.getElementById('dateFilter').value = '';
    document.getElementById('monthFilter').value = '';
    document.getElementById('yearFilter').value = '';
    
    filteredReceipts = [...allReceipts];
    renderReceipts(filteredReceipts);
    updateSummary(filteredReceipts);
}

// Render receipts in table
function renderReceipts(receipts) {
    const tbody = document.getElementById('receiptsTableBody');
    const noResults = document.getElementById('noResults');
    
    tbody.innerHTML = '';
    
    if (receipts.length === 0) {
        noResults.style.display = 'block';
        return;
    }
    
    noResults.style.display = 'none';
    
    receipts.forEach(receipt => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td><strong>#${receipt.receipt_no}</strong></td>
            <td>
                <a href="#" class="student-name" onclick="showPrintModal(${receipt.id}); return false;">
                    ${receipt.student_name}
                </a>
            </td>
            <td>${formatDate(receipt.payment_date)}</td>
            <td><strong>₹${formatNumber(receipt.paid_fees)}</strong></td>
            <td><strong>₹${formatNumber(receipt.remaining_fees)}</strong></td>
            <td>
                <div class="actions-cell">
                    <button class="btn btn-edit" onclick="openEditModal(${receipt.id})">
                        ✏️ Edit
                    </button>
                    <button class="btn btn-print" onclick="showPrintModal(${receipt.id})">
                        🖨️ Print
                    </button>
                    <button class="btn btn-delete" onclick="deleteReceipt(${receipt.id})">
                        🗑️ Delete
                    </button>
                </div>
            </td>
        `;
        tbody.appendChild(row);
    });
}

// Update summary cards
function updateSummary(receipts) {
    const totalReceipts = receipts.length;
    const totalPaid = receipts.reduce((sum, r) => sum + parseFloat(r.paid_fees || 0), 0);
    const totalRemaining = receipts.reduce((sum, r) => sum + parseFloat(r.remaining_fees || 0), 0);
    
    document.getElementById('totalReceipts').textContent = totalReceipts;
    document.getElementById('totalPaid').textContent = '₹' + formatNumber(totalPaid);
    document.getElementById('totalRemaining').textContent = '₹' + formatNumber(totalRemaining);
}

// Open edit modal
function openEditModal(receiptId) {
    const receipt = allReceipts.find(r => r.id === receiptId);
    if (!receipt) {
        showError('Receipt not found');
        return;
    }
    
    document.getElementById('editReceiptId').value = receipt.id;
    document.getElementById('editStudentName').value = receipt.student_name;
    document.getElementById('editPaymentDate').value = receipt.payment_date;
    document.getElementById('editPaidFees').value = receipt.paid_fees;
    document.getElementById('editRemainingFees').value = receipt.remaining_fees;
    
    const modal = document.getElementById('editModal');
    modal.classList.add('active');
    document.body.style.overflow = 'hidden';
}

// Close edit modal
function closeEditModal() {
    const modal = document.getElementById('editModal');
    modal.classList.remove('active');
    document.body.style.overflow = 'auto';
    document.getElementById('editForm').reset();
}

// Handle edit form submit
async function handleEditSubmit(e) {
    e.preventDefault();
    
    const receiptId = document.getElementById('editReceiptId').value;
    const formData = {
        payment_date: document.getElementById('editPaymentDate').value,
        paid_fees: document.getElementById('editPaidFees').value,
        remaining_fees: document.getElementById('editRemainingFees').value
    };
    
    try {
        const response = await fetch(`/api/receipts/${receiptId}/update/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify(formData)
        });
        
        const data = await response.json();
        
        if (data.success) {
            showNotification('Receipt updated successfully!', 'success');
            closeEditModal();
            loadReceipts(); // Reload receipts
        } else {
            showNotification(data.error || 'Failed to update receipt', 'error');
        }
    } catch (error) {
        console.error('Error:', error);
        showNotification('Error updating receipt. Please try again.', 'error');
    }
}

// Delete receipt function
async function deleteReceipt(receiptId) {
    const receipt = allReceipts.find(r => r.id === receiptId);
    if (!receipt) {
        showError('Receipt not found');
        return;
    }
    
    // Confirm deletion
    const confirmMessage = `Are you sure you want to delete this receipt?\n\n` +
                          `Receipt No: ${receipt.receipt_no}\n` +
                          `Student: ${receipt.student_name}\n` +
                          `Amount: ₹${formatNumber(receipt.paid_fees)}\n\n` +
                          `⚠️ Warning: This will also update the student's paid fees!`;
    
    if (!confirm(confirmMessage)) {
        return;
    }
    
    try {
        showLoading(true);
        
        const response = await fetch(`/api/receipts/${receiptId}/delete/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            }
        });
        
        const data = await response.json();
        
        if (data.success) {
            showNotification('Receipt deleted successfully!', 'success');
            loadReceipts(); // Reload receipts
        } else {
            showNotification(data.error || 'Failed to delete receipt', 'error');
        }
        
        showLoading(false);
    } catch (error) {
        console.error('Error:', error);
        showNotification('Error deleting receipt. Please try again.', 'error');
        showLoading(false);
    }
}

// Show print modal
function showPrintModal(receiptId) {
    const receipt = allReceipts.find(r => r.id === receiptId);
    if (!receipt) {
        showError('Receipt not found');
        return;
    }
    
    // Generate receipt HTML
    const receiptHTML = `
        <div class="receipt-header">
            <h1>Shri Samarth Computer Education</h1>
            <p>Contact: 9960638066</p>
            <p>Address: Samarth Road, Behind Bus Stand, Shivaji Nagar, Murud</p>
            <p>TQ. DIST. Latur - 413510</p>
            <p><strong>MKCL Code: 45210017</strong></p>
        </div>
        
        <h2 style="text-align: center; color: #667eea; margin: 20px 0; text-transform: uppercase;">
            🧾 Fee Payment Receipt
        </h2>
        
        <div class="receipt-info">
            <div class="info-group">
                <label>Receipt No.</label>
                <span>${receipt.receipt_no}</span>
            </div>
            <div class="info-group">
                <label>Date</label>
                <span>${formatDate(receipt.payment_date)} ${receipt.payment_time || ''}</span>
            </div>
            <div class="info-group">
                <label>Student Name</label>
                <span>${receipt.student_name}</span>
            </div>
            <div class="info-group">
                <label>Course</label>
                <span>${receipt.course || 'N/A'}</span>
            </div>
            <div class="info-group">
                <label>Mobile</label>
                <span>${receipt.mobile}</span>
            </div>
            <div class="info-group">
                <label>Payment Mode</label>
                <span>${receipt.payment_mode}</span>
            </div>
        </div>
        
        <div class="receipt-details">
            <div class="detail-row">
                <span>Total Fees:</span>
                <span>₹${formatNumber(receipt.total_fees)}</span>
            </div>
            <div class="detail-row">
                <span>Previously Paid:</span>
                <span>₹${formatNumber(receipt.paid_before_this)}</span>
            </div>
            <div class="detail-row">
                <span>Paid Now:</span>
                <span>₹${formatNumber(receipt.paid_fees)}</span>
            </div>
            <div class="detail-row">
                <span>Remaining:</span>
                <span>₹${formatNumber(receipt.remaining_fees)}</span>
            </div>
        </div>
        
        <div class="receipt-footer">
            <p>Thank you for your payment!</p>
            <small>This is a computer-generated receipt</small>
            <div style="text-align: right; margin-top: 40px; padding-right: 20px;">
                <div style="border-top: 2px solid #000; width: 200px; margin-left: auto; margin-bottom: 5px;"></div>
                <strong>Authorized Signature</strong>
            </div>
        </div>
    `;
    
    document.getElementById('receiptContent').innerHTML = receiptHTML;
    const modal = document.getElementById('printModal');
    modal.classList.add('active');
    document.body.style.overflow = 'hidden';
}

// Close print modal
function closePrintModal() {
    const modal = document.getElementById('printModal');
    modal.classList.remove('active');
    document.body.style.overflow = 'auto';
}

// Print receipt
function printReceipt() {
    window.print();
}

// Export to Excel
async function exportToExcel() {
    try {
        showLoading(true);
        
        // Build query parameters
        const params = new URLSearchParams();
        
        const searchTerm = document.getElementById('searchInput').value;
        const dateFilter = document.getElementById('dateFilter').value;
        const monthFilter = document.getElementById('monthFilter').value;
        const yearFilter = document.getElementById('yearFilter').value;
        
        if (searchTerm) params.append('search', searchTerm);
        if (dateFilter) params.append('date', dateFilter);
        if (monthFilter) params.append('month', monthFilter);
        if (yearFilter) params.append('year', yearFilter);
        
        // Download file
        window.location.href = `/api/receipts/export/?${params.toString()}`;
        
        showLoading(false);
        showNotification('Export started! Your download will begin shortly.', 'success');
    } catch (error) {
        console.error('Error exporting:', error);
        showError('Failed to export receipts. Please try again.');
        showLoading(false);
    }
}

// Show/hide loading
function showLoading(show) {
    const spinner = document.getElementById('loadingSpinner');
    if (spinner) {
        spinner.style.display = show ? 'block' : 'none';
    }
}

// Show error message
function showError(message) {
    showNotification(message, 'error');
}

// Show notification
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

// Format date
function formatDate(dateString) {
    const date = new Date(dateString);
    const options = { year: 'numeric', month: 'short', day: 'numeric' };
    return date.toLocaleDateString('en-US', options);
}

// Format number with commas
function formatNumber(number) {
    return parseFloat(number).toLocaleString('en-IN', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    });
}

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

// Close modals on ESC key
document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
        closeEditModal();
        closePrintModal();
    }
});

// Close modals on outside click
window.addEventListener('click', function(e) {
    const editModal = document.getElementById('editModal');
    const printModal = document.getElementById('printModal');
    
    if (e.target === editModal) {
        closeEditModal();
    }
    if (e.target === printModal) {
        closePrintModal();
    }
});