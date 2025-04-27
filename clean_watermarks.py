#!/usr/bin/env python3
import re
import argparse
import sys
import unicodedata
import json
from collections import Counter

def analyze_watermarks(text, preserve_multiple_spaces=True):
    """
    Detect, analyze and remove various text watermarking techniques.
    
    Args:
        text: The original text to analyze
        preserve_multiple_spaces: If True, multiple spaces will be preserved in the output
    
    Returns:
        - cleaned text
        - detailed statistics on removed watermarks
        - character-by-character analysis of removed elements
    """
    original_text = text
    watermark_stats = {}
    character_analysis = []
    
    # Track position shifts as we remove characters
    position_shift = 0
    
    # 1. Analyze invisible Unicode characters
    invisible_chars = {
        '\u200B': 'Zero Width Space',
        '\u200C': 'Zero Width Non-Joiner',
        '\u200D': 'Zero Width Joiner',
        '\u202F': 'Narrow No-Break Space',
        '\u2060': 'Word Joiner',
        '\uFEFF': 'Zero Width No-Break Space'
    }
    
    invisible_counts = Counter()
    
    for match in re.finditer(r'[\u200B\u200C\u200D\u202F\u2060\uFEFF]', text):
        char = match.group(0)
        orig_pos = match.start()
        invisible_counts[char] += 1
        
        # Record detailed analysis
        character_analysis.append({
            'original_position': orig_pos,
            'adjusted_position': orig_pos - position_shift,
            'character': char,
            'unicode': f'U+{ord(char):04X}',
            'name': invisible_chars.get(char, 'Unknown invisible character'),
            'category': 'Invisible Character',
            'context': get_context(text, orig_pos)
        })
    
    # Update the text by removing invisible characters
    invisible_chars_pattern = re.compile(r'[\u200B\u200C\u200D\u202F\u2060\uFEFF]')
    text = invisible_chars_pattern.sub('', text)
    
    if sum(invisible_counts.values()) > 0:
        watermark_stats["Invisible Characters"] = {
            'total': sum(invisible_counts.values()),
            'details': {f"U+{ord(char):04X} ({invisible_chars[char]})": count 
                       for char, count in invisible_counts.items()}
        }
        position_shift += sum(invisible_counts.values())
    
    # 2. Detect and replace homoglyphs (characters that look like standard ones)
    homoglyph_map = {
        # Cyrillic letters that look like Latin
        'а': ('a', 'Cyrillic small letter a'),
        'е': ('e', 'Cyrillic small letter ie'),
        'о': ('o', 'Cyrillic small letter o'),
        'р': ('p', 'Cyrillic small letter er'),
        'с': ('c', 'Cyrillic small letter es'),
        'х': ('x', 'Cyrillic small letter ha'),
        'В': ('B', 'Cyrillic capital letter ve'),
        'Н': ('H', 'Cyrillic capital letter en'),
        'М': ('M', 'Cyrillic capital letter em'),
        'К': ('K', 'Cyrillic capital letter ka'),
        
        # Mathematical symbols that look like letters
        '𝐚': ('a', 'Mathematical bold small a'),
        '𝐛': ('b', 'Mathematical bold small b'),
        '𝐀': ('A', 'Mathematical bold capital A'),
        '𝐁': ('B', 'Mathematical bold capital B'),
        '𝑎': ('a', 'Mathematical italic small a'),
        '𝑏': ('b', 'Mathematical italic small b'),
        '𝒂': ('a', 'Mathematical bold italic small a'),
        '𝒃': ('b', 'Mathematical bold italic small b'),
        
        # Other common homoglyphs
        'ɑ': ('a', 'Latin small letter alpha'),
        'ℯ': ('e', 'Script small e'),
        'ｉ': ('i', 'Fullwidth latin small letter i'),
        'ｏ': ('o', 'Fullwidth latin small letter o'),
    }
    
    homoglyph_counts = Counter()
    
    # We need to search for homoglyphs one by one to track their positions
    for char, (replacement, description) in homoglyph_map.items():
        for match in re.finditer(re.escape(char), text):
            orig_pos = match.start()
            homoglyph_counts[char] += 1
            
            # Record detailed analysis
            character_analysis.append({
                'original_position': orig_pos,
                'adjusted_position': orig_pos - position_shift,
                'character': char,
                'replacement': replacement,
                'unicode': f'U+{ord(char):04X}',
                'name': description,
                'category': 'Homoglyph Substitution',
                'context': get_context(text, orig_pos)
            })
    
    # Replace homoglyphs
    for char, (replacement, _) in homoglyph_map.items():
        text = text.replace(char, replacement)
    
    if sum(homoglyph_counts.values()) > 0:
        watermark_stats["Homoglyph Substitutions"] = {
            'total': sum(homoglyph_counts.values()),
            'details': {f"U+{ord(char):04X} ({homoglyph_map[char][1]})": count 
                       for char, count in homoglyph_counts.items()}
        }
    
    # 3. Analyze whitespace variations
    whitespace_map = {
        '\u00A0': 'Non-Breaking Space',
        '\u2000': 'En Quad',
        '\u2001': 'Em Quad',
        '\u2002': 'En Space',
        '\u2003': 'Em Space',
        '\u2004': 'Three-Per-Em Space',
        '\u2005': 'Four-Per-Em Space',
        '\u2006': 'Six-Per-Em Space',
        '\u2007': 'Figure Space',
        '\u2008': 'Punctuation Space',
        '\u2009': 'Thin Space',
        '\u200A': 'Hair Space',
        '\u2028': 'Line Separator',
        '\u2029': 'Paragraph Separator',
        '\u205F': 'Medium Mathematical Space',
        '\u3000': 'Ideographic Space'
    }
    
    whitespace_counts = Counter()
    
    # Find all special whitespace characters
    for match in re.finditer(r'[\u00A0\u2000-\u200A\u2028\u2029\u205F\u3000]', text):
        char = match.group(0)
        orig_pos = match.start()
        whitespace_counts[char] += 1
        
        # Record detailed analysis
        character_analysis.append({
            'original_position': orig_pos,
            'adjusted_position': orig_pos - position_shift,
            'character': char,
            'replacement': ' ',
            'unicode': f'U+{ord(char):04X}',
            'name': whitespace_map.get(char, 'Special whitespace'),
            'category': 'Whitespace Variation',
            'context': get_context(text, orig_pos)
        })
    
    # Replace special whitespace with regular spaces
    whitespace_pattern = re.compile(r'[\u00A0\u2000-\u200A\u2028\u2029\u205F\u3000]')
    text = whitespace_pattern.sub(' ', text)
    
    # ANALYSIS ONLY: Detect multiple spaces but DO NOT replace them
    multiple_spaces_pattern = re.compile(r' {2,}')
    multiple_spaces_count = 0
    
    # Just analyze multiple spaces without replacing them
    for match in re.finditer(multiple_spaces_pattern, text):
        spaces = match.group(0)
        orig_pos = match.start()
        multiple_spaces_count += 1
        
        # Record detailed analysis
        character_analysis.append({
            'original_position': orig_pos,
            'adjusted_position': orig_pos - position_shift,
            'character': spaces,
            'replacement': spaces,  # No replacement, we preserve the spaces
            'unicode': 'N/A',
            'name': f'Multiple Spaces ({len(spaces)} spaces)',
            'category': 'Multiple Spaces',
            'context': get_context(text, orig_pos),
            'preserved': True
        })
    
    if sum(whitespace_counts.values()) > 0 or multiple_spaces_count > 0:
        watermark_stats["Whitespace Variations"] = {
            'total': sum(whitespace_counts.values()) + multiple_spaces_count,
            'details': {
                **{f"U+{ord(char):04X} ({whitespace_map[char]})": count 
                   for char, count in whitespace_counts.items()},
                "Multiple spaces (preserved)": multiple_spaces_count
            }
        }
    
    # 4. Detect control characters
    control_chars_counts = Counter()
    
    for match in re.finditer(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F-\x9F]', text):
        char = match.group(0)
        orig_pos = match.start()
        control_chars_counts[char] += 1
        
        # Get character name if available
        try:
            char_name = unicodedata.name(char)
        except ValueError:
            char_name = f"Control character (0x{ord(char):02X})"
        
        # Record detailed analysis
        character_analysis.append({
            'original_position': orig_pos,
            'adjusted_position': orig_pos - position_shift,
            'character': char,
            'unicode': f'U+{ord(char):04X}',
            'name': char_name,
            'category': 'Control Character',
            'context': get_context(text, orig_pos)
        })
    
    # Remove control characters
    control_chars_pattern = re.compile(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F-\x9F]')
    text = control_chars_pattern.sub('', text)
    
    if sum(control_chars_counts.values()) > 0:
        watermark_stats["Control Characters"] = {
            'total': sum(control_chars_counts.values()),
            'details': {f"U+{ord(char):04X}": count for char, count in control_chars_counts.items()}
        }
        position_shift += sum(control_chars_counts.values())
    
    # Calculate total modifications (excluding preserved multiple spaces)
    preserved_count = sum(1 for item in character_analysis if item.get('preserved', False))
    total_modifications = sum(
        value['total'] for value in watermark_stats.values()
    ) - preserved_count
    
    char_difference = len(original_text) - len(text)
    
    # Sort character analysis by original position
    character_analysis.sort(key=lambda x: x['original_position'])
    
    # Add watermark density analysis
    pattern_analysis = analyze_watermark_patterns(original_text, character_analysis)
    
    result = {
        'text': text,
        'stats': watermark_stats,
        'total_modifications': total_modifications,
        'char_difference': char_difference,
        'character_analysis': character_analysis,
        'pattern_analysis': pattern_analysis,
        'preserved_multiple_spaces': True
    }
    
    return result

