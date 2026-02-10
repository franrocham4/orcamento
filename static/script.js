// Conectar ao servidor WebSocket
const socket = io();

// Verificar autenticacao ao carregar a pagina
window.addEventListener('load', function() {
    checkAuth();
    // Mostrar nome do usuario
    const user = JSON.parse(localStorage.getItem('user') || '{}');
    if (user.full_name) {
        document.getElementById('user-name').textContent = 'Olá, ' + user.full_name;
    } else if (user.username) {
        document.getElementById('user-name').textContent = 'Olá, ' + user.username;
    }
});

// Verificar autenticacao
function checkAuth() {
    const token = localStorage.getItem('token');
    if (!token) {
        window.location.href = '/login';
        return false;
    }
    return true;
}

// Obter token
function getToken() {
    return localStorage.getItem('token');
}

// Fazer logout
function logout() {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    window.location.href = '/login';
}

// Estado da aplicacao
let currentData = {
    companies: [],
    statistics: {},
    last_update: null,
    file_path: null
};

let filteredCompanies = [];
let selectedCompany = null;

// Elementos do DOM
const statusDot = document.getElementById('status-dot');
const statusLabel = document.getElementById('status-label');
const lastSync = document.getElementById('last-sync');
const searchInput = document.getElementById('search-input');
const companiesList = document.getElementById('companies-list');
const tableInfo = document.getElementById('table-info');
const companiesBadge = document.getElementById('companies-badge');
const detailModal = document.getElementById('detail-modal');

// Eventos do Socket.IO
socket.on('connect', function() {
    console.log('Conectado ao servidor');
    updateStatus(true);
});

socket.on('disconnect', function() {
    console.log('Desconectado do servidor');
    updateStatus(false);
});

socket.on('update', function(data) {
    console.log('Dados recebidos:', data);
    if (data && typeof data === 'object') {
        currentData = data;
        updateUI();
    }
});

socket.on('error', function(error) {
    console.error('Erro:', error);
});

// Atualizar status de conexão
function updateStatus(connected) {
    if (connected) {
        statusDot.classList.add('connected');
        statusDot.classList.remove('disconnected');
        statusLabel.textContent = 'Conectado';
    } else {
        statusDot.classList.remove('connected');
        statusDot.classList.add('disconnected');
        statusLabel.textContent = 'Desconectado';
    }
}

// Atualizar interface
function updateUI() {
    updateStatistics();
    filterCompanies();
    renderCompanies();
    updateLastSync();
}

// Atualizar estatísticas
function updateStatistics() {
    const stats = currentData.statistics || {};

    const totalContracted = document.getElementById('total-contracted');
    const totalSpent = document.getElementById('total-spent');
    const avgUtil = document.getElementById('average-utilization');
    const compCount = document.getElementById('companies-count');

    if (totalContracted) totalContracted.textContent = formatCurrency(stats.total_contracted || 0);
    if (totalSpent) totalSpent.textContent = formatCurrency(stats.total_spent || 0);
    if (avgUtil) avgUtil.textContent = (stats.average_utilization || 0).toFixed(1) + '%';
    if (compCount) compCount.textContent = stats.companies_count || 0;
}

// Filtrar empresas
function filterCompanies() {
    const searchTerm = searchInput.value.toLowerCase();

    filteredCompanies = (currentData.companies || []).filter(company =>
        company.name.toLowerCase().includes(searchTerm) ||
        company.code.toLowerCase().includes(searchTerm)
    );

    // Ordenar por nome
    filteredCompanies.sort((a, b) => a.name.localeCompare(b.name));
}

