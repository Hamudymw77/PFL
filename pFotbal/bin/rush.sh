
# برنامج نصي للتشغيل لنظامي التشغيل لينكس/ماك
echo "=== Training Planner CLI (Linux/macOS) ==="
echo "Attempting to run the application..."

# تغيير الدليل إلى جذر المشروع
DIR="$(dirname "$0")"
cd "$DIR"

# جرب بايثوني
if command -v python3 &>/dev/null; then
    PYTHON_CMD="python3"
elif command -v python &>/dev/null; then
    PYTHON_CMD="python"
elif command -v py &>/dev/null; then
    PYTHON_CMD="py"
else
    echo "ERROR: Python 3 was not found. Please ensure Python is installed and in your PATH."
    exit 1
fi

echo "Using command: $PYTHON_CMD"
# نفذ ملف واجهة سطر الأوامر الرئيسي
"$PYTHON_CMD" src/cli.py

echo "Script finished."
