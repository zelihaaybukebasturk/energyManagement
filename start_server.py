"""
Startup script for the AI-Driven Building Energy Efficiency System
Run this from the project root directory.
"""

import sys
import platform
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

if __name__ == "__main__":
    import uvicorn
    # Windows'ta reload=True multiprocessing named pipe hatası verir (Erişim engellendi)
    use_reload = platform.system() != "Windows"
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=use_reload)

