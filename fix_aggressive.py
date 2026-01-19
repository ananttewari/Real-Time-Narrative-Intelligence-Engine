# Aggressive fix - remove all broken lines
with open('elasticsearch_consumer.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Remove any lines that contain broken strip patterns
cleaned_lines = []
skip_next = False
for i, line in enumerate(lines):
    # Skip lines with the broken pattern
    if "words[i-1].strip(" in line and "is_negated" in line and len(line.strip()) < 100:
        # This is a broken line, skip it
        continue
    elif line.strip().startswith("'.,!?"):
        # This is a continuation of a broken string, skip it
        continue
    else:
        cleaned_lines.append(line)

# Now add the correct lines at the right position
final_lines = []
for i, line in enumerate(cleaned_lines):
    final_lines.append(line)
    # After the "Remove punctuation for matching" comment, add the correct lines
    if '# Remove punctuation for matching' in line:
        # Next line should be clean_word
        if i+1 < len(cleaned_lines) and 'clean_word' in cleaned_lines[i+1]:
            final_lines.append("        clean_word = word.strip('.,!?;:\"\\'')\r\n")
            # Skip the potentially broken version
            continue
    # After the "Check if previous word is a negation" comment, add the correct line
    elif '# Check if previous word is a negation' in line:
        if i+1 < len(cleaned_lines):
            final_lines.append("        is_negated = (i > 0 and words[i-1].strip('.,!?;:\"\\''') in negations)\r\n")

with open('elasticsearch_consumer.py', 'w', encoding='utf-8') as f:
    f.writelines(final_lines)

print("✅ Aggressively cleaned!")
