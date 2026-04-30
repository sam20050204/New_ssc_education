// Finance Details JavaScript

// ============================================================
// SCROLLBAR SYNCHRONIZATION - Keep horizontal scrollbars in sync
// ============================================================

function syncScrollbars() {
    const tableContainer = document.getElementById('tableContainer');
    const stickyScrollbars = document.querySelectorAll('.sticky-scrollbar-container');
    const stickyScrollbarTracks = document.querySelectorAll('.sticky-scrollbar-track');
    
    if (!tableContainer || stickyScrollbars.length === 0) return;
    if (tableContainer.dataset.scrollSyncInitialized === 'true') return;
    tableContainer.dataset.scrollSyncInitialized = 'true';
    
    let isSyncing = false;

    function updateScrollbarWidths() {
        stickyScrollbarTracks.forEach(track => {
            track.style.width = tableContainer.scrollWidth + 'px';
        });
    }

    function syncToScrollLeft(scrollLeft, sourceElement) {
        if (sourceElement !== tableContainer) {
            tableContainer.scrollLeft = scrollLeft;
        }
        stickyScrollbars.forEach(scrollbar => {
            if (scrollbar !== sourceElement) {
                scrollbar.scrollLeft = scrollLeft;
            }
        });
    }

    updateScrollbarWidths();

    tableContainer.addEventListener('scroll', function() {
        if (isSyncing) return;
        isSyncing = true;
        syncToScrollLeft(tableContainer.scrollLeft, tableContainer);
        isSyncing = false;
    }, { passive: true });
    
    stickyScrollbars.forEach(scrollbar => {
        scrollbar.addEventListener('scroll', function() {
            if (isSyncing) return;
            isSyncing = true;
            syncToScrollLeft(scrollbar.scrollLeft, scrollbar);
            isSyncing = false;
        }, { passive: true });
    });

    window.addEventListener('resize', updateScrollbarWidths);

    if (window.ResizeObserver) {
        const observer = new ResizeObserver(updateScrollbarWidths);
        observer.observe(tableContainer);
        const table = document.getElementById('financeTable');
        if (table) observer.observe(table);
    }
    
    console.log('Scrollbar synchronization initialized');
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

function getCsrfToken() {
    const formTokenInput = document.querySelector('#financeCsrfForm input[name="csrfmiddlewaretoken"]');
    if (formTokenInput && formTokenInput.value) {
        return formTokenInput.value;
    }

    const globalTokenInput = document.querySelector('input[name="csrfmiddlewaretoken"]');
    if (globalTokenInput && globalTokenInput.value) {
        return globalTokenInput.value;
    }

    return getCookie('csrftoken');
}

function updateField(studentId, field, value) {
    const csrftoken = getCsrfToken();
    const indicator = document.getElementById('saveIndicator');
    
    // Show saving indicator
    indicator.textContent = 'Saving...';
    indicator.classList.remove('error-indicator');
    indicator.style.display = 'block';
    
    fetch('/update-finance-detail/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'X-CSRFToken': csrftoken,
            'X-Requested-With': 'XMLHttpRequest'
        },
        credentials: 'same-origin',
        body: JSON.stringify({
            student_id: studentId,
            field: field,
            value: value
        })
    })
    .then(async response => {
        let data = null;

        try {
            data = await response.json();
        } catch (error) {
            if (!response.ok) {
                throw new Error(`Request failed with status ${response.status}`);
            }
            throw new Error('Invalid server response');
        }

        if (!response.ok) {
            throw new Error(data.error || `Request failed with status ${response.status}`);
        }

        return data;
    })
    .then(data => {
        if (data.success) {
            // Update calculated fields
            const mkclTotalCell = document.querySelector(`.mkcl-total-cell[data-student-id="${studentId}"]`);
            if (mkclTotalCell) {
                mkclTotalCell.textContent = parseFloat(data.mkcl_total).toFixed(2);
            }
            
            const profitCell = document.querySelector(`.profit-${studentId}`);
            if (profitCell) {
                updateProfitCell(profitCell, parseFloat(data.profit));
                
                // Update profit color
                profitCell.classList.remove('profit-positive', 'profit-negative');
                profitCell.classList.add(data.profit >= 0 ? 'profit-positive' : 'profit-negative');
            }
            
            // Show success indicator
            indicator.textContent = '✓ Saved successfully!';
            indicator.classList.remove('error-indicator');
            
            // Hide after 2 seconds
            setTimeout(() => {
                indicator.style.display = 'none';
            }, 2000);
            
        } else {
            // Show error indicator
            showError('Error: ' + (data.error || 'Failed to save'));
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showError(error.message || 'Failed to save');
    });
}

