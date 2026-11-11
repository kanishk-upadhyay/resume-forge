"""Shell autocompletion script generator for ResumeForge CLI."""

from typing import List


COMMANDS = [
    "compile", "export", "audit", "diff", "letter",
    "hunt", "tailor", "variant", "template", "studio", "completion"
]

TEMPLATES = [
    "cern", "harvard", "jakes", "minimalist", "quant", "awesome", "academic"
]


def generate_bash_completion() -> str:
    return f"""# bash completion for resume-forge
_resume_forge_completion() {{
    local cur prev words cword
    _init_completion || return

    local commands="{' '.join(COMMANDS)}"
    local templates="{' '.join(TEMPLATES)}"

    case "${{prev}}" in
        -t|--template)
            COMPREPLY=( $(compgen -W "${{templates}}" -- "${{cur}}") )
            return 0
            ;;
        -f|--format)
            COMPREPLY=( $(compgen -W "pdf tex json html md png webp" -- "${{cur}}") )
            return 0
            ;;
        *)
            ;;
    esac

    if [[ ${{cword}} -eq 1 ]]; then
        COMPREPLY=( $(compgen -W "${{commands}}" -- "${{cur}}") )
        return 0
    fi

    case "${{words[1]}}" in
        compile)
            COMPREPLY=( $(compgen -W "-o --output -t --template --all-templates -f --format --dpi --font-size --line-height --margin" -- "${{cur}}") )
            ;;
        export)
            COMPREPLY=( $(compgen -W "-o --output -t --template --all-templates -f --format" -- "${{cur}}") )
            ;;
        audit)
            COMPREPLY=( $(compgen -W "--jd -v --verbose" -- "${{cur}}") )
            ;;
        diff)
            COMPREPLY=( $(compgen -W "--json --no-color" -- "${{cur}}") )
            ;;
        letter)
            COMPREPLY=( $(compgen -W "create compile export --company --role --recipient --output -t --template" -- "${{cur}}") )
            ;;
        template)
            COMPREPLY=( $(compgen -W "list info ${{templates}}" -- "${{cur}}") )
            ;;
        *)
            ;;
    esac
}}
complete -F _resume_forge_completion resume-forge
"""


def generate_zsh_completion() -> str:
    return f"""#compdef resume-forge

_resume_forge() {{
    local -a commands templates formats
    commands=({' '.join(COMMANDS)})
    templates=({' '.join(TEMPLATES)})
    formats=(pdf tex json html md png webp)

    _arguments -C \\
        '1: :->command' \\
        '*:: :->args'

    case $state in
        command)
            _describe -t commands 'resume-forge command' commands
            ;;
        args)
            case $words[1] in
                compile)
                    _arguments \\
                        '-o[Output destination path]:file:_files' \\
                        '-t[Selected template]:template:($templates)' \\
                        '--template[Selected template]:template:($templates)' \\
                        '--all-templates[Compile all 7 templates simultaneously]' \\
                        '-f[Format (pdf, png, webp)]:format:($formats)' \\
                        '--format[Format (pdf, png, webp)]:format:($formats)' \\
                        '--dpi[DPI for image export (default: 300)]' \\
                        '*:input file:_files'
                    ;;
                export)
                    _arguments \\
                        '-o[Output destination path]:file:_files' \\
                        '-t[Selected template]:template:($templates)' \\
                        '--all-templates[Export across all templates]' \\
                        '-f[Output format]:format:(tex json html md)' \\
                        '*:input file:_files'
                    ;;
                audit)
                    _arguments \\
                        '--jd[Job description text, file path, or live URL]' \\
                        '*:resume file:_files'
                    ;;
                diff)
                    _arguments \\
                        '--json[Output JSON formatted diff]' \\
                        '--no-color[Disable ANSI terminal colors]' \\
                        '1:first resume file:_files' \\
                        '2:second resume file:_files'
                    ;;
                letter)
                    _arguments \\
                        '1:(create compile export)' \\
                        '-t[Selected template]:template:($templates)' \\
                        '--company[Target company name]' \\
                        '--role[Target role title]' \\
                        '-o[Output file path]:file:_files' \\
                        '*:resume file:_files'
                    ;;
                template)
                    _arguments \\
                        '1:(list info)' \\
                        '2:template:($templates)'
                    ;;
            esac
            ;;
    esac
}}

_resume_forge "$@"
"""


def generate_fish_completion() -> str:
    return f"""# fish completion for resume-forge
set -l commands {' '.join(COMMANDS)}
set -l templates {' '.join(TEMPLATES)}

complete -c resume-forge -f
complete -c resume-forge -n "__fish_use_subcommand" -a "$commands"

# Template flags
complete -c resume-forge -s t -l template -x -a "$templates"
complete -c resume-forge -s f -l format -x -a "pdf tex json html md png webp"

# Subcommands
complete -c resume-forge -n "__fish_seen_subcommand_from template" -a "list info $templates"
complete -c resume-forge -n "__fish_seen_subcommand_from letter" -a "create compile export"
complete -c resume-forge -n "__fish_seen_subcommand_from diff" -l json -d "Export JSON diff"
complete -c resume-forge -n "__fish_seen_subcommand_from compile" -l all-templates -d "Compile all 7 templates"
"""
