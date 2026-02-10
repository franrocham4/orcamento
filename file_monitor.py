import os
import time
import threading
import logging
from pathlib import Path
from typing import Callable, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class FileMonitor:
    """Monitor de arquivo Excel com detecção de mudanças"""

    def __init__(self, folder_path: str, pattern: str = "*.xlsm", check_interval: int = 2):
        """
        Inicializa o monitor

        Args:
            folder_path: Caminho da pasta a monitorar
            pattern: Padrão de arquivo (ex: *.xlsm)
            check_interval: Intervalo de verificação em segundos
        """
        self.folder_path = Path(folder_path)
        self.pattern = pattern
        self.check_interval = check_interval
        self.is_running = False
        self.thread: Optional[threading.Thread] = None
        self.on_file_changed: Optional[Callable] = None
        self.last_modified_time = 0
        self.current_file: Optional[Path] = None

    def start(self, on_file_changed: Callable) -> bool:
        """
        Inicia o monitoramento

        Args:
            on_file_changed: Função callback quando arquivo muda

        Returns:
            True se iniciou com sucesso
        """
        if not self.folder_path.exists():
            logger.error(f"Pasta não encontrada: {self.folder_path}")
            return False

        self.on_file_changed = on_file_changed
        self.is_running = True
        self.thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.thread.start()

        logger.info(f"Monitor iniciado para: {self.folder_path}")
        return True

    def stop(self):
        """Para o monitoramento"""
        self.is_running = False
        if self.thread:
            self.thread.join(timeout=5)
        logger.info("Monitor parado")

    def _monitor_loop(self):
        """Loop de monitoramento"""
        while self.is_running:
            try:
                self._check_file()
                time.sleep(self.check_interval)
            except Exception as e:
                logger.error(f"Erro no monitor: {e}")
                time.sleep(self.check_interval)

    def _check_file(self):
        """Verifica se o arquivo foi modificado"""
        try:
            # Procurar arquivo que corresponde ao padrão
            files = list(self.folder_path.glob(self.pattern))

            if not files:
                logger.debug(f"Nenhum arquivo encontrado com padrão {self.pattern}")
                return

            # Usar o arquivo mais recente
            latest_file = max(files, key=lambda p: p.stat().st_mtime)

            # Verificar se é um arquivo novo ou foi modificado
            try:
                current_mtime = latest_file.stat().st_mtime
            except OSError:
                # Arquivo pode estar sendo acessado
                return

            # Se é um arquivo novo ou foi modificado
            if latest_file != self.current_file or current_mtime != self.last_modified_time:
                # Aguardar um pouco para garantir que o arquivo foi completamente salvo
                time.sleep(1)

                # Verificar novamente se o arquivo não está sendo modificado
                try:
                    new_mtime = latest_file.stat().st_mtime
                    if new_mtime == current_mtime:
                        # Arquivo estável, chamar callback
                        self.current_file = latest_file
                        self.last_modified_time = current_mtime

                        if self.on_file_changed:
                            logger.info(f"Arquivo detectado: {latest_file.name}")
                            self.on_file_changed(str(latest_file))
                except OSError:
                    pass

        except Exception as e:
            logger.error(f"Erro ao verificar arquivo: {e}")

    def get_current_file(self) -> Optional[str]:
        """Retorna o caminho do arquivo atual"""
        return str(self.current_file) if self.current_file else None