// Real-time update function for Excel-like experience
function updateFieldRealTime(studentId, field, value) {
    // Update MKCL total and profit in real-time (before saving to server)
    if (field === 'mkcl_1' || field === 'mkcl_2' || field === 'mkcl_3') {
        // Get the row for this student
        const row = document.querySelector(`tr[data-student-id="${studentId}"]`);
        if (row) {
            // Find MKCL 1 and MKCL 2 inputs (last two editable cells before readonly MKCL Total)
            const editableCells = row.querySelectorAll('.editable-cell');
            let mkcl1 = 0, mkcl2 = 0;
            
            if (editableCells.length >= 2) {
                mkcl1 = parseFloat(editableCells[editableCells.length - 2].querySelector('input').value) || 0;
                mkcl2 = parseFloat(editableCells[editableCells.length - 1].querySelector('input').value) || 0;
            }
            
            // Calculate MKCL total immediately
            const mkclTotal = mkcl1 + mkcl2;
            const mkclTotalCell = document.querySelector(`.mkcl-total-cell[data-student-id="${studentId}"]`);
            if (mkclTotalCell) {
                mkclTotalCell.textContent = mkclTotal.toFixed(2);
            }
            
            // Calculate profit: get the total paid from readonly cell
            // Find the "Total Paid" cell (4th readonly cell in Fees Paid By Learner section)
            const readonlyCells = row.querySelectorAll('.readonly-cell');
            if (readonlyCells.length >= 4) {
                // Total Paid is in the 4th readonly cell (after first_inst, second_inst, third_inst)
                const totalPaidText = readonlyCells[3].textContent.trim();
                const totalPaid = parseFloat(totalPaidText) || 0;
                
                // Calculate profit: Total Paid - MKCL Total
                const profit = totalPaid - mkclTotal;
                
                // Update profit cell
                const profitCell = document.querySelector(`.profit-${studentId}`);
                if (profitCell) {
                    updateProfitCell(profitCell, profit);
                    
                    // Update profit color based on positive/negative
                    profitCell.classList.remove('profit-positive', 'profit-negative');
                    profitCell.classList.add(profit >= 0 ? 'profit-positive' : 'profit-negative');
                }
            }
        }
    }
}

function showError(message) {
    const indicator = document.getElementById('saveIndicator');
    indicator.textContent = '✗ ' + message;
    indicator.classList.add('error-indicator');
    indicator.style.display = 'block';
    
    // Hide after 3 seconds
    setTimeout(() => {
        indicator.style.display = 'none';
    }, 3000);
}

function updateProfitCell(profitCell, profit) {
    const profitText = '₹ ' + profit.toFixed(2);
    const profitBadge = profitCell.querySelector('.profit-badge');

    if (profitBadge) {
        profitBadge.textContent = profitText;
    } else {
        profitCell.textContent = profitText;
    }
}

