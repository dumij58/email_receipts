// Reminder Upload JavaScript
document.addEventListener('DOMContentLoaded', function() {
    const uploadArea = document.getElementById('uploadArea');
    const fileInput = document.getElementById('csv_file');
    const fileName = document.getElementById('fileName');
    const submitBtn = document.getElementById('submitBtn');
    const resetBtn = document.getElementById('resetBtn');
    const csvPreview = document.getElementById('csvPreview');
    const csvTable = document.getElementById('csvTable');
    const csvHeader = document.getElementById('csvHeader');
    const csvBody = document.getElementById('csvBody');
    const recordCount = document.getElementById('recordCount');
    const reminderForm = document.getElementById('reminderForm');

    // Click to upload
    uploadArea.addEventListener('click', () => {
        fileInput.click();
    });

    // Drag and drop
    uploadArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadArea.style.borderColor = '#764ba2';
        uploadArea.style.background = '#f8f9fa';
    });

    uploadArea.addEventListener('dragleave', () => {
        uploadArea.style.borderColor = '#3e1c68';
        uploadArea.style.background = 'transparent';
    });

    uploadArea.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadArea.style.borderColor = '#3e1c68';
        uploadArea.style.background = 'transparent';
        
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            fileInput.files = files;
            handleFileSelect();
        }
    });

    // File selection
    fileInput.addEventListener('change', handleFileSelect);

    // Reset button
    resetBtn.addEventListener('click', () => {
        fileInput.value = '';
        fileName.style.display = 'none';
        submitBtn.disabled = true;
        resetBtn.style.display = 'none';
        csvPreview.style.display = 'none';
        uploadArea.style.display = 'block';
    });

    function handleFileSelect() {
        const file = fileInput.files[0];
        
        if (file) {
            fileName.innerHTML = `<i class="bi bi-file-earmark-check" style="color: #28a745; margin-right: 5px;"></i> ${file.name}`;
            fileName.style.display = 'block';
            
            // Read and preview CSV
            const reader = new FileReader();
            reader.onload = function(e) {
                const text = e.target.result;
                previewCSV(text);
            };
            reader.readAsText(file);
            
            submitBtn.disabled = false;
            resetBtn.style.display = 'inline-block';
            uploadArea.style.display = 'none';
        }
    }

    function previewCSV(csvText) {
        const lines = csvText.trim().split('\n');
        if (lines.length < 2) {
            alert('CSV file is empty or invalid');
            return;
        }

        // Parse header
        const headers = lines[0].split(',').map(h => h.trim());
        
        // Build table header
        let headerHTML = '<tr>';
        headers.forEach(header => {
            headerHTML += `<th>${escapeHtml(header)}</th>`;
        });
        headerHTML += '</tr>';
        csvHeader.innerHTML = headerHTML;

        // Build table body (show first 50 rows)
        let bodyHTML = '';
        const maxRows = Math.min(lines.length - 1, 50);
        for (let i = 1; i <= maxRows; i++) {
            const cells = lines[i].split(',').map(c => c.trim());
            bodyHTML += '<tr>';
            cells.forEach(cell => {
                bodyHTML += `<td title="${escapeHtml(cell)}">${escapeHtml(cell)}</td>`;
            });
            bodyHTML += '</tr>';
        }
        csvBody.innerHTML = bodyHTML;

        // Show record count
        const totalRecords = lines.length - 1;
        const displayedRecords = maxRows;
        recordCount.innerHTML = `<strong>Total Records:</strong> ${totalRecords} ${displayedRecords < totalRecords ? `(showing first ${displayedRecords})` : ''}`;

        // Show preview
        csvPreview.style.display = 'block';
    }

    function escapeHtml(text) {
        const map = {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#039;'
        };
        return String(text).replace(/[&<>"']/g, m => map[m]);
    }

    // Form submission
    reminderForm.addEventListener('submit', function(e) {
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<i class="bi bi-hourglass-split"></i> Sending...';
    });
});
