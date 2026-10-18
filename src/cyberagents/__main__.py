"""Run the project with python -m cyberagents from the repository environment."""
import argparse
import json
from pathlib import Path
from .config import CONFIG


def main():
    from .pipeline import ROOT
    if (ROOT / '.env').exists():
        from dotenv import load_dotenv
        load_dotenv(ROOT / '.env', override=False)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['prepare', 'run', 'evaluate', 'results', 'freeze-system', 'report'])
    parser.add_argument('--system', choices=['S0', 'S1', 'S3'], default='S3')
    parser.add_argument('--seed', type=int, default=42)
    parser.add_argument('--live', action='store_true', help='Permit uncached LLM calls')
    parser.add_argument('--force', action='store_true', help='Replace seed-42 output only')
    args = parser.parse_args()
    from .pipeline import run_system, check_retrieval, record_system_freeze, render_incident
    from .attack_kb import build_kb
    from .evaluate import evaluate_saved, render_results
    path = Path(CONFIG['paths']['out']) / f'{args.system}_seed{args.seed}.json'
    if args.command == 'prepare':
        result = check_retrieval()
        if result['passed'] < 5:
            raise SystemExit('Retrieval threshold missed; record a decision before changing the embedding design')
    elif args.command == 'run':
        result = run_system(args.system, args.seed, live=args.live, force=args.force)
        print(json.dumps({key: result[key] for key in ['system', 'seed', 'execution', 'runtime_s', 'llm_calls']}, indent=2))
    elif args.command == 'evaluate':
        print(json.dumps(evaluate_saved(path, build_kb()), indent=2))
    elif args.command == 'results':
        print(render_results().to_string(index=False))
    elif args.command == 'freeze-system':
        print(json.dumps(record_system_freeze(), indent=2))
    else:
        print(render_incident(path, Path(CONFIG['paths']['out']) / 'demo_incident.md'))


if __name__ == '__main__':
    main()
