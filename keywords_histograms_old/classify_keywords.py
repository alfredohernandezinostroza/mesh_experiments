import csv
import re

# Define classification rules based on keyword patterns
def classify_keyword(keyword):
    kw_lower = keyword.lower()
    
    # Cerebellum Structure & Anatomy
    cerebellar_terms = ['cerebell', 'purkinje', 'granule cell', 'climbing fiber', 'climbing fibre', 
                        'mossy fiber', 'mossy fibre', 'parallel fiber', 'parallel fibre', 'floccul',
                        'vermis', 'parafloccul', 'fastigial', 'interposed', 'dentate nucleus', 
                        'inferior olive', 'pons', 'pontine', 'deep cerebellar', 'basket cell',
                        'stellate cell', 'golgi cell', 'lobule']
    
    # Cellular Neuroscience
    cellular_terms = ['neuron', 'synapse', 'dendrite', 'axon', 'spine', 'cell', 'membrane potential',
                     'action potential', 'ion channel', 'receptor', 'postsynaptic', 'presynaptic',
                     'glia', 'astrocyte', 'oligodendrocyte', 'microglia', 'interneuron', 'soma']
    
    # Neural Circuitry & Connectivity
    circuit_terms = ['circuit', 'pathway', 'connectivity', 'network', 'projection', 'tract',
                    'corticospinal', 'thalamocortical', 'corticostriatal', 'loop', 'connection',
                    'fasciculus', 'commissure', 'fiber tract', 'white matter']
    
    # Motor Learning & Motor Control
    motor_learning_terms = ['motor learning', 'motor control', 'motor skill', 'motor adaptation',
                           'motor training', 'motor practice', 'skill acquisition', 'motor memory',
                           'procedural learning', 'motor performance', 'movement learning']
    
    # Learning & Memory
    learning_memory_terms = ['learning', 'memory', 'consolidation', 'retention', 'recall',
                            'acquisition', 'transfer', 'forgetting', 'interference', 'practice',
                            'training', 'ltp', 'ltd', 'potentiation', 'depression']
    
    # Oculomotor & Eye Movement Systems
    eye_terms = ['eye movement', 'saccade', 'pursuit', 'oculomotor', 'vestibulo-ocular', 'vor',
                'gaze', 'fixation', 'visual tracking', 'optokinetic']
    
    # Plasticity
    plasticity_terms = ['plasticity', 'neuroplasticity', 'synaptic plasticity', 'reorganization',
                       'adaptation', 'potentiation', 'depression', 'metaplasticity']
    
    # Neurological & Psychiatric Disorders
    disorder_terms = ['parkinson', 'dystonia', 'ataxia', 'stroke', 'cerebral palsy', 'autism',
                     'schizophrenia', 'alzheimer', 'dementia', 'adhd', 'epilepsy', 'huntington',
                     'tremor', 'disease', 'disorder', 'syndrome', 'injury', 'lesion']
    
    # Brain Regions
    brain_region_terms = ['cortex', 'striatum', 'thalamus', 'hippocampus', 'amygdala', 'basal ganglia',
                         'prefrontal', 'motor cortex', 'premotor', 'parietal', 'frontal', 'temporal',
                         'occipital', 'insula', 'cingulate', 'substantia nigra', 'putamen', 'caudate',
                         'globus pallidus', 'nucleus']
    
    # Behavioral Neuroscience / Paradigms
    behavioral_terms = ['task', 'paradigm', 'test', 'behavior', 'performance', 'reaching', 'grasping',
                       'walking', 'gait', 'balance', 'coordination', 'reaction time', 'response time']
    
    # Methods & Technologies
    methods_terms = ['fmri', 'mri', 'eeg', 'meg', 'tms', 'tdcs', 'pet', 'imaging', 'recording',
                    'stimulation', 'electrode', 'electrophysiology', 'microscopy', 'optogenetic',
                    'calcium imaging', 'virtual reality', 'robot', 'simulation']
    
    # Neurochemistry & Molecular Biology
    neurochemistry_terms = ['dopamine', 'serotonin', 'glutamate', 'gaba', 'acetylcholine', 'receptor',
                           'neurotransmitter', 'protein', 'gene', 'nmda', 'ampa', 'bdnf', 'kinase',
                           'phosphatase', 'enzyme', 'molecule']
    
    # Biomechanics & Motor Function
    biomechanics_terms = ['kinematics', 'kinetics', 'force', 'torque', 'velocity', 'acceleration',
                         'trajectory', 'movement', 'posture', 'joint', 'muscle', 'emg', 'grip',
                         'reach', 'biomechanics']
    
    # Animal Models
    animal_terms = ['mouse', 'rat', 'monkey', 'primate', 'rodent', 'animal model', 'transgenic',
                   'knockout', 'mutant', 'mice', 'zebrafish', 'bird', 'songbird']
    
    # Clinical Research & Medicine
    clinical_terms = ['patient', 'clinical', 'therapy', 'rehabilitation', 'treatment', 'intervention',
                     'diagnosis', 'medical', 'surgery', 'hospital', 'healthcare']
    
    # Vision & Sensory Processing
    sensory_terms = ['visual', 'vision', 'sensory', 'somatosensory', 'proprioception', 'tactile',
                    'auditory', 'vestibular', 'perception', 'feedback']
    
    # Cognitive Psychology & Behavior
    cognitive_terms = ['attention', 'cognition', 'cognitive', 'awareness', 'consciousness', 'decision',
                      'motivation', 'emotion', 'psychology', 'mental']
    
    # Computational & Theoretical Models
    computational_terms = ['model', 'computational', 'algorithm', 'simulation', 'neural network',
                          'machine learning', 'prediction', 'theory', 'mathematical']
    
    # Priority order for classification (more specific to less specific)
    if any(term in kw_lower for term in cerebellar_terms):
        return "Cerebellum Structure & Anatomy"
    elif any(term in kw_lower for term in eye_terms):
        return "Oculomotor & Eye Movement Systems"
    elif any(term in kw_lower for term in motor_learning_terms):
        return "Motor Learning & Motor Control"
    elif any(term in kw_lower for term in disorder_terms):
        return "Neurological & Psychiatric Disorders"
    elif any(term in kw_lower for term in methods_terms):
        return "Methods & Technologies"
    elif any(term in kw_lower for term in animal_terms):
        return "Animal Models"
    elif any(term in kw_lower for term in clinical_terms):
        return "Clinical Research & Medicine"
    elif any(term in kw_lower for term in circuit_terms):
        return "Neural Circuitry & Connectivity"
    elif any(term in kw_lower for term in cellular_terms):
        return "Cellular Neuroscience"
    elif 'plasticity' in kw_lower or 'plastic' in kw_lower:
        return "Plasticity"
    elif any(term in kw_lower for term in neurochemistry_terms):
        return "Neurochemistry & Molecular Biology"
    elif any(term in kw_lower for term in brain_region_terms):
        return "Brain Regions"
    elif any(term in kw_lower for term in biomechanics_terms):
        return "Biomechanics & Motor Function"
    elif any(term in kw_lower for term in sensory_terms):
        return "Vision & Sensory Processing"
    elif any(term in kw_lower for term in learning_memory_terms):
        return "Learning & Memory"
    elif any(term in kw_lower for term in cognitive_terms):
        return "Cognitive Psychology & Behavior"
    elif any(term in kw_lower for term in behavioral_terms):
        return "Behavioral Neuroscience / Paradigms"
    elif any(term in kw_lower for term in computational_terms):
        return "Computational & Theoretical Models"
    else:
        return "Cognitive Psychology & Behavior"  # Default category

# Read keywords from the document and classify
with open('keywords_histograms/all_keywords_processed.txt', 'r', encoding='utf-8') as f:
    keywords = [line.strip() for line in f if line.strip()]
    
# Create CSV output
output_data = []
for keyword in keywords:
    category = classify_keyword(keyword)
    output_data.append([keyword, category])

# Write to CSV
with open('keyword_classification.csv', 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(['keyword', 'category'])
    writer.writerows(output_data)

print(f"Classified {len(output_data)} keywords into categories")
print("Output saved to keyword_classification.csv")