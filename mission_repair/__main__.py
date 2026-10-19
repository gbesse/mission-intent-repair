import json
import sys
from pathlib import Path

from .solver import check_plan, contingency, repair

ROOT = Path(__file__).resolve().parent
MESSAGES = {
    "fr": {"help": "Utilisation : python -m mission_repair demo|repair dossier.json|check dossier.json plan.json|serve [port] [--lang fr|en|es]", "error": "Entrée non valide", "missing": "Fichier introuvable", "ready": "Démonstration locale"},
    "en": {"help": "Usage: python -m mission_repair demo|repair case.json|check case.json plan.json|serve [port] [--lang fr|en|es]", "error": "Invalid input", "missing": "File not found", "ready": "Local demonstration"},
    "es": {"help": "Uso: python -m mission_repair demo|repair caso.json|check caso.json plan.json|serve [puerto] [--lang fr|en|es]", "error": "Entrada no válida", "missing": "Archivo no encontrado", "ready": "Demostración local"},
}


def demo():
    case = json.loads((ROOT / "examples/lunar-relay.json").read_text())
    return {"case": case, "original": repair(case),
            "outage": repair(contingency(case, ["relay-primary"]))}


def main(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)
    lang = "en"
    if "--lang" in args:
        i = args.index("--lang")
        if i + 1 < len(args):
            lang = args[i + 1] if args[i + 1] in MESSAGES else "en"
        del args[i:i + 2]
    msg = MESSAGES[lang]
    try:
        if not args or args[0] in ("help", "--help", "-h"):
            print(msg["help"])
            return 0
        command = args.pop(0)
        if command == "demo":
            result = demo()
        elif command == "repair" and len(args) == 1:
            result = repair(json.loads(Path(args[0]).read_text()))
        elif command == "check" and len(args) == 2:
            plan = json.loads(Path(args[1]).read_text())
            result = check_plan(json.loads(Path(args[0]).read_text()), plan.get("plan", plan))
        elif command == "serve":
            from .server import serve
            port = int(args[0]) if args else 8764
            print(f'{msg["ready"]}: http://127.0.0.1:{port}/?lang={lang}', flush=True)
            serve(port)
            return 0
        else:
            print(msg["help"], file=sys.stderr)
            return 2
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 1 if result.get("valid") is False or result.get("status") in ("INFEASIBLE", "UNKNOWN") else 0
    except FileNotFoundError:
        print(json.dumps({"error": "missing_file", "message": msg["missing"]}), file=sys.stderr)
        return 2
    except (ValueError, TypeError, KeyError) as error:
        code = str(error) if isinstance(error, ValueError) and str(error).startswith("invalid_") else "invalid_input"
        print(json.dumps({"error": code, "message": msg["error"]}), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
