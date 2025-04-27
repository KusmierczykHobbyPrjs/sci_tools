import re
import sys
import argparse
from collections import OrderedDict
from latex_math import (
    process_greek_letters_in_text,
    protect_math_regions,
    restore_math_regions,
    process_math_content,
)


def clean_text(text):
    """Clean special characters for LaTeX"""
    text = text.replace("&", "\\&")  # Fix ampersand for LaTeX
    text = text.replace(
        """, "``")   # Fix opening quotes
    text = text.replace(""",
        "''",
    )  # Fix closing quotes
    text = text.replace("%", "\\%")  # Escape percent signs
    # Don't escape underscores globally - will handle in context
    return text


def clean_url(url):
    """Clean URLs by removing fragments and parameters"""
    # return re.sub(r"[#?].*", "", url)  # Remove fragments and parameters from URL
    # print(f"clean url {url}")
    return url.split("#")[0]


def fix_missing_parenthesis_href(text):
    """
    Appends ")" after each \\href{something}{something} occurrence.
    """
    pattern = r"(\\href\{[^}]+\}\{[^}]+\})"
    modified_text = re.sub(pattern, r"\1)", text)
    return modified_text


def replace_empty_hrefs(latex_text: str, href_directly: bool = True) -> str:
    """
    Replaces empty hrefs in LaTeX with their address.

    Args:
        latex_text (str): The input LaTeX string.
        href_directly (bool): If True, use the URL as link text
    """
    pattern = re.compile(r"(\\href\{([^{}]*)\}\{\})")

    if href_directly:
        return pattern.sub(
            lambda m: f"\\href{{{m.group(2)}}}{{{m.group(2)}}}", latex_text
        )
    else:
        return pattern.sub(lambda m: f"\\href{{{m.group(2)}}}{{link}}", latex_text)


def process_links(content):
    """
    Process all markdown links to LaTeX href commands with improved cleaning
    """
    content = re.sub(
        r"\[(.*?)\]\((https?:\/\/[^\s]+)\)",
        lambda m: f"\\href{{{clean_url(m.group(2))}}}{{{m.group(1)}}}",
        content,
    )
    content = replace_empty_hrefs(content)
    content = fix_missing_parenthesis_href(content)
    return content


def remove_duplicates(pairs):
    """
    Removes duplicate keys while keeping the first occurrence in order,
    but retaining the longest value for each key.

    Args:
        pairs (list of tuple): List of (value, key) pairs.

    Returns:
        list of tuple: Filtered list maintaining order and longest value preference.
    """
    seen = OrderedDict()

    for value, key in pairs:
        if key not in seen or len(value) > len(seen[key]):
            seen[key] = value

    return [(seen[key], key) for key in seen]


def collect_references(content):
    """
    Collect all links from the content for the references section
    Returns a list of tuples (link_text, url)
    """
    references = []
    # Match [text](url) pattern
    pattern = r"\[(.*?)\]\((https?:\/\/[^\s)]+)(?:[^\)])?\)"
    for match in re.finditer(pattern, content):
        link_text = match.group(1)
        url = clean_url(match.group(2))
        link_text = link_text.split("]")[-1]
        references.append((link_text, url))

    return remove_duplicates(references)


def upgrade_sections_depth(text):
    """Upgrade section levels if needed"""
    i = 0
    while not ("\n# " in text):
        text = text.replace("\n##", "\n#")
        i += 1
        if i > 4:
            break
    return text


def remove_section_numbers(markdown_text):
    """
    Removes hardcoded section numbers from markdown headers, ensuring robustness for various formats.
    """
    pattern = r"^(#+)\s*\**\d+(?:\.\d+)*\.?\s*(.*)\**$"
    modified_text = re.sub(pattern, r"\1 **\2**", markdown_text, flags=re.MULTILINE)
    return modified_text


def protect_code_blocks(content):
    code_blocks = {}
    for i, match in enumerate(re.finditer(r"```(.*?)```", content, flags=re.DOTALL)):
        placeholder = f"__CODE_BLOCK_{i}__"
        code_blocks[placeholder] = match.group(0)
        content = content.replace(match.group(0), placeholder, 1)
    return content, code_blocks


