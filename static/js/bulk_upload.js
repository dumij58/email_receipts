document.addEventListener('DOMContentLoaded', function() {
    const fileInput = document.getElementById('csv_file');
    const fileName = document.getElementById('fileName');
    const submitBtn = document.getElementById('submitBtn');
    const uploadArea = document.getElementById('uploadArea');
    const csvPreview = document.getElementById('csvPreview');
    const resetBtn = document.getElementById('resetBtn');
    const csvTable = document.getElementById('csvTable');
    const csvHeader = document.getElementById('csvHeader');
    const csvBody = document.getElementById('csvBody');
    const recordCount = document.getElementById('recordCount');
    
    console.log('Upload area initialized:', uploadArea);
    
    // Click to upload - simpler approach
    uploadArea.addEventListener('click', function() {
        console.log('Upload area clicked');
        fileInput.click();
    });
    
    // Reset functionality
    resetBtn.addEventListener('click', function() {
        fileInput.value = '';
        fileName.style.display = 'none';
        csvPreview.style.display = 'none';
        uploadArea.style.display = 'block';
        resetBtn.style.display = 'none';
        submitBtn.disabled = true;
        csvHeader.innerHTML = '';
        csvBody.innerHTML = '';
    });
    
    // Parse and display CSV
    function parseAndDisplayCSV(file) {
        const reader = new FileReader();
        reader.onload = function(e) {
            const text = e.target.result;
            const lines = text.trim().split('\n');
            
            if (lines.length < 2) {
                alert('CSV file appears to be empty or invalid');
                return;
            }
            
            // Parse header
            const headers = lines[0].split(',').map(h => h.trim());
            
            // Parse data rows (show first 50 rows or all if less)
            const maxRows = Math.min(lines.length - 1, 50);
            const rows = [];
            for (let i = 1; i <= maxRows; i++) {
                const values = parseCSVLine(lines[i]);
                rows.push(values);
            }
            
            // Display in table
            displayCSVTable(headers, rows, lines.length - 1);
            
            // Hide upload area and show preview
            uploadArea.style.display = 'none';
            csvPreview.style.display = 'block';
            resetBtn.style.display = 'inline-block';
            submitBtn.disabled = false;
        };
        reader.readAsText(file);
    }
    
    // Parse a CSV line handling quoted values
    function parseCSVLine(line) {
        const result = [];
        let current = '';
        let inQuotes = false;
        
        for (let i = 0; i < line.length; i++) {
            const char = line[i];
            
            if (char === '"') {
                inQuotes = !inQuotes;
            } else if (char === ',' && !inQuotes) {
                result.push(current.trim());
                current = '';
            } else {
                current += char;
            }
        }
        result.push(current.trim());
        
        return result;
    }
    
    // Display CSV data in table
    function displayCSVTable(headers, rows, totalRows) {
        // Create header
        const headerRow = document.createElement('tr');
        headers.forEach(header => {
            const th = document.createElement('th');
            th.textContent = header;
            headerRow.appendChild(th);
        });
        csvHeader.innerHTML = '';
        csvHeader.appendChild(headerRow);
        
        // Create body rows
        csvBody.innerHTML = '';
        rows.forEach(row => {
            const tr = document.createElement('tr');
            row.forEach((cell, index) => {
                const td = document.createElement('td');
                // Truncate long text with ellipsis
                if (cell.length > 50) {
                    td.textContent = cell.substring(0, 47) + '...';
                    td.title = cell; // Show full text on hover
                } else {
                    td.textContent = cell;
                }
                tr.appendChild(td);
            });
            csvBody.appendChild(tr);
        });
        
        // Update record count
        const showing = rows.length;
        if (totalRows > 50) {
            recordCount.innerHTML = `<strong>${totalRows}</strong> records found. Showing first <strong>${showing}</strong> rows.`;
        } else {
            recordCount.innerHTML = `<strong>${totalRows}</strong> record${totalRows !== 1 ? 's' : ''} found.`;
        }
    }
    
    // Handle file selection
    fileInput.addEventListener('change', function() {
        console.log('File selected:', this.files);
        if (this.files.length > 0) {
            const file = this.files[0];
            fileName.textContent = '📄 Selected file: ' + file.name;
            fileName.style.display = 'block';
            parseAndDisplayCSV(file);
            console.log('File info displayed:', file.name);
        }
    });
    
    // Drag and drop functionality
    uploadArea.addEventListener('dragover', function(e) {
        e.preventDefault();
        e.stopPropagation();
        this.style.borderColor = '#764ba2';
        this.style.background = '#f8f9fa';
    });
    
    uploadArea.addEventListener('dragleave', function(e) {
        e.preventDefault();
        e.stopPropagation();
        this.style.borderColor = '#3e1c68';
        this.style.background = 'transparent';
    });
    
    uploadArea.addEventListener('drop', function(e) {
        e.preventDefault();
        e.stopPropagation();
        this.style.borderColor = '#3e1c68';
        this.style.background = 'transparent';
        
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            if (files[0].name.endsWith('.csv')) {
                // Manually set the file and display info
                try {
                    fileInput.files = e.dataTransfer.files;
                    const file = files[0];
                    fileName.textContent = '📄 Selected file: ' + file.name;
                    fileName.style.display = 'block';
                    parseAndDisplayCSV(file);
                } catch (err) {
                    console.error('Error setting files:', err);
                    alert('Please click to upload instead of drag and drop');
                }
            } else {
                alert('Please upload a CSV file');
            }
        }
    });
});
