function confirmDelete(id){
    if(confirm("Are you sure you want to delete this enquiry?")){
        window.location.href = `/enquiries/delete/${id}/`;
    }
}
