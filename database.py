"""
Gerenciador de banco de dados SQLite para o dashboard
"""

import sqlite3
import os
from datetime import datetime
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

DB_PATH = 'dashboard.db'


class Database:
    """Gerenciador de banco de dados"""

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self.init_db()

    def get_connection(self):
        """Obter conexão com o banco de dados"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self):
        """Inicializar banco de dados com tabelas"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            # Tabela de lançamentos de gastos
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS expenses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    company_code TEXT NOT NULL,
                    company_name TEXT NOT NULL,
                    description TEXT,
                    amount REAL NOT NULL,
                    expense_date TEXT NOT NULL,
                    category TEXT,
                    notes TEXT,
                    created_by TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Tabela de ajustes de valores
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS company_adjustments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    company_code TEXT NOT NULL UNIQUE,
                    company_name TEXT NOT NULL,
                    contract_value REAL,
                    spent_value REAL,
                    reason TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Tabela de usuarios
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL UNIQUE,
                    password TEXT NOT NULL,
                    full_name TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            conn.commit()
            conn.close()
            logger.info("Banco de dados inicializado com sucesso")

        except Exception as e:
            logger.error(f"Erro ao inicializar banco de dados: {e}")

    # ============ EXPENSES ============

    def add_expense(self, company_code: str, company_name: str, amount: float,
                   description: str = "", expense_date: str = None,
                   category: str = "", notes: str = "", created_by: str = None) -> bool:
        """Adicionar novo lançamento de gasto"""
        try:
            if expense_date is None:
                expense_date = datetime.now().strftime('%Y-%m-%d')

            conn = self.get_connection()
            cursor = conn.cursor()

            cursor.execute('''
                INSERT INTO expenses 
                (company_code, company_name, description, amount, expense_date, category, notes, created_by)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (company_code, company_name, description, amount, expense_date, category, notes, created_by))

            conn.commit()
            conn.close()

            logger.info(f"Lançamento adicionado: {company_name} - R${amount}")
            return True

        except Exception as e:
            logger.error(f"Erro ao adicionar lançamento: {e}")
            return False

    def get_expenses(self, company_code: str = None) -> List[Dict[str, Any]]:
        """Obter lançamentos de gastos"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            if company_code:
                cursor.execute('''
                    SELECT * FROM expenses 
                    WHERE company_code = ?
                    ORDER BY expense_date DESC
                ''', (company_code,))
            else:
                cursor.execute('''
                    SELECT * FROM expenses 
                    ORDER BY expense_date DESC
                ''')

            rows = cursor.fetchall()
            conn.close()

            return [dict(row) for row in rows]

        except Exception as e:
            logger.error(f"Erro ao obter lançamentos: {e}")
            return []

    def delete_expense(self, expense_id: int) -> bool:
        """Deletar lançamento de gasto"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            cursor.execute('DELETE FROM expenses WHERE id = ?', (expense_id,))
            conn.commit()
            conn.close()

            logger.info(f"Lançamento {expense_id} deletado")
            return True

        except Exception as e:
            logger.error(f"Erro ao deletar lançamento: {e}")
            return False

    # ============ ADJUSTMENTS ============

    def set_company_adjustment(self, company_code: str, company_name: str,
                              contract_value: float = None, spent_value: float = None,
                              reason: str = "") -> bool:
        """Definir ou atualizar ajuste de valores da empresa"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            # Verificar se já existe
            cursor.execute('SELECT id FROM company_adjustments WHERE company_code = ?', (company_code,))
            exists = cursor.fetchone()

            if exists:
                # Atualizar
                updates = []
                params = []

                if contract_value is not None:
                    updates.append('contract_value = ?')
                    params.append(contract_value)

                if spent_value is not None:
                    updates.append('spent_value = ?')
                    params.append(spent_value)

                if reason:
                    updates.append('reason = ?')
                    params.append(reason)

                updates.append('updated_at = CURRENT_TIMESTAMP')
                params.append(company_code)

                query = f'UPDATE company_adjustments SET {", ".join(updates)} WHERE company_code = ?'
                cursor.execute(query, params)
            else:
                # Inserir
                cursor.execute('''
                    INSERT INTO company_adjustments 
                    (company_code, company_name, contract_value, spent_value, reason)
                    VALUES (?, ?, ?, ?, ?)
                ''', (company_code, company_name, contract_value, spent_value, reason))

            conn.commit()
            conn.close()

            logger.info(f"Ajuste salvo para {company_name}")
            return True

        except Exception as e:
            logger.error(f"Erro ao salvar ajuste: {e}")
            return False

    def get_company_adjustment(self, company_code: str) -> Optional[Dict[str, Any]]:
        """Obter ajuste de valores da empresa"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            cursor.execute('SELECT * FROM company_adjustments WHERE company_code = ?', (company_code,))
            row = cursor.fetchone()
            conn.close()

            return dict(row) if row else None

        except Exception as e:
            logger.error(f"Erro ao obter ajuste: {e}")
            return None

    def get_all_adjustments(self) -> List[Dict[str, Any]]:
        """Obter todos os ajustes"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            cursor.execute('SELECT * FROM company_adjustments ORDER BY company_name')
            rows = cursor.fetchall()
            conn.close()

            return [dict(row) for row in rows]

        except Exception as e:
            logger.error(f"Erro ao obter ajustes: {e}")
            return []

    # ============ STATISTICS ============

    def get_expenses_by_company(self, company_code: str) -> float:
        """Obter total de gastos lançados para uma empresa"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            cursor.execute('''
                SELECT SUM(amount) as total FROM expenses 
                WHERE company_code = ?
            ''', (company_code,))

            row = cursor.fetchone()
            conn.close()

            return row['total'] if row['total'] else 0

        except Exception as e:
            logger.error(f"Erro ao obter gastos: {e}")
            return 0

    def get_total_expenses(self) -> float:
        """Obter total de todos os gastos lançados"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            cursor.execute('SELECT SUM(amount) as total FROM expenses')
            row = cursor.fetchone()
            conn.close()

            return row['total'] if row['total'] else 0

        except Exception as e:
            logger.error(f"Erro ao obter total de gastos: {e}")
            return 0

    # ============ USERS ============

    def create_user(self, username: str, password: str, full_name: str = "") -> bool:
        """Criar novo usuário"""
        try:
            import hashlib
            
            # Hash da senha
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            
            conn = self.get_connection()
            cursor = conn.cursor()

            cursor.execute('''
                INSERT INTO users (username, password, full_name)
                VALUES (?, ?, ?)
            ''', (username, password_hash, full_name))

            conn.commit()
            conn.close()

            logger.info(f"Usuário criado: {username}")
            return True

        except Exception as e:
            logger.error(f"Erro ao criar usuário: {e}")
            return False

    def authenticate_user(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """Autenticar usuário"""
        try:
            import hashlib
            
            # Hash da senha
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            
            conn = self.get_connection()
            cursor = conn.cursor()

            cursor.execute('''
                SELECT * FROM users 
                WHERE username = ? AND password = ?
            ''', (username, password_hash))

            row = cursor.fetchone()
            conn.close()

            return dict(row) if row else None

        except Exception as e:
            logger.error(f"Erro ao autenticar usuário: {e}")
            return None

    def get_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Obter dados do usuário"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            cursor.execute('SELECT id, username, full_name FROM users WHERE id = ?', (user_id,))
            row = cursor.fetchone()
            conn.close()

            return dict(row) if row else None

        except Exception as e:
            logger.error(f"Erro ao obter usuário: {e}")
            return None

    def user_exists(self, username: str) -> bool:
        """Verificar se usuário existe"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            cursor.execute('SELECT id FROM users WHERE username = ?', (username,))
            row = cursor.fetchone()
            conn.close()

            return row is not None

        except Exception as e:
            logger.error(f"Erro ao verificar usuário: {e}")
            return False