function exportToExcel() {
    try {
        console.log('Export function called');
        
        // Get table data
        const table = document.querySelector('.finance-table');
        if (!table) {
            alert('No data to export - Table not found');
            return;
        }
        
        console.log('Table found');
        
        // Create CSV content with headers (3 learner installments + 3 MKCL installments + totals)
        let csv = 'Sr.No.,Learner Name,Mobile No.,Batch,Course,I Inst,II Inst,III Inst,Total Paid,Total Fees,1st Inst MKCL,2nd Inst MKCL,3rd Inst MKCL,Total Paid MKCL,Profit\n';
        
        const rows = table.querySelectorAll('tbody tr');
        console.log('Total rows found:', rows.length);
        
        let rowCount = 0;
        let totalProfitSum = 0;
        let totalMKCLSum = 0;
        let totalPaidSum = 0;
        let totalFeesSum = 0;
        
        rows.forEach((row, index) => {
            // Skip empty rows or rows with colspan
            const colspanCell = row.querySelector('td[colspan]');
            if (colspanCell) {
                console.log('Skipping row', index, '- has colspan');
                return;
            }
            
            const cells = row.querySelectorAll('td');
            if (cells.length === 0) {
                console.log('Skipping row', index, '- no cells');
                return;
            }
            
            rowCount++;
            console.log('Processing row', rowCount);
            
            // Extract data from cells (fixed indexing for 14 columns)
            const srNo = rowCount;
            
            // Student Details (cells 0-4)
            const learnerName = cells[1] ? cells[1].textContent.trim() : '';
            const course = cells[2] ? cells[2].textContent.trim() : '';
            const mobile = cells[3] ? cells[3].textContent.trim() : '';
            const batch = cells[4] ? cells[4].textContent.trim() : '';
            
            // Fees Paid By Learner - 3 installments only (cells 5-7)
            let firstInst = '0';
            let secondInst = '0';
            let thirdInst = '0';
            
            if (cells[5]) firstInst = cells[5].textContent.replace('₹', '').trim() || '0';
            if (cells[6]) secondInst = cells[6].textContent.replace('₹', '').trim() || '0';
            if (cells[7]) thirdInst = cells[7].textContent.replace('₹', '').trim() || '0';
            
            // Auto-calculated fields (cells 8-9)
            let totalPaid = '0';
            let totalFees = '0';
            
            if (cells[8]) totalPaid = cells[8].textContent.replace('₹', '').trim() || '0';
            if (cells[9]) totalFees = cells[9].textContent.replace('₹', '').trim() || '0';
            
            // MKCL Installments (cells 10-12)
            const mkcl1 = cells[10] ? parseFloat(cells[10].querySelector('input')?.value || cells[10].textContent) || 0 : 0;
            const mkcl2 = cells[11] ? parseFloat(cells[11].querySelector('input')?.value || cells[11].textContent) || 0 : 0;
            const mkcl3 = cells[12] ? parseFloat(cells[12].querySelector('input')?.value || cells[12].textContent) || 0 : 0;
            
            const mkclTotal = mkcl1 + mkcl2 + mkcl3;
            
            // MKCL Total Paid (cell 13)
            const mkclTotalPaidText = cells[13] ? cells[13].textContent.replace('₹', '').trim() : '0';
            const mkclTotalPaid = parseFloat(mkclTotalPaidText) || 0;
            
            // Profit (cell 14)
            const profitText = cells[14] ? cells[14].textContent.replace('₹', '').trim() : '0';
            const profit = parseFloat(profitText) || 0;
            
            // Add to totals
            totalProfitSum += profit;
            totalMKCLSum += mkclTotal;
            totalPaidSum += parseFloat(totalPaid) || 0;
            totalFeesSum += parseFloat(totalFees) || 0;
            
            // Build CSV row - escape quotes in names (15 columns)
            const escapeName = (str) => String(str).replace(/"/g, '""');
            csv += `${srNo},"${escapeName(learnerName)}","${escapeName(mobile)}","${escapeName(batch)}","${escapeName(course)}",${firstInst},${secondInst},${thirdInst},${totalPaid},${totalFees},${mkcl1},${mkcl2},${mkcl3},${mkclTotalPaid},${profit}\n`;
        });
        
        console.log('Total rows processed:', rowCount);
        
        if (rowCount === 0) {
            alert('No data to export');
            return;
        }
        
        // Add summary section with totals
        csv += '\n\n--- SUMMARY ---\n';
        csv += `Total Records,${rowCount}\n`;
        csv += `Total Fees Paid by Learners,${totalPaidSum.toFixed(2)}\n`;
        csv += `Total Fees Paid to MKCL,${totalMKCLSum.toFixed(2)}\n`;
        csv += `Total Profit,${totalProfitSum.toFixed(2)}\n`;
        
        // Create and download file
        const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
        const link = document.createElement('a');
        const url = URL.createObjectURL(blob);
        
        const date = new Date();
        const dateStr = date.getFullYear() + '_' + 
                       String(date.getMonth() + 1).padStart(2, '0') + '_' + 
                       String(date.getDate()).padStart(2, '0') + '_' +
                       String(date.getHours()).padStart(2, '0') +
                       String(date.getMinutes()).padStart(2, '0');
        
        link.setAttribute('href', url);
        link.setAttribute('download', `student_finance_details_${dateStr}.csv`);
        link.style.visibility = 'hidden';
        document.body.appendChild(link);
        
        console.log('Triggering download');
        link.click();
        
        // Clean up
        setTimeout(() => {
            document.body.removeChild(link);
            URL.revokeObjectURL(url);
        }, 100);
        
        // Show success message
        const indicator = document.getElementById('saveIndicator');
        if (indicator) {
            indicator.textContent = '✓ Data exported successfully!';
            indicator.classList.remove('error-indicator');
            indicator.style.display = 'block';
            setTimeout(() => {
                indicator.style.display = 'none';
            }, 2000);
        }
        
    } catch (error) {
        console.error('Export error:', error);
        alert('Error exporting data: ' + error.message);
    }
}

// Auto-save functionality with debouncing
let saveTimeout;
function debouncedUpdate(studentId, field, value) {
    clearTimeout(saveTimeout);
    saveTimeout = setTimeout(() => {
        updateField(studentId, field, value);
    }, 500);
}

// Function to calculate and update MKCL total when installments change
function updateMKCLTotal(studentId) {
    // Get all MKCL installment inputs for this student
    const row = document.querySelector(`tr[data-student-id="${studentId}"]`);
    if (!row) return;
    
    const mkcl1Input = row.querySelector('.mkcl-inst-1');
    const mkcl2Input = row.querySelector('.mkcl-inst-2');
    const mkcl3Input = row.querySelector('.mkcl-inst-3');
    
    if (!mkcl1Input || !mkcl2Input || !mkcl3Input) return;
    
    // Get values from inputs (default to 0 if empty)
    const mkcl1 = parseFloat(mkcl1Input.value) || 0;
    const mkcl2 = parseFloat(mkcl2Input.value) || 0;
    const mkcl3 = parseFloat(mkcl3Input.value) || 0;
    
    // Calculate total
    const mkclTotal = mkcl1 + mkcl2 + mkcl3;
    
    // Update the total cell in real-time
    const mkcl_total_cell = row.querySelector(`.mkcl-total-cell[data-student-id="${studentId}"]`);
    if (mkcl_total_cell) {
        mkcl_total_cell.textContent = mkclTotal.toFixed(2);
    }
    
    // Calculate and update profit in real-time
    // Get Total Paid by Learner (from readonly cells in Fees Paid By Learner section)
    const readonlyCells = row.querySelectorAll('.readonly-cell');
    if (readonlyCells.length >= 1) {
        // Find the Total Paid from Fees Paid By Learner (4th readonly cell, index 3)
        const totalPaidText = readonlyCells[3].textContent.trim();
        const totalPaidByLearner = parseFloat(totalPaidText) || 0;
        
        // Calculate profit: Total Paid by Learner - Total Fees Paid to MKCL
        const profit = totalPaidByLearner - mkclTotal;
        const profitCell = row.querySelector(`.profit-${studentId}`);
        if (profitCell) {
            updateProfitCell(profitCell, profit);
            profitCell.classList.remove('profit-positive', 'profit-negative');
            profitCell.classList.add(profit >= 0 ? 'profit-positive' : 'profit-negative');
        }
    }
    
    // Update total profit on the page
    updateTotalProfit();
}

// Function to calculate and update the total profit across all students
function updateTotalProfit() {
    const profitCells = document.querySelectorAll('[class^="profit-"]');
    let totalProfit = 0;
    
    profitCells.forEach(cell => {
        const profitText = cell.textContent.replace('₹', '').trim();
        const profit = parseFloat(profitText) || 0;
        totalProfit += profit;
    });
    
    // Update the total profit box
    const totalProfitAmount = document.getElementById('totalProfitAmount');
    if (totalProfitAmount) {
        totalProfitAmount.textContent = '₹ ' + totalProfit.toFixed(2);
    }
}

// Set up event listeners for MKCL installment inputs
function setupMKCLInstallmentListeners() {
    const mkcl_inputs = document.querySelectorAll('.mkcl-installment');
    
    mkcl_inputs.forEach(input => {
        input.addEventListener('input', function() {
            const studentId = this.getAttribute('data-student-id');
            const field = this.getAttribute('data-field');
            const value = this.value;
            
            // Update MKCL total and profit in real-time
            updateMKCLTotal(studentId);
            
            // Save to server with debouncing
            debouncedUpdate(studentId, field, value);
        });
        
        input.addEventListener('blur', function() {
            const value = this.value.trim();
            if (value === '') {
                this.value = '0.00';
            } else if (!isNaN(value)) {
                this.value = parseFloat(value).toFixed(2);
            }
            const studentId = this.getAttribute('data-student-id');
            updateMKCLTotal(studentId);
        });
    });
}

function formatCurrency(value) {
    const amount = parseFloat(value) || 0;
    return '₹ ' + amount.toFixed(2);
}

function setFinanceModalText(id, value) {
    const element = document.getElementById(id);
    if (element) {
        element.textContent = value || '-';
    }
}

function openFinanceStudentModal(studentId) {
    const modal = document.getElementById('financeStudentModal');
    if (!modal) return;

    modal.classList.add('active');
    modal.setAttribute('aria-hidden', 'false');
    document.body.style.overflow = 'hidden';

    setFinanceModalText('financeModalName', 'Loading...');
    setFinanceModalText('financeModalCourse', '-');
    setFinanceModalText('financeModalMobile', '-');
    setFinanceModalText('financeModalParentMobile', '-');
    setFinanceModalText('financeModalBatch', '-');
    setFinanceModalText('financeModalAdmissionDate', '-');
    setFinanceModalText('financeModalTotalFees', '-');
    setFinanceModalText('financeModalPaidFees', '-');
    setFinanceModalText('financeModalRemainingFees', '-');
    setFinanceModalText('financeModalAddress', '-');
    const paymentsContainer = document.getElementById('financeModalPayments');
    if (paymentsContainer) paymentsContainer.innerHTML = '<p class="finance-modal-empty">Loading payments...</p>';

    fetch(`/admission/${studentId}/detail/`, {
        method: 'GET',
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
            'Accept': 'application/json'
        }
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Unable to load student details');
        }
        return response.json();
    })
    .then(data => {
        const fullName = data.full_name || [data.surname, data.student_name, data.father_name].filter(Boolean).join(' ');
        const batch = data.batch_display || [data.batch_month, data.batch_year].filter(Boolean).join(' ');
        const address = [data.address, data.city, data.tehsil_block, data.district, data.pin_code].filter(Boolean).join(', ');

        setFinanceModalText('financeModalName', fullName);
        setFinanceModalText('financeModalCourse', data.course || data.custom_course || '-');
        setFinanceModalText('financeModalMobile', data.mobile_own);
        setFinanceModalText('financeModalParentMobile', data.parent_mobile);
        setFinanceModalText('financeModalBatch', batch);
        setFinanceModalText('financeModalAdmissionDate', data.admission_date);
        setFinanceModalText('financeModalTotalFees', formatCurrency(data.total_fees));
        setFinanceModalText('financeModalPaidFees', formatCurrency(data.paid_fees));
        setFinanceModalText('financeModalRemainingFees', formatCurrency(data.remaining_fees));
        setFinanceModalText('financeModalAddress', address);

        const photo = document.getElementById('financeModalPhoto');
        if (photo) {
            if (data.photo) {
                photo.src = data.photo;
            } else {
                const firstLetter = (fullName || 'S').charAt(0).toUpperCase();
                photo.src = `data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" width="120" height="120"><rect width="120" height="120" fill="%236366f1"/><text x="50%" y="50%" font-size="48" fill="white" text-anchor="middle" dy=".35em">${firstLetter}</text></svg>`;
            }
        }

        renderFinancePaymentHistory(data.payment_history || []);
    })
    .catch(error => {
        setFinanceModalText('financeModalName', 'Error loading student');
        if (paymentsContainer) {
            paymentsContainer.innerHTML = `<p class="finance-modal-empty">${error.message}</p>`;
        }
    });
}

