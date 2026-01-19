# Ultimate fix - rebuild the entire analyze_sentiment function
with open('elasticsearch_consumer.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find the start of the for loop
start_idx = None
for i, line in enumerate(lines):
    if 'for i, word in enumerate(words):' in line:
        start_idx = i
        break

if start_idx:
    # Replace the problematic section (lines 133-138)
    new_lines = [
        "    for i, word in enumerate(words):\r\n",
        "        # Remove punctuation for matching\r\n",
        "        clean_word = word.strip('.,!?;:\"\\'')\r\n",
        "        \r\n",
        "        # Check if previous word is a negation\r\n",
        "        is_negated = (i > 0 and words[i-1].strip('.,!?;:\"\\''') in negations)\r\n",
    ]
    
    # Find how many lines to replace (from "for i" to "is_negated")
    end_idx = start_idx
    for i in range(start_idx, min(start_idx + 20, len(lines))):
        if 'is_negated' in lines[i]:
            end_idx = i
            break
    
    # Rebuild the list
    lines = lines[:start_idx] + new_lines + lines[end_idx+1:]
    
    with open('elasticsearch_consumer.py', 'w', encoding='utf-8') as f:
        f.writelines(lines)
    print(f"✅ Fixed lines {start_idx+1} to {end_idx+1}")
else:
    print("❌ Could not find the for loop")
