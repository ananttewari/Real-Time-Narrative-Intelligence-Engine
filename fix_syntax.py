# Fix the syntax error in elasticsearch_consumer.py
import re

with open('elasticsearch_consumer.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Fix line 135 (index 134)
lines[134] = "        clean_word = word.strip('.,!?;:\"\\'')\n"

# Fix line 138 (index 137)  
lines[137] = "        is_negated = (i > 0 and words[i-1].strip('.,!?;:\"\\''') in negations)\n"

with open('elasticsearch_consumer.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)

print("✅ Fixed syntax errors in elasticsearch_consumer.py")