// Renderizar empresas como cards
function renderCompanies() {
    const badge = document.getElementById('companies-badge');
    if (badge) {
        badge.textContent = filteredCompanies.length + ' empresa' + (filteredCompanies.length !== 1 ? 's' : '');
    }

    if (filteredCompanies.length === 0) {
        companiesList.innerHTML = '<div class="loading-state"><span>Nenhuma empresa encontrada</span></div>';
        return;
    }

    companiesList.innerHTML = filteredCompanies.map(company => {
        const percentage = company.percentage || 0;
        const statusClass = getStatusClass(percentage);
        
        return `
            <div class="company-card" onclick="openModal(event, '${escapeHtml(company.code)}')">
                <div class="company-info">
                    <div class="company-name">${escapeHtml(company.name)}</div>
                    <div class="company-code">Cód: ${escapeHtml(company.code)}</div>
                </div>
                <div class="company-value">
                    <div class="company-value-label">Valor Total</div>
                    <div class="company-value-amount">${formatCurrency(company.contract_value || 0)}</div>
                </div>
                <div class="company-spent">
                    <div class="company-spent-label">Gasto</div>
                    <div class="company-spent-amount">${formatCurrency(company.spent_value || 0)}</div>
                </div>
                <div class="company-percentage">
                    <div class="progress-bar-small">
                        <div class="progress-fill ${statusClass}" style="width: ${Math.min(percentage, 100)}%"></div>
                    </div>
                    <div class="percentage-badge ${company.status || 'ok'}">${percentage.toFixed(1)}%</div>
                </div>
            </div>
        `;
    }).join('');
}

// Abrir modal com detalhes
function openModal(event, companyCode) {
    event.preventDefault();
    
    const company = filteredCompanies.find(c => c.code === companyCode);
    if (!company) return;

    selectedCompany = company;
    const available = (company.contract_value || 0) - (company.spent_value || 0);
    const percentage = company.percentage || 0;
    const statusText = company.status === 'ok' ? 'Dentro do Orçamento' : 
                      company.status === 'warning' ? 'Atenção - Acima de 70%' : 
                      'Crítico - Acima de 90%';

    // Atualizar aba de detalhes
    document.getElementById('modal-company-name').textContent = company.name;
    document.getElementById('modal-code').textContent = company.code;
    document.getElementById('modal-contract').textContent = formatCurrency(company.contract_value || 0);
    document.getElementById('modal-spent').textContent = formatCurrency(company.spent_value || 0);
    document.getElementById('modal-available').textContent = formatCurrency(available);
    document.getElementById('modal-percentage').textContent = percentage.toFixed(1) + '%';
    
    // Atualizar progress bar
    const progressFill = document.getElementById('modal-progress');
    progressFill.style.width = Math.min(percentage, 100) + '%';
    progressFill.className = 'progress-fill ' + getStatusClass(percentage);

    // Atualizar status badge
    const statusBadge = document.getElementById('modal-status');
    statusBadge.textContent = statusText;
    statusBadge.className = 'status-badge ' + (company.status || 'ok');

    // Atualizar aba de edição
    document.getElementById('edit-contract').value = company.contract_value || 0;
    document.getElementById('edit-spent').value = company.spent_value || 0;
    document.getElementById('edit-reason').value = '';

    // Atualizar aba de lançamentos
    loadExpenses(company.code);

    // Definir data padrão para novo lançamento
    const today = new Date().toISOString().split('T')[0];
    document.getElementById('expense-date').value = today;

    detailModal.classList.add('active');
}

// Fechar modal
function closeModal() {
    detailModal.classList.remove('active');
    selectedCompany = null;
}

// Alternar abas
function switchTab(tabName) {
    // Remover ativa de todas as abas
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.classList.remove('active');
    });
    document.querySelectorAll('.tab-button').forEach(btn => {
        btn.classList.remove('active');
    });

    // Ativar aba selecionada
    document.getElementById('tab-' + tabName).classList.add('active');
    event.target.classList.add('active');
}

// Salvar ajuste de valores
function saveAdjustment(event) {
    event.preventDefault();

    if (!selectedCompany) return;

    const contractValue = parseFloat(document.getElementById('edit-contract').value);
    const spentValue = parseFloat(document.getElementById('edit-spent').value);
    const reason = document.getElementById('edit-reason').value;

    fetch('/api/company/adjustment', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            company_code: selectedCompany.code,
            company_name: selectedCompany.name,
            contract_value: contractValue,
            spent_value: spentValue,
            reason: reason
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert('Alterações salvas com sucesso!');
            // Recarregar dados
            fetch('/api/data')
                .then(r => r.json())
                .then(d => {
                    currentData = d;
                    updateUI();
                    closeModal();
                });
        } else {
            alert('Erro ao salvar alterações');
        }
    })
    .catch(error => {
        console.error('Erro:', error);
        alert('Erro ao salvar alterações');
    });
}

