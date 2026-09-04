#!/usr/bin/env bash
#
# upload_report.sh
#
# Sube de forma recursiva los archivos de una carpeta de reporte de pruebas
# a un directorio especifico en un servidor remoto, usando scp.
#
# Compatible con Linux y macOS de forma nativa. En Windows requiere Git Bash
# (incluido en Git for Windows) o WSL, ya que Bash no viene nativo en Windows.
#
# USO:
#   ./upload_report.sh <user> <src> <dest> [--port PORT] [--host HOST]
#
# PARAMETROS:
#   user      Usuario SSH para acceder al servidor. Ejemplo: fulanito
#   src       Carpeta origen que se desea subir (recursivo).
#             Ejemplo: reports/20260903-125014
#   dest      Carpeta destino en el servidor.
#             Ejemplo: /var/www/html/qa_reports
#   --port    (Opcional) Puerto SSH/SCP. Si no se indica, se usa 2210.
#   --host    (Opcional) Host o IP del servidor. Si no se indica, se usa
#             el valor definido en DEFAULT_HOST (ver mas abajo).
#
# EJEMPLOS:
#   ./upload_report.sh fulanito reports/20260903-125014 /var/www/html/qa_reports
#   ./upload_report.sh fulanito reports/20260903-125014 /var/www/html/qa_reports --port 2222
#   ./upload_report.sh fulanito reports/20260903-125014 /var/www/html/qa_reports --host qa.miempresa.com
#
# NOTA IMPORTANTE:
#   El valor de HOST esta definido como un PLACEHOLDER en la variable
#   DEFAULT_HOST (mas abajo en este mismo archivo). Reemplazalo por el
#   host/IP real de tu servidor antes de usar el script de forma habitual,
#   o bien indicalo en cada ejecucion con --host.

set -euo pipefail

# --------------------------------------------------------------------------
# CONFIGURACION POR DEFECTO (editable)
# --------------------------------------------------------------------------
DEFAULT_PORT="2210"
DEFAULT_HOST="black.digitum.com.mx"  # <-- PLACEHOLDER: reemplazar por el host/IP real

SCRIPT_NAME="$(basename "$0")"

usage() {
  cat <<EOF
Uso: ${SCRIPT_NAME} <user> <src> <dest> [--port PORT] [--host HOST]

  user      Usuario SSH para acceder al servidor. Ejemplo: fulanito
  src       Carpeta origen a subir (recursivo). Ejemplo: reports/20260903-125014
  dest      Carpeta destino en el servidor. Ejemplo: /var/www/html/qa_reports
  --port    (Opcional) Puerto SSH/SCP. Por defecto: ${DEFAULT_PORT}
  --host    (Opcional) Host o IP del servidor. Por defecto: placeholder en el script.
EOF
}

error() {
  echo "[ERROR] $1" >&2
  exit "${2:-1}"
}

# --------------------------------------------------------------------------
# Parseo de argumentos: separa flags opcionales (--port/--host) de los
# argumentos posicionales (user, src, dest), sin importar el orden en que
# se hayan escrito.
# --------------------------------------------------------------------------
POSITIONAL=()
PORT="$DEFAULT_PORT"
HOST="$DEFAULT_HOST"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --port)
      [[ $# -ge 2 ]] || error "Falta el valor para --port"
      PORT="$2"
      shift 2
      ;;
    --host)
      [[ $# -ge 2 ]] || error "Falta el valor para --host"
      HOST="$2"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      POSITIONAL+=("$1")
      shift
      ;;
  esac
done

set -- "${POSITIONAL[@]}"

if [[ $# -ne 3 ]]; then
  usage
  error "Numero de parametros invalido. Se esperan 3 parametros posicionales: user src dest"
fi

USER_SSH="$1"
SRC="$2"
DEST="$3"

# --------------------------------------------------------------------------
# Validaciones
# --------------------------------------------------------------------------

# Validar que el placeholder de host haya sido reemplazado o indicado explicitamente
#if [[ "$HOST" == "$DEFAULT_HOST" ]]; then
#  error "El host aun tiene el valor de placeholder '${DEFAULT_HOST}'. Edita la variable DEFAULT_HOST dentro de este script, o indica el servidor real con --host."
#fi

# Validar que el comando 'scp' este disponible en el PATH
if ! command -v scp >/dev/null 2>&1; then
  error "No se encontro el comando 'scp' en el PATH. Instala un cliente SSH/SCP (OpenSSH) y vuelve a intentar."
fi

# Validar que la carpeta origen exista y sea un directorio
if [[ ! -d "$SRC" ]]; then
  error "La carpeta origen '${SRC}' no existe o no es un directorio."
fi

# Validar que existan archivos para subir (busqueda recursiva)
FILE_COUNT="$(find "$SRC" -type f | wc -l | tr -d ' ')"

if [[ "$FILE_COUNT" -eq 0 ]]; then
  error "No se encontraron archivos para subir dentro de '${SRC}'."
fi

echo "Se encontraron ${FILE_COUNT} archivo(s) para subir desde '${SRC}'."

REMOTE_DEST="${USER_SSH}@${HOST}:${DEST}"

echo "Ejecutando: scp -r -P ${PORT} \"${SRC}\" \"${REMOTE_DEST}\""

scp -r -P "$PORT" "$SRC" "$REMOTE_DEST"

echo "Carga completada exitosamente."
