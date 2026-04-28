/**
 * FamiliDocs — Liquid Glass UI
 * Animations, interactions & utilities
 */

document.addEventListener('DOMContentLoaded', function() {
    initTooltips();
    initAlertAutoDismiss();
    initDeleteConfirmations();
    initFileUploadPreview();
    initFormValidation();
    initUploadProgress();
    initSessionWarning();
    initKeyboardShortcuts();
    initScrollReveal();
    initCardHoverEffects();
    initSmoothTransitions();
    initCountUp();
});

/**
 * Bootstrap tooltips
 */
function initTooltips() {
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (el) {
        return new bootstrap.Tooltip(el);
    });
}

/**
 * Auto-dismiss alerts with fade out
 */
function initAlertAutoDismiss() {
    var alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
    alerts.forEach(function(alert) {
        setTimeout(function() {
            alert.style.transition = 'opacity 0.4s ease, transform 0.4s ease';
            alert.style.opacity = '0';
            alert.style.transform = 'translateY(-8px) scale(0.98)';
            setTimeout(function() {
                var bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
                bsAlert.close();
            }, 400);
        }, 4500);
    });
}

/**
 * Delete confirmations with custom styling
 */
function initDeleteConfirmations() {
    var deleteButtons = document.querySelectorAll('[data-confirm-delete]');
    deleteButtons.forEach(function(button) {
        button.addEventListener('click', function(e) {
            var message = this.getAttribute('data-confirm-delete') || 'Etes-vous sur de vouloir supprimer cet element ?';
            if (!confirm(message)) {
                e.preventDefault();
                return false;
            }
        });
    });
}

/**
 * File upload preview
 */
function initFileUploadPreview() {
    var fileInputs = document.querySelectorAll('input[type="file"]');
    fileInputs.forEach(function(input) {
        input.addEventListener('change', function() {
            var fileName = this.files[0] ? this.files[0].name : 'Aucun fichier selectionne';
            var nameInput = document.getElementById('name');

            if (nameInput && !nameInput.value) {
                var fileNameWithoutExt = fileName.replace(/\.[^/.]+$/, '');
                nameInput.value = fileNameWithoutExt;
            }

            var label = this.nextElementSibling;
            if (label && label.classList.contains('custom-file-label')) {
                label.textContent = fileName;
            }
        });
    });
}

/**
 * Form validation
 */
function initFormValidation() {
    var forms = document.querySelectorAll('form.needs-validation');
    forms.forEach(function(form) {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        }, false);
    });
}

/**
 * Scroll reveal — fade in elements as they enter viewport
 */
function initScrollReveal() {
    if (typeof IntersectionObserver === 'undefined') return;

    var observer = new IntersectionObserver(function(entries) {
        entries.forEach(function(entry) {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
                observer.unobserve(entry.target);
            }
        });
    }, {
        threshold: 0.08,
        rootMargin: '0px 0px -30px 0px'
    });

    // Observe cards, stat-cards, accordion items
    var elements = document.querySelectorAll('.card, .stat-card, .accordion-item');
    elements.forEach(function(el, i) {
        el.style.opacity = '0';
        el.style.transform = 'translateY(16px)';
        el.style.transition = 'opacity 0.5s cubic-bezier(0.16, 1, 0.3, 1) ' + (i * 0.06) + 's, transform 0.5s cubic-bezier(0.16, 1, 0.3, 1) ' + (i * 0.06) + 's';
        observer.observe(el);
    });
}

/**
 * Enhanced card hover — subtle glass shimmer
 */
function initCardHoverEffects() {
    var cards = document.querySelectorAll('.stat-card');
    cards.forEach(function(card) {
        card.addEventListener('mouseenter', function() {
            this.style.willChange = 'transform, box-shadow';
        });
        card.addEventListener('mouseleave', function() {
            this.style.willChange = 'auto';
        });
    });
}

/**
 * Smooth page transitions for internal links
 */
function initSmoothTransitions() {
    // Add subtle press feedback to all buttons
    var buttons = document.querySelectorAll('.btn');
    buttons.forEach(function(btn) {
        btn.addEventListener('mousedown', function() {
            this.style.transform = 'scale(0.96)';
        });
        btn.addEventListener('mouseup', function() {
            this.style.transform = '';
        });
        btn.addEventListener('mouseleave', function() {
            this.style.transform = '';
        });
    });
}

