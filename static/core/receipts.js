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
    const batchYearFilter = document.getElementById('batchYearFilter');
    const currentYear = new Date().getFullYear();
    for (let year = currentYear; year >= currentYear - 5; year--) {
        const option = document.createElement('option');
        option.value = year;
        option.textContent = year;
        yearFilter.appendChild(option);
        
        const batchOption = document.createElement('option');
        batchOption.value = year;
        batchOption.textContent = year;
        batchYearFilter.appendChild(batchOption);
    }
    
    // Populate course dropdown from loaded data
    populateCourseFilter();
}

// Setup event listeners
function setupEventListeners() {
    // Search input - real-time search
    document.getElementById('searchInput').addEventListener('input', debounce(applyFilters, 300));
    
    // Apply filter button
    document.getElementById('applyFilterBtn').addEventListener('click', function(e) {
        e.preventDefault();
        applyFilters();
        closeFilterDrawer();
        displayActiveFilters();
    });
    
    // Clear filter button
    document.getElementById('clearFilterBtn').addEventListener('click', clearFilters);
    
    // Export button
    document.getElementById('exportBtn').addEventListener('click', exportToExcel);
    
    // Edit form submit
    document.getElementById('editForm').addEventListener('submit', handleEditSubmit);
    
    // FILTER DRAWER CONTROLS
    document.getElementById('filterToggleBtn').addEventListener('click', openFilterDrawer);
    document.getElementById('drawerCloseBtn').addEventListener('click', closeFilterDrawer);
    document.getElementById('filterOverlay').addEventListener('click', closeFilterDrawer);
    
    // FILTER TYPE TOGGLE (Regular/Batch)
    document.getElementById('filterTypeSelect').addEventListener('change', toggleBatchFields);
    
    // SORT BY CHANGE - Apply sorting immediately
    document.getElementById('sortBySelect').addEventListener('change', function() {
        applySorting();
        renderReceipts(filteredReceipts);
    });
}

