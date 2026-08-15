"""Generate the human-readable AT command reference from the registry."""

from __future__ import annotations

from pathlib import Path

from campnet.at_registry import COMMAND_REGISTRY


def generate_command_reference() -> str:
    lines = [
        "# CampNet AT Command Reference",
        "",
        "Generated from `campnet.at_registry`; do not edit by hand.",
        "",
    ]
    for item in sorted(COMMAND_REGISTRY.values(), key=lambda value: value.identifier):
        if item.execution.recommended_timeout_seconds > 30:
            invocation = f"gl_modem -B 1-1.2 SAT sp {item.command}"
        else:
            invocation = f"gl_modem -B 1-1.2 AT '{item.command}'"
        lines.extend(
            [
                f"## `{item.identifier}`",
                "",
                f"- Command: `{item.command}`",
                f"- Category: {item.category}",
                f"- Type: {item.command_type}",
                f"- Safety: {item.safety}",
                f"- Timeout: {item.execution.recommended_timeout_seconds:g} seconds",
                f"- Parser: `{item.parser}`" if item.parser else "- Parser: none",
                "",
                item.summary,
                "",
                f"Purpose: {item.purpose}",
                "",
                f"Expected response: {item.expected_response}",
                "",
            ]
        )
        if item.side_effects:
            lines.extend(("Side effects:", "", *(f"- {value}" for value in item.side_effects), ""))
        lines.extend(
            (
                "```bash",
                f"# {item.summary}",
                f"# {item.purpose}",
                invocation,
                "```",
                "",
            )
        )
    return "\n".join(lines)


def main() -> None:
    target = Path("docs/at-command-reference.md")
    target.write_text(generate_command_reference(), encoding="utf-8")


if __name__ == "__main__":
    main()