def restore_code_blocks(content, code_blocks):
    for placeholder, code_block in code_blocks.items():
        code_match = re.match(r"```(.*?)```", code_block, flags=re.DOTALL)
        if code_match:
            code_content = code_match.group(1)
            language_line = code_content.split("\n", 1)

            if len(language_line) > 1 and language_line[0].strip() == "math":
                # Math code blocks go to equation environment
                math_content = language_line[1]
                processed_math = process_math_content(math_content)
                replacement = (
                    f"\\begin{{equation}}\n{processed_math}\n\\end{{equation}}"
                )
            else:
                # Regular code blocks go to verbatim
                replacement = f"\\begin{{verbatim}}{code_content}\\end{{verbatim}}"

            content = content.replace(placeholder, replacement)
    return content


def process_lists(content):
    list_sections = re.findall(r"(?:^|\n)(?:- .*(?:\n|$))+", content)
    for section in list_sections:
        items = re.findall(r"^- (.*)$", section, re.MULTILINE)
        if items:
            replacement = "\\begin{itemize}\n"
            for item in items:
                replacement += f"\\item {item.strip()}\n"
            replacement += "\\end{itemize}"
            content = content.replace(section, replacement)
    return content


def markdown_to_latex(input_file, output_file, include_references=True):
    """Main function to convert markdown to LaTeX"""
    with open(input_file, "r", encoding="utf-8") as f:
        content = f.read()

    # Collect references before any processing
    references = collect_references(content)

    # Step 1: Clean basic text (but don't escape underscores yet)
    content = clean_text(content)

    # Step 2: Protect code blocks
    content, code_blocks = protect_code_blocks(content)

    # Step 3: Protect math regions from markdown formatting
    content, math_regions = protect_math_regions(content)

    # Step 4: Convert headers
    content = remove_section_numbers(content)
    content = upgrade_sections_depth(content)
    content = re.sub(r"^# (.*?)$", r"\\section{\1}", content, flags=re.MULTILINE)
    content = re.sub(r"^## (.*?)$", r"\\subsection{\1}", content, flags=re.MULTILINE)
    content = re.sub(
        r"^### (.*?)$", r"\\subsubsection{\1}", content, flags=re.MULTILINE
    )
    content = re.sub(r"^#### (.*?)$", r"\\paragraph{\1}", content, flags=re.MULTILINE)
    content = re.sub(r"^##### (.*?)$", r"\1", content, flags=re.MULTILINE)

    # Step 5: Apply markdown formatting (bold, italic, etc.)
    content = re.sub(r"\*\*(.*?)\*\*", r"\\textbf{\1}", content)
    content = re.sub(r"\*(.*?)\*", r"\\textit{\1}", content)

    # Step 6: Process Greek letters in text portions
    content = process_greek_letters_in_text(content, math_regions)

    # Step 7: Process links
    # Use the new link processing function
    content = process_links(content)

    # Step 8: Now process math regions
    content = restore_math_regions(
        content,
        math_regions,
    )

    # Restore code blocks and convert them to verbatim
    content = restore_code_blocks(content, code_blocks)

    # Process itemized lists
    content = process_lists(content)

    # Add references section if requested
    if include_references and references:
        content += "\n\n%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%\n\n\\section{References}\n\\begin{enumerate}\n"
        for i, (text, url) in enumerate(references, 1):
            content += f"\\item {text}: \\url{{{url}}}\n"
        content += "\\end{enumerate}\n"

    # Final cleanup - check for trailing periods after \href commands
    content = re.sub(r"(\\href\{[^{}]*\}\{[^{}]*\})\.", r"\1.", content)

    # Wrap document in LaTeX structure
    latex_doc = (
        """\\documentclass{article}
            \\usepackage{amsmath, amssymb, url, hyperref}
            \\begin{document}
            """
        + content
        + """
        \\end{document}
        """
    )

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(latex_doc)

    print(f"Converted {input_file} to {output_file}")


def main():
    parser = argparse.ArgumentParser(
        description="Converts (GPT-generated) Markdown to LaTeX"
    )
    parser.add_argument("input", help="Input markdown file")
    parser.add_argument("output", help="Output LaTeX file")
    parser.add_argument(
        "--no-references",
        dest="include_references",
        action="store_false",
        help="Disable the references section",
    )

    args = parser.parse_args()

    markdown_to_latex(args.input, args.output, args.include_references)


if __name__ == "__main__":
    main()