// Populate course filter dropdown
function populateCourseFilter() {
    const courseFilter = document.getElementById('courseFilter');
    const courses = new Set();
    
    // Extract unique courses from allReceipts
    allReceipts.forEach(receipt => {
        if (receipt.course) {
            courses.add(receipt.course);
        }
    });
    
    // Sort and add to dropdown
    Array.from(courses).sort().forEach(course => {
        const option = document.createElement('option');
        option.value = course;
        option.textContent = course;
        courseFilter.appendChild(option);
    });
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
        console.log('Loading receipts...');
        showLoading(true);
        
        // ✅ FIXED: Use correct endpoint from urls.py
        const response = await fetch('/receipts/api/');  // Changed from '/api/receipts/'
        console.log('Response status:', response.status);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        console.log('Received data:', data);
        
        if (data.success) {
            allReceipts = data.receipts || [];
            filteredReceipts = [...allReceipts];
            
            console.log('Total receipts loaded:', allReceipts.length);
            
            // Populate course filter after loading data
            populateCourseFilter();
            
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
    const monthFilter = document.getElementById('monthFilter').value;
    const yearFilter = document.getElementById('yearFilter').value;
    const courseFilter = document.getElementById('courseFilter').value;
    const batchMonthFilter = document.getElementById('batchMonthFilter').value;
    const batchYearFilter = document.getElementById('batchYearFilter').value;
    const dateFromFilter = document.getElementById('dateFromFilter').value;
    const dateToFilter = document.getElementById('dateToFilter').value;
    
    console.log('Applying filters:', { searchTerm, monthFilter, yearFilter, courseFilter, batchMonthFilter, batchYearFilter, dateFromFilter, dateToFilter }); // Debug log
    
    filteredReceipts = allReceipts.filter(receipt => {
        // Search filter
        if (searchTerm && !receipt.student_name.toLowerCase().includes(searchTerm) && !receipt.receipt_no.toLowerCase().includes(searchTerm)) {
            return false;
        }
        
        // Date range filter
        if (dateFromFilter || dateToFilter) {
            const receiptDate = new Date(receipt.payment_date);
            
            if (dateFromFilter) {
                const fromDate = new Date(dateFromFilter);
                if (receiptDate < fromDate) {
                    return false;
                }
            }
            
            if (dateToFilter) {
                const toDate = new Date(dateToFilter);
                // Set time to end of day to include the entire day
                toDate.setHours(23, 59, 59, 999);
                if (receiptDate > toDate) {
                    return false;
                }
            }
        }
        
        // Month and Year filter (payment date)
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
        
        // Course filter
        if (courseFilter && receipt.course !== courseFilter) {
            return false;
        }
        
        // Batch Month and Batch Year filter
        if (batchMonthFilter || batchYearFilter) {
            const batchDate = new Date(receipt.batch_date);
            const batchMonth = String(batchDate.getMonth() + 1).padStart(2, '0');
            const batchYear = String(batchDate.getFullYear());
            
            if (batchMonthFilter && batchMonth !== batchMonthFilter) {
                return false;
            }
            
            if (batchYearFilter && batchYear !== batchYearFilter) {
                return false;
            }
        }
        
        return true;
    });
    
    console.log('Filtered receipts:', filteredReceipts.length); // Debug log
    
    // Apply sorting
    applySorting();
    
    renderReceipts(filteredReceipts);
    updateSummary(filteredReceipts);
}

// Clear all filters
function clearFilters() {
    document.getElementById('searchInput').value = '';
    document.getElementById('monthFilter').value = '';
    document.getElementById('yearFilter').value = '';
    document.getElementById('courseFilter').value = '';
    document.getElementById('batchMonthFilter').value = '';
    document.getElementById('batchYearFilter').value = '';
    document.getElementById('dateFromFilter').value = '';
    document.getElementById('dateToFilter').value = '';
    document.getElementById('filterTypeSelect').value = 'regular';
    document.getElementById('sortBySelect').value = 'date-desc';
    
    // Hide batch fields
    document.getElementById('batchFields').style.display = 'none';
    
    // Hide active filter chips
    document.getElementById('activeFiltersContainer').style.display = 'none';
    
    filteredReceipts = [...allReceipts];
    applySorting();
    renderReceipts(filteredReceipts);
    updateSummary(filteredReceipts);
}

// Apply sorting
function applySorting() {
    const sortBy = document.getElementById('sortBySelect').value || 'date-desc';
    
    filteredReceipts.sort((a, b) => {
        switch(sortBy) {
            case 'date-asc':
                // Oldest first
                return new Date(a.payment_date) - new Date(b.payment_date);
            
            case 'date-desc':
                // Newest first (default)
                return new Date(b.payment_date) - new Date(a.payment_date);
            
            case 'name-asc':
                // A-Z: Surname, First Name, Middle Name
                return compareNames(a, b);
            
            case 'name-desc':
                // Z-A: Surname, First Name, Middle Name
                return compareNames(b, a);
            
            case 'amount-asc':
                // Low to high
                return parseFloat(a.paid_fees) - parseFloat(b.paid_fees);
            
            case 'amount-desc':
                // High to low
                return parseFloat(b.paid_fees) - parseFloat(a.paid_fees);
            
            default:
                return 0;
        }
    });
}

// Compare names in format: Surname, First Name, Middle Name
function compareNames(receipt1, receipt2) {
    const name1 = (receipt1.surname || '') + ' ' + (receipt1.student_name || '') + ' ' + (receipt1.father_name || '');
    const name2 = (receipt2.surname || '') + ' ' + (receipt2.student_name || '') + ' ' + (receipt2.father_name || '');
    
    return name1.toLowerCase().localeCompare(name2.toLowerCase());
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
        // Format name as: Surname Student Name Father Name
        const formattedName = [receipt.surname, receipt.student_name, receipt.father_name]
            .filter(n => n && n.trim())
            .join(' ');
        
        row.innerHTML = `
            <td><strong>#${receipt.receipt_no}</strong></td>
            <td>
                <a href="#" class="student-name" onclick="showPrintModal(${receipt.id}); return false;">
                    ${formattedName}
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

// Open edit modal - ✅ FIXED
function openEditModal(receiptId) {
    console.log('Opening edit modal for receipt:', receiptId); // Debug log
    
    const receipt = allReceipts.find(r => r.id === receiptId);
    if (!receipt) {
        showError('❌ Receipt not found');
        console.error('Receipt not found in allReceipts:', receiptId);
        return;
    }
    
    console.log('Receipt data:', receipt); // Debug log
    
    // Clear previous form data
    document.getElementById('editForm').reset();
    
    // Populate form fields
    document.getElementById('editReceiptId').value = receipt.id;
    document.getElementById('editStudentName').value = receipt.student_name || '';
    document.getElementById('editPaymentDate').value = receipt.payment_date || '';
    document.getElementById('editPaidFees').value = receipt.paid_fees || '';
    document.getElementById('editRemainingFees').value = receipt.remaining_fees || '';
    
    // Store original total fees for calculation
    document.getElementById('editPaidFees').dataset.totalFees = receipt.paid_fees + receipt.remaining_fees;
    
    console.log('Form populated'); // Debug log
    
    // Show modal
    const modal = document.getElementById('editModal');
    modal.classList.add('active');
    document.body.style.overflow = 'hidden';
    
    // Add event listener for auto-calculating remaining fees
    const paidFeesInput = document.getElementById('editPaidFees');
    paidFeesInput.removeEventListener('input', calculateRemainingFees);
    paidFeesInput.addEventListener('input', calculateRemainingFees);
    
    // Focus on first input
    document.getElementById('editPaymentDate').focus();
}

// Auto-calculate remaining fees when paid fees change
function calculateRemainingFees() {
    const paidFeesInput = document.getElementById('editPaidFees');
    const remainingFeesInput = document.getElementById('editRemainingFees');
    const totalFees = parseFloat(paidFeesInput.dataset.totalFees) || 0;
    const paidFees = parseFloat(paidFeesInput.value) || 0;
    
    const remainingFees = Math.max(0, totalFees - paidFees);
    remainingFeesInput.value = remainingFees.toFixed(2);
}


// Close edit modal
function closeEditModal() {
    const modal = document.getElementById('editModal');
    modal.classList.remove('active');
    document.body.style.overflow = 'auto';
    document.getElementById('editForm').reset();
}

// Handle edit form submit - ✅ FIXED
async function handleEditSubmit(e) {
    e.preventDefault();
    
    const receiptId = document.getElementById('editReceiptId').value;
    const paymentDate = document.getElementById('editPaymentDate').value;
    const paidFees = document.getElementById('editPaidFees').value;
    
    console.log('Submitting edit:', { receiptId, paymentDate, paidFees }); // Debug log
    
    // Validate inputs
    if (!paymentDate) {
        showError('Please enter a payment date');
        return;
    }
    
    if (!paidFees || parseFloat(paidFees) <= 0) {
        showError('Please enter a valid paid amount');
        return;
    }
    
    const formData = {
        payment_date: paymentDate,
        amount: parseFloat(paidFees)
    };
    
    try {
        showLoading(true);
        
        // ✅ FIXED: Use correct endpoint
        const response = await fetch(`/receipts/${receiptId}/update/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCsrfToken()
            },
            body: JSON.stringify(formData)
        });
        
        console.log('Response status:', response.status); // Debug log
        
        const data = await response.json();
        console.log('Response data:', data); // Debug log
        
        if (data.success) {
            showNotification('✅ Receipt updated successfully!', 'success');
            closeEditModal();
            loadReceipts(); // Reload receipts to show updated data
        } else {
            showNotification('❌ ' + (data.error || 'Failed to update receipt'), 'error');
        }
        
        showLoading(false);
    } catch (error) {
        console.error('Error:', error);
        showNotification('❌ Error updating receipt. Please try again.', 'error');
        showLoading(false);
    }
}


