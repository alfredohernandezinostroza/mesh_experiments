import csv
import re

# The 25 broad classification terms
# A keyword is classified into ALL categories for which it contains a matching term.
CATEGORIES = {
    'A. Neuroscience & Neuroanatomy': ['brain', 'cortex', 'gyrus', 'lobe', 'striatum', 'thalamus', 'hippocampus', 'amygdala', 'basal ganglia', 'cerebellum', 'nucleus', 'substantia nigra', 'putamen', 'caudate', 'pallidus', 'ventricular', 'neocortex', 'corpus callosum', 'white matter', 'gray matter', 'axon', 'dendrite', 'neuron', 'glia', 'meningeal', 'myelin', 'spinal cord', 'brainstem'],
    'B. Neuropharmacology & Biochemistry': ['dopamine', 'serotonin', 'glutamate', 'gaba', 'acetylcholine', 'nicotinic', 'muscarinic', 'nmda', 'ampa', 'neurotransmitter', 'receptor', 'chemical', 'molecule', 'drug', 'agonist', 'antagonist', 'kinase', 'phosphatase', 'enzyme', 'cannabinoid', 'bdnf', 'l-dopa', 'protein', 'peptide', 'dna', 'rna'],
    'C. Neurophysiology & Brain Activity': ['eeg', 'meg', 'bold', 'oscillation', 'rhythm', 'alpha', 'beta', 'gamma', 'theta', 'wave', 'coherence', 'synchronization', 'evoked potential', 'mep', 'erp', 'lfp', 'potential', 'firing', 'burst', 'power', 'erp'],
    'D. Brain Stimulation & Intervention': ['tms', 'tdcs', 'stimulation', 'microstimulation', 'optogenetic', 'chemogenetic', 'electrical stimulation', 'epidural', 'neurostimulation', 'deep brain stimulation', 'dbs', 'nibs', 'ct bs', 'tbs'],
    'E. Motor Skills & Performance': ['skill', 'performance', 'expertise', 'athlete', 'sport', 'tennis', 'golf', 'baseball', 'basketball', 'soccer', 'swimming', 'dance', 'drawing', 'typing', 'handwriting', 'juggling', 'kicking', 'throwing', 'aiming', 'reach', 'grasp', 'dexterity', 'musician', 'pianist', 'surgeon', 'surgical skill', 'rowing', 'fencing', 'martial arts', 'suturing'],
    'F. Motor Control & Execution': ['motor control', 'control', 'kinematics', 'kinetics', 'force', 'torque', 'velocity', 'acceleration', 'dynamics', 'trajectory', 'movement', 'posture', 'synergy', 'redundancy', 'degrees of freedom', 'df', 'dof', 'inverse model', 'forward model', 'feedback', 'feedforward', 'primitives', 'jerk', 'coordination', 'gait', 'balance'],
    'G. Motor Learning: General/Theory': ['motor learning', 'learning', 'skill acquisition', 'acquisition', 'retention', 'transfer', 'generalization', 'theory', 'schema', 'consolidation', 'memory', 'savings', 're-learning', 'automatization', 'practice', 'training', 'procedural learning'],
    'H. Motor Learning: Mechanisms & Factors': ['practice', 'feedback', 'instruction', 'knowledge of results', 'kr', 'knowledge of performance', 'kp', 'schedule', 'variability', 'interference', 'contextual', 'dosage', 'error', 'amplification', 'difficulty', 'guidance', 'repetition', 'spacing', 'massed', 'yoked'],
    'I. Implicit vs. Explicit Learning': ['implicit', 'explicit', 'awareness', 'conscious', 'procedural', 'declarative', 'unconscious', 'non-declarative', 'monitoring', 'controlled processing'],
    'J. Sensory & Perceptual Systems': ['sensory', 'somatosensory', 'proprioception', 'tactile', 'haptic', 'auditory', 'vestibular', 'perception', 'integration', 'recalibration', 'cross-modal', 'multisensory', 'senses', 'afferent', 'efferent', 'vision'],
    'K. Plasticity & Adaptation': ['plasticity', 'adaptation', 'ltp', 'ltd', 'potentiation', 'depression', 'metaplasticity', 'reorganization', 're-organization', 'remapping', 'use-dependent'],
    'L. Cognition & Executive Function': ['cognition', 'cognitive', 'attention', 'executive function', 'working memory', 'wm', 'processing', 'load', 'task switch', 'mental', 'decision making', 'planning', 'control', 'mind', 'reasoning', 'computational psychiatry', 'memory'],
    'M. Computational & Modeling': ['model', 'computational', 'algorithm', 'simulation', 'neural network', 'deep learning', 'machine learning', 'predictive', 'bayesian', 'dynamical system', 'theory', 'optimization', 'prediction', 'manifold', 'complexity', 'artificial intelligence', 'robot control'],
    'N. Robotics & Technology': ['robot', 'virtual reality', 'vr', 'exoskeleton', 'assistive', 'bmi', 'bci', 'wearable', 'haptic device', 'kinect', 'mri-compatible', 'technology', 'system design', 'interface', 'simulator', 'laparoscopy'],
    'O. Clinical Conditions & Disease Models': ['parkinson', 'dystonia', 'ataxia', 'stroke', 'cerebral palsy', 'autism', 'schizophrenia', 'alzheimer', 'dementia', 'adhd', 'epilepsy', 'huntington', 'disease', 'disorder', 'syndrome', 'injury', 'lesion', 'hemiparesis', 'tremor', 'multiple sclerosis', 'ms', 'dcd', 'pain'],
    'P. Rehabilitation & Therapy': ['rehabilitation', 'therapy', 'treatment', 'intervention', 'clinical', 'physical therapy', 'occupational therapy', 'cimt', 'music-supported', 'gait training', 'assistive', 'functional recovery', 'neurorehabilitation', 'prehab', 'neurodevelopmental treatment'],
    'Q. Psychological Factors & Motivation': ['motivation', 'emotion', 'anxiety', 'self-efficacy', 'self-control', 'goal', 'stress', 'mindfulness', 'imagery', 'mental practice', 'mental-training', 'attitude', 'expectancy', 'psychology', 'social', 'confidence'],
    'R. Timing & Rhythm': ['timing', 'rhythm', 'temporal', 'synchronization', 'metronome', 'interval', 'period', 'tempo', 'timing'],
    'S. Research Methodology & Statistics': ['study', 'method', 'trial', 'experiment', 'analysis', 'anova', 'regression', 'statistic', 'measurement', 'assessment', 'test', 'scale', 'questionnaire', 'survey', 'reliability', 'validity', 'electrophysiology', 'quantitative', 'qualitative', 'bias', 'longitudinal', 'cross-sectional', 'head'],
    'T. Human & Animal Subjects': ['human', 'animal', 'subject', 'patient', 'child', 'infant', 'adult', 'elderly', 'older', 'adolescent', 'male', 'female', 'mice', 'rat', 'monkey', 'primate', 'songbird', 'athlete', 'gamer', 'novice', 'expert', 'td', 'typical', 'population'],
    'U. Vision & Oculomotor Control': ['saccade', 'eye movement', 'gaze', 'ocular', 'oculomotor', 'vor', 'visual tracking', 'visual field', 'vision', 'visual'],
    'V. Speech & Language': ['speech', 'language', 'vocal', 'stutter', 'phonetics', 'pronunciation', 'grammar', 'tongue', 'articulation', 'singing', 'apraxia of speech', 'dysarthria', 'communication'],
    'W. Development & Lifespan': ['development', 'aging', 'infancy', 'childhood', 'adolescence', 'postnatal', 'critical period', 'life-span', 'developmental coordination disorder', 'dcd', 'maturation', 'onset', 'developmental'],
    'X. Imaging & Assessment Techniques': ['fmri', 'mri', 'eeg', 'meg', 'pet', 'dti', 'fnirs', 'electromyography', 'emg', 'biomechanics', 'posturography', 'kinematics', 'kinetics', 'assessment', 'test', 'scale', 'survey', 'imaging', 'spectroscopy', 'microscopy', 'analysis'],
    'Z. Unclassified': ['( R )-(+)-[2,3-dihydro-5-methyl-3-(4-morpholinylmethyl)pyrrolo[1,2,3-de]-1,4-benzoxazin-6-yl]-1-naphthalenylmethanone mesylate', '2 S', '2', '212-2 mesylate', '2300', '2320', '2323', '2326', '2330', '2340', '2343', '3-dicarboxylic acid1s', '3-dicarboxylic acidt-acpd', '3-dicarboxylic acid±-trans-acpd', '3-dione', '3-dionecnqx', '3380', '3700', '3720', '3r)-1-aminocyclopentane-1', '4c3hpg', '5-dihydroxyphenilglycine', '7-nina', 'aida', 'ap-v (ap-5)', 'bapta', 'bis(2-aminophenoxy)ethane-n', 'chpg', 'cpccoet', 'dag', 'dcg-iv', 'dl-amino-5-phosphonopentanoic acid', 'dl-amino-5-phosphonopentanoic acidap-v ap-5', 'dnqx 6', 'dopamineda', 'egta', 'entopeduncular nucleusepn', 'epsp', 'ethylene glycol bisβ-aminoethyl ether-n', 'excitatory post-synaptic potentialepsp', 'g-protein coupled receptorgprc', 'gprc', 'hd', 'hfs', 'i-ltp', 'inositol-3-phosphateip3', 'ip3', 'l-2-amino-3-phosphonopropionatel-ap3', 'l-ap3', 'l-ccg-i', 'l-name', 'l-serine-o-phosphatel-sop', 'l-sop', 'ltd', 'mcp g', 'mglur', 'mglur1 knock-outmglur1-/-', 'mglur1-/-', 'mglur5 knock-outmglur5-/-', 'mglur5-/-', 'mma', 'mpep', 'msop', 'n', 'n′', 'o bis(2-aminoethyl)ethyleneglycol-n', 'nac', 'ng-nitro-l-arginine methylesterl-name', 'nmda', 'nos', 'nacl', 'protein phosphatase 1pp-1', 'rs-1-aminoindan-1', 'rs-2-chloro-5-hydroxyphenylglycinechpg', 's-α-methylserine-o-phosphatemsop', 's-4-carboxy-3-hydroxyphenylglycine4c3hpg', 's-4-carboxyphenylglycine4-cpg', 'snap', 'sd', 'snc/r', 'stn', 't-acpd', 'tea', 'tetrodotoxinttx', 'tpa', 'ttx', 'vdcc', '±-trans-1-aminocyclopentane-1', 'vdp']
}

