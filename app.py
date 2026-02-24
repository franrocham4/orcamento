import logging
from datetime import datetime
from flask import Flask, render_template, jsonify, request, send_file
from flask_socketio import SocketIO, emit
from excel_processor import ExcelProcessor
from file_monitor import FileMonitor
from database import Database
from export_excel import ExcelExporter
import config

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Criar aplicacao Flask
app = Flask(__name__, template_folder=str(config.TEMPLATES_DIR), static_folder=str(config.STATIC_DIR))

# Inicializar SocketIO
socketio = SocketIO(app, cors_allowed_origins="*")

# Inicializar processador, monitor e banco de dados
processor = ExcelProcessor()
monitor = FileMonitor(config.WATCH_FOLDER, config.EXCEL_PATTERN, config.CHECK_INTERVAL)
db = Database()
exporter = ExcelExporter()

# Dados atuais
current_data = {
    'companies': [],
    'statistics': {},
    'last_update': None,
    'file_path': None
}


def apply_adjustments_to_companies(companies):
    """Aplica ajustes do banco de dados aos dados das empresas"""
    for company in companies:
        adjustment = db.get_company_adjustment(company['code'])
        if adjustment:
            # Aplicar ajustes se existirem
            if adjustment.get('contract_value') is not None:
                company['contract_value'] = adjustment['contract_value']
            if adjustment.get('spent_value') is not None:
                company['spent_value'] = adjustment['spent_value']
            else:
                # Se não há ajuste de spent_value, usar soma de lançamentos
                total_expenses = db.get_expenses_by_company(company['code'])
                if total_expenses > 0:
                    company['spent_value'] = total_expenses
        else:
            # Se não há ajuste, usar soma de lançamentos
            total_expenses = db.get_expenses_by_company(company['code'])
            if total_expenses > 0:
                company['spent_value'] = total_expenses
        
        # Recalcular percentual
        if company['contract_value'] > 0:
            company['percentage'] = round((company['spent_value'] / company['contract_value']) * 100, 2)
        else:
            company['percentage'] = 0
        
        # Recalcular status
        if company['percentage'] > 90:
            company['status'] = 'critical'
        elif company['percentage'] > 70:
            company['status'] = 'warning'
        else:
            company['status'] = 'ok'
    
    return companies



@app.route('/')
def index():
    """Pagina principal"""
    return render_template('index.html')


@app.route('/api/data')
def get_data():
    """Retorna dados atuais em JSON"""
    return jsonify(current_data)


@app.route('/api/expenses', methods=['GET'])
def get_expenses():
    """Obter lancamentos de gastos"""
    company_code = request.args.get('company_code')
    expenses = db.get_expenses(company_code)
    return jsonify(expenses)


@app.route('/api/expenses', methods=['POST'])
def add_expense():
    """Adicionar novo lancamento"""
    data = request.json
    amount = float(data.get('amount', 0))
    company_code = data.get('company_code')
    company_name = data.get('company_name')
    created_by = 'sistema'
    
    success = db.add_expense(
        company_code=company_code,
        company_name=company_name,
        amount=amount,
        description=data.get('description', ''),
        expense_date=data.get('expense_date'),
        category=data.get('category', ''),
        notes=data.get('notes', ''),
        created_by=created_by
    )
    
    if success:
        # Obter valor total de lancamentos da empresa
        total_spent = db.get_expenses_by_company(company_code)
        
        # Atualizar valor gasto na empresa no banco de dados
        db.set_company_adjustment(
            company_code=company_code,
            company_name=company_name,
            spent_value=total_spent
        )
        
        # Reprocessar dados para atualizar
        current_file = monitor.get_current_file()
        if current_file:
            companies = processor.process_file(current_file)
            companies = apply_adjustments_to_companies(companies)
            statistics = processor.get_statistics(companies)
            
            current_data['companies'] = companies
            current_data['statistics'] = statistics
            current_data['last_update'] = datetime.now().isoformat()
        
        socketio.emit('update', current_data, namespace='/')
    
    return jsonify({'success': success})


@app.route('/api/expenses/<int:expense_id>', methods=['DELETE'])
def delete_expense(expense_id):
    """Deletar lancamento"""
    success = db.delete_expense(expense_id)
    
    if success:
        # Recalcular valor gasto para todas as empresas
        socketio.emit('update', current_data, namespace='/')
    
    return jsonify({'success': success})


