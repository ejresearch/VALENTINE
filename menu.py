#!/usr/bin/env python3
"""Interactive menu for screenplay formatter."""

import os
import sys
from pathlib import Path

def show_menu():
    """Display the main menu."""
    print("\n" + "="*50)
    print("       SCREENPLAY FORMATTER MENU")
    print("="*50)
    print("1. Format screenplay")
    print("2. Fix screenplay with AI (requires OpenAI API key)")
    print("3. Smart format (auto-detect if AI fixing needed)")
    print("4. Configuration (set API key, preferences)")
    print("5. List files in current directory")
    print("6. Exit")
    print("="*50)

def get_input_file():
    """Get input file from user."""
    while True:
        filename = input("Enter input filename: ").strip()
        if not filename:
            print("Please enter a filename.")
            continue
        if not os.path.exists(filename):
            print(f"File '{filename}' not found.")
            continue
        return filename

def get_output_file(default_ext="txt"):
    """Get output file from user."""
    filename = input(f"Enter output filename (or press Enter for auto-generated .{default_ext}): ").strip()
    if not filename:
        return f"output.{default_ext}"
    return filename

def choose_format():
    """Let user choose output format."""
    print("\nChoose output format:")
    print("1. Text (.txt)")
    print("2. Word Document (.docx)")
    print("3. PDF (.pdf)")

    while True:
        format_choice = input("Enter format choice (1-3): ").strip()
        if format_choice == "1":
            return "text", "txt"
        elif format_choice == "2":
            return "docx", "docx"
        elif format_choice == "3":
            return "pdf", "pdf"
        else:
            print("Invalid choice. Please enter 1, 2, or 3.")

def run_command(cmd):
    """Run a command and show the result."""
    print(f"\nRunning: {cmd}")
    print("-" * 50)
    result = os.system(cmd)
    if result == 0:
        print("✓ Command completed successfully!")
    else:
        print("✗ Command failed!")
    input("\nPress Enter to continue...")

def list_files():
    """List files in current directory."""
    print("\nFiles in current directory:")
    print("-" * 30)
    for file in sorted(os.listdir(".")):
        if os.path.isfile(file):
            size = os.path.getsize(file)
            print(f"{file:<30} ({size} bytes)")
    input("\nPress Enter to continue...")

def config_menu():
    """Configuration menu."""
    while True:
        print("\n" + "="*40)
        print("      CONFIGURATION MENU")
        print("="*40)
        print("1. Show current configuration")
        print("2. Set OpenAI API key")
        print("3. Remove API key")
        print("4. Set default model")
        print("5. Set default confidence")
        print("6. Set strict validation")
        print("7. Reset to defaults")
        print("8. Back to main menu")
        print("="*40)

        choice = input("\nEnter your choice (1-8): ").strip()

        if choice == "1":
            # Show config
            cmd = 'screenplay-format config --show'
            run_command(cmd)

        elif choice == "2":
            # Set API key
            api_key = input("Enter your OpenAI API key: ").strip()
            if api_key:
                cmd = f'screenplay-format config --set-api-key "{api_key}"'
                run_command(cmd)

        elif choice == "3":
            # Remove API key
            cmd = 'screenplay-format config --remove-api-key'
            run_command(cmd)

        elif choice == "4":
            # Set model
            print("Available models: gpt-4o, gpt-4o-mini, gpt-4-turbo, gpt-3.5-turbo")
            model = input("Enter model name: ").strip()
            if model:
                cmd = f'screenplay-format config --model "{model}"'
                run_command(cmd)

        elif choice == "5":
            # Set confidence
            confidence = input("Enter confidence threshold (0.0-1.0): ").strip()
            if confidence:
                cmd = f'screenplay-format config --confidence {confidence}'
                run_command(cmd)

        elif choice == "6":
            # Set strict validation
            strict = input("Enable strict validation? (y/n): ").strip().lower()
            if strict in ['y', 'n']:
                strict_bool = 'true' if strict == 'y' else 'false'
                cmd = f'screenplay-format config --strict {strict_bool}'
                run_command(cmd)

        elif choice == "7":
            # Reset config
            cmd = 'screenplay-format config --reset'
            run_command(cmd)

        elif choice == "8":
            # Back to main menu
            break

        else:
            print("\nInvalid choice. Please enter 1-8.")
            input("Press Enter to continue...")

