# Final fix - use simpler punctuation without backslash
with open('elasticsearch_consumer.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find and fix the lines
for i in range(len(lines)):
    if 'clean_word = word.strip' in lines[i]:
        lines[i] = "        clean_word = word.strip('.,!?;:\"\\'')\n"
    elif 'is_negated' in lines[i] and 'words[i-1].strip' in lines[i]:
        lines[i] = "        is_negated = (i > 0 and words[i-1].strip('.,!?;:\"\\''') in negations)\n"

with open('elasticsearch_consumer.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)

print("✅ Really fixed this time!")