# Function for multi-label classification
def classify_keyword_multi_label(keyword):
    kw_lower = keyword.lower()
    matched_categories = []

    # Check for unclassified first (exact match only for highly specific, fragmented terms)
    # The 'Z. Unclassified' list contains items the user explicitly mentioned or are fragments.
    if keyword in CATEGORIES['Z. Unclassified']:
        return ['Z. Unclassified']

    # Iterate through all categories and assign ALL matches (multi-label)
    for category, terms in CATEGORIES.items():
        if category == 'Z. Unclassified':
            continue  # Skip checking general keywords against the unclassified list

        # General approach: check if any term is a substring
        if any(term in kw_lower for term in terms):
            matched_categories.append(category)
    
    # If no matches found in any category, assign to unclassified (catch-all for new ambiguous terms)
    if not matched_categories:
        return ['Z. Unclassified']
    
    # Remove duplicates and sort for consistency
    return sorted(list(set(matched_categories)))

# Read keywords from the document and classify
input_file = 'keywords_histograms/all_keywords_processed.txt'
output_file = 'keyword_classification_25_categories.csv'

try:
    with open(input_file, 'r', encoding='utf-8') as f:
        keywords = [line.strip() for line in f if line.strip()]
except FileNotFoundError:
    print(f"Error: Input file {input_file} not found.")
    keywords = []