@app.route('/api/download/expenses/<company_code>')
def download_expenses(company_code):
    """Baixar relatorio de movimentos da empresa"""
    try:
        company = None
        for c in current_data.get('companies', []):
            if c['code'] == company_code:
                company = c
                break
        
        if not company:
            return jsonify({'error': 'Empresa nao encontrada'}), 404
        
        expenses = db.get_expenses(company_code)
        
        filepath = exporter.export_company_expenses(
            company_name=company['name'],
            company_code=company_code,
            contract_value=company['contract_value'],
            spent_value=company['spent_value'],
            expenses=expenses
        )
        
        if not filepath:
            return jsonify({'error': 'Erro ao gerar arquivo'}), 500
        
        return send_file(
            filepath,
            as_attachment=True,
            download_name=f"Movimentos_{company_code}.xlsx"
        )
    
    except Exception as e:
        logger.error(f"Erro ao baixar arquivo: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/company/adjustment', methods=['GET'])
def get_adjustment():
    """Obter ajuste de valores da empresa"""
    company_code = request.args.get('company_code')
    adjustment = db.get_company_adjustment(company_code)
    return jsonify(adjustment or {})


@app.route('/api/company/adjustment', methods=['POST'])
def set_adjustment():
    """Salvar ajuste de valores da empresa"""
    data = request.json
    success = db.set_company_adjustment(
        company_code=data.get('company_code'),
        company_name=data.get('company_name'),
        contract_value=float(data.get('contract_value')) if data.get('contract_value') else None,
        spent_value=float(data.get('spent_value')) if data.get('spent_value') else None,
        reason=data.get('reason', '')
    )
    
    if success:
        # Reprocessar dados para atualizar
        current_file = monitor.get_current_file()
        if current_file:
            companies = processor.process_file(current_file)
            companies = apply_adjustments_to_companies(companies)
            statistics = processor.get_statistics(companies)
            
            current_data['companies'] = companies
            current_data['statistics'] = statistics
            current_data['last_update'] = datetime.now().isoformat()
        
        socketio.emit('update', current_data, namespace='/')
    
    return jsonify({'success': success})


@socketio.on('connect')
def handle_connect():
    """Quando cliente se conecta"""
    logger.info(f"Cliente conectado: {request.sid}")
    # Enviar dados atuais
    emit('update', current_data)


@socketio.on('disconnect')
def handle_disconnect():
    """Quando cliente se desconecta"""
    logger.info(f"Cliente desconectado: {request.sid}")


def on_file_changed(file_path: str):
    """Callback quando arquivo e detectado/modificado"""
    try:
        logger.info(f"Processando arquivo: {file_path}")

        # Processar arquivo
        companies = processor.process_file(file_path)
        
        # Aplicar ajustes do banco de dados
        companies = apply_adjustments_to_companies(companies)
        
        statistics = processor.get_statistics(companies)

        # Atualizar dados
        current_data['companies'] = companies
        current_data['statistics'] = statistics
        current_data['file_path'] = file_path
        current_data['last_update'] = datetime.now().isoformat()

        # Emitir atualizacao para todos os clientes conectados
        socketio.emit('update', current_data, namespace='/')
        logger.info(f"Dados atualizados: {len(companies)} empresas")

    except Exception as e:
        logger.error(f"Erro ao processar arquivo: {e}")
        import traceback
        traceback.print_exc()
        socketio.emit('error', {'message': str(e)}, namespace='/')


def start_monitor():
    """Inicia o monitor de arquivo"""
    if monitor.start(on_file_changed):
        logger.info("Monitor de arquivo iniciado")
    else:
        logger.error("Falha ao iniciar monitor")


if __name__ == '__main__':
    try:
        # Iniciar monitor
        start_monitor()

        # Executar servidor
        logger.info(f"Iniciando servidor em http://{config.HOST}:{config.PORT}")
        socketio.run(app, host=config.HOST, port=config.PORT, debug=False, allow_unsafe_werkzeug=True)

    except KeyboardInterrupt:
        logger.info("Encerrando...")
        monitor.stop()
    except Exception as e:
        logger.error(f"Erro fatal: {e}")
        import traceback
        traceback.print_exc()
        monitor.stop()
