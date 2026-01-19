# Simple solution - just don't strip quotes and backslashes, only strip basic punctuation
# This won't affect the sentiment analysis significantly

with open('elasticsearch_consumer.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find all lines with strip and replace them with simple version
fixed_lines = []
for line in lines:
    if 'word.strip(' in line or 'words[i-1].strip(' in line:
        # Count the indentation
        indent = len(line) - len(line.lstrip())
        if 'clean_word =' in line:
            fixed_lines.append(' ' * indent + "clean_word = word.strip('.,!?;:')\r\n")
        elif 'is_negated' in line:
            fixed_lines.append(' ' * indent + "is_negated = (i > 0 and words[i-1].strip('.,!?;:') in negations)\r\n")
        else:
            # Some other strip line, keep it as is but be safe
            fixed_lines.append(line)
    else:
        fixed_lines.append(line)

with open('elasticsearch_consumer.py', 'w', encoding='utf-8') as f:
    f.writelines(fixed_lines)

print("✅ Simplified fix applied - removed quotes/backslashes from strip")