/**
 * Show notification toast
 */
function showNotification(message, type) {
    type = type || 'info';
    var alertDiv = document.createElement('div');
    alertDiv.className = 'alert alert-' + type + ' alert-dismissible fade show';
    alertDiv.setAttribute('role', 'alert');
    alertDiv.innerHTML = message +
        '<button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>';

    var container = document.querySelector('.flash-container') || document.querySelector('.main-content');
    if (container) {
        container.insertBefore(alertDiv, container.firstChild);
        setTimeout(function() {
            alertDiv.style.transition = 'opacity 0.4s ease, transform 0.4s ease';
            alertDiv.style.opacity = '0';
            alertDiv.style.transform = 'translateY(-8px)';
            setTimeout(function() {
                var bsAlert = bootstrap.Alert.getOrCreateInstance(alertDiv);
                bsAlert.close();
            }, 400);
        }, 4500);
    }
}

/**
 * Copy to clipboard
 */
function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(function() {
        showNotification('Copie dans le presse-papier !', 'success');
    }).catch(function(err) {
        console.error('Erreur lors de la copie:', err);
        showNotification('Erreur lors de la copie', 'danger');
    });
}

/**
 * Format date
 */
function formatDate(date) {
    var d = new Date(date);
    var day = String(d.getDate()).padStart(2, '0');
    var month = String(d.getMonth() + 1).padStart(2, '0');
    var year = d.getFullYear();
    return day + '/' + month + '/' + year;
}

/**
 * Format file size
 */
function formatFileSize(bytes) {
    if (bytes === 0) return '0 o';
    var k = 1024;
    var sizes = ['o', 'Ko', 'Mo', 'Go'];
    var i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
}

/**
 * Password strength check
 */
function checkPasswordStrength(password) {
    var strength = 0;
    if (password.length >= 8) strength++;
    if (password.match(/[a-z]/)) strength++;
    if (password.match(/[A-Z]/)) strength++;
    if (password.match(/[0-9]/)) strength++;
    if (password.match(/[^a-zA-Z0-9]/)) strength++;
    return strength;
}

/**
 * Bulk selection for documents
 */
function toggleBulkSelect(checkbox) {
    var bar = document.getElementById('bulkActionBar');
    var countSpan = document.getElementById('bulkCount');
    var checked = document.querySelectorAll('.bulk-check:checked');
    if (bar) {
        bar.style.display = checked.length > 0 ? 'block' : 'none';
        if (countSpan) countSpan.textContent = checked.length;
    }
}

function selectAllDocs(master) {
    var checkboxes = document.querySelectorAll('.bulk-check');
    checkboxes.forEach(function(cb) { cb.checked = master.checked; });
    toggleBulkSelect(master);
}

function submitBulk(action) {
    if (!confirm('Confirmer cette operation sur les documents selectionnes ?')) return;
    var form = document.getElementById('bulkForm');
    document.getElementById('bulkActionType').value = action;
    var container = document.getElementById('bulkIds');
    container.innerHTML = '';
    document.querySelectorAll('.bulk-check:checked').forEach(function(cb) {
        var input = document.createElement('input');
        input.type = 'hidden'; input.name = 'doc_ids'; input.value = cb.value;
        container.appendChild(input);
    });
    form.submit();
}

function clearBulk() {
    document.querySelectorAll('.bulk-check').forEach(function(cb) { cb.checked = false; });
    var master = document.getElementById('selectAll');
    if (master) master.checked = false;
    toggleBulkSelect(null);
}

/**
 * Upload progress bar
 */
