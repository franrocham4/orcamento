import subprocess
import sys

packages = [
    'Flask==3.0.0',
    'Flask-SocketIO==5.3.5',
    'python-socketio==5.10.0',
    'python-engineio==4.8.0',
    'openpyxl==3.1.2',
    'Werkzeug==3.0.1',
    'PyJWT==2.11.0'
]

print("=" * 60)
print("INSTALADOR - Dashboard de Pagamentos 2025")
print("=" * 60)
print()

for package in packages:
    print(f"Instalando {package}...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--only-binary=:all:", package])
        print(f"OK: {package}")
    except:
        print(f"Tentando sem --only-binary para {package}...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
            print(f"OK: {package}")
        except Exception as e:
            print(f"Erro em {package}: {e}")

print()
print("=" * 60)
print("Pronto! Execute: python app.py")
print("=" * 60)