def main():
    """Main menu loop."""
    while True:
        show_menu()
        choice = input("\nEnter your choice (1-6): ").strip()

        if choice == "1":
            # Format screenplay
            input_file = get_input_file()
            format_type, extension = choose_format()
            output_file = get_output_file(extension)
            cmd = f'screenplay-format format "{input_file}" "{output_file}" --format {format_type} --validate'
            run_command(cmd)

        elif choice == "2":
            # Fix with AI
            input_file = get_input_file()
            dry_run = input("Dry run mode? (y/n): ").strip().lower() == 'y'
            confidence = input("Minimum confidence (0.1-1.0, default 0.8): ").strip()
            if not confidence:
                confidence = "0.8"

            cmd = f'screenplay-format fix "{input_file}"'
            if dry_run:
                cmd += " --dry-run"
            cmd += f" --confidence {confidence}"

            audit_file = input("Export audit log? (filename or Enter to skip): ").strip()
            if audit_file:
                cmd += f' --audit "{audit_file}"'

            run_command(cmd)

        elif choice == "3":
            # Smart format (auto-detect if AI fixing needed)
            input_file = get_input_file()

            print("\nAnalyzing screenplay formatting...")
            # First, validate the screenplay to check if it has errors
            validate_cmd = f'screenplay-format validate "{input_file}"'
            print(f"Running: {validate_cmd}")
            result = os.system(validate_cmd)

            if result == 0:
                # No validation errors - use regular formatting
                print("\n✓ Screenplay is well-formatted. Using standard formatting...")
                format_type, extension = choose_format()
                output_file = get_output_file(extension)
                cmd = f'screenplay-format format "{input_file}" "{output_file}" --format {format_type} --validate'
                run_command(cmd)
            else:
                # Validation errors found - use AI fixing
                print("\n⚠ Formatting issues detected. Using AI-powered fixing...")

                # Check if API key is configured
                config_check_cmd = 'screenplay-format config --show'
                print("Checking API configuration...")
                os.system(config_check_cmd)

                if input("\nProceed with AI fixing? (y/n): ").strip().lower() == 'y':
                    dry_run = input("Dry run mode first? (y/n): ").strip().lower() == 'y'
                    confidence = input("Minimum confidence (0.1-1.0, default 0.8): ").strip()
                    if not confidence:
                        confidence = "0.8"

                    cmd = f'screenplay-format fix "{input_file}"'
                    if dry_run:
                        cmd += " --dry-run"
                    cmd += f" --confidence {confidence}"

                    audit_file = input("Export audit log? (filename or Enter to skip): ").strip()
                    if audit_file:
                        cmd += f' --audit "{audit_file}"'

                    run_command(cmd)

                    # If not dry run, offer to format the result
                    if not dry_run:
                        if input("\nFormat the AI-corrected screenplay? (y/n): ").strip().lower() == 'y':
                            format_type, extension = choose_format()
                            output_file = get_output_file(extension)
                            fixed_input = input("Enter the AI-corrected filename: ").strip() or input_file
                            cmd = f'screenplay-format format "{fixed_input}" "{output_file}" --format {format_type}'
                            run_command(cmd)

        elif choice == "4":
            # Configuration menu
            config_menu()

        elif choice == "5":
            # List files
            list_files()

        elif choice == "6":
            print("\nGoodbye!")
            sys.exit(0)

        else:
            print("\nInvalid choice. Please enter 1-6.")
            input("Press Enter to continue...")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nGoodbye!")
        sys.exit(0)