function initUploadProgress() {
    var uploadForms = document.querySelectorAll('form[enctype="multipart/form-data"]');
    uploadForms.forEach(function(form) {
        form.addEventListener('submit', function(e) {
            var fileInput = form.querySelector('input[type="file"]');
            if (!fileInput || !fileInput.files.length) return;

            e.preventDefault();
            var formData = new FormData(form);

            var progressWrap = document.createElement('div');
            progressWrap.className = 'progress mt-3';
            progressWrap.style.height = '8px';
            progressWrap.innerHTML = '<div class="progress-bar" role="progressbar" style="width: 0%"></div>';
            form.appendChild(progressWrap);
            var progressBar = progressWrap.querySelector('.progress-bar');

            var submitBtn = form.querySelector('button[type="submit"]');
            if (submitBtn) {
                submitBtn.disabled = true;
                submitBtn.style.opacity = '0.6';
            }

            var xhr = new XMLHttpRequest();
            xhr.open('POST', form.action, true);

            xhr.upload.onprogress = function(e) {
                if (e.lengthComputable) {
                    var pct = Math.round((e.loaded / e.total) * 100);
                    progressBar.style.width = pct + '%';
                }
            };

            xhr.onload = function() {
                if (xhr.status >= 200 && xhr.status < 400) {
                    progressBar.style.background = 'linear-gradient(90deg, var(--color-success), #28b34c)';
                    setTimeout(function() {
                        if (xhr.responseURL) {
                            window.location.href = xhr.responseURL;
                        } else {
                            window.location.reload();
                        }
                    }, 300);
                } else {
                    progressBar.style.background = 'var(--color-danger)';
                    if (submitBtn) {
                        submitBtn.disabled = false;
                        submitBtn.style.opacity = '';
                    }
                }
            };

            xhr.onerror = function() {
                progressBar.style.background = 'var(--color-danger)';
                if (submitBtn) {
                    submitBtn.disabled = false;
                    submitBtn.style.opacity = '';
                }
            };

            var csrfMeta = document.querySelector('meta[name="csrf-token"]');
            if (csrfMeta) {
                xhr.setRequestHeader('X-CSRFToken', csrfMeta.getAttribute('content'));
            }

            xhr.send(formData);
        });
    });
}

/**
 * Session expiry warning
 */
function initSessionWarning() {
    if (!document.querySelector('.sidebar')) return;

    var SESSION_DURATION = 120 * 60 * 1000;
    var WARNING_BEFORE = 5 * 60 * 1000;

    setTimeout(function() {
        showNotification(
            '<i class="bi bi-clock me-2"></i><strong>Session bientot expiree</strong><br>Votre session expire dans 5 minutes.',
            'warning'
        );
    }, SESSION_DURATION - WARNING_BEFORE);
}

/**
 * Keyboard shortcuts
 */
function initKeyboardShortcuts() {
    document.addEventListener('keydown', function(e) {
        if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
            e.preventDefault();
            var searchInput = document.getElementById('quickSearchInput');
            if (searchInput) searchInput.focus();
        }
        if (e.key === 'Escape') {
            var openModals = document.querySelectorAll('.modal.show');
            openModals.forEach(function(modal) {
                var bsModal = bootstrap.Modal.getInstance(modal);
                if (bsModal) bsModal.hide();
            });
        }
    });
}

/**
 * Count-up animation for stat card values
 */
function initCountUp() {
    var values = document.querySelectorAll('.stat-card-value');
    if (!values.length) return;

    var observer = new IntersectionObserver(function(entries) {
        entries.forEach(function(entry) {
            if (entry.isIntersecting) {
                var el = entry.target;
                var target = parseInt(el.textContent, 10);
                if (isNaN(target) || target === 0) return;
                observer.unobserve(el);

                var start = 0;
                var duration = 600;
                var startTime = null;

                function animate(ts) {
                    if (!startTime) startTime = ts;
                    var progress = Math.min((ts - startTime) / duration, 1);
                    // ease-out
                    var ease = 1 - Math.pow(1 - progress, 3);
                    el.textContent = Math.round(start + (target - start) * ease);
                    if (progress < 1) requestAnimationFrame(animate);
                }
                requestAnimationFrame(animate);
            }
        });
    }, { threshold: 0.3 });

    values.forEach(function(el) { observer.observe(el); });
}

/**
 * Password strength indicator
 */
function showPasswordStrength(inputId, indicatorId) {
    var input = document.getElementById(inputId);
    var indicator = document.getElementById(indicatorId);

    if (input && indicator) {
        input.addEventListener('input', function() {
            var strength = checkPasswordStrength(this.value);
            var colors = ['danger', 'warning', 'warning', 'info', 'success'];
            var labels = ['Tres faible', 'Faible', 'Moyen', 'Bon', 'Excellent'];

            indicator.className = 'badge bg-' + colors[strength - 1];
            indicator.textContent = labels[strength - 1] || '';
        });
    }
}