function renderFinancePaymentHistory(payments) {
    const container = document.getElementById('financeModalPayments');
    if (!container) return;

    if (!payments.length) {
        container.innerHTML = '<p class="finance-modal-empty">No payment history available.</p>';
        return;
    }

    container.innerHTML = payments.map((payment, index) => `
        <div class="finance-payment-row">
            <div>
                <strong>Installment ${index + 1}</strong>
                <span>${payment.payment_date || '-'}</span>
            </div>
            <div>
                <strong>${formatCurrency(payment.amount)}</strong>
                <span>${payment.payment_mode || '-'} ${payment.receipt_no ? ' • ' + payment.receipt_no : ''}</span>
            </div>
            <div>
                <strong>${formatCurrency(payment.remaining_after)}</strong>
                <span>Remaining</span>
            </div>
        </div>
    `).join('');
}

function closeFinanceStudentModal() {
    const modal = document.getElementById('financeStudentModal');
    if (!modal) return;
    modal.classList.remove('active');
    modal.setAttribute('aria-hidden', 'true');
    document.body.style.overflow = '';
}

document.addEventListener('click', function(event) {
    const modal = document.getElementById('financeStudentModal');
    if (modal && event.target === modal) {
        closeFinanceStudentModal();
    }
});

document.addEventListener('keydown', function(event) {
    if (event.key === 'Escape') {
        closeFinanceStudentModal();
    }
});