// Adicionar lançamento
function addExpense(event) {
    event.preventDefault();

    if (!selectedCompany) return;

    const description = document.getElementById('expense-description').value;
    const amount = parseFloat(document.getElementById('expense-amount').value);
    const date = document.getElementById('expense-date').value;
    const category = document.getElementById('expense-category').value;
    const notes = document.getElementById('expense-notes').value;

    fetch('/api/expenses', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer ' + getToken()
        },
        body: JSON.stringify({
            company_code: selectedCompany.code,
            company_name: selectedCompany.name,
            description: description,
            amount: amount,
            expense_date: date,
            category: category,
            notes: notes
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            document.getElementById('expense-form').reset();
            const today = new Date().toISOString().split('T')[0];
            document.getElementById('expense-date').value = today;
            
            // Recarregar lançamentos
            loadExpenses(selectedCompany.code);
            
            // Recarregar dados da empresa no modal
            setTimeout(function() {
                fetch('/api/data')
                    .then(r => r.json())
                    .then(d => {
                        currentData = d;
                        // Atualizar empresa selecionada
                        const updatedCompany = currentData.companies.find(c => c.code === selectedCompany.code);
                        if (updatedCompany) {
                            selectedCompany = updatedCompany;
                            const available = (updatedCompany.contract_value || 0) - (updatedCompany.spent_value || 0);
                            const percentage = updatedCompany.percentage || 0;
                            
                            // Atualizar valores no modal
                            document.getElementById('modal-spent').textContent = formatCurrency(updatedCompany.spent_value || 0);
                            document.getElementById('modal-available').textContent = formatCurrency(available);
                            document.getElementById('modal-percentage').textContent = percentage.toFixed(1) + '%';
                            
                            // Atualizar progress bar
                            const progressFill = document.getElementById('modal-progress');
                            progressFill.style.width = Math.min(percentage, 100) + '%';
                            progressFill.className = 'progress-fill ' + getStatusClass(percentage);
                            
                            // Atualizar status
                            const statusBadge = document.getElementById('modal-status');
                            const statusText = updatedCompany.status === 'ok' ? 'Dentro do Orçamento' : 
                                              updatedCompany.status === 'warning' ? 'Atenção - Acima de 70%' : 
                                              'Crítico - Acima de 90%';
                            statusBadge.textContent = statusText;
                            statusBadge.className = 'status-badge ' + (updatedCompany.status || 'ok');
                            
                            // Atualizar lista de empresas
                            updateStatistics();
                            filterCompanies();
                            renderCompanies();
                        }
                    });
            }, 500);
        } else {
            alert('Erro ao adicionar lançamento');
        }
    })
    .catch(error => {
        console.error('Erro:', error);
        alert('Erro ao adicionar lançamento');
    });
}

// Carregar lançamentos
function loadExpenses(companyCode) {
    fetch('/api/expenses?company_code=' + companyCode)
        .then(response => response.json())
        .then(expenses => {
            const list = document.getElementById('expenses-list');
            
            if (!expenses || expenses.length === 0) {
                list.innerHTML = '<p>Nenhum lançamento registrado</p>';
                return;
            }

            list.innerHTML = expenses.map(expense => {
                const date = new Date(expense.expense_date).toLocaleDateString('pt-BR');
                return `
                    <div class="expense-item">
                        <div class="expense-info">
                            <div class="expense-description">${escapeHtml(expense.description)}</div>
                            <div class="expense-meta">
                                ${date} - ${expense.category || 'Sem categoria'}
                                ${expense.notes ? ' - ' + escapeHtml(expense.notes) : ''}
                            </div>
                        </div>
                        <div class="expense-amount">${formatCurrency(expense.amount)}</div>
                        <button class="expense-delete" onclick="deleteExpense(${expense.id})">Deletar</button>
                    </div>
                `;
            }).join('');
        })
        .catch(error => {
            console.error('Erro ao carregar lançamentos:', error);
            document.getElementById('expenses-list').innerHTML = '<p>Erro ao carregar lançamentos</p>';
        });
}

