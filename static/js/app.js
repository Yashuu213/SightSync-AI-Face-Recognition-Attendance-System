// Handle Add Employee Form Submission
const addEmployeeForm = document.getElementById('addEmployeeForm');
if (addEmployeeForm) {
    const faceImageInput = document.getElementById('faceImageInput');
    const imagePreview = document.getElementById('imagePreview');
    const previewArea = document.getElementById('previewArea');
    const uploadArea = document.getElementById('uploadArea');
    const resetImageBtn = document.getElementById('resetImageBtn');
    const submitBtn = document.getElementById('submitBtn');
    const formMessage = document.getElementById('formMessage');

    // Handle image preview
    faceImageInput.addEventListener('change', function() {
        const file = this.files[0];
        if (file) {
            const reader = new FileReader();
            reader.onload = function(e) {
                imagePreview.src = e.target.result;
                uploadArea.style.display = 'none';
                previewArea.style.display = 'block';
            }
            reader.readAsDataURL(file);
        }
    });

    // Reset image
    resetImageBtn.addEventListener('click', function() {
        faceImageInput.value = '';
        imagePreview.src = '';
        uploadArea.style.display = 'block';
        previewArea.style.display = 'none';
    });

    // Submit form via AJAX
    addEmployeeForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Registering...';
        formMessage.innerHTML = '';

        const formData = new FormData(this);

        try {
            const response = await fetch('/add_employee', {
                method: 'POST',
                body: formData
            });
            const data = await response.json();

            if (data.success) {
                formMessage.innerHTML = `<div style="color: green; padding: 10px; background: #D1FAE5; border-radius: 8px;">${data.message}</div>`;
                this.reset();
                resetImageBtn.click();
                setTimeout(() => {
                    window.location.href = '/employees';
                }, 1500);
            } else {
                formMessage.innerHTML = `<div style="color: red; padding: 10px; background: #FEE2E2; border-radius: 8px;">${data.message}</div>`;
            }
        } catch (error) {
            formMessage.innerHTML = `<div style="color: red; padding: 10px; background: #FEE2E2; border-radius: 8px;">An error occurred. Please try again.</div>`;
        } finally {
            submitBtn.disabled = false;
            submitBtn.innerHTML = '<i class="fa-solid fa-save"></i> Register Employee';
        }
    });
}

// Delete Employee func
async function deleteEmployee(employeeId) {
    if (confirm(`Are you sure you want to delete employee ${employeeId}? All associated face encodings will be removed.`)) {
        try {
            const response = await fetch(`/delete_employee/${employeeId}`, {
                method: 'POST'
            });
            const data = await response.json();
            if (data.success) {
                window.location.reload();
            }
        } catch (error) {
            alert('Failed to delete employee.');
        }
    }
}