// Add keyboard shortcut for export (Ctrl+E)
document.addEventListener('keydown', function(e) {
    if (e.ctrlKey && e.key === 'e') {
        e.preventDefault();
        exportToExcel();
    }
});

// ===================== SETUP STICKY SCROLLBAR =====================
function setupStickyScrollbar() {
    syncScrollbars();
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function() {
        setupStickyScrollbar();
        setupMKCLInstallmentListeners();
    });
} else {
    setupStickyScrollbar();
    setupMKCLInstallmentListeners();
}

// ------------------------
// FILTER DRAWER CONTROLS
// ------------------------
document.addEventListener('DOMContentLoaded', function() {
    // Drawer controls - if elements exist
    const filterToggleBtn = document.getElementById('filterToggleBtn');
    const filterDrawer = document.getElementById('filterDrawer');
    const drawerCloseBtn = document.getElementById('drawerCloseBtn');
    const filterOverlay = document.getElementById('filterOverlay');
    const applyFilterBtn = document.getElementById('applyFilterBtn');
    const clearFilterBtn = document.getElementById('clearFilterBtn');

    if (filterToggleBtn && filterDrawer) {
        filterToggleBtn.addEventListener('click', function() {
            openFilterDrawer();
        });
    }

    if (drawerCloseBtn) {
        drawerCloseBtn.addEventListener('click', closeFilterDrawer);
    }

    if (filterOverlay) {
        filterOverlay.addEventListener('click', closeFilterDrawer);
    }

    if (applyFilterBtn) {
        applyFilterBtn.addEventListener('click', function(e) {
            e.preventDefault();
            applyFiltersFromDrawer();
            closeFilterDrawer();
        });
    }

    if (clearFilterBtn) {
        clearFilterBtn.addEventListener('click', function(e) {
            e.preventDefault();
            clearDrawerFilters();
        });
    }
});

