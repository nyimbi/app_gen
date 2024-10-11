import re
import random
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
import nltk

# Download required NLTK data
nltk.download('punkt')
nltk.download('stopwords')

# Custom synonym dictionary (extend this with more words and synonyms)
# Expanded synonym dictionary
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


def get_wordnet_pos(word):
    """Map POS tag to first character used by WordNet"""
    tag = nltk.pos_tag([word])[0][1][0].upper()
    tag_dict = {"J": wordnet.ADJ,
                "N": wordnet.NOUN,
                "V": wordnet.VERB,
                "R": wordnet.ADV}
    return tag_dict.get(tag, wordnet.NOUN)

def get_synonyms(word):
    synonyms = []

    # First, check our custom dictionary
    if word.lower() in synonym_dict:
        synonyms.extend(synonym_dict[word.lower()])

    # Then, use WordNet to find additional synonyms
    for syn in wordnet.synsets(word, pos=get_wordnet_pos(word)):
        for lemma in syn.lemmas():
            if lemma.name().lower() != word.lower() and lemma.name().lower() not in synonyms:
                synonyms.append(lemma.name().lower())

    return list(set(synonyms))  # Remove duplicates

def replace_word(word, ignore_case=True):
    lower_word = word.lower()

    # Check if it's a stop word
    if lower_word in stopwords.words('english'):
        return word

    # Try to replace with synonym
    synonyms = get_synonyms(word)
    if synonyms and random.random() < 0.7:  # 70% chance
        replacement = random.choice(synonyms)
        return match_case(replacement, word)

    # Try to replace spelling
    if lower_word in spelling_variants and random.random() < 0.5:  # 50% chance
        replacement = spelling_variants[lower_word]
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

def process_markdown(text):
    def replace_match(match):
        return replace_word(match.group(0))

    # Use regex to match words while preserving formatting
    pattern = r'\b\w+\b'
    return re.sub(pattern, replace_match, text)

# Main function to process the file
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














# def replace_word(word, ignore_case=True):
#     lower_word = word.lower()

#     # Check if it's a stop word
#     if lower_word in stopwords.words('english'):
#         return word

#     # Try to replace with synonym
#     if lower_word in synonym_dict and random.random() < 0.7:  # 70% chance
#         replacement = random.choice(synonym_dict[lower_word])
#         return match_case(replacement, word)

#     # Try to replace spelling
#     if lower_word in spelling_variants and random.random() < 0.5:  # 50% chance
#         replacement = spelling_variants[lower_word]
#         return match_case(replacement, word)

#     return word

# def match_case(word, target):
#     if target.islower():
#         return word.lower()
#     if target.isupper():
#         return word.upper()
#     if target.istitle():
#         return word.capitalize()
#     return word

# def process_markdown(text):
#     def replace_match(match):
#         return replace_word(match.group(0))

#     # Use regex to match words while preserving formatting
#     pattern = r'\b\w+\b'
#     return re.sub(pattern, replace_match, text)

# # Main function to process the file
# def process_file(input_file, output_file):
#     with open(input_file, 'r', encoding='utf-8') as file:
#         content = file.read()

#     processed_content = process_markdown(content)

#     with open(output_file, 'w', encoding='utf-8') as file:
#         file.write(processed_content)

# # Usage
# input_file = 'input.md'
# output_file = 'output.md'
# process_file(input_file, output_file)
# print(f"Processed {input_file} and saved results to {output_file}")
