document.addEventListener('DOMContentLoaded', function() {
    {% for fournisseur in fournisseurs %}
    var ctxFournisseur{{ fournisseur.fournisseur_id }} = document.getElementById('fournisseurChart{{ fournisseur.fournisseur_id }}').getContext('2d');
    var fournisseurChart{{ fournisseur.fournisseur_id }} = new Chart(ctxFournisseur{{ fournisseur.fournisseur_id }}, {
        type: 'bar',
        data: {
            labels: {{ fournisseur_materials[fournisseur.fournisseur_id]|map(attribute='code_a_barre')|list }},
            datasets: [{
                label: 'Materials',
                data: {{ fournisseur_materials[fournisseur.fournisseur_id]|map(attribute='material_id')|list }},
                backgroundColor: 'rgba(153, 102, 255, 0.2)',
                borderColor: 'rgba(153, 102, 255, 1)',
                borderWidth: 1
            }]
        },
        options: {
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });
    {% endfor %}
});
