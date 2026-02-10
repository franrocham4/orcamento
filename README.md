# Dashboard de Controle de Pagamentos 2025

Sistema Python com interface web para monitorar contratos e gastos de empresas em tempo real.

## Características

- ✅ Monitoramento automático de arquivo Excel
- ✅ Atualização em tempo real sem upload manual
- ✅ Dashboard elegante e responsivo
- ✅ Processamento de abas VALIDAÇÕES e LIQUIDAÇÃO 2025
- ✅ Indicadores visuais com progress bars
- ✅ Busca e ordenação de empresas
- ✅ Estatísticas gerais

## Requisitos

- Python 3.8+
- pip (gerenciador de pacotes Python)

## Instalação Rápida

1. Extraia os arquivos
2. Abra Prompt de Comando na pasta
3. Execute:
   ```bash
   python instalar.py
   ```

4. Depois execute:
   ```bash
   python app.py
   ```

5. Abra o navegador em `http://localhost:5000`

## Como Usar

1. Coloque seu arquivo Excel (`CONTROLEDEPAGAMENTO2025.xlsm`) em:
   ```
   C:\Users\danielcoelho\Desktop\Nova pasta
   ```

2. O dashboard detectará automaticamente o arquivo

3. Sempre que você salvar o Excel, o dashboard atualiza em tempo real!

## Estrutura do Projeto

```
dashboard_pagamentos/
├── app.py                 # Servidor Flask principal
├── config.py              # Configurações
├── excel_processor.py     # Processamento de Excel
├── file_monitor.py        # Monitoramento de arquivo
├── instalar.py            # Script de instalação
├── requirements.txt       # Dependências
├── templates/
│   └── index.html        # Interface web
└── static/
    ├── style.css         # Estilos
    └── script.js         # Lógica frontend
```

## Solução de Problemas

### Erro: "TemplateNotFound: index.html"
Certifique-se que a pasta `templates` existe e contém `index.html`

### Erro: "ModuleNotFoundError"
Execute: `python instalar.py` novamente

### Porta 5000 em uso
Abra `config.py` e altere `PORT = 5000` para outra porta

## Suporte

Para dúvidas ou problemas, verifique:
1. Se Python está instalado: `python --version`
2. Se as dependências estão instaladas: `pip list`
3. Se o arquivo Excel está no local correto
"# Sistema-Orcamento" 