// Delete receipt function
async function deleteReceipt(receiptId) {
    const receipt = allReceipts.find(r => r.id === receiptId);
    if (!receipt) {
        showError('Receipt not found');
        return;
    }
    
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
        
        // ✅ FIXED: Use correct endpoint from urls.py
        const response = await fetch(`/receipts/${receiptId}/delete/`, {  // Changed from '/api/receipts/${receiptId}/delete/'
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCsrfToken()
            }
        });
        
        const data = await response.json();
        
        if (data.success) {
            showNotification('Receipt deleted successfully!', 'success');
            loadReceipts();
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

// Show print modal - ✅ UPDATED WITH PROPER FORMAT AND BATCH
function showPrintModal(receiptId) {
    const receipt = allReceipts.find(r => r.id === receiptId);
    if (!receipt) {
        showError('Receipt not found');
        return;
    }
    
    console.log('Receipt data for print:', receipt); // Debug log
    
    // Get batch information
    const batchDisplay = receipt.batch || receipt.batch_display || 'Not Assigned';
    
    // Generate receipt HTML - SAME FORMAT AS FEES PAYMENT PAGE
    const receiptHTML = `
        <div class="receipt-header">
            <div class="institute-name">Shri Samarth Computer Education Murud</div>
            <div class="institute-details">
                Contact No: 9960638066<br>
                Address: Samarth Road, Behind Bus Stand, Shivaji Nagar, Murud<br>
                TQ. DIST. Latur - 413510<br>
                <strong>MKCL Authorized Center Code: 45210017</strong>
            </div>
        </div>

        <h2 class="receipt-title">🧾 FEE PAYMENT RECEIPT</h2>

        <div class="receipt-info">
            <span class="receipt-label">Receipt No:</span>
            <span class="receipt-value">${receipt.receipt_no}</span>

            <span class="receipt-label">Date:</span>
            <span class="receipt-value">${formatDate(receipt.payment_date)}</span>

            <span class="receipt-label">Student Name:</span>
            <span class="receipt-value">${receipt.student_name}</span>

            <span class="receipt-label">Course:</span>
            <span class="receipt-value">${receipt.course || 'N/A'}</span>

            <span class="receipt-label">Batch:</span>
            <span class="receipt-value">${batchDisplay}</span>

            <span class="receipt-label">Mobile:</span>
            <span class="receipt-value">${receipt.mobile}</span>

            <span class="receipt-label">Payment Mode:</span>
            <span class="receipt-value">${receipt.payment_mode || 'N/A'}</span>
        </div>
        <hr class="receipt-divider">

        <div class="amount-section">
            <div class="amount-row">
                <span>Total Course Fees:</span>
                <strong>₹${formatNumber(receipt.total_fees || 0)}</strong>
            </div>
            <div class="amount-row">
                <span>Previously Paid:</span>
                <strong>₹${formatNumber(receipt.paid_before_this || 0)}</strong>
            </div>
            <div class="amount-row paid">
                <span>Amount Paid Now:</span>
                <strong>₹${formatNumber(receipt.paid_fees)}</strong>
            </div>
            <div class="amount-row">
                <span>Remaining:</span>
                <strong>₹${formatNumber(receipt.remaining_fees)}</strong>
            </div>
            <div class="amount-in-words">
                <strong>In Words:</strong> ${convertToWords(parseFloat(receipt.paid_fees))}
            </div>
        </div>

        <hr class="receipt-divider">

        <div class="receipt-footer">
            <p style="text-align: center;">Thank you for your payment!</p>
            <p style="text-align: center;"><small>This is a computer-generated receipt</small></p>
            <div style="text-align: right; margin-top: 40px; padding-right: 20px;">
                <div style="border-top: 2px solid #333; width: 200px; margin-left: auto; margin-bottom: 5px;"></div>
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
        
        const params = new URLSearchParams();
        
        const searchTerm = document.getElementById('searchInput').value;
        const dateFilter = document.getElementById('dateFilter').value;
        const monthFilter = document.getElementById('monthFilter').value;
        const yearFilter = document.getElementById('yearFilter').value;
        
        if (searchTerm) params.append('search', searchTerm);
        if (dateFilter) params.append('date', dateFilter);
        if (monthFilter) params.append('month', monthFilter);
        if (yearFilter) params.append('year', yearFilter);
        
        // ✅ FIXED: Use correct endpoint from urls.py
        window.location.href = `/receipts/export/?${params.toString()}`;  // Changed from '/api/receipts/export/'
        
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
function getCsrfToken() {
    const formTokenInput = document.querySelector('#receiptsCsrfForm input[name="csrfmiddlewaretoken"]');
    if (formTokenInput && formTokenInput.value) {
        return formTokenInput.value;
    }

    const globalTokenInput = document.querySelector('input[name="csrfmiddlewaretoken"]');
    if (globalTokenInput && globalTokenInput.value) {
        return globalTokenInput.value;
    }

    return getCookie('csrftoken');
}

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

// Convert number to words - ✅ NEW FUNCTION
function convertToWords(num) {
    const ones = ['', 'One', 'Two', 'Three', 'Four', 'Five', 'Six', 'Seven', 'Eight', 'Nine'];
    const tens = ['', '', 'Twenty', 'Thirty', 'Forty', 'Fifty', 'Sixty', 'Seventy', 'Eighty', 'Ninety'];
    const teens = ['Ten', 'Eleven', 'Twelve', 'Thirteen', 'Fourteen', 'Fifteen', 'Sixteen', 'Seventeen', 'Eighteen', 'Nineteen'];
    const scales = ['', 'Thousand', 'Lakh', 'Crore'];

    if (num === 0) return 'Zero';

    let parts = [];
    let scaleIndex = 0;

    while (num > 0) {
        let part = num % 1000;
        
        if (part !== 0) {
            parts.unshift(convertHundreds(part) + (scaleIndex > 0 ? ' ' + scales[scaleIndex] : ''));
        }
        
        num = Math.floor(num / 1000);
        scaleIndex++;
    }

    return parts.join(' ') + ' Rupees Only';
}

// Helper function for convertToWords
function convertHundreds(num) {
    const ones = ['', 'One', 'Two', 'Three', 'Four', 'Five', 'Six', 'Seven', 'Eight', 'Nine'];
    const tens = ['', '', 'Twenty', 'Thirty', 'Forty', 'Fifty', 'Sixty', 'Seventy', 'Eighty', 'Ninety'];
    const teens = ['Ten', 'Eleven', 'Twelve', 'Thirteen', 'Fourteen', 'Fifteen', 'Sixteen', 'Seventeen', 'Eighteen', 'Nineteen'];

    let result = '';

    // Hundreds place
    let hundred = Math.floor(num / 100);
    if (hundred > 0) {
        result += ones[hundred] + ' Hundred';
    }

    // Tens and ones place
    let remainder = num % 100;
    if (remainder >= 10 && remainder < 20) {
        if (result) result += ' ';
        result += teens[remainder - 10];
    } else {
        let ten = Math.floor(remainder / 10);
        let one = remainder % 10;
        
        if (ten > 0) {
            if (result) result += ' ';
            result += tens[ten];
        }
        
        if (one > 0) {
            if (result) result += ' ';
            result += ones[one];
        }
    }

    return result;
}

// ✅ FORMAT NUMBER WITH 2 DECIMAL PLACES
function formatNumber(num) {
    if (!num) return '0.00';
    return parseFloat(num).toFixed(2);
}

// ✅ FORMAT DATE FROM YYYY-MM-DD TO DD-MM-YYYY
function formatDate(dateString) {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    const day = String(date.getDate()).padStart(2, '0');
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const year = date.getFullYear();
    return `${day}-${month}-${year}`;
}

// ✅ CONVERT NUMBER TO INDIAN CURRENCY WORDS
function convertToWords(num) {
    const ones = ['', 'One', 'Two', 'Three', 'Four', 'Five', 'Six', 'Seven', 'Eight', 'Nine'];
    const tens = ['', '', 'Twenty', 'Thirty', 'Forty', 'Fifty', 'Sixty', 'Seventy', 'Eighty', 'Ninety'];
    const teens = ['Ten', 'Eleven', 'Twelve', 'Thirteen', 'Fourteen', 'Fifteen', 'Sixteen', 'Seventeen', 'Eighteen', 'Nineteen'];
    const scales = ['', 'Thousand', 'Lakh', 'Crore'];

    if (num === 0) return 'Zero';
    if (!num) return 'Zero';

    num = Math.floor(num);
    let parts = [];
    let scaleIndex = 0;

    while (num > 0) {
        let part = num % 1000;
        
        if (part !== 0) {
            parts.unshift(convertHundreds(part) + (scaleIndex > 0 ? ' ' + scales[scaleIndex] : ''));
        }
        
        num = Math.floor(num / 1000);
        scaleIndex++;
    }

    return parts.join(' ') + ' Rupees Only';
}

// ✅ HELPER: CONVERT HUNDREDS PLACE
function convertHundreds(num) {
    const ones = ['', 'One', 'Two', 'Three', 'Four', 'Five', 'Six', 'Seven', 'Eight', 'Nine'];
    const tens = ['', '', 'Twenty', 'Thirty', 'Forty', 'Fifty', 'Sixty', 'Seventy', 'Eighty', 'Ninety'];
    const teens = ['Ten', 'Eleven', 'Twelve', 'Thirteen', 'Fourteen', 'Fifteen', 'Sixteen', 'Seventeen', 'Eighteen', 'Nineteen'];

    let result = '';

    // Hundreds place
    let hundred = Math.floor(num / 100);
    if (hundred > 0) {
        result += ones[hundred] + ' Hundred';
    }

    // Tens and ones place
    let remainder = num % 100;
    if (remainder >= 10 && remainder < 20) {
        if (result) result += ' ';
        result += teens[remainder - 10];
    } else {
        let ten = Math.floor(remainder / 10);
        let one = remainder % 10;
        
        if (ten > 0) {
            if (result) result += ' ';
            result += tens[ten];
        }
        
        if (one > 0) {
            if (result) result += ' ';
            result += ones[one];
        }
    }

    return result;
}

// ✅ CLOSE PRINT MODAL
function closePrintModal() {
    const modal = document.getElementById('printModal');
    if (modal) {
        modal.classList.remove('active');
        document.body.style.overflow = 'auto';
        
        const receiptContent = document.getElementById('receiptContent');
        if (receiptContent) {
            receiptContent.innerHTML = '';
        }
    }
}

// ✅ PRINT RECEIPT
function printReceipt() {
    const receiptContent = document.getElementById('receiptContent');
    if (!receiptContent || !receiptContent.innerHTML) {
        alert('❌ Receipt not found');
        return;
    }
    
    const printWindow = window.open('', '', 'width=900,height=700');
    
    if (!printWindow) {
        alert('❌ Please allow popups to print the receipt');
        return;
    }
    
    const printHTML = `
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Fee Payment Receipt - Print</title>
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
                    padding: 30px;
                    border: 1px solid #ddd;
                }
                .receipt-header { 
                    text-align: center; 
                    border-bottom: 3px solid #333; 
                    padding-bottom: 15px; 
                    margin-bottom: 20px;
                }
                .institute-name { 
                    font-size: 20px; 
                    font-weight: bold; 
                    margin-bottom: 8px;
                }
                .institute-details { 
                    font-size: 11px; 
                    line-height: 1.6;
                }
                .receipt-title { 
                    text-align: center; 
                    font-size: 18px; 
                    margin: 20px 0; 
                    font-weight: bold;
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
                    text-align: center;
                }
                @media print {
                    body { margin: 0; padding: 0; }
                    .receipt-container { border: none; }
                }
            </style>
        </head>
        <body>
            <div class="receipt-container">
                ${receiptContent.innerHTML}
            </div>
            <script>
                window.focus();
                window.print();
                setTimeout(function() {
                    window.close();
                }, 1000);
            </script>
        </body>
        </html>
    `;
    
    printWindow.document.write(printHTML);
    printWindow.document.close();
}

function formatReceiptStudentName(receipt) {
    return [receipt.surname, receipt.student_name, receipt.father_name]
        .map(part => (part || '').trim())
        .filter(Boolean)
        .join(' ');
}

function showPrintModal(receiptId) {
    const receipt = allReceipts.find(r => r.id === receiptId);
    if (!receipt) {
        showError('Receipt not found');
        return;
    }

    const batchDisplay = receipt.batch || receipt.batch_display || 'Not Assigned';
    const studentFullName = formatReceiptStudentName(receipt) || receipt.student_name || 'N/A';

    const receiptHTML = `
        <div class="receipt-header">
            <div style="display: flex; justify-content: space-between; align-items: flex-start; gap: 20px; margin-bottom: 14px;">
                <div style="flex: 1;">
                    <div class="institute-name" style="font-size: 28px; letter-spacing: 0.4px; margin-bottom: 6px;">Shri Samarth Computer Education, Murud</div>
                    <div style="width: 88px; height: 3px; background: linear-gradient(90deg, #0f766e, #f97316); border-radius: 999px; margin-bottom: 10px;"></div>
                    <div class="institute-details" style="line-height: 1.75;">
                        Samarth Road, Behind Bus Stand, Shivaji Nagar, Murud<br>
                        TQ. Dist. Latur - 413510<br>
                        Contact No: 9960638066<br>
                        <strong>MKCL Authorized Center Code: 45210017</strong>
                    </div>
                </div>
                <div style="min-width: 180px; text-align: right; border: 1px solid #cbd5e1; border-radius: 12px; padding: 12px 14px; background: linear-gradient(180deg, #f8fafc 0%, #eef6ff 100%);">
                    <div style="font-size: 11px; text-transform: uppercase; letter-spacing: 1px; color: #475569; margin-bottom: 4px;">Receipt Date</div>
                    <div style="font-size: 18px; font-weight: 700; color: #0f172a;">${formatDate(receipt.payment_date)}</div>
                </div>
            </div>
        </div>

        <h2 class="receipt-title" style="letter-spacing: 0.8px;">FEE PAYMENT RECEIPT</h2>

        <div class="receipt-info" style="grid-template-columns: 170px 1fr; gap: 12px 14px;">
            <span class="receipt-label">Receipt No:</span>
            <span class="receipt-value">${receipt.receipt_no}</span>

            <span class="receipt-label">Student Name:</span>
            <span class="receipt-value">${studentFullName}</span>

            <span class="receipt-label">Course:</span>
            <span class="receipt-value">${receipt.course || 'N/A'}</span>

            <span class="receipt-label">Batch:</span>
            <span class="receipt-value">${batchDisplay}</span>

            <span class="receipt-label">Mobile:</span>
            <span class="receipt-value">${receipt.mobile}</span>

            <span class="receipt-label">Payment Mode:</span>
            <span class="receipt-value">${receipt.payment_mode || 'N/A'}</span>
        </div>
        <hr class="receipt-divider">

        <div class="amount-section">
            <div class="amount-row">
                <span>Total Course Fees:</span>
                <strong>Rs. ${formatNumber(receipt.total_fees || 0)}</strong>
            </div>
            <div class="amount-row">
                <span>Previously Paid:</span>
                <strong>Rs. ${formatNumber(receipt.paid_before_this || 0)}</strong>
            </div>
            <div class="amount-row paid">
                <span>Amount Paid Now:</span>
                <strong>Rs. ${formatNumber(receipt.paid_fees)}</strong>
            </div>
            <div class="amount-row">
                <span>Remaining:</span>
                <strong>Rs. ${formatNumber(receipt.remaining_fees)}</strong>
            </div>
            <div class="amount-in-words">
                <strong>In Words:</strong> ${convertToWords(parseFloat(receipt.paid_fees))}
            </div>
        </div>

        <hr class="receipt-divider">

        <div class="receipt-footer">
            <p style="text-align: center;">Thank you for your payment!</p>
            <p style="text-align: center;"><small>This is a computer-generated receipt</small></p>
            <div style="text-align: right; margin-top: 46px; padding-right: 20px;">
                <div style="border-top: 2px solid #333; width: 200px; margin-left: auto; margin-bottom: 5px;"></div>
                <strong>Authorized Signature</strong>
            </div>
        </div>
    `;

    document.getElementById('receiptContent').innerHTML = receiptHTML;
    const modal = document.getElementById('printModal');
    modal.classList.add('active');
    document.body.style.overflow = 'hidden';
}

function printReceipt() {
    const receiptContent = document.getElementById('receiptContent');
    if (!receiptContent || !receiptContent.innerHTML) {
        alert('Receipt not found');
        return;
    }

    const printWindow = window.open('', '', 'width=900,height=700');

    if (!printWindow) {
        alert('Please allow popups to print the receipt');
        return;
    }

    const printHTML = `
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Fee Payment Receipt - Print</title>
            <style>
                * { margin: 0; padding: 0; box-sizing: border-box; }
                body {
                    font-family: "Segoe UI", Arial, sans-serif;
                    padding: 20px;
                    background: white;
                    color: #1e293b;
                }
                .receipt-container {
                    max-width: 760px;
                    margin: 0 auto;
                    background: white;
                    padding: 32px;
                    border: 1px solid #cbd5e1;
                    border-radius: 18px;
                }
                .receipt-header {
                    border-bottom: 3px solid #0f766e;
                    padding-bottom: 16px;
                    margin-bottom: 20px;
                }
                .institute-name {
                    font-size: 22px;
                    font-weight: 800;
                    color: #0f172a;
                }
                .institute-details {
                    font-size: 11px;
                    line-height: 1.6;
                    color: #334155;
                }
                .receipt-title {
                    text-align: center;
                    font-size: 19px;
                    margin: 22px 0 18px;
                    font-weight: 800;
                    color: #0f172a;
                }
                .receipt-info {
                    display: grid;
                    grid-template-columns: 170px 1fr;
                    gap: 10px 14px;
                    margin: 20px 0;
                    font-size: 13px;
                }
                .receipt-label {
                    font-weight: 700;
                    color: #475569;
                }
                .receipt-value {
                    font-weight: 600;
                    color: #0f172a;
                }
                .receipt-divider {
                    border: none;
                    border-top: 1px dashed #94a3b8;
                    margin: 18px 0;
                }
                .amount-section {
                    margin: 20px 0;
                    font-size: 13px;
                }
                .amount-row {
                    display: flex;
                    justify-content: space-between;
                    padding: 10px 0;
                    border-bottom: 1px dotted #cbd5e1;
                }
                .amount-row.paid {
                    background: linear-gradient(90deg, #ecfdf5 0%, #f0fdf4 100%);
                    padding: 14px 12px;
                    font-weight: 700;
                    border: 2px solid #22c55e;
                    border-radius: 10px;
                    margin: 10px 0;
                }
                .amount-in-words {
                    margin-top: 15px;
                    padding: 12px;
                    background: #f8fafc;
                    border-left: 4px solid #0f766e;
                    border-radius: 8px;
                    font-size: 12px;
                }
                .receipt-footer {
                    margin-top: 30px;
                    text-align: center;
                }
                @media print {
                    body { margin: 0; padding: 0; }
                    .receipt-container { border: none; border-radius: 0; padding: 18px; }
                }
            </style>
        </head>
        <body>
            <div class="receipt-container">
                ${receiptContent.innerHTML}
            </div>
            <script>
                window.focus();
                window.print();
                setTimeout(function() {
                    window.close();
                }, 1000);
            </script>
        </body>
        </html>
    `;

    printWindow.document.write(printHTML);
    printWindow.document.close();
}

// ===================== FILTER DRAWER FUNCTIONS =====================

// Open filter drawer
function openFilterDrawer() {
    const drawer = document.getElementById('filterDrawer');
    const overlay = document.getElementById('filterOverlay');
    drawer.classList.add('active');
    overlay.classList.add('active');
    document.body.style.overflow = 'hidden'; // Prevent scrolling
}

// Close filter drawer
function closeFilterDrawer() {
    const drawer = document.getElementById('filterDrawer');
    const overlay = document.getElementById('filterOverlay');
    drawer.classList.remove('active');
    overlay.classList.remove('active');
    document.body.style.overflow = 'auto'; // Allow scrolling
}

// Toggle batch fields based on filter type
function toggleBatchFields() {
    const filterType = document.getElementById('filterTypeSelect').value;
    const batchFields = document.getElementById('batchFields');
    
    if (filterType === 'batch') {
        batchFields.style.display = 'block';
    } else {
        batchFields.style.display = 'none';
        // Clear batch fields when hiding
        document.getElementById('batchMonthFilter').value = '';
        document.getElementById('batchYearFilter').value = '';
    }
}

// Display active filters as chips
function displayActiveFilters() {
    const searchTerm = document.getElementById('searchInput').value;
    const monthFilter = document.getElementById('monthFilter').value;
    const yearFilter = document.getElementById('yearFilter').value;
    const courseFilter = document.getElementById('courseFilter').value;
    const filterType = document.getElementById('filterTypeSelect').value;
    const batchMonthFilter = document.getElementById('batchMonthFilter').value;
    const batchYearFilter = document.getElementById('batchYearFilter').value;
    const dateFromFilter = document.getElementById('dateFromFilter').value;
    const dateToFilter = document.getElementById('dateToFilter').value;
    
    const activeFilters = [];
    
    if (searchTerm) {
        activeFilters.push({ label: 'Search', value: searchTerm });
    }
    if (monthFilter) {
        const monthNames = ['', 'January', 'February', 'March', 'April', 'May', 'June', 
                           'July', 'August', 'September', 'October', 'November', 'December'];
        activeFilters.push({ label: 'Month', value: monthNames[parseInt(monthFilter)] });
    }
    if (yearFilter) {
        activeFilters.push({ label: 'Year', value: yearFilter });
    }
    if (courseFilter) {
        activeFilters.push({ label: 'Course', value: courseFilter });
    }
    if (filterType === 'batch') {
        if (batchMonthFilter) {
            const monthNames = ['', 'January', 'February', 'March', 'April', 'May', 'June', 
                               'July', 'August', 'September', 'October', 'November', 'December'];
            activeFilters.push({ label: 'Batch Month', value: monthNames[parseInt(batchMonthFilter)] });
        }
        if (batchYearFilter) {
            activeFilters.push({ label: 'Batch Year', value: batchYearFilter });
        }
    }
    if (dateFromFilter) {
        activeFilters.push({ label: 'From Date', value: dateFromFilter });
    }
    if (dateToFilter) {
        activeFilters.push({ label: 'To Date', value: dateToFilter });
    }
    
    const container = document.getElementById('activeFiltersContainer');
    const chipsContainer = document.getElementById('activeFilterChips');
    
    if (activeFilters.length > 0) {
        chipsContainer.innerHTML = '';
        activeFilters.forEach((filter, index) => {
            const chip = document.createElement('div');
            chip.className = 'filter-chip';
            chip.innerHTML = `
                <span>${filter.label}: ${filter.value}</span>
                <button class="chip-remove" data-index="${index}" type="button">✕</button>
            `;
            
            chip.querySelector('.chip-remove').addEventListener('click', function() {
                removeFilter(filter.label);
            });
            
            chipsContainer.appendChild(chip);
        });
        container.style.display = 'flex';
    } else {
        container.style.display = 'none';
    }
}

// Remove specific filter
function removeFilter(filterLabel) {
    const monthNames = ['', 'January', 'February', 'March', 'April', 'May', 'June', 
                       'July', 'August', 'September', 'October', 'November', 'December'];
    
    switch(filterLabel) {
        case 'Search':
            document.getElementById('searchInput').value = '';
            break;
        case 'Month':
            document.getElementById('monthFilter').value = '';
            break;
        case 'Year':
            document.getElementById('yearFilter').value = '';
            break;
        case 'Course':
            document.getElementById('courseFilter').value = '';
            break;
        case 'Batch Month':
            document.getElementById('batchMonthFilter').value = '';
            break;
        case 'Batch Year':
            document.getElementById('batchYearFilter').value = '';
            break;
        case 'From Date':
            document.getElementById('dateFromFilter').value = '';
            break;
        case 'To Date':
            document.getElementById('dateToFilter').value = '';
            break;
    }
    
    applyFilters();
    displayActiveFilters();
}