def get_context(text, position, context_size=20):
    """Extract text context around a specific position."""
    start = max(0, position - context_size)
    end = min(len(text), position + context_size + 1)
    
    # Extract before and after parts
    before = text[start:position]
    after = text[position:end]
    
    return {
        'before': before,
        'after': after,
        'position_in_context': position - start
    }

def analyze_watermark_patterns(text, character_analysis):
    """Analyze potential watermark patterns in the text."""
    if not character_analysis:
        return {'patterns_detected': False}
    
    # Filter out preserved elements for pattern analysis
    analysis_items = [item for item in character_analysis if not item.get('preserved', False)]
    
    if not analysis_items:
        return {'patterns_detected': False}
    
    results = {'patterns_detected': False}
    
    # Check for character frequency patterns
    char_positions = {}
    for item in analysis_items:
        char = item['unicode']
        if char not in char_positions:
            char_positions[char] = []
        char_positions[char].append(item['original_position'])
    
    # Analyze intervals between watermarks
    interval_patterns = {}
    for char, positions in char_positions.items():
        if len(positions) > 1:
            # Calculate intervals
            intervals = [positions[i+1] - positions[i] for i in range(len(positions)-1)]
            
            # Check if intervals follow a pattern
            if len(intervals) > 2:
                # Look for consistent intervals
                interval_counts = Counter(intervals)
                most_common_interval, count = interval_counts.most_common(1)[0]
                
                if count >= len(intervals) * 0.6:  # 60% or more have the same interval
                    interval_patterns[char] = {
                        'common_interval': most_common_interval,
                        'consistency': count / len(intervals),
                        'count': count,
                        'total_intervals': len(intervals)
                    }
                    results['patterns_detected'] = True
    
    # Check word or character position patterns
    word_positions = []
    current_word_idx = 0
    current_char_idx = 0
    
    for i, char in enumerate(text):
        if char.isspace() and not text[i-1].isspace() if i > 0 else False:
            current_word_idx += 1
            current_char_idx = 0
            continue
            
        if not char.isspace():
            for item in analysis_items:
                if item['original_position'] == i:
                    word_positions.append({
                        'word_index': current_word_idx,
                        'char_index': current_char_idx,
                        'unicode': item['unicode'],
                        'category': item['category']
                    })
            current_char_idx += 1
    
    # Check for positional patterns (e.g., always at the beginning of words)
    if word_positions:
        position_patterns = {}
        
        # Check for first/last character patterns
        first_char_count = sum(1 for p in word_positions if p['char_index'] == 0)
        last_char_patterns = {}
        
        # Group by word to check for last character
        words_with_watermarks = {}
        for pos in word_positions:
            if pos['word_index'] not in words_with_watermarks:
                words_with_watermarks[pos['word_index']] = []
            words_with_watermarks[pos['word_index']].append(pos)
        
        for word_idx, positions in words_with_watermarks.items():
            max_char_idx = max(p['char_index'] for p in positions)
            last_char_count = sum(1 for p in positions if p['char_index'] == max_char_idx)
            
            if last_char_count > 0:
                if 'last_char' not in last_char_patterns:
                    last_char_patterns['last_char'] = 0
                last_char_patterns['last_char'] += last_char_count
        
        if first_char_count > len(word_positions) * 0.4:  # 40% threshold
            position_patterns['first_char'] = {
                'count': first_char_count,
                'total': len(word_positions),
                'percentage': first_char_count / len(word_positions)
            }
            results['patterns_detected'] = True
        
        if last_char_patterns.get('last_char', 0) > len(word_positions) * 0.4:
            position_patterns['last_char'] = {
                'count': last_char_patterns['last_char'],
                'total': len(word_positions),
                'percentage': last_char_patterns['last_char'] / len(word_positions)
            }
            results['patterns_detected'] = True
    
        if position_patterns:
            results['position_patterns'] = position_patterns
    
    if interval_patterns:
        results['interval_patterns'] = interval_patterns
    
    # Check for potential encoding patterns (e.g., binary or hex encoding)
    if len(analysis_items) >= 8:
        invisible_chars = [item for item in analysis_items 
                          if item['category'] == 'Invisible Character']
        
        if len(invisible_chars) >= 8:
            # Check for binary pattern (e.g., 8 bits could encode ASCII)
            char_types = [item['unicode'] for item in invisible_chars[:32]]  # First 32 chars
            unique_chars = set(char_types)
            
            if len(unique_chars) == 2:
                results['encoding_analysis'] = {
                    'possible_binary_encoding': True,
                    'unique_characters': list(unique_chars)
                }
                results['patterns_detected'] = True
    
    return results

