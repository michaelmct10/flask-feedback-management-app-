document.querySelectorAll('form button.btn-danger').forEach(function(button) {
    console.log("Attaching event listener to delete button.");
    button.addEventListener('click', function(event) {
        console.log("Delete button clicked.");

        if (!confirm('Are you sure you want to delete this feedback? This action cannot be undone.')) {
            console.log("User canceled the deletion.");
            event.preventDefault(); // Prevent form submission if user cancels
        } else {
            console.log("User confirmed the deletion.");
        }
    });
});

