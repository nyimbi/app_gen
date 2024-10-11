import re
import random
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

# Custom synonym dictionary and spelling variants (keep your existing dictionaries here)
synonym_dict = {
    # Existing entries
    "analyze": ["examine", "investigate", "scrutinize", "study", "assess", "evaluate"],
    "implications": ["consequences", "effects", "ramifications", "repercussions", "outcomes"],
    "comprehensive": ["thorough", "extensive", "complete", "exhaustive", "all-encompassing"],
    "vulnerabilities": ["weaknesses", "flaws", "susceptibilities", "exposures", "liabilities"],
    "strategic": ["tactical", "planned", "calculated", "deliberate", "considered"],
    "implement": ["execute", "carry out", "perform", "enact", "apply", "realize"],
    "enhance": ["improve", "augment", "upgrade", "boost", "elevate", "amplify"],
    "critical": ["crucial", "essential", "vital", "key", "important", "significant"],
    "rapid": ["swift", "quick", "fast", "speedy", "prompt", "expeditious"],
    "innovative": ["novel", "groundbreaking", "creative", "inventive", "pioneering"],
    "evolving": ["developing", "changing", "progressing", "advancing", "transforming"],
    "robust": ["strong", "sturdy", "resilient", "durable", "hardy", "solid"],
    "efficient": ["effective", "productive", "competent", "capable", "proficient"],
    "sophisticated": ["advanced", "complex", "intricate", "elaborate", "refined"],
    "proliferation": ["spread", "increase", "expansion", "growth", "dissemination"],
    "mitigate": ["alleviate", "reduce", "diminish", "lessen", "ease", "moderate"],
    "leverage": ["utilize", "use", "employ", "exploit", "harness", "apply"],
    "integrate": ["incorporate", "combine", "merge", "unify", "consolidate"],
    "optimize": ["improve", "enhance", "refine", "perfect", "streamline"],
    "facilitate": ["enable", "assist", "aid", "help", "support", "promote"],
    "imperative": ["crucial", "essential", "vital", "critical", "necessary"],
    "paramount": ["supreme", "dominant", "preeminent", "foremost", "chief"],
    "unprecedented": ["unparalleled", "unique", "extraordinary", "exceptional", "unmatched"],
    "potential": ["possible", "prospective", "likely", "probable", "feasible"],
    "significant": ["important", "considerable", "substantial", "notable", "major"],
    "emerging": ["developing", "rising", "growing", "evolving", "budding"],
    "challenge": ["difficulty", "obstacle", "hurdle", "problem", "issue"],
    "initiative": ["program", "project", "undertaking", "endeavor", "venture"],
    "collaboration": ["cooperation", "partnership", "alliance", "teamwork", "synergy"],
    "impact": ["effect", "influence", "consequence", "result", "outcome"],

    # New entries from the provided list
    # "democratization": ["popularization", "expansion", "spread"],
    "unprecedented": ["unparalleled", "unique", "extraordinary"],
    "analyze": ["examine", "investigate", "study"],
    "strategic": ["tactical", "planned", "calculated"],
    "uncensored": ["unrestricted", "unfiltered", "uncontrolled"],
    "empower": ["enable", "authorize", "equip"],
    "capabilities": ["abilities", "competencies", "skills"],
    "reveals": ["discloses", "exposes", "uncovers"],
    "pressing": ["urgent", "critical", "immediate"],
    "developing": ["creating", "generating", "producing"],
    "strengthening": ["reinforcing", "fortifying", "bolstering"],
    "fostering": ["encouraging", "nurturing", "promoting"],
    "substantial": ["significant", "considerable", "important"],
    "disrupting": ["interrupting", "disturbing", "destabilizing"],
    "implementation": ["execution", "application", "realization"],
    "resilience": ["toughness", "durability", "flexibility"],
    "address": ["tackle", "confront", "deal with"],
    "growing": ["increasing", "expanding", "rising"],
    "harnessing": ["utilizing", "exploiting", "leveraging"],
    "inexorable": ["relentless", "unstoppable", "inevitable"],
    "march": ["advance", "progress", "movement"],
    "progress": ["advancement", "development", "improvement"],
    "juncture": ["point", "moment", "stage"],
    "evolution": ["development", "progression", "transformation"],
    "warfare": ["conflict", "hostilities", "combat"],
    "advent": ["arrival", "emergence", "appearance"],
    "altered": ["changed", "modified", "transformed"],
    "landscape": ["terrain", "environment", "scene"],
    "generating": ["producing", "creating", "forming"],
    "performing": ["executing", "carrying out", "conducting"],
    "intricate": ["complicated", "complex", "elaborate"],
    "amplified": ["intensified", "increased", "magnified"],
    "emergence": ["appearance", "rise", "development"],
    "lowered": ["reduced", "decreased", "diminished"],
    "barriers": ["obstacles", "hurdles", "impediments"],
    "entry": ["access", "admission", "ingress"],
    "historically": ["traditionally", "conventionally", "customarily"],
    "maintained": ["preserved", "sustained", "kept"],
    "monopoly": ["dominance", "control", "supremacy"],
    "upended": ["overturned", "upset", "reversed"],
    "paradigm": ["model", "framework", "pattern"],
    "empowered": ["enabled", "authorized", "equipped"],
    "diverse": ["varied", "assorted", "mixed"],
    "fundamentally": ["essentially", "basically", "inherently"],
    "reshaping": ["transforming", "remodeling", "restructuring"],
    "dynamics": ["interactions", "relationships", "forces"],
    "burgeoning": ["growing", "expanding", "developing"],
    "opportunities": ["chances", "prospects", "possibilities"],
    "innovation": ["invention", "creation", "novelty"],
    "advancements": ["improvements", "developments", "progress"],
    "commensurate": ["proportionate", "corresponding", "equivalent"],
    "measures": ["actions", "steps", "procedures"],
    "rendering": ["making", "causing", "effecting"],
    "particularly": ["especially", "specifically", "notably"],
    "vulnerable": ["susceptible", "exposed", "at risk"],
    "exploitation": ["abuse", "misuse", "taking advantage"],
    "wielding": ["using", "employing", "exercising"],
    "aims": ["goals", "objectives", "purposes"],
    "investigate": ["examine", "probe", "research"],
    "removal": ["elimination", "eradication", "exclusion"],
    "enables": ["allows", "permits", "facilitates"],
    "creation": ["formation", "generation", "production"],
    "assess": ["evaluate", "appraise", "gauge"],
    "risks": ["dangers", "hazards", "threats"],
    "explore": ["investigate", "examine", "probe"],
    "delve": ["dig", "investigate", "research"],
    "propose": ["suggest", "recommend", "put forward"],
    "actionable": ["practical", "feasible", "doable"],
    "conduct": ["perform", "carry out", "execute"],
    "grounded": ["based", "founded", "rooted"],
    "elucidates": ["explains", "clarifies", "illuminates"],
    "propagate": ["spread", "disseminate", "circulate"],
    "relevant": ["applicable", "pertinent", "appropriate"],
    "understanding": ["comprehension", "knowledge", "grasp"],
    "adoption": ["implementation", "acceptance", "embracing"],
    "conceptualize": ["envision", "imagine", "conceive"],
    "determine": ["ascertain", "establish", "decide"],
    "project": ["forecast", "predict", "estimate"],
    "posits": ["proposes", "suggests", "hypothesizes"],
    "drivers": ["factors", "causes", "influences"],
    "shaping": ["molding", "forming", "influencing"],
    "altering": ["changing", "modifying", "adjusting"],
    "redefining": ["reframing", "reconceptualizing", "reimagining"],
    "encompasses": ["includes", "covers", "comprises"],
    "constrained": ["limited", "restricted", "confined"],
    "inherent": ["intrinsic", "innate", "inherent"],
    "difficulty": ["challenge", "problem", "obstacle"],
    "predicting": ["forecasting", "projecting", "anticipating"],
    "conducted": ["carried out", "performed", "executed"],
    "extensive": ["comprehensive", "thorough", "wide-ranging"],
    "supplement": ["complement", "augment", "enhance"],
    "ensure": ["guarantee", "secure", "assure"],
    "underscore": ["emphasize", "highlight", "stress"],
    "adapt": ["adjust", "modify", "acclimate"],
    "foster": ["promote", "encourage", "nurture"],
    "harness": ["utilize", "employ", "exploit"],
    "presents": ["poses", "offers", "introduces"],
    "uncovered": ["revealed", "discovered", "exposed"],
    "insights": ["understanding", "perceptions", "realizations"],
    "availability": ["accessibility", "obtainability", "presence"],
    "conducting": ["performing", "carrying out", "executing"],
    "observed": ["noted", "noticed", "perceived"],
    "concern": ["worry", "apprehension", "unease"],
    "recognized": ["acknowledged", "identified", "accepted"],
    "affect": ["influence", "impact", "alter"],
    "traditional": ["conventional", "customary", "established"],
    "integration": ["incorporation", "assimilation", "combination"],
    "enhancement": ["improvement", "upgrade", "augmentation"],
    "spreading": ["disseminating", "distributing", "propagating"],
    "profound": ["deep", "significant", "far-reaching"],
    "urgency": ["necessity", "exigency", "imperativeness"],
    "building": ["developing", "constructing", "establishing"],
    "expertise": ["knowledge", "skill", "proficiency"],
    "underscoring": ["emphasizing", "highlighting", "stressing"],
    "updating": ["revising", "modernizing", "refreshing"],
    "various": ["different", "diverse", "assorted"],
    "highlighting": ["emphasizing", "accentuating", "underscoring"],
    "improved": ["enhanced", "upgraded", "bettered"],
    "robust": ["strong", "sturdy", "resilient"],
    "protect": ["safeguard", "defend", "shield"],
    "exploration": ["investigation", "examination", "research"],
    "investment": ["funding", "financing", "backing"],
    "tailored": ["customized", "adapted", "personalized"],
    "initiated": ["started", "begun", "launched"],
    "looming": ["impending", "imminent", "approaching"],
    "breaking": ["cracking", "fracturing", "shattering"],
    "leveraging": ["utilizing", "using", "exploiting"],
    "emphasized": ["stressed", "highlighted", "accentuated"],
    "increased": ["enhanced", "augmented", "expanded"],
    "homegrown": ["indigenous", "native", "local"],
    "effectively": ["efficiently", "successfully", "competently"],
    "navigate": ["manage", "negotiate", "traverse"],
    "posed": ["presented", "introduced", "raised"],
    "allocate": ["assign", "distribute", "allot"],
    "recommendations": ["suggestions", "proposals", "advice"],
    "establish": ["create", "set up", "found"],
    "curricula": ["programs", "courses", "syllabi"],
    "engage": ["participate", "involve", "take part"],
    "advocated": ["supported", "promoted", "championed"],
    "capacity": ["ability", "capability", "competence"],
    "frameworks": ["structures", "systems", "models"],
    "considerations": ["factors", "aspects", "elements"]
}

