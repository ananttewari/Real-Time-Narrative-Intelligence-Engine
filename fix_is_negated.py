# Add the missing is_negated line
with open('elasticsearch_consumer.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find the line with clean_word and add is_negated check after it
new_lines = []
for i, line in enumerate(lines):
    new_lines.append(line)
    # After clean_word line and some blank lines, before "# Count positive words"
    if 'clean_word = word.strip' in line:
        # Add blank line and the check
        new_lines.append("        \r\n")
        new_lines.append("        # Check if previous word is a negation\r\n")
        new_lines.append("        is_negated = (i > 0 and words[i-1].strip('.,!?;:') in negations)\r\n")
        print(f"✅ Added is_negated definition after line {i+1}")

with open('elasticsearch_consumer.py', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print("✅ Fixed is_negated error!")