def evaluate_watermark_impact(result):
    """Evaluate the potential impact of detected watermarks."""
    impact_analysis = {
        'readability_impact': 'None',
        'text_structure_impact': 'None',
        'information_leakage': 'None',
        'intended_purpose': 'Unknown',
        'risk_level': 'Low'
    }
    
    # Check for readability impact
    if result['stats'].get('Invisible Characters', {}).get('total', 0) > 0:
        # Invisible characters typically don't affect readability
        impact_analysis['readability_impact'] = 'Minimal'
    
    if result['stats'].get('Homoglyph Substitutions', {}).get('total', 0) > 0:
        # Homoglyphs might affect search, copy-paste and accessibility
        impact_analysis['readability_impact'] = 'Medium'
        impact_analysis['text_structure_impact'] = 'Medium'
    
    if result['stats'].get('Control Characters', {}).get('total', 0) > 0:
        # Control characters can cause issues in different systems
        impact_analysis['readability_impact'] = 'Medium'
        impact_analysis['text_structure_impact'] = 'High'
        impact_analysis['risk_level'] = 'Medium'
    
    # Check for pattern-based watermarks
    if result['pattern_analysis']['patterns_detected']:
        impact_analysis['information_leakage'] = 'Possible'
        impact_analysis['intended_purpose'] = 'Tracking or Identification'
        impact_analysis['risk_level'] = 'Medium'
        
        # If there are interval patterns, this could be an encoded message
        if result['pattern_analysis'].get('interval_patterns'):
            impact_analysis['information_leakage'] = 'Likely'
            impact_analysis['risk_level'] = 'High'
        
        # If there's a binary encoding pattern, this could be deliberate data
        if result['pattern_analysis'].get('encoding_analysis', {}).get('possible_binary_encoding', False):
            impact_analysis['information_leakage'] = 'High'
            impact_analysis['intended_purpose'] = 'Data Embedding'
            impact_analysis['risk_level'] = 'High'
    
    return impact_analysis

