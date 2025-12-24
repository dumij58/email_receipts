document.addEventListener('DOMContentLoaded', function() {
    const fileInput = document.getElementById('csv_file');
    const fileName = document.getElementById('fileName');
    const submitBtn = document.getElementById('submitBtn');
    const uploadArea = document.getElementById('uploadArea');
    
    console.log('Upload area initialized:', uploadArea);
    
    // Click to upload - simpler approach
    uploadArea.addEventListener('click', function() {
        console.log('Upload area clicked');
        fileInput.click();
    });
    
    // Handle file selection
    fileInput.addEventListener('change', function() {
        console.log('File selected:', this.files);
        if (this.files.length > 0) {
            const file = this.files[0];
            fileName.textContent = '📄 Selected file: ' + file.name;
            fileName.style.display = 'block';
            submitBtn.disabled = false;
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
                    fileName.textContent = '📄 Selected file: ' + files[0].name;
                    fileName.style.display = 'block';
                    submitBtn.disabled = false;
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
