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
                mkclTotalCell.textContent = '₹ ' + parseFloat(data.mkcl_total).toFixed(2);
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
        let csv = 'Sr.No.,Learner Name,Student ID,Mobile No.,Batch,Course,I Inst,II Inst,III Inst,Total Paid,Total Fees,Balance Fees,MKCL I Inst,MKCL II Inst,MKCL Total,Profit\n';
        
        const rows = table.querySelectorAll('tbody tr');
        console.log('Total rows found:', rows.length);
        
        let rowCount = 0;
        
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
            
            // Extract data from cells
            const srNo = rowCount;
            
            // Learner Name and Student ID
            const learnerNameCell = cells[1];
            const learnerName = learnerNameCell.querySelector('strong') ? 
                learnerNameCell.querySelector('strong').textContent.trim() : '';
            const studentIdText = learnerNameCell.querySelector('small') ? 
                learnerNameCell.querySelector('small').textContent.replace('ID:', '').trim() : '';
            
            const mobile = cells[2] ? cells[2].textContent.trim() : '';
            const batch = cells[3] ? cells[3].textContent.trim() : '';
            const course = cells[4] ? cells[4].textContent.trim() : '';
            
            // Get installment values (read-only cells)
            const firstInst = cells[5] ? cells[5].textContent.replace('₹', '').trim() : '0';
            const secondInst = cells[6] ? cells[6].textContent.replace('₹', '').trim() : '0';
            const thirdInst = cells[7] ? cells[7].textContent.replace('₹', '').trim() : '0';
            
            // Get readonly values
            const totalPaid = cells[8] ? cells[8].textContent.replace('₹', '').trim() : '0';
            const totalFees = cells[9] ? cells[9].textContent.replace('₹', '').trim() : '0';
            const balanceFees = cells[10] ? cells[10].textContent.replace('₹', '').trim() : '0';
            
            // Get MKCL values (from input fields in editable cells)
            let mkclFirst = '0';
            let mkclSecond = '0';
            
            if (cells[11]) {
                const mkclFirstInput = cells[11].querySelector('input');
                mkclFirst = mkclFirstInput ? mkclFirstInput.value : cells[11].textContent.replace('₹', '').trim();
            }
            
            if (cells[12]) {
                const mkclSecondInput = cells[12].querySelector('input');
                mkclSecond = mkclSecondInput ? mkclSecondInput.value : cells[12].textContent.replace('₹', '').trim();
            }
            
            const mkclTotal = cells[13] ? cells[13].textContent.replace('₹', '').trim() : '0';
            const profit = cells[14] ? cells[14].textContent.replace('₹', '').trim() : '0';
            
            // Build CSV row - escape quotes in names
            const escapeName = (str) => String(str).replace(/"/g, '""');
            csv += `${srNo},"${escapeName(learnerName)}","${escapeName(studentIdText)}","${escapeName(mobile)}","${escapeName(batch)}","${escapeName(course)}",${firstInst},${secondInst},${thirdInst},${totalPaid},${totalFees},${balanceFees},${mkclFirst},${mkclSecond},${mkclTotal},${profit}\n`;
        });
        
        console.log('Total rows processed:', rowCount);
        
        if (rowCount === 0) {
            alert('No data to export');
            return;
        }
        
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