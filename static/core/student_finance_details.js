// Finance Details JavaScript

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

function updateField(studentId, field, value) {
    const csrftoken = getCookie('csrftoken');
    const indicator = document.getElementById('saveIndicator');
    
    // Show saving indicator
    indicator.textContent = 'Saving...';
    indicator.classList.remove('error-indicator');
    indicator.style.display = 'block';
    
    fetch('/update-finance-detail/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrftoken
        },
        body: JSON.stringify({
            student_id: studentId,
            field: field,
            value: value
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Update calculated fields
            const mkclTotalCell = document.querySelector(`.mkcl-total-${studentId}`);
            if (mkclTotalCell) {
                mkclTotalCell.textContent = parseFloat(data.mkcl_total).toFixed(2);
            }
            
            const profitCell = document.querySelector(`.profit-${studentId}`);
            if (profitCell) {
                profitCell.textContent = '₹ ' + parseFloat(data.profit).toFixed(2);
                
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
        showError('Network error. Please check your connection.');
    });
}

// Real-time update function for Excel-like experience
function updateFieldRealTime(studentId, field, value) {
    // Update MKCL total and profit in real-time (before saving to server)
    if (field === 'mkcl_1' || field === 'mkcl_2') {
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
            const mkclTotalCell = document.querySelector(`.mkcl-total-${studentId}`);
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
                    profitCell.textContent = '₹ ' + profit.toFixed(2);
                    
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
        
        // Create CSV content with headers
        let csv = 'Sr.No.,Learner Name,Mobile No.,Batch,Course,I Inst,II Inst,III Inst,IV Inst,V Inst,Total Paid,Total Fees,Balance Fees,MKCL I Inst,MKCL II Inst,MKCL Total,Profit\n';
        
        const rows = table.querySelectorAll('tbody tr');
        console.log('Total rows found:', rows.length);
        
        let rowCount = 0;
        let totalProfitSum = 0;
        let totalMKCLSum = 0;
        let totalPaidSum = 0;
        
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
            
            // Extract data from cells (fixed indexing for 16 columns)
            const srNo = rowCount;
            
            // Student Details (cells 0-4)
            const learnerName = cells[1] ? cells[1].textContent.trim() : '';
            const course = cells[2] ? cells[2].textContent.trim() : '';
            const mobile = cells[3] ? cells[3].textContent.trim() : '';
            const batch = cells[4] ? cells[4].textContent.trim() : '';
            
            // Fees Paid By Learner - 5 installments (cells 5-9)
            let firstInst = '0';
            let secondInst = '0';
            let thirdInst = '0';
            let fourthInst = '0';
            let fifthInst = '0';
            
            if (cells[5]) firstInst = cells[5].textContent.replace('₹', '').trim() || '0';
            if (cells[6]) secondInst = cells[6].textContent.replace('₹', '').trim() || '0';
            if (cells[7]) thirdInst = cells[7].textContent.replace('₹', '').trim() || '0';
            if (cells[8]) fourthInst = cells[8].textContent.replace('₹', '').trim() || '0';
            if (cells[9]) fifthInst = cells[9].textContent.replace('₹', '').trim() || '0';
            
            // Auto-calculated fields (cells 10-12)
            const totalPaid = cells[10] ? parseFloat(cells[10].textContent.replace('₹', '').trim()) || 0 : 0;
            const totalFees = cells[11] ? parseFloat(cells[11].textContent.replace('₹', '').trim()) || 0 : 0;
            const balanceFees = cells[12] ? parseFloat(cells[12].textContent.replace('₹', '').trim()) || 0 : 0;
            
            // Get MKCL values from input fields (cells 13-14)
            let mkclFirst = '0';
            let mkclSecond = '0';
            
            if (cells[13]) {
                const mkclFirstInput = cells[13].querySelector('input');
                mkclFirst = mkclFirstInput ? mkclFirstInput.value : cells[13].textContent.replace('₹', '').trim() || '0';
            }
            
            if (cells[14]) {
                const mkclSecondInput = cells[14].querySelector('input');
                mkclSecond = mkclSecondInput ? mkclSecondInput.value : cells[14].textContent.replace('₹', '').trim() || '0';
            }
            
            // MKCL Total and Profit (cells 15-16)
            const mkclTotal = cells[15] ? parseFloat(cells[15].textContent.replace('₹', '').trim()) || 0 : 0;
            const profitText = cells[16] ? cells[16].textContent.replace('₹', '').trim() : '0';
            const profit = parseFloat(profitText) || 0;
            
            // Add to totals
            totalProfitSum += profit;
            totalMKCLSum += mkclTotal;
            totalPaidSum += totalPaid;
            
            // Build CSV row - escape quotes in names
            const escapeName = (str) => String(str).replace(/"/g, '""');
            csv += `${srNo},"${escapeName(learnerName)}","${escapeName(mobile)}","${escapeName(batch)}","${escapeName(course)}",${firstInst},${secondInst},${thirdInst},${fourthInst},${fifthInst},${totalPaid},${totalFees},${balanceFees},${mkclFirst},${mkclSecond},${mkclTotal},${profit}\n`;
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

// Add keyboard shortcut for export (Ctrl+E)
document.addEventListener('keydown', function(e) {
    if (e.ctrlKey && e.key === 'e') {
        e.preventDefault();
        exportToExcel();
    }
});

// ===================== SETUP STICKY SCROLLBAR =====================
function setupStickyScrollbar() {
    const tableContainer = document.getElementById('tableContainer');
    const stickyScrollbar = document.getElementById('stickyScrollbar');
    const stickyScrollbarTrack = document.querySelector('.sticky-scrollbar-track');
    
    if (!tableContainer || !stickyScrollbar || !stickyScrollbarTrack) {
        return;
    }
    
    let isScrollingSynced = false;
    let scrollAnimationFrame = null;
    
    // Set initial width
    stickyScrollbarTrack.style.width = tableContainer.scrollWidth + 'px';
    
    // Sync table scroll to sticky scrollbar using requestAnimationFrame for smooth updates
    tableContainer.addEventListener('scroll', function() {
        if (isScrollingSynced) return;
        
        if (scrollAnimationFrame) {
            cancelAnimationFrame(scrollAnimationFrame);
        }
        
        scrollAnimationFrame = requestAnimationFrame(() => {
            isScrollingSynced = true;
            stickyScrollbar.scrollLeft = tableContainer.scrollLeft;
            isScrollingSynced = false;
        });
    }, { passive: true });
    
    // Sync sticky scrollbar to table using requestAnimationFrame for smooth updates
    stickyScrollbar.addEventListener('scroll', function() {
        if (isScrollingSynced) return;
        
        if (scrollAnimationFrame) {
            cancelAnimationFrame(scrollAnimationFrame);
        }
        
        scrollAnimationFrame = requestAnimationFrame(() => {
            isScrollingSynced = true;
            tableContainer.scrollLeft = stickyScrollbar.scrollLeft;
            isScrollingSynced = false;
        });
    }, { passive: true });
    
    // Update width when content changes
    const observer = new ResizeObserver(function() {
        stickyScrollbarTrack.style.width = tableContainer.scrollWidth + 'px';
    });
    observer.observe(tableContainer);
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', setupStickyScrollbar);
} else {
    setupStickyScrollbar();
}