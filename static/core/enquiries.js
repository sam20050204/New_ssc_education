function confirmDelete(id){
    if(confirm("Are you sure you want to delete this enquiry?")){
        window.location.href = `/enquiries/delete/${id}/`;
    }
}
document.getElementById('courseEnquiry').addEventListener('change', function() {
    const otherCourseField = document.getElementById('otherCourseEnquiry');
    if (this.value === 'Other') {
        otherCourseField.style.display = 'block';
        otherCourseField.required = true;
    } else {
        otherCourseField.style.display = 'none';
        otherCourseField.required = false;
        otherCourseField.value = '';
    }
});

// ... (keep existing viewEnquiry function)

// Close View Modal
function closeViewModal() {
    document.getElementById('viewEnquiryModal').classList.remove('active');
    document.body.style.overflow = 'auto';
}

// Open New Enquiry Modal
function openNewEnquiryModal() {
    document.getElementById('newEnquiryModal').classList.add('active');
    document.body.style.overflow = 'hidden';
}

// Close New Enquiry Modal
function closeNewEnquiryModal() {
    document.getElementById('newEnquiryModal').classList.remove('active');
    document.body.style.overflow = 'auto';
    document.getElementById('newEnquiryForm').reset();
    document.getElementById('successMessageEnquiry').classList.remove('show');
    // Hide "Other" course field if shown
    document.getElementById('otherCourseEnquiry').style.display = 'none';
    document.getElementById('otherCourseEnquiry').required = false;
}

// Handle New Enquiry Form Submission with AJAX
document.getElementById('newEnquiryForm').addEventListener('submit', function(e) {
    e.preventDefault();
    
    const formData = new FormData(this);
    const submitBtn = this.querySelector('.btn-submit');
    const originalText = submitBtn.innerHTML;
    
    // Show loading state
    submitBtn.innerHTML = '⏳ Submitting...';
    submitBtn.disabled = true;
    
    fetch('{% url "enquiry_list" %}', {
        method: 'POST',
        body: formData,
        headers: {
            'X-CSRFToken': getCookie('csrftoken'),
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(response => {
        if (response.ok) {
            // Show success message
            const successMsg = document.getElementById('successMessageEnquiry');
            successMsg.textContent = '✅ Enquiry added successfully!';
            successMsg.classList.add('show');
            
            // Clear form fields
            document.getElementById('newEnquiryForm').reset();
            
            // Hide "Other" course field if shown
            document.getElementById('otherCourseEnquiry').style.display = 'none';
            document.getElementById('otherCourseEnquiry').required = false;
            
            // Hide success message after 3 seconds
            setTimeout(() => {
                successMsg.classList.remove('show');
            }, 3000);
            
            // Reset submit button
            submitBtn.innerHTML = originalText;
            submitBtn.disabled = false;
            
            // Note: Modal stays open for next entry
        } else {
            throw new Error('Submission failed');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('❌ Error adding enquiry. Please try again.');
        submitBtn.innerHTML = originalText;
        submitBtn.disabled = false;
    });
});

// Close modals on ESC key
document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
        closeViewModal();
        closeNewEnquiryModal();
    }
});

// Close modals on outside click
window.addEventListener('click', function(e) {
    const viewModal = document.getElementById('viewEnquiryModal');
    const newModal = document.getElementById('newEnquiryModal');
    
    if (e.target === viewModal) {
        closeViewModal();
    }
    if (e.target === newModal) {
        closeNewEnquiryModal();
    }
});