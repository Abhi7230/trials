"""Command-line interface for skill-lint."""

import argparse
import sys
from pathlib import Path

from .config import Config
from .linter import lint_path
from .reporters import format_json, format_sarif, format_text


def main() -> int:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="skill-lint",
        description="Offline linter and quality scorer for agent SKILL.md files",
    )
    
    parser.add_argument(
        "paths",
        nargs="+",
        type=Path,
        help="Path(s) to SKILL.md file(s) or directories",
    )
    
    parser.add_argument(
        "--format",
        choices=["text", "json", "sarif"],
        default="text",
        help="Output format (default: text)",
    )
    
    parser.add_argument(
        "--no-color",
        action="store_true",
        help="Disable colored output",
    )
    
    parser.add_argument(
        "--llm",
        action="store_true",
        help="Use LLM-based critique (requires API key)",
    )
    
    parser.add_argument(
        "--config",
        type=Path,
        help="Path to skill-lint.toml config file",
    )
    
    parser.add_argument(
        "--min-score",
        type=int,
        default=0,
        help="Minimum score required (exit 1 if below)",
    )
    
    parser.add_argument(
        "--fix",
        action="store_true",
        help="Apply safe fixes (not implemented yet)",
    )
    
    args = parser.parse_args()
    
    # Load config
    config = Config(config_path=args.config)
    if args.min_score:
        config.min_score = args.min_score
    
    # Lint all paths
    all_reports = []
    for path in args.paths:
        if not path.exists():
            print(f"Error: Path does not exist: {path}", file=sys.stderr)
            return 1
        
        try:
            report = lint_path(path, config=config, use_llm=args.llm)
            all_reports.append(report)
        except Exception as e:
            print(f"Error linting {path}: {e}", file=sys.stderr)
            return 1
    
    # Combine reports
    if len(all_reports) == 1:
        combined = all_reports[0]
    else:
        # Merge multiple reports
        combined = all_reports[0]
        for report in all_reports[1:]:
            combined.skills.extend(report.skills)
            combined.findings.update(report.findings)
            combined.scores.update(report.scores)
        
        # Recalculate summary
        total_findings = sum(len(f) for f in combined.findings.values())
        avg_score = (
            sum(s.value for s in combined.scores.values()) / len(combined.scores)
            if combined.scores
            else 0
        )
        combined.summary = {
            "total_skills": len(combined.skills),
            "total_findings": total_findings,
            "average_score": round(avg_score, 1),
        }
    
    # Format output
    if args.format == "json":
        output = format_json(combined)
    elif args.format == "sarif":
        output = format_sarif(combined)
    else:
        output = format_text(combined, use_color=not args.no_color)
    
    print(output)
    
    # Check exit code
    has_errors = any(
        any(f.severity.value == "error" for f in findings)
        for findings in combined.findings.values()
    )
    
    below_min_score = any(
        score.value < config.min_score for score in combined.scores.values()
    )
    
    if has_errors or below_min_score:
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
