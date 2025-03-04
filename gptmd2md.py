import re
import argparse
from collections import OrderedDict
from latex_math import (
    process_greek_letters_in_text,
    protect_math_regions,
    restore_math_regions,
)


def clean_text(text):
    """Clean special characters for LaTeX"""
    text = text.replace("&", "and")  # Fix ampersand for LaTeX
    text = text.replace("`", "'")  # Fix opening quotes
    text = text.replace("’", "'")  # Fix opening quotes
    text = text.replace("“", '"')  # Fix opening quotes
    text = text.replace("”", '"')  # Fix opening quotes

    return text


def clean_url(url):
    """Clean URLs by removing fragments and parameters"""
    # return re.sub(r"[#?].*", "", url)  # Remove fragments and parameters from URL
    # print(f"clean url {url}")
    return url.split("#")[0]


def fix_missing_parenthesis_href(text):
    """
    Appends ")" after each \href{something}{something} occurrence.
    """
    pattern = r"(\\href\{[^}]+\}\{[^}]+\})"
    modified_text = re.sub(pattern, r"\1)", text)
    return modified_text


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


def clean_markdown(
    input_file,
    output_file,
    include_references=True,
    eq_marker="$$",
    eq_marker_end="$$",
    inline_math_marker="$",
    inline_math_marker_end="$",
    escape_underscores=False,
):
    """Main function to convert markdown"""
    with open(input_file, "r", encoding="utf-8") as f:
        content = f.read()

    # Collect references before any processing
    references = collect_references(content)

    # Step 1: Clean basic text (but don't escape underscores yet)
    content = clean_text(content)

    # Step 3: Protect math regions from markdown formatting
    content, math_regions = protect_math_regions(content)

    # Step 6: Process Greek letters in text portions
    content = process_greek_letters_in_text(content, math_regions)

    # Step 8: Now process math regions
    content = restore_math_regions(
        content,
        math_regions,
        eq_marker,
        eq_marker_end,
        inline_math_marker,
        inline_math_marker_end,
        escape_underscores=escape_underscores,
    )

    # Add references section if requested
    if include_references and references:
        content += "\n\n# References\n"
        for i, (text, url) in enumerate(references, 1):
            content += f" - {text}: {url}\n"

    # Wrap document
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"Converted {input_file} to {output_file}")


def main():
    parser = argparse.ArgumentParser(description="Cleans GPT Markdown")
    parser.add_argument("input", help="Input markdown file")
    parser.add_argument("output", help="Output markdown file")
    parser.add_argument(
        "--gdoc_math",
        dest="gdoc_math",
        action="store_true",
        # default=False,
        help="Use $$ for math blocks and escape underscores (for Google Docs with Auto-LaTeX Equations extension)",
    )
    parser.add_argument(
        "--no-references",
        dest="include_references",
        action="store_false",
        help="Disable the references section",
    )
    parser.add_argument(
        "--math",
        dest="math",
        action="store_true",
        # default=False,
        help="Use <equation> for math blocks",
    )

    args = parser.parse_args()

    if args.math:
        eq_marker = "<equation>"
        eq_marker_end = "</equation>"
        inline_math_marker = "<equation>"
        inline_math_marker_end = "</equation>"
    else:
        eq_marker = "\n$$"
        eq_marker_end = "$$\n"
        if args.gdoc_math:
            inline_math_marker = "$$"
            inline_math_marker_end = "$$"
            escape_underscores = True
        else:
            inline_math_marker = "$"
            inline_math_marker_end = "$"
            escape_underscores = False

    clean_markdown(
        args.input,
        args.output,
        args.include_references,
        eq_marker,
        eq_marker_end,
        inline_math_marker,
        inline_math_marker_end,
        escape_underscores=escape_underscores,
    )


if __name__ == "__main__":
    main()