// Deletar lançamento
function deleteExpense(expenseId) {
    if (!confirm('Tem certeza que deseja deletar este lançamento?')) return;

    fetch('/api/expenses/' + expenseId, {
        method: 'DELETE'
    })
    .then(response => response.json())
    .then(data => {
        if (data.success && selectedCompany) {
            loadExpenses(selectedCompany.code);
            
            // Recarregar dados da empresa
            fetch('/api/data')
                .then(r => r.json())
                .then(d => {
                    currentData = d;
                    const updatedCompany = currentData.companies.find(c => c.code === selectedCompany.code);
                    if (updatedCompany) {
                        selectedCompany = updatedCompany;
                        const available = (updatedCompany.contract_value || 0) - (updatedCompany.spent_value || 0);
                        const percentage = updatedCompany.percentage || 0;
                        
                        document.getElementById('modal-spent').textContent = formatCurrency(updatedCompany.spent_value || 0);
                        document.getElementById('modal-available').textContent = formatCurrency(available);
                        document.getElementById('modal-percentage').textContent = percentage.toFixed(1) + '%';
                        
                        const progressFill = document.getElementById('modal-progress');
                        progressFill.style.width = Math.min(percentage, 100) + '%';
                        progressFill.className = 'progress-fill ' + getStatusClass(percentage);
                        
                        updateStatistics();
                        filterCompanies();
                        renderCompanies();
                    }
                });
        }
    })
    .catch(error => console.error('Erro:', error));
}

// Baixar relatorio de movimentos
function downloadExpenses() {
    if (!selectedCompany) {
        alert('Nenhuma empresa selecionada');
        return;
    }
    
    const url = '/api/download/expenses/' + selectedCompany.code;
    const link = document.createElement('a');
    link.href = url;
    link.download = 'Movimentos_' + selectedCompany.code + '.xlsx';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}

// Fechar modal ao clicar fora
detailModal.addEventListener('click', function(e) {
    if (e.target === detailModal) {
        closeModal();
    }
});

// Fechar modal com ESC
document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
        closeModal();
    }
});

// Atualizar última sincronização
function updateLastSync() {
    if (currentData.last_update) {
        try {
            const date = new Date(currentData.last_update);
            const hours = String(date.getHours()).padStart(2, '0');
            const minutes = String(date.getMinutes()).padStart(2, '0');
            const seconds = String(date.getSeconds()).padStart(2, '0');
            lastSync.textContent = 'Última atualização: ' + hours + ':' + minutes + ':' + seconds;
        } catch (e) {
            lastSync.textContent = 'Última atualização: --:--:--';
        }
    } else {
        lastSync.textContent = 'Última atualização: --:--:--';
    }
}

// Obter classe de status
function getStatusClass(percentage) {
    if (percentage > 90) return 'danger';
    if (percentage > 70) return 'warning';
    return '';
}

// Formatar moeda
function formatCurrency(value) {
    try {
        return new Intl.NumberFormat('pt-BR', {
            style: 'currency',
            currency: 'BRL'
        }).format(value || 0);
    } catch (e) {
        return 'R$ 0,00';
    }
}

// Escapar HTML
function escapeHtml(text) {
    if (!text) return '';
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    };
    return String(text).replace(/[&<>"']/g, function(m) { return map[m]; });
}

// Event Listeners
if (searchInput) {
    searchInput.addEventListener('input', function() {
        filterCompanies();
        renderCompanies();
    });
}

// Inicializar
document.addEventListener('DOMContentLoaded', function() {
    console.log('Página carregada');
    // Solicitar dados iniciais
    fetch('/api/data')
        .then(function(response) {
            if (!response.ok) throw new Error('Erro na resposta');
            return response.json();
        })
        .then(function(data) {
            if (data && typeof data === 'object') {
                currentData = data;
                updateUI();
            }
        })
        .catch(function(error) {
            console.error('Erro ao carregar dados:', error);
        });
});