# delete the first two since they are the title of the file
keywords.pop(0)
keywords.pop(0)
# Create CSV output
output_data = []
for keyword in keywords:
    categories = classify_keyword_multi_label(keyword)
    # Join multiple categories into a single string for the CSV cell, separated by a semicolon
    output_data.append([keyword, '; '.join(categories)])

# Write to CSV
if output_data:
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['keyword', 'categories'])
        writer.writerows(output_data)

# Prepare data for histogram (frequency count)
category_counts = {}
for _, categories_str in output_data:
    # Split the string of categories to count each one
    categories_list = categories_str.split('; ')
    for category in categories_list:
        category_counts[category] = category_counts.get(category, 0) + 1

# Sort categories for presentation
sorted_counts = sorted(category_counts.items(), key=lambda item: item[1], reverse=True)

# Print the final summary
print(f"Total classified keywords: {len(output_data)}")
print(f"Classification saved to {output_file} (FileTag: keyword_classification_25_categories.csv)")
print("\nTop 10 Category Frequencies (from total keyword classifications):")
for category, count in sorted_counts[:10]:
    print(f"- {category}: {count}")

unclassified_count = category_counts.get('Z. Unclassified', 0)
print(f"\nTotal Z. Unclassified count: {unclassified_count}")

# Print the complete list of 25 categories and their counts
print("\nAll 25 Category Frequencies:")
all_category_counts = {cat: 0 for cat in CATEGORIES.keys()}
all_category_counts.update(category_counts)
sorted_all_counts = sorted(all_category_counts.items(), key=lambda item: item[0]) # Sort alphabetically by category code

for category, count in sorted_all_counts:
    print(f"{category}: {count}")

import matplotlib.pyplot as plt
import pandas as pd
from collections import Counter

# Parameters matching the attached image and your code
title = 'All counts of keyword\'s broad categories'
meta = {'displaylabel': f"Basic: {title}", 'color': 'green'}
top_n = 25 # Plotting all mock data points
out_dir = './' # Use current directory for saving files

# --- Core Plotting Logic (adapted from your snippet) ---
# Create a DataFrame from the mock data, simulating the output of counts.most_common()
counts = Counter(all_category_counts)
df = pd.DataFrame(counts.most_common(), columns=["broad_term", "count"])
# df = df.sort_values("broad_term")

# The actual file saving logic from your code:
df.to_csv(f"all_keywords_count.csv", index=False)

# Plot top N
top = df.head(top_n)
# Reverse the lists to ensure the highest frequency is at the top of the bar chart (plt.barh default)
# and the labels are in ascending frequency order on the Y-axis (as in your image)
labels = top['broad_term'].tolist()[::-1]
values = top['count'].tolist()[::-1]

# Plotting setup
plt.figure(figsize=(10, max(4, len(labels) * 0.25))) # Dynamic figure size
color = meta.get('color', '#333333')
plt.barh(labels, values, color=color)

# Labels and Title configuration
plt.xlabel('Frequency')
plt.title(meta.get('displaylabel'))
plt.tight_layout()

# The actual file saving logic from your code:
plt.savefig(f"all_keywords_count.png", dpi=150)
# plt.close()

# Display the plot
# plt.show()

print(f"Generated plot data for class: {meta['displaylabel']}")