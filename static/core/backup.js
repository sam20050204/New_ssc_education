// ====================== BACKUP PAGE JAVASCRIPT ====================== 

let selectedFile = null;

// ==================== EXPORT DATABASE ====================
function exportDatabase() {
    const exportBtn = document.getElementById('exportBtn');
    const exportStatus = document.getElementById('exportStatus');
    
    // Disable button and show loading
    exportBtn.disabled = true;
    const originalText = exportBtn.innerHTML;
    exportBtn.innerHTML = '<span class="btn-icon">⏳</span><span class="btn-text">Exporting...</span>';
    
    // Show loading status
    exportStatus.classList.add('show', 'loading');
    exportStatus.textContent = '⏳ Exporting database and photos...';
    
    fetch(EXPORT_URL, {
        method: 'GET',
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
        }
    })
    .then(response => {
        console.log('Export response status:', response.status);
        console.log('Export response headers:', response.headers.get('content-type'));
        
        if (!response.ok) {
            // Try to parse as JSON error
            return response.json().then(data => {
                throw new Error(data.error || `HTTP ${response.status}`);
            }).catch(() => {
                throw new Error(`HTTP ${response.status}`);
            });
        }
        
        // Check content type
        const contentType = response.headers.get('content-type');
        if (contentType && contentType.includes('application/json')) {
            // It's an error response
            return response.json().then(data => {
                throw new Error(data.error || 'Export failed');
            });
        }
        
        // Get filename from headers if available
        const contentDisposition = response.headers.get('content-disposition');
        let filename = 'ssc_education_backup.zip';
        if (contentDisposition) {
            const match = contentDisposition.match(/filename="(.+)"/);
            if (match) filename = match[1];
        }
        
        return response.blob().then(blob => ({ blob, filename }));
    })
    .then(({ blob, filename }) => {
        console.log('Download starting for:', filename);
        
        // Create download link
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
        
        // Show success message
        exportStatus.classList.remove('loading');
        exportStatus.classList.add('success');
        exportStatus.textContent = '✅ Database and photos exported successfully! Download started.';
        
        // Reset button after 3 seconds
        setTimeout(() => {
            exportBtn.disabled = false;
            exportBtn.innerHTML = originalText;
            exportStatus.classList.remove('show', 'success');
        }, 3000);
    })
    .catch(error => {
        console.error('Export error:', error);
        
        // Show error message
        exportStatus.classList.remove('loading');
        exportStatus.classList.add('error');
        exportStatus.textContent = `❌ Error: ${error.message}`;
        

        
        // Reset button
        exportBtn.disabled = false;
        exportBtn.innerHTML = originalText;
        
        // Hide error after 5 seconds
        setTimeout(() => {
            exportStatus.classList.remove('show', 'error');
        }, 5000);
    });
}

// ==================== FILE UPLOAD HANDLING ====================
function handleDragOver(event) {
    event.preventDefault();
    event.stopPropagation();
    const uploadArea = document.getElementById('uploadArea');
    uploadArea.classList.add('drag-over');
}

function handleDragLeave(event) {
    event.preventDefault();
    event.stopPropagation();
    const uploadArea = document.getElementById('uploadArea');
    uploadArea.classList.remove('drag-over');
}

function handleDrop(event) {
    event.preventDefault();
    event.stopPropagation();
    
    const uploadArea = document.getElementById('uploadArea');
    uploadArea.classList.remove('drag-over');
    
    const files = event.dataTransfer.files;
    if (files.length > 0) {
        handleFileSelect({ target: { files: files } });
    }
}

function handleFileSelect(event) {
    const files = event.target.files;
    if (files.length === 0) return;
    
    const file = files[0];
    
    // Validate file type
    const validTypes = ['application/x-sqlite3', 'application/octet-stream', 'application/zip'];
    const validExtensions = ['db', 'sqlite', 'sqlite3', 'zip'];
    const fileExtension = file.name.split('.').pop().toLowerCase();
    
    if (!validExtensions.includes(fileExtension) && !validTypes.includes(file.type)) {
        showError('Invalid file type. Please select a .db, .sqlite, .sqlite3, or .zip file.');
        return;
    }
    
    // Validate file size (max 500 MB for ZIP files with photos)
    const maxSize = 500 * 1024 * 1024; // 500 MB
    if (file.size > maxSize) {
        showError('File too large. Maximum size is 500 MB.');
        return;
    }
    
    // Store selected file
    selectedFile = file;
    
    // Display selected file info
    displaySelectedFile(file);
    
    // Enable import button
    document.getElementById('importBtn').disabled = false;
}

function displaySelectedFile(file) {
    const selectedFileDiv = document.getElementById('selectedFile');
    const fileName = document.getElementById('fileName');
    const fileSize = document.getElementById('fileSize');
    
    fileName.textContent = file.name;
    fileSize.textContent = formatFileSize(file.size);
    
    selectedFileDiv.classList.remove('hidden');
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i];
}

function clearFileSelection() {
    selectedFile = null;
    document.getElementById('fileInput').value = '';
    document.getElementById('selectedFile').classList.add('hidden');
    document.getElementById('importBtn').disabled = true;
}

// ==================== IMPORT DATABASE ====================
function importDatabase() {
    if (!selectedFile) {
        showError('Please select a database file.');
        return;
    }
    
    // Show confirmation dialog
    document.getElementById('confirmDialog').classList.remove('hidden');
}

function cancelImport() {
    document.getElementById('confirmDialog').classList.add('hidden');
}

function proceedImport() {
    document.getElementById('confirmDialog').classList.add('hidden');
    
    const importBtn = document.getElementById('importBtn');
    const importStatus = document.getElementById('importStatus');
    
    // Disable button and show loading
    importBtn.disabled = true;
    const originalText = importBtn.innerHTML;
    importBtn.innerHTML = '<span class="btn-icon">⏳</span><span class="btn-text">Importing...</span>';
    
    // Show loading status
    importStatus.classList.add('show', 'loading');
    importStatus.textContent = '⏳ Importing database... This may take a few moments.';
    
    // Create FormData for file upload
    const formData = new FormData();
    formData.append('database_file', selectedFile);
    formData.append('csrfmiddlewaretoken', getCookie('csrftoken'));
    
    fetch(IMPORT_URL, {
        method: 'POST',
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
        },
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Show success message
            importStatus.classList.remove('loading');
            importStatus.classList.add('success');
            importStatus.textContent = '✅ Database imported successfully! The page will refresh in 3 seconds.';
            
            // Clear file selection
            clearFileSelection();
            
            // Refresh page after 3 seconds
            setTimeout(() => {
                window.location.reload();
            }, 3000);
        } else {
            throw new Error(data.error || 'Import failed');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        
        // Show error message
        importStatus.classList.remove('loading');
        importStatus.classList.add('error');
        importStatus.textContent = `❌ Error importing database: ${error.message}`;
        
        // Reset button
        importBtn.disabled = false;
        importBtn.innerHTML = originalText;
        
        // Hide error after 5 seconds
        setTimeout(() => {
            importStatus.classList.remove('show', 'error');
        }, 5000);
    });
}

// ==================== UTILITY FUNCTIONS ====================
function showError(message) {
    const importStatus = document.getElementById('importStatus');
    importStatus.classList.add('show', 'error');
    importStatus.textContent = `❌ ${message}`;
    
    setTimeout(() => {
        importStatus.classList.remove('show', 'error');
    }, 5000);
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
