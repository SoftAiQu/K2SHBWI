// K2SHBWI Demo - Main JavaScript File

document.addEventListener('DOMContentLoaded', function() {
    console.log('K2SHBWI Demo loaded');
    initializeEventListeners();
    loadDemoData();
});

// ============================================
// Event Listeners & Initialization
// ============================================

function initializeEventListeners() {
    // Mobile menu toggle
    const navToggle = document.querySelector('.navbar-toggler');
    if (navToggle) {
        navToggle.addEventListener('click', function() {
            const navMenu = document.querySelector('.navbar-collapse');
            navMenu.classList.toggle('show');
        });
    }

    // Smooth scroll for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            const href = this.getAttribute('href');
            if (href !== '#') {
                e.preventDefault();
                const element = document.querySelector(href);
                if (element) {
                    element.scrollIntoView({ behavior: 'smooth' });
                }
            }
        });
    });
}

// ============================================
// API Calls & Data Management
// ============================================

async function loadDemoData() {
    try {
        // Load algorithm comparison data
        const comparisonResponse = await fetch('/api/algorithm-comparison');
        if (comparisonResponse.ok) {
            const data = await comparisonResponse.json();
            console.log('Algorithm comparison loaded:', data);
        }

        // Load demo metrics
        const metricsResponse = await fetch('/api/demo-metrics');
        if (metricsResponse.ok) {
            const data = await metricsResponse.json();
            console.log('Demo metrics loaded:', data);
        }
    } catch (error) {
        console.error('Error loading demo data:', error);
    }
}

// ============================================
// Image Upload & Processing
// ============================================

function handleImageUpload(file) {
    if (!file) return;

    // Validate file type
    const validTypes = ['image/jpeg', 'image/png', 'image/webp', 'image/gif'];
    if (!validTypes.includes(file.type)) {
        showError('Please upload a valid image file (JPEG, PNG, WebP, GIF)');
        return;
    }

    // Validate file size (max 50MB)
    if (file.size > 50 * 1024 * 1024) {
        showError('File size exceeds 50MB limit');
        return;
    }

    uploadFile(file);
}