def generate_report(original_text, result, impact_analysis):
    """Generate a detailed human-readable report."""
    report = []
    
    # Add header
    report.append("# Watermark Analysis Report")
    report.append("")
    
    # Add summary
    report.append("## Summary")
    report.append("")
    report.append(f"- Original text length: {len(original_text)} characters")
    report.append(f"- Cleaned text length: {len(result['text'])} characters")
    report.append(f"- Characters removed: {result['char_difference']}")
    
    # Calculate actual modifications (excluding preserved spaces)
    modified_count = result['total_modifications']
    report.append(f"- Distinct modifications: {modified_count}")
    
    # Mention preserved content
    if result.get('preserved_multiple_spaces'):
        report.append("- Multiple spaces were preserved")
    
    report.append(f"- Risk level: {impact_analysis['risk_level']}")
    report.append("")
    
    # Add watermark statistics
    if result['stats']:
        report.append("## Detected Watermarks")
        report.append("")
        
        for category, details in result['stats'].items():
            report.append(f"### {category}")
            report.append(f"- Total: {details['total']}")
            
            if details.get('details'):
                report.append("- Breakdown:")
                for char_desc, count in details['details'].items():
                    if "preserved" in char_desc.lower():
                        report.append(f"  - {char_desc}: {count} (analyzed but not modified)")
                    else:
                        report.append(f"  - {char_desc}: {count}")
            
            report.append("")
    else:
        report.append("## No watermarks detected")
        report.append("")
    
    # Add pattern analysis
    if result['pattern_analysis']['patterns_detected']:
        report.append("## Pattern Analysis")
        report.append("")
        report.append("Watermarks appear to follow specific patterns:")
        
        if result['pattern_analysis'].get('interval_patterns'):
            report.append("### Character Interval Patterns")
            report.append("The following characters appear at regular intervals:")
            
            for char, pattern in result['pattern_analysis']['interval_patterns'].items():
                report.append(f"- {char}: Appears every {pattern['common_interval']} characters " 
                             f"({pattern['consistency']*100:.1f}% consistency)")
            
            report.append("")
        
        if result['pattern_analysis'].get('position_patterns'):
            report.append("### Word Position Patterns")
            patterns = result['pattern_analysis']['position_patterns']
            
            if 'first_char' in patterns:
                report.append(f"- {patterns['first_char']['percentage']*100:.1f}% of watermarks appear " 
                             f"at the beginning of words")
            
            if 'last_char' in patterns:
                report.append(f"- {patterns['last_char']['percentage']*100:.1f}% of watermarks appear " 
                             f"at the end of words")
            
            report.append("")
        
        if result['pattern_analysis'].get('encoding_analysis', {}).get('possible_binary_encoding', False):
            report.append("### Possible Binary Encoding")
            report.append("The pattern of invisible characters suggests a possible binary encoding scheme, " 
                         "which could be embedding data within the text.")
            report.append("")
    
    # Add impact analysis
    report.append("## Impact Analysis")
    report.append("")
    report.append(f"- Readability Impact: {impact_analysis['readability_impact']}")
    report.append(f"- Text Structure Impact: {impact_analysis['text_structure_impact']}")
    report.append(f"- Information Leakage: {impact_analysis['information_leakage']}")
    report.append(f"- Likely Purpose: {impact_analysis['intended_purpose']}")
    report.append(f"- Risk Level: {impact_analysis['risk_level']}")
    report.append("")
    
    # Add detailed explanation of impacts
    report.append("### Impact Explanation")
    report.append("")
    
    if impact_analysis['readability_impact'] != 'None':
        report.append("**Readability Impact:**")
        if impact_analysis['readability_impact'] == 'Minimal':
            report.append("The watermarks detected are unlikely to affect readability of the text for humans, " 
                         "but may interfere with machine processing or accessibility tools.")
        elif impact_analysis['readability_impact'] == 'Medium':
            report.append("The watermarks could affect readability in some contexts, particularly " 
                         "when copied to different platforms or processed by different software.")
        elif impact_analysis['readability_impact'] == 'High':
            report.append("The watermarks significantly impact readability or reliability of the text " 
                         "when processed by software or assistive technologies.")
        report.append("")
    
    if impact_analysis['information_leakage'] != 'None':
        report.append("**Information Leakage:**")
        if impact_analysis['information_leakage'] == 'Possible':
            report.append("The watermarks may be tracking the origin or distribution of this text.")
        elif impact_analysis['information_leakage'] == 'Likely':
            report.append("The watermarks appear designed to encode identifying information about " 
                         "the source, recipient, or distribution path of the text.")
        elif impact_analysis['information_leakage'] == 'High':
            report.append("The watermarks contain sophisticated encoded data that could include " 
                         "personally identifiable information or other sensitive data.")
        report.append("")
    
    if result['pattern_analysis']['patterns_detected']:
        report.append("**Watermarking Technology:**")
        report.append("The patterns detected are consistent with modern text watermarking techniques " 
                     "commonly used for:\n"
                     "- Source identification\n"
                     "- Copy tracking\n"
                     "- User identification\n"
                     "- Data leakage prevention")
        report.append("")
    
    # Note about preserved formatting
    if result.get('preserved_multiple_spaces'):
        report.append("**Preserved Formatting:**")
        report.append("Multiple spaces were detected but preserved in the output text. " 
                     "While these might be part of a watermarking strategy, they could also be " 
                     "intentional formatting, so they were not modified.")
        report.append("")
    
    # Add recommendations
    report.append("## Recommendations")
    report.append("")
    
    if impact_analysis['risk_level'] == 'Low':
        report.append("- The watermarks detected are minimal and likely benign.")
        report.append("- No significant action necessary beyond removing the watermarks if desired.")
    elif impact_analysis['risk_level'] == 'Medium':
        report.append("- Consider whether the source of this text is trustworthy.")
        report.append("- Be cautious about sharing sensitive information with the source.")
        report.append("- Consider using the cleaned version for further distribution.")
    elif impact_analysis['risk_level'] == 'High':
        report.append("- Exercise caution with the source of this text.")
        report.append("- Do not share sensitive information with the source.")
        report.append("- Consider using alternative sources or platforms.")
        report.append("- Always use the cleaned version for any further distribution.")
    
    report.append("")
    report.append("---")
    
    return "\n".join(report)



