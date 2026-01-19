# Nuclear option - just find the problematic function and replace the ENTIRE strip character set
# with something simpler that doesn't need backslashes

with open('elasticsearch_consumer.py', 'rb') as f:
    content = f.read()

# Convert to string
text = content.decode('utf-8', errors='ignore')

# Find and replace ANY occurrence of the pattern (including broken ones across lines)
import re

# Remove all broken multiline patterns first
text = re.sub(r"strip\('\..*?\n.*?'\)", "strip('.,!?;:')", text, flags=re.DOTALL)

# Now add back the correct ones
text = re.sub(r"clean_word = word\.strip\([^)]+\)", "clean_word = word.strip('.,!?;:')", text)
text = re.sub(r"words\[i-1\]\.strip\([^)]+\) in negations", "words[i-1].strip('.,!?;:') in negations", text)

with open('elasticsearch_consumer.py', 'w', encoding='utf-8') as f:
    f.write(text)

print("✅ Nuclear fix applied!")