async function uploadFile(file) {
    const formData = new FormData();
    formData.append('file', file);

    try {
        showLoading('Processing image...');

        const response = await fetch('/api/upload-image', {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            throw new Error('Upload failed');
        }

        const result = await response.json();

        if (result.success) {
            handleUploadSuccess(result);
        } else {
            showError(result.error || 'Upload failed');
        }
    } catch (error) {
        console.error('Upload error:', error);
        showError('Error uploading file: ' + error.message);
    } finally {
        hideLoading();
    }
}

function handleUploadSuccess(result) {
    console.log('Upload successful:', result);

    // Update UI with results
    updateResultsUI(result);

    // Show notification
    showSuccess('Image compressed successfully!');

    // Trigger download option
    enableDownload(result.compressed.filename);
}

// ============================================
// UI Updates
// ============================================

function updateResultsUI(result) {
    const metrics = result.metrics;

    // Update metrics display
    updateMetric('compressionRatio', metrics.compression_ratio + '%');
    updateMetric('qualityPreserved', metrics.quality_preserved.toFixed(1) + '%');
    updateMetric('processingTime', metrics.processing_time.toFixed(3) + 's');
    updateMetric('psnrScore', metrics.psnr.toFixed(2) + ' dB');

    // Update images
    const originalImg = document.getElementById('originalImg');
    const compressedImg = document.getElementById('compressedImg');

    if (originalImg && result.original.base64) {
        originalImg.src = 'data:image/jpeg;base64,' + result.original.base64;
    }

    if (compressedImg && result.compressed.base64) {
        compressedImg.src = 'data:image/jpeg;base64,' + result.compressed.base64;
    }

    // Show results section
    const resultsSection = document.getElementById('resultsSection');
    if (resultsSection) {
        resultsSection.classList.remove('d-none');
    }
}

function updateMetric(elementId, value) {
    const element = document.getElementById(elementId);
    if (element) {
        element.textContent = value;
    }
}

// ============================================
// Notifications
// ============================================

function showError(message) {
    showNotification(message, 'danger');
}

function showSuccess(message) {
    showNotification(message, 'success');
}

function showNotification(message, type = 'info') {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `alert alert-${type} alert-dismissible fade show`;
    notification.setAttribute('role', 'alert');

    const icons = {
        'success': '<i class="fas fa-check-circle"></i>',
        'danger': '<i class="fas fa-exclamation-circle"></i>',
        'info': '<i class="fas fa-info-circle"></i>',
        'warning': '<i class="fas fa-exclamation-triangle"></i>'
    };

    notification.innerHTML = `
        ${icons[type] || ''}
        <strong>${message}</strong>
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;

    // Add to page
    const container = document.querySelector('body');
    container.insertBefore(notification, container.firstChild);

    // Add padding for notification
    notification.style.position = 'fixed';
    notification.style.top = '20px';
    notification.style.right = '20px';
    notification.style.zIndex = '9999';
    notification.style.minWidth = '300px';

    // Auto-dismiss after 5 seconds
    setTimeout(() => {
        notification.remove();
    }, 5000);
}

function showLoading(message = 'Loading...') {
    const loadingDiv = document.createElement('div');
    loadingDiv.id = 'loadingIndicator';
    loadingDiv.className = 'position-fixed top-0 start-0 w-100 h-100 d-flex align-items-center justify-content-center';
    loadingDiv.style.backgroundColor = 'rgba(0, 0, 0, 0.5)';
    loadingDiv.style.zIndex = '9998';
    loadingDiv.innerHTML = `
        <div class="text-center text-white">
            <div class="spinner-border mb-3" role="status">
                <span class="visually-hidden">Loading...</span>
            </div>
            <p>${message}</p>
        </div>
    `;
    document.body.appendChild(loadingDiv);
}

function hideLoading() {
    const loadingDiv = document.getElementById('loadingIndicator');
    if (loadingDiv) {
        loadingDiv.remove();
    }
}

// ============================================
// File Download
// ============================================

function enableDownload(filename) {
    const downloadBtn = document.getElementById('downloadBtn');
    if (downloadBtn) {
        downloadBtn.onclick = function() {
            downloadFile('/api/download/' + filename);
        };
    }
}

function downloadFile(url) {
    const a = document.createElement('a');
    a.href = url;
    a.download = true;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
}

// ============================================
// Chart Utilities
// ============================================

function createBarChart(elementId, labels, data, title) {
    if (typeof Plotly === 'undefined') {
        console.error('Plotly not loaded');
        return;
    }

    const trace = {
        x: labels,
        y: data,
        type: 'bar',
        marker: {
            color: '#0d6efd'
        }
    };

    const layout = {
        title: title,
        xaxis: { title: 'Categories' },
        yaxis: { title: 'Values' },
        margin: { b: 100 }
    };

    Plotly.newPlot(elementId, [trace], layout, { responsive: true });
}

function createScatterChart(elementId, xData, yData, labels, title) {
    if (typeof Plotly === 'undefined') {
        console.error('Plotly not loaded');
        return;
    }

    const trace = {
        x: xData,
        y: yData,
        mode: 'markers+text',
        text: labels,
        textposition: 'top center',
        marker: {
            size: 12,
            color: xData,
            colorscale: 'Viridis',
            showscale: true
        }
    };

    const layout = {
        title: title,
        xaxis: { title: 'X Axis' },
        yaxis: { title: 'Y Axis' },
        hovermode: 'closest'
    };

    Plotly.newPlot(elementId, [trace], layout, { responsive: true });
}

function createHeatmap(elementId, z, x, y, title) {
    if (typeof Plotly === 'undefined') {
        console.error('Plotly not loaded');
        return;
    }

    const trace = {
        z: z,
        x: x,
        y: y,
        type: 'heatmap',
        colorscale: 'Viridis'
    };

    const layout = {
        title: title,
        margin: { b: 100, l: 100 }
    };

    Plotly.newPlot(elementId, [trace], layout, { responsive: true });
}

// ============================================
// Utility Functions
// ============================================

function formatBytes(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

function formatNumber(num) {
    return num.toLocaleString('en-US', { maximumFractionDigits: 2 });
}

function getCurrentDate() {
    return new Date().toISOString().split('T')[0];
}

// ============================================
// Debugging & Development
// ============================================

function debugLog(message, data) {
    if (typeof console !== 'undefined') {
        console.log(`[K2SHBWI] ${message}`, data || '');
    }
}

// Export functions for use in templates
window.K2SHBWI = {
    uploadFile,
    handleImageUpload,
    downloadFile,
    showNotification,
    showError,
    showSuccess,
    createBarChart,
    createScatterChart,
    createHeatmap,
    formatBytes,
    formatNumber,
    debugLog
};