def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(
        description="Remove and analyze text watermarks while preserving multiple spaces"
    )
    
    parser.add_argument(
        "input_file", 
        help="Input file path"
    )
    
    parser.add_argument(
        "output_file",
        help="Output file path"
    )
    
    parser.add_argument(
        "--report",
        help="Path to save detailed analysis report (markdown format)",
        default=None
    )
    
    parser.add_argument(
        "--json",
        help="Path to save analysis data in JSON format",
        default=None
    )
    
    parser.add_argument(
        "--modify-spaces",
        action="store_true",
        help="If specified, multiple spaces will be collapsed to single spaces"
    )
    
    args = parser.parse_args()
    
    try:
        # Read input file
        with open(args.input_file, 'r', encoding='utf-8') as f:
            original_text = f.read()
        
        # Process the text
        print(f"Processing file: {args.input_file}")
        result = analyze_watermarks(original_text, preserve_multiple_spaces=not args.modify_spaces)
        
        # Evaluate impact
        impact_analysis = evaluate_watermark_impact(result)
        
        # Write to output file
        with open(args.output_file, 'w', encoding='utf-8') as f:
            f.write(result['text'])
        
        # Generate and save report if requested
        if args.report:
            report_text = generate_report(original_text, result, impact_analysis)
            with open(args.report, 'w', encoding='utf-8') as f:
                f.write(report_text)
            print(f"Detailed report saved to: {args.report}")
        
        # Save JSON data if requested
        if args.json:
            # Prepare JSON-safe data (remove context to reduce size)
            json_data = {
                'stats': result['stats'],
                'total_modifications': result['total_modifications'],
                'char_difference': result['char_difference'],
                'pattern_analysis': result['pattern_analysis'],
                'impact_analysis': impact_analysis,
                'preserved_multiple_spaces': result.get('preserved_multiple_spaces', False),
                'character_analysis': [{k: v for k, v in item.items() if k != 'context'} 
                                     for item in result['character_analysis']]
            }
            
            with open(args.json, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, indent=2)
            print(f"Analysis data saved to: {args.json}")
        
        # Report results to console
        print("\nWatermark Analysis Results:")
        print(f"- Original size: {len(original_text)} characters")
        print(f"- Cleaned size: {len(result['text'])} characters")
        print(f"- Characters removed: {result['char_difference']}")
        if result.get('preserved_multiple_spaces'):
            print("- Multiple spaces were preserved")
        
        if result['stats']:
            print("\nWatermarks detected:")
            for category, details in result['stats'].items():
                if category == "Whitespace Variations" and "Multiple spaces (preserved)" in details.get('details', {}):
                    preserved_spaces = details['details']["Multiple spaces (preserved)"]
                    actual_count = details['total'] - preserved_spaces
                    print(f"- {category}: {actual_count} removed, {preserved_spaces} analyzed but preserved")
                else:
                    print(f"- {category}: {details['total']}")
            
            print(f"\nRisk level: {impact_analysis['risk_level']}")
            
            if result['pattern_analysis']['patterns_detected']:
                print("\nPattern detected: Watermarks appear to follow specific patterns")
                if impact_analysis['information_leakage'] != 'None':
                    print(f"Potential information leakage: {impact_analysis['information_leakage']}")
        else:
            print("\nNo watermarks detected.")
        
        print(f"\nCleaned text saved to: {args.output_file}")
        
    except FileNotFoundError:
        print(f"Error: File '{args.input_file}' not found", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
   
