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

    var container = document.querySelector('.container');
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
