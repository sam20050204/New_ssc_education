// Statistics Page JavaScript

function filterByYear() {
    const year = document.getElementById('yearSelect').value;
    const url = new URL(window.location.href);
    if (year) {
        url.searchParams.set('year', year);
    } else {
        url.searchParams.delete('year');
    }
    window.location.href = url.toString();
}

function showSection(section) {
    hideAllSections();
    
    const sectionMap = {
        'finance': 'financeSection',
        'performance': 'performanceSection',
        'attendance': 'attendanceSection',
        'courses': 'coursesSection'
    };
    
    const sectionId = sectionMap[section];
    if (sectionId) {
        document.getElementById('statisticsGrid').style.display = 'none';
        document.getElementById(sectionId).classList.add('active');
        
        // Load finance data if finance section
        if (section === 'finance') {
            loadFinanceData();
        }
    }
}

function hideAllSections() {
    document.querySelectorAll('.detail-section').forEach(section => {
        section.classList.remove('active');
    });
    document.getElementById('statisticsGrid').style.display = 'grid';
}

function loadFinanceData() {
    const yearSelect = document.getElementById('yearSelect');
    const year = yearSelect ? yearSelect.value : '';
    const url = `/student-finance-details/?year=${year}`;
    
    const financeContent = document.getElementById('financeContent');
    financeContent.innerHTML = '<p style="text-align: center; padding: 40px; color: #666;"><span class="loading-spinner"></span> Loading...</p>';
    
    fetch(url)
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.text();
        })
        .then(html => {
            financeContent.innerHTML = html;
        })
        .catch(error => {
            financeContent.innerHTML = 
                '<p style="color: red; text-align: center; padding: 40px;">Error loading data. Please try again.</p>';
            console.error('Error:', error);
        });
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    // Add any initialization code here if needed
});