import os, sys, subprocess
PYTHON_PATH = r"Y:\Supply Chain\PLAN PRODUCCION\PANEL\_SISTEMA\runtime_python\python.exe"

def main():
    if len(sys.argv) < 2:
        print("Uso: ops_sync.py \"mensaje del commit\"")
        sys.exit(1)
    
    msg = sys.argv[1]
    
    print("Iniciando Sincronizacion...")
    
    # 1. QA Audit
    print("Ejecutando QA Scanner...")
    qa = subprocess.run([PYTHON_PATH, "scripts/qa_scanner.py"])
    if qa.returncode != 0:
        print("Fallo el QA Scanner. Abortando.")
        sys.exit(1)
    
    # 2. Git Ops
    print("Preparando commit...")
    subprocess.run(["git", "add", "."])
    subprocess.run(["git", "commit", "-m", msg])
    
    print("Subiendo a GitHub (backup)...")
    push = subprocess.run(["git", "push", "backup", "main"])
    
    if push.returncode == 0:
        print("Todo sincronizado correctamente.")
    else:
        print("Error en el push. Verifica la conexion o el repositorio remoto.")
    
    sys.exit(0)

if __name__ == "__main__":
    main()
