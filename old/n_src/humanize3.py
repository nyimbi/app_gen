import re
import random
import json
from nltk.corpus import stopwords, wordnet
from nltk.tokenize import word_tokenize, sent_tokenize
import nltk
from nltk.tag import pos_tag
from nltk.chunk import ne_chunk
import spacy

# Download required NLTK data
nltk.download('punkt')
nltk.download('stopwords')
nltk.download('wordnet')
nltk.download('averaged_perceptron_tagger')
nltk.download('maxent_ne_chunker')
nltk.download('words')

# Load spaCy model
nlp = spacy.load("en_core_web_sm")

# Load synonym dictionary and spelling variants from JSON file
with open('dictionary_data.json', 'r') as file:
    data = json.load(file)
    synonym_dict = data['synonym_dict']
    spelling_variants = data['spelling_variants']

# Regex patterns for Markdown elements
MARKDOWN_PATTERNS = [
    (r'(?P<fence>^```)[\s\S]*?^```', 'code_block'),  # Code blocks
    (r'`[^`\n]+`', 'inline_code'),  # Inline code
    (r'\[([^\]]+)\]\(([^)]+)\)', 'link'),  # Links
    (r'!\[([^\]]*)\]\(([^)]+)\)', 'image'),  # Images
    (r'^#{1,6}\s.*$', 'header'),  # Headers
    (r'^\s*[-*+]\s', 'list_item'),  # List items
    (r'^\s*\d+\.\s', 'numbered_list_item'),  # Numbered list items
    (r'\*\*[^*\n]+\*\*', 'bold'),  # Bold text
    (r'\*[^*\n]+\*', 'italic'),  # Italic text
    (r'~~[^~\n]+~~', 'strikethrough'),  # Strikethrough text
    (r'^>.*$', 'blockquote'),  # Blockquotes
    (r'^(-{3,}|\*{3,}|_{3,})$', 'horizontal_rule'),  # Horizontal rules
]

def get_wordnet_pos(treebank_tag):
    if treebank_tag.startswith('J'):
        return wordnet.ADJ
    elif treebank_tag.startswith('V'):
        return wordnet.VERB
    elif treebank_tag.startswith('N'):
        return wordnet.NOUN
    elif treebank_tag.startswith('R'):
        return wordnet.ADV
    else:
        return None

def get_synonyms(word, pos):
    synonyms = []
    
    # First, check our custom dictionary
    if word.lower() in synonym_dict:
        synonyms.extend(synonym_dict[word.lower()])
    
    # Then, use WordNet to find additional synonyms
    if pos:
        for syn in wordnet.synsets(word, pos=pos):
            for lemma in syn.lemmas():
                if lemma.name().lower() != word.lower() and lemma.name().lower() not in synonyms:
                    synonyms.append(lemma.name().lower())
    
    return list(set(synonyms))  # Remove duplicates

def is_named_entity(word, tagged_sent):
    chunked = ne_chunk(tagged_sent)
    for subtree in chunked:
        if isinstance(subtree, nltk.Tree) and word in [leave[0] for leave in subtree.leaves()]:
            return True
    return False

def replace_word(word, pos, tagged_sent):
    if word.lower() in stopwords.words('english'):
        return word
    
    if is_named_entity(word, tagged_sent):
        return word
    
    synonyms = get_synonyms(word, pos)
    if synonyms and random.random() < 0.7:  # 70% chance
        replacement = random.choice(synonyms)
        return match_case(replacement, word)
    
    if word.lower() in spelling_variants and random.random() < 0.5:  # 50% chance
        replacement = spelling_variants[word.lower()]
        return match_case(replacement, word)
    
    return word

def match_case(word, target):
    if target.islower():
        return word.lower()
    if target.isupper():
        return word.upper()
    if target.istitle():
        return word.capitalize()
    return word

def process_sentence(sentence):
    doc = nlp(sentence)
    tagged_sent = pos_tag(word_tokenize(sentence))
    new_words = []
    
    for token in doc:
        word = token.text
        pos = get_wordnet_pos(token.tag_)
        new_word = replace_word(word, pos, tagged_sent)
        
        # Ensure agreement with dependencies
        if token.dep_ in ['nsubj', 'nsubjpass'] and token.head.pos_ == 'VERB':
            # Ensure subject-verb agreement
            if token.tag_.startswith('NN') and not new_word.endswith('s'):
                new_word += 's'
        elif token.dep_ == 'det' and token.head.tag_.startswith('NN'):
            # Ensure determiner-noun agreement
            if new_word in ['a', 'an']:
                if token.head.text[0].lower() in 'aeiou':
                    new_word = 'an'
                else:
                    new_word = 'a'
        
        new_words.append(new_word)
    
    return ' '.join(new_words)

def process_markdown_content(content):
    def replace_match(match):
        return process_sentence(match.group(0))
    
    # Use regex to match text content while preserving formatting
    pattern = r'(?<=[.!?]\s)(\S.+?)(?=[.!?]\s|$)'  # Matches sentences
    return re.sub(pattern, replace_match, content)

def process_markdown(text):
    def process_block(block, block_type):
        if block_type in ['code_block', 'inline_code', 'link', 'image', 'header', 'horizontal_rule']:
            # Don't process these elements
            return block
        elif block_type in ['list_item', 'numbered_list_item', 'blockquote']:
            # Process the content after the Markdown syntax
            prefix, content = block.split(None, 1)
            processed_content = process_markdown_content(content)
            return f"{prefix} {processed_content}"
        else:
            # For other elements (bold, italic, strikethrough, plain text), process the content
            return process_markdown_content(block)

    # Split the text into blocks based on Markdown patterns
    blocks = []
    last_end = 0
    for pattern, block_type in MARKDOWN_PATTERNS:
        for match in re.finditer(pattern, text, re.MULTILINE):
            if match.start() > last_end:
                blocks.append((text[last_end:match.start()], 'plain'))
            blocks.append((match.group(), block_type))
            last_end = match.end()
    if last_end < len(text):
        blocks.append((text[last_end:], 'plain'))

    # Process each block
    processed_blocks = [process_block(block, block_type) for block, block_type in blocks]

    return ''.join(processed_blocks)

def process_file(input_file, output_file):
    with open(input_file, 'r', encoding='utf-8') as file:
        content = file.read()
    
    processed_content = process_markdown(content)
    
    with open(output_file, 'w', encoding='utf-8') as file:
        file.write(processed_content)

# Usage
input_file = 'input.md'
output_file = 'output.md'
process_file(input_file, output_file)
print(f"Processed {input_file} and saved results to {output_file}")