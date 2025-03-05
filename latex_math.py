import re


# Define Greek letters mapping to LaTeX notation
greek_letters = {
    "α": "\\alpha",
    "β": "\\beta",
    "γ": "\\gamma",
    "δ": "\\delta",
    "ε": "\\epsilon",
    "ζ": "\\zeta",
    "η": "\\eta",
    "θ": "\\theta",
    "ι": "\\iota",
    "κ": "\\kappa",
    "λ": "\\lambda",
    "μ": "\\mu",
    "ν": "\\nu",
    "ξ": "\\xi",
    "ο": "o",
    "π": "\\pi",
    "ρ": "\\rho",
    "σ": "\\sigma",
    "τ": "\\tau",
    "υ": "\\upsilon",
    "φ": "\\phi",
    "χ": "\\chi",
    "ψ": "\\psi",
    "ω": "\\omega",
    "Γ": "\\Gamma",
    "Δ": "\\Delta",
    "Θ": "\\Theta",
    "Λ": "\\Lambda",
    "Ξ": "\\Xi",
    "Π": "\\Pi",
    "Σ": "\\Sigma",
    "Υ": "\\Upsilon",
    "Φ": "\\Phi",
    "Ψ": "\\Psi",
    "Ω": "\\Omega",
}


def simplify_equations(equation):
    """Clean up equation formatting for LaTeX"""
    equation = equation.replace("\\left(", "(").replace("\\right)", ")")
    equation = equation.replace("\\left[", "[").replace("\\right]", "]")
    equation = equation.replace("\\left{", "{").replace("\\right}", "}")
    equation = equation.replace("\\!", "")  # Remove unnecessary spacing commands

    equation = equation.replace(")\\,", ")")
    for s in ["=", "|", "\\le", "\\ge", "\\|", "-"]:

        equation = equation.replace(f"\n;{s};", f" {s} ")
        equation = equation.replace(f"\n\\;{s}\\;", f" {s} ")
        equation = equation.replace(f"\n\\,{s}\\,", f" {s} ")

        equation = equation.replace(f";{s};", f" {s} ")
        equation = equation.replace(f"\\;{s}\\;", f" {s} ")
        equation = equation.replace(f"\\,{s}\\,", f" {s} ")

    equation = equation.replace("=", " = ")  # Ensure proper spacing around equals sign

    # Fix common special characters in math
    equation = equation.replace("·", "\\cdot ")
    equation = equation.replace("…", "\\ldots ")
    equation = equation.replace("*", "\\ast ")  # Treat asterisks as multiplication

    return equation


def process_subscripts_in_math(math_content):
    """Process subscripts in math content to ensure proper LaTeX format"""
    # This regex finds patterns like x_i, x_{i}, etc.
    math_content = re.sub(r"_([a-zA-Z0-9])", r"_{\1}", math_content)

    return math_content


def protect_math_regions(content):
    """
    Protect math regions from markdown formatting by replacing them with placeholders
    Returns the modified content and a mapping to restore the math regions later
    """
    math_regions = {}

    # Handle display math first: $$..$$ and \[..\]
    patterns = [
        (
            r"\$\$(.*?)\$\$",
            "__DISPLAY_MATH_DOLLARS_{}__",
        ),  # Correctly handles double dollar display math
        (
            r"\$(.*?)\$",
            "__INLINE_MATH_DOLLARS_{}__",
        ),  # Added pattern for single dollar inline math
        (
            r"\\\[(.*?)\\\]",
            "__DISPLAY_MATH_BRACKETS_{}__",
        ),  # Corrects handling for \\[ \\] display math
        (
            r"\\\((.*?)\\\)",
            "__INLINE_MATH_PAREN_{}__",
        ),  # Added pattern for \\( \\) inline math
        (
            r"\\begin{equation}(.*?)\\end{equation}",
            "__DISPLAY_MATH_EQUATION_{}__",
        ),  # Correct pattern for equation environment
    ]

    for pattern, placeholder_template in patterns:
        matches = re.finditer(pattern, content, re.DOTALL)
        offset = 0
        content_modified = content

        for i, match in enumerate(matches):
            full_match = match.group(0)
            # math_content = match.group(1)
            placeholder = placeholder_template.format(i)

            # Get position in the modified content
            start_pos = content_modified.find(full_match, offset)
            if start_pos == -1:
                continue

            end_pos = start_pos + len(full_match)

            # Replace this instance with placeholder
            content_modified = (
                content_modified[:start_pos] + placeholder + content_modified[end_pos:]
            )

            # Store the original content
            math_regions[placeholder] = full_match

            # Update offset for next search
            offset = start_pos + len(placeholder)

        content = content_modified

    # Now handle inline math $...$
    inline_matches = re.finditer(r"\$(.*?)\$", content, re.DOTALL)
    offset = 0
    content_modified = content

    for i, match in enumerate(inline_matches):
        full_match = match.group(0)
        # math_content = match.group(1)
        placeholder = f"__INLINE_MATH_{i}__"

        # Get position in the modified content
        start_pos = content_modified.find(full_match, offset)
        if start_pos == -1:
            continue

        end_pos = start_pos + len(full_match)

        # Make sure this is not part of a display math that was missed
        if (start_pos > 0 and content_modified[start_pos - 1] == "$") or (
            end_pos < len(content_modified) and content_modified[end_pos] == "$"
        ):
            offset = end_pos
            continue

        # Replace this instance with placeholder
        content_modified = (
            content_modified[:start_pos] + placeholder + content_modified[end_pos:]
        )

        # Store the original content
        math_regions[placeholder] = full_match

        # Update offset for next search
        offset = start_pos + len(placeholder)

    return content_modified, math_regions


