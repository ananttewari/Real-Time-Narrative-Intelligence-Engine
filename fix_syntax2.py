# Better fix for the syntax error
with open('elasticsearch_consumer.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace the problematic patterns
content = content.replace(
    "clean_word = word.strip('.,!?;:\"\\\\'')",
    "clean_word = word.strip('.,!?;:\"'\"'\"')"
)

content = content.replace(
    "words[i-1].strip('.,!?;:\"\\\\''')",
    "words[i-1].strip('.,!?;:\"'\"'\"')"
)

with open('elasticsearch_consumer.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Fixed!")