function openFilterDrawer() {
    const drawer = document.getElementById('filterDrawer');
    const overlay = document.getElementById('filterOverlay');
    if (!drawer) return;
    drawer.classList.add('active');
    if (overlay) overlay.style.display = 'block';
    drawer.setAttribute('aria-hidden', 'false');
}

function closeFilterDrawer() {
    const drawer = document.getElementById('filterDrawer');
    const overlay = document.getElementById('filterOverlay');
    if (!drawer) return;
    drawer.classList.remove('active');
    if (overlay) overlay.style.display = 'none';
    drawer.setAttribute('aria-hidden', 'true');
}

function applyFiltersFromDrawer() {
    // Read values from drawer inputs and submit via GET
    const year = document.getElementById('drawerYearFilter') ? document.getElementById('drawerYearFilter').value : '';
    const course = document.getElementById('drawerCourseFilter') ? document.getElementById('drawerCourseFilter').value : '';
    const batch = document.getElementById('drawerBatchFilter') ? document.getElementById('drawerBatchFilter').value : '';
    const sort = document.getElementById('drawerSortSelect') ? document.getElementById('drawerSortSelect').value : '';

    // Build query string and navigate (server expects GET params)
    const params = new URLSearchParams(window.location.search);
    if (year) params.set('year', year); else params.delete('year');
    if (course) params.set('course', course); else params.delete('course');
    if (batch) params.set('batch', batch); else params.delete('batch');
    if (sort) params.set('sort', sort); else params.delete('sort');

    window.location.search = params.toString();
}

