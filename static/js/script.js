// Medical Appointment System - Main JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'))
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl)
    });

    // Auto-hide alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            if (alert.parentNode) {
                alert.style.opacity = '0';
                setTimeout(() => alert.remove(), 300);
            }
        }, 5000);
    });

    // Form validation enhancement
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            const requiredFields = form.querySelectorAll('[required]');
            let valid = true;

            requiredFields.forEach(field => {
                if (!field.value.trim()) {
                    valid = false;
                    field.classList.add('is-invalid');
                    
                    // Add error message
                    if (!field.nextElementSibling || !field.nextElementSibling.classList.contains('invalid-feedback')) {
                        const errorDiv = document.createElement('div');
                        errorDiv.className = 'invalid-feedback';
                        errorDiv.textContent = 'Trường này là bắt buộc';
                        field.parentNode.appendChild(errorDiv);
                    }
                } else {
                    field.classList.remove('is-invalid');
                    const errorDiv = field.nextElementSibling;
                    if (errorDiv && errorDiv.classList.contains('invalid-feedback')) {
                        errorDiv.remove();
                    }
                }
            });

            if (!valid) {
                e.preventDefault();
                showNotification('Vui lòng điền đầy đủ các trường bắt buộc!', 'danger');
            }
        });
    });

    // Phone number formatting
    const phoneInputs = document.querySelectorAll('input[type="tel"]');
    phoneInputs.forEach(input => {
        input.addEventListener('input', function(e) {
            let value = e.target.value.replace(/\D/g, '');
            if (value.length > 10) {
                value = value.slice(0, 10);
            }
            
            // Format phone number
            if (value.length >= 4) {
                value = value.replace(/(\d{4})(\d{3})(\d{3})/, '$1 $2 $3');
            } else if (value.length >= 3) {
                value = value.replace(/(\d{3})/, '$1 ');
            }
            
            e.target.value = value;
        });
    });

    // Date validation - prevent past dates
    const dateInputs = document.querySelectorAll('input[type="date"]');
const today = new Date().toISOString().split('T')[0];
dateInputs.forEach(input => {
    // Skip date of birth fields
    if (input.name === 'date_of_birth' || input.name === 'dob') {
        // For date of birth, set max to today and no min
        input.setAttribute('max', today);
        return;
    }
    
    // For other date fields, set min to today
    input.setAttribute('min', today);
    
    // Add change event to validate date
    input.addEventListener('change', function() {
        if (this.value < today && this.name !== 'date_of_birth' && this.name !== 'dob') {
            this.setCustomValidity('Không thể chọn ngày trong quá khứ');
            this.reportValidity();
        } else {
            this.setCustomValidity('');
        }
    });
});

    // Time validation
    const timeInputs = document.querySelectorAll('input[type="time"]');
    timeInputs.forEach(input => {
        input.addEventListener('change', function() {
            const time = this.value;
            if (time) {
                const [hours, minutes] = time.split(':').map(Number);
                if (hours < 7 || hours > 18) {
                    this.setCustomValidity('Thời gian làm việc từ 7:00 đến 18:00');
                    this.reportValidity();
                } else {
                    this.setCustomValidity('');
                }
            }
        });
    });

    // Auto-format patient information when selecting from dropdown
    const patientSelects = document.querySelectorAll('select[name="patient_id"]');
    patientSelects.forEach(select => {
        select.addEventListener('change', function() {
            const selectedOption = this.options[this.selectedIndex];
            if (selectedOption.value && selectedOption.value !== 'new') {
                const phone = selectedOption.getAttribute('data-phone');
                const email = selectedOption.getAttribute('data-email');
                
                // You can auto-fill related fields here if needed
                console.log('Selected patient:', { phone, email });
            }
        });
    });
});

// Utility function to show loading state
function showLoading(button) {
    const originalText = button.innerHTML;
    button.innerHTML = '<span class="loading me-2"></span> Đang xử lý...';
    button.disabled = true;
    return originalText;
}

function hideLoading(button, originalText) {
    button.innerHTML = originalText;
    button.disabled = false;
}

// Utility function for API calls
async function makeApiCall(url, options = {}) {
    try {
        const response = await fetch(url, {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        });
        
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        
        return await response.json();
    } catch (error) {
        console.error('API call failed:', error);
        throw error;
    }
}

// Notification system
function showNotification(message, type = 'info') {
    // Remove existing notifications
    const existingNotifications = document.querySelectorAll('.custom-notification');
    existingNotifications.forEach(notification => notification.remove());

    const notification = document.createElement('div');
    notification.className = `custom-notification alert alert-${type} alert-dismissible fade show`;
    notification.innerHTML = `
        <i class="fas fa-${type === 'success' ? 'check-circle' : type === 'danger' ? 'exclamation-circle' : 'info-circle'} me-2"></i>
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        z-index: 9999;
        min-width: 300px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    `;
    
    document.body.appendChild(notification);
    
    // Auto remove after 5 seconds
    setTimeout(() => {
        if (notification.parentNode) {
            notification.remove();
        }
    }, 5000);
}

// Form data serialization
function serializeForm(form) {
    const formData = new FormData(form);
    const data = {};
    for (let [key, value] of formData.entries()) {
        data[key] = value;
    }
    return data;
}

// Date formatting utilities
function formatDate(dateString) {
    if (!dateString) return '';
    const date = new Date(dateString);
    return date.toLocaleDateString('vi-VN');
}

function formatTime(timeString) {
    if (!timeString) return '';
    return timeString.substring(0, 5); // Remove seconds if present
}

// Export functions for global use
window.MedicalAppointment = {
    showLoading,
    hideLoading,
    makeApiCall,
    showNotification,
    serializeForm,
    formatDate,
    formatTime
};

// Keyboard shortcuts
document.addEventListener('keydown', function(e) {
    // Ctrl + / for search focus
    if (e.ctrlKey && e.key === '/') {
        e.preventDefault();
        const searchInput = document.querySelector('input[type="search"], input[placeholder*="tìm"]');
        if (searchInput) {
            searchInput.focus();
        }
    }
    
    // Escape key to close modals
    if (e.key === 'Escape') {
        const openModal = document.querySelector('.modal.show');
        if (openModal) {
            const modal = bootstrap.Modal.getInstance(openModal);
            if (modal) {
                modal.hide();
            }
        }
    }
});

// Print functionality
function printElement(elementId) {
    const element = document.getElementById(elementId);
    if (element) {
        const printWindow = window.open('', '_blank');
        printWindow.document.write(`
            <html>
                <head>
                    <title>In ${document.title}</title>
                    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
                    <style>
                        body { font-family: Arial, sans-serif; }
                        @media print {
                            .no-print { display: none !important; }
                        }
                    </style>
                </head>
                <body>
                    ${element.innerHTML}
                    <script>
                        window.onload = function() {
                            window.print();
                            setTimeout(() => window.close(), 500);
                        }
                    <\/script>
                </body>
            </html>
        `);
        printWindow.document.close();
    }
}