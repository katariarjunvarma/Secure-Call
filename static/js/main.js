/**
 * Main JavaScript file for SecureOS System Call Interface
 */

// Wait for the DOM to be fully loaded
document.addEventListener('DOMContentLoaded', function() {
    
    // Initialize tooltips
    const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]');
    if (tooltipTriggerList.length > 0) {
        [...tooltipTriggerList].map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl));
    }
    
    // Initialize popovers
    const popoverTriggerList = document.querySelectorAll('[data-bs-toggle="popover"]');
    if (popoverTriggerList.length > 0) {
        [...popoverTriggerList].map(popoverTriggerEl => new bootstrap.Popover(popoverTriggerEl));
    }
    
    // Auto-dismiss alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
    alerts.forEach(alert => {
        setTimeout(() => {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });
    
    // Handle command examples in execute.html
    const commandExamples = document.querySelectorAll('.command-example');
    if (commandExamples.length > 0) {
        commandExamples.forEach(button => {
            button.addEventListener('click', function() {
                const command = this.getAttribute('data-command');
                document.getElementById('command').value = command;
                // Focus the command input
                document.getElementById('command').focus();
            });
        });
    }
    
    // Log search functionality
    const logSearch = document.getElementById('logSearch');
    if (logSearch) {
        logSearch.addEventListener('keyup', function() {
            const searchValue = this.value.toLowerCase();
            const table = document.getElementById('logsTable');
            if (table) {
                const rows = table.querySelectorAll('tbody tr');
                rows.forEach(row => {
                    const text = row.textContent.toLowerCase();
                    row.style.display = text.includes(searchValue) ? '' : 'none';
                });
            }
        });
    }
    
    // Status filter functionality
    const statusFilter = document.getElementById('statusFilter');
    if (statusFilter) {
        statusFilter.addEventListener('change', function() {
            const filterValue = this.value;
            const table = document.getElementById('logsTable');
            if (table) {
                const rows = table.querySelectorAll('tbody tr');
                rows.forEach(row => {
                    if (!filterValue || row.getAttribute('data-status') === filterValue) {
                        row.style.display = '';
                    } else {
                        row.style.display = 'none';
                    }
                });
            }
        });
    }
    
    // Time filter functionality
    const timeFilter = document.getElementById('timeFilter');
    if (timeFilter) {
        timeFilter.addEventListener('change', function() {
            const filterValue = this.value;
            
            // This could be enhanced with actual date filtering logic
            // For now, we'll just use it as an indicator that would be
            // implemented with server-side filtering
            
            // Redirect to logs endpoint with filter param
            if (filterValue !== 'all') {
                window.location.href = `/system/logs?time_filter=${filterValue}`;
            } else {
                window.location.href = '/system/logs';
            }
        });
    }
    
    // Output modal functionality
    const outputModal = document.getElementById('outputModal');
    if (outputModal) {
        outputModal.addEventListener('show.bs.modal', function(event) {
            const button = event.relatedTarget;
            const output = button.getAttribute('data-output');
            const command = button.getAttribute('data-command');
            document.getElementById('modalOutput').textContent = output;
            document.getElementById('modalCommand').textContent = command;
        });
    }
    
    // Copy to clipboard functionality for command outputs
    const copyButtons = document.querySelectorAll('.copy-output');
    if (copyButtons.length > 0) {
        copyButtons.forEach(button => {
            button.addEventListener('click', function() {
                const textToCopy = this.getAttribute('data-output');
                navigator.clipboard.writeText(textToCopy).then(() => {
                    // Show success tooltip
                    const originalTitle = this.getAttribute('title');
                    this.setAttribute('title', 'Copied!');
                    bootstrap.Tooltip.getInstance(this).show();
                    
                    // Reset after 2 seconds
                    setTimeout(() => {
                        this.setAttribute('title', originalTitle);
                        bootstrap.Tooltip.getInstance(this).hide();
                    }, 2000);
                }).catch(err => {
                    console.error('Failed to copy: ', err);
                });
            });
        });
    }
});