function clearDrawerFilters() {
    // Clear drawer inputs and remove query params
    if (document.getElementById('drawerYearFilter')) document.getElementById('drawerYearFilter').value = '';
    if (document.getElementById('drawerCourseFilter')) document.getElementById('drawerCourseFilter').value = '';
    if (document.getElementById('drawerBatchFilter')) document.getElementById('drawerBatchFilter').value = '';
    if (document.getElementById('drawerSortSelect')) document.getElementById('drawerSortSelect').value = '';

    const params = new URLSearchParams(window.location.search);
    params.delete('year');
    params.delete('course');
    params.delete('batch');
    params.delete('sort');
    window.location.search = params.toString();
}

// Compute and apply left offsets for sticky columns dynamically
function computeStickyOffsets() {
    const table = document.querySelector('.finance-table');
    const tableContainer = document.getElementById('tableContainer');
    if (!table || !tableContainer) return;

    // Number of sticky columns to compute (adjust if you add/remove sticky columns)
    const stickyCount = 5;
    let left = 0;

    for (let i = 1; i <= stickyCount; i++) {
        const cls = `sticky-col-${i}`;
        // Find the first element with this class inside the table (header or first row)
        const ref = table.querySelector(`.${cls}`);
        if (!ref) continue;

        // Use offsetWidth to get computed width including borders
        const w = ref.offsetWidth;

        // Apply left offset to all cells with this class (th and td)
        const nodes = document.querySelectorAll(`.${cls}`);
        nodes.forEach(n => {
            n.style.left = left + 'px';
        });

        // Increment left by this column's width
        left += w;
    }
}

// Recompute sticky offsets on resize and content changes
window.addEventListener('resize', function() {
    computeStickyOffsets();
});

// observe table changes to recompute offsets when widths change (e.g., window fonts/load)
document.addEventListener('DOMContentLoaded', function() {
    computeStickyOffsets();
    try {
        const table = document.querySelector('.finance-table');
        const container = document.getElementById('tableContainer');
        if (window.ResizeObserver && (table || container)) {
            const ro = new ResizeObserver(() => computeStickyOffsets());
            if (table) ro.observe(table);
            if (container) ro.observe(container);
        }
    } catch (e) {
        // noop
        console.warn('Sticky offset observer failed', e);
    }
});