def remove_prefix(input_string, prefix):
    """
    Removes a prefix from the beginning of a string if it exists.

    Args:
    input_string (str): The string from which to remove the prefix.
    prefix (str): The prefix to remove.

    Returns:
    str: The string with the prefix removed if it was present.
    """
    if input_string.startswith(prefix):
        return input_string[len(prefix) :]
    return input_string


def remove_suffix(input_string, suffix):
    """
    Removes a suffix from the end of a string if it exists.

    Args:
    input_string (str): The string from which to remove the suffix.
    suffix (str): The suffix to remove.

    Returns:
    str: The string with the suffix removed if it was present.
    """
    if input_string.endswith(suffix):
        return input_string[: -len(suffix)]
    return input_string


def remove_presuffix(input_string, prefix, suffix):
    return remove_suffix(remove_prefix(input_string, prefix), suffix)


def remove_math_presuffix(input_string):
    prefixes_suffixes = [
        ("$$", "$$"),
        ("\\[", "\\]"),
        ("\\begin{equation}", "\\end{equation}"),
        ("$", "$"),
        ("\\(", "\\)"),
    ]
    for prefix, suffix in prefixes_suffixes:
        output_string = remove_suffix(remove_prefix(input_string, prefix), suffix)
        if output_string != input_string:
            break
        input_string = output_string
    return output_string


def process_math_content(math_content, escape_underscores=False):
    """Process math content to ensure proper LaTeX formatting"""
    # First, unescape any already escaped underscores
    math_content = math_content.replace("\\_", "_")

    # Convert Greek letters
    for greek, latex in greek_letters.items():
        math_content = math_content.replace(greek, latex)

    # Handle subscripts
    math_content = process_subscripts_in_math(math_content)

    # Clean up equation formatting
    math_content = simplify_equations(math_content)

    if escape_underscores:
        math_content = math_content.replace("_", "\\_")

    return math_content.strip()


def restore_math_regions(
    content,
    math_regions,
    # eq_marker="<equation>",
    # eq_marker_end="</equation>",
    # inline_math_marker="<math>",
    # inline_math_marker_end="</math>",
    eq_marker="$$",
    eq_marker_end="$$",
    inline_math_marker="$",
    inline_math_marker_end="$",
    escape_underscores=False,
):
    for placeholder, math_text in math_regions.items():
        # Process based on placeholder type
        if placeholder.startswith("__DISPLAY_MATH_DOLLARS_"):
            # Display math mode with $$..$$
            math_content = remove_presuffix(math_text, "$$", "$$")  # Remove $$ markers
            processed_math = process_math_content(math_content, escape_underscores)
            math_regions[
                placeholder
            ] = f"{eq_marker}\n{processed_math}\n{eq_marker_end}"
        elif placeholder.startswith("__DISPLAY_MATH_BRACKETS_"):
            # Already in display math mode with \[..\]
            math_content = remove_presuffix(
                math_text, "\\[", "\\]"
            )  # Remove \[ and \] markers
            processed_math = process_math_content(math_content, escape_underscores)
            math_regions[
                placeholder
            ] = f"{eq_marker}\n{processed_math}\n{eq_marker_end}"
        elif placeholder.startswith("__DISPLAY_MATH_EQUATION_"):
            # Already in equation environment
            math_content = math_content = remove_presuffix(
                math_text, "\\begin{equation}", "\\end{equation}"
            )
            processed_math = process_math_content(math_content, escape_underscores)
            math_regions[
                placeholder
            ] = f"{eq_marker}\n{processed_math}\n{eq_marker_end}"
        elif placeholder.startswith("__INLINE_MATH_"):
            # Inline math with $...$
            math_content = remove_math_presuffix(math_text)  # Remove markers
            processed_math = process_math_content(math_content, escape_underscores)
            math_regions[
                placeholder
            ] = f"{inline_math_marker}{processed_math}{inline_math_marker_end}"
        else:
            print("Failed: unknown placeholder={placeholder}")

    # Restore math regions (already processed earlier)
    for placeholder, processed_math_text in math_regions.items():
        content = content.replace(placeholder, processed_math_text)
    return content


def process_greek_letters_in_text(content, math_regions):
    """Process Greek letters in text (non-math) portions"""
    # Process text character by character, skipping math placeholders
    result = []
    i = 0
    while i < len(content):
        # Check if current position starts a math placeholder
        is_math_placeholder = False
        for placeholder in math_regions.keys():
            if content[i:].startswith(placeholder):
                result.append(placeholder)
                i += len(placeholder)
                is_math_placeholder = True
                break

        if is_math_placeholder:
            continue

        # If not a math placeholder, check for Greek letters
        found_greek = False
        for greek, latex in greek_letters.items():
            if i + len(greek) <= len(content) and content[i : i + len(greek)] == greek:
                result.append(
                    f"${latex}$"
                )  # Changed to use inline math for Greek in text
                i += len(greek)
                found_greek = True
                break

        if not found_greek:
            result.append(content[i])
            i += 1

    return "".join(result)
