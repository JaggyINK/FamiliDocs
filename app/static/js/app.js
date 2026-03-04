/**
 * FamiliDocs - JavaScript principal
 * Coffre Administratif Numerique Familial
 */

// Attendre que le DOM soit charge
document.addEventListener('DOMContentLoaded', function() {
    // Initialisation des tooltips Bootstrap
    initTooltips();

    // Auto-dismiss des alertes
    initAlertAutoDismiss();

    // Confirmation de suppression
    initDeleteConfirmations();

    // Preview du nom de fichier lors de l'upload
    initFileUploadPreview();

    // Validation des formulaires
    initFormValidation();

    // T18 - Progress bar upload
    initUploadProgress();

    // T20 - Session expiry warning
    initSessionWarning();

    // T34 - Raccourcis clavier
    initKeyboardShortcuts();
});

/**
 * Initialise les tooltips Bootstrap
 */
function initTooltips() {
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

/**
 * Auto-dismiss des alertes apres 5 secondes
 */
function initAlertAutoDismiss() {
    var alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
    alerts.forEach(function(alert) {
        setTimeout(function() {
            var bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });
}

/**
 * Confirmation avant suppression
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
 * Preview du nom de fichier lors de l'upload
 */
function initFileUploadPreview() {
    var fileInputs = document.querySelectorAll('input[type="file"]');
    fileInputs.forEach(function(input) {
        input.addEventListener('change', function() {
            var fileName = this.files[0] ? this.files[0].name : 'Aucun fichier selectionne';
            var nameInput = document.getElementById('name');

            // Si le champ nom est vide, le remplir avec le nom du fichier (sans extension)
            if (nameInput && !nameInput.value) {
                var fileNameWithoutExt = fileName.replace(/\.[^/.]+$/, '');
                nameInput.value = fileNameWithoutExt;
            }

            // Afficher le nom du fichier
            var label = this.nextElementSibling;
            if (label && label.classList.contains('custom-file-label')) {
                label.textContent = fileName;
            }
        });
    });
}

/**
 * Validation des formulaires
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
 * Fonction utilitaire pour afficher une notification
 */
function showNotification(message, type) {
    type = type || 'info';
    var alertDiv = document.createElement('div');
    alertDiv.className = 'alert alert-' + type + ' alert-dismissible fade show';
    alertDiv.setAttribute('role', 'alert');
    alertDiv.innerHTML = message +
        '<button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>';

    var container = document.querySelector('.flash-container') || document.querySelector('.main-content') || document.querySelector('.container');
    if (container) {
        container.insertBefore(alertDiv, container.firstChild);

        // Auto-dismiss apres 5 secondes
        setTimeout(function() {
            var bsAlert = new bootstrap.Alert(alertDiv);
            bsAlert.close();
        }, 5000);
    }
}

/**
 * Fonction pour copier du texte dans le presse-papier
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
 * Fonction pour formater une date
 */
function formatDate(date) {
    var d = new Date(date);
    var day = String(d.getDate()).padStart(2, '0');
    var month = String(d.getMonth() + 1).padStart(2, '0');
    var year = d.getFullYear();
    return day + '/' + month + '/' + year;
}

/**
 * Fonction pour formater la taille d'un fichier
 */
function formatFileSize(bytes) {
    if (bytes === 0) return '0 o';
    var k = 1024;
    var sizes = ['o', 'Ko', 'Mo', 'Go'];
    var i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
}

/**
 * Verification de la force du mot de passe
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
 * T17 - Bulk selection pour documents
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
 * T18 - Progress bar pour upload de fichiers
 */
function initUploadProgress() {
    var uploadForms = document.querySelectorAll('form[enctype="multipart/form-data"]');
    uploadForms.forEach(function(form) {
        form.addEventListener('submit', function(e) {
            var fileInput = form.querySelector('input[type="file"]');
            if (!fileInput || !fileInput.files.length) return;

            e.preventDefault();
            var formData = new FormData(form);

            // Creer la barre de progression
            var progressWrap = document.createElement('div');
            progressWrap.className = 'progress mt-3';
            progressWrap.innerHTML = '<div class="progress-bar progress-bar-striped progress-bar-animated" role="progressbar" style="width: 0%">0%</div>';
            form.appendChild(progressWrap);
            var progressBar = progressWrap.querySelector('.progress-bar');

            // Desactiver le bouton submit
            var submitBtn = form.querySelector('button[type="submit"]');
            if (submitBtn) submitBtn.disabled = true;

            var xhr = new XMLHttpRequest();
            xhr.open('POST', form.action, true);

            xhr.upload.onprogress = function(e) {
                if (e.lengthComputable) {
                    var pct = Math.round((e.loaded / e.total) * 100);
                    progressBar.style.width = pct + '%';
                    progressBar.textContent = pct + '%';
                }
            };

            xhr.onload = function() {
                if (xhr.status >= 200 && xhr.status < 400) {
                    // Rediriger vers la reponse
                    if (xhr.responseURL) {
                        window.location.href = xhr.responseURL;
                    } else {
                        window.location.reload();
                    }
                } else {
                    progressBar.classList.remove('progress-bar-animated');
                    progressBar.classList.add('bg-danger');
                    progressBar.textContent = 'Erreur';
                    if (submitBtn) submitBtn.disabled = false;
                }
            };

            xhr.onerror = function() {
                progressBar.classList.add('bg-danger');
                progressBar.textContent = 'Erreur reseau';
                if (submitBtn) submitBtn.disabled = false;
            };

            // Ajouter le CSRF token
            var csrfMeta = document.querySelector('meta[name="csrf-token"]');
            if (csrfMeta) {
                xhr.setRequestHeader('X-CSRFToken', csrfMeta.getAttribute('content'));
            }

            xhr.send(formData);
        });
    });
}

/**
 * T20 - Avertissement expiration de session (2h - 5min = 115min)
 */
function initSessionWarning() {
    // Ne pas activer sur les pages non authentifiees
    if (!document.querySelector('.sidebar')) return;

    var SESSION_DURATION = 120 * 60 * 1000; // 2h en ms
    var WARNING_BEFORE = 5 * 60 * 1000; // 5 min avant

    setTimeout(function() {
        var toast = document.createElement('div');
        toast.className = 'alert alert-warning alert-dismissible fade show position-fixed';
        toast.style.cssText = 'bottom: 20px; right: 20px; z-index: 9999; max-width: 400px;';
        toast.innerHTML = '<i class="bi bi-clock me-2"></i><strong>Session bientot expiree</strong><br>Votre session expire dans 5 minutes. Sauvegardez votre travail.' +
            '<button type="button" class="btn-close" data-bs-dismiss="alert"></button>';
        document.body.appendChild(toast);
    }, SESSION_DURATION - WARNING_BEFORE);
}

/**
 * T34 - Raccourcis clavier
 */
function initKeyboardShortcuts() {
    document.addEventListener('keydown', function(e) {
        // Ctrl+K : focus recherche
        if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
            e.preventDefault();
            var searchInput = document.getElementById('quickSearchInput');
            if (searchInput) searchInput.focus();
        }
        // Escape : fermer les modals ouvertes
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
 * Afficher l'indicateur de force du mot de passe
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