# Dictionary for alternative spellings
spelling_variants = {
    "analyze": "analyse",
    "color": "colour",
    "defense": "defence",
    "center": "centre",
    "organize": "organise",
    "behavior": "behaviour",
    "favor": "favour",
    "labor": "labour",
    "neighbor": "neighbour",
    "catalog": "catalogue",
    "dialog": "dialogue",
    "program": "programme",
    "realize": "realise",
    "customize": "customise",
    "optimize": "optimise",
    "memorize": "memorise",
    "prioritize": "prioritise",
    "recognize": "recognise",
    "specialize": "specialise",
    "standardize": "standardise",
    "synchronize": "synchronise",
    "theater": "theatre",
    "meter": "metre",
    "liter": "litre",
    "fiber": "fibre",
    "canceled": "cancelled",
    "counselor": "counsellor",
    "enrollment": "enrolment",
    "fulfill": "fulfil",
    "installment": "instalment",
    "jewelry": "jewellery",
    "labeled": "labelled",
    "modeling": "modelling",
    "traveled": "travelled",
    "gray": "grey",
    "pajamas": "pyjamas",
    "aluminum": "aluminium",
    "artifact": "artefact",
    "check": "cheque",
    "draft": "draught",
    "plow": "plough",
    "skeptic": "sceptic",
    "tire": "tyre",
    "cybersecurity": "cyber-security"
}

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