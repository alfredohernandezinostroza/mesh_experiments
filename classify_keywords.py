import csv
import re

# The 25 broad classification terms
# A keyword is classified into ALL categories for which it contains a matching term.
CATEGORIES = {
    'A. Neuroscience & Neuroanatomy': [
        # Existing
        'brain', 'cortex', 'gyrus', 'lobe', 'striatum', 'thalamus', 'hippocampus', 'amygdala', 
        'basal ganglia', 'cerebellum', 'nucleus', 'substantia nigra', 'putamen', 'caudate', 
        'pallidus', 'ventricular', 'neocortex', 'corpus callosum', 'white matter', 'gray matter', 
        'axon', 'dendrite', 'neuron', 'glia', 'meningeal', 'myelin', 'spinal cord', 'brainstem',
        'colliculus', 'sulcus', 'tegmentum', 'red nucleus', 'olive', 'dentate', 'fastigial', 
        'interposed', 'purkinje', 'granule cell', 'climbing fiber', 'mossy fiber', 'parallel fiber', 
        'astrocyte', 'microglia', 'oligodendrocyte', 'schwann', 'node of ranvier', 'synapse', 
        'spine', 'bouton', 'soma', 'intraparietal', 'supramarginal', 'precuneus', 'fusiform', 
        'cingulate', 'entorhinal', 'subthalamic', 'prefrontal', 'motor cortex', 'sensory cortex', 
        'parietal', 'temporal', 'frontal', 'occipital', 'insula', 'operculum', 'nerve', 'ganglion',
        'corticospinal', 'pyramidal tract', 'extrapyramidal', 'neuroma', 'radiculopathy', 'plexus',
        'subventricular', 'perineuronal', 'connectome', 'connectomics', 'cytoarchitecture',
        '(bg) basal ganglia', '(h less/more-affected ) less/more affected hemisphere', '(lh) left hemisphere', 
        '(m1) motor cortex', '(rh) right hemisphere', '1st through 4th cerebellar lobules ( 1–4cb )', 
        '3d brain cortex', 'abductor digiti minimi muscle ( adm )', 'abductor pollicis brevis muscle ( apb )', 
        'abductor pollicis longus muscle', 'achilles tendon', 'acoustic nerve', 'acoustic neuroma', 
        'agranular insular area ( iag )', 'amygdaloid body', 'anterior auditory field ( aaf )', 
        'anterior cingulate cortex ( acc )', 'anterior cingulated zone', 'anterior cruciate ligament', 
        'anterior deltoid ( ad )', 'anterior division of the rostral cingulate zone ( rcza )', 
        'anterior dorsal field ( adf )', 'anterior dorsal nucleus of the medial geniculate complex ( mgad )', 
        'anterior ectosylvian auditory area ( faes )', 'anterior ectosylvian somatosensory area ( siv )', 
        'anterior ectosylvian sulcus ( aes )', 'anterior ectosylvian visual area ( aev )', 
        'anterior forebrain pathway', 'anterior forebrain pathway ( afp )', 'anterior intraparietal area ( aip )', 
        'anterior striatum', 'anterior ventral field ( avf )', 'arcuate fasciculus', 'area v5/mt', 
        'articulatory motor cortex', 'association cortex', 'atlanto-axial joint', 'auditory cortex', 
        'auditory cortex ( ac )', 'auditory cortex ( au )',
        # New Additions
        'auditory field aes ( faes )', 'auditory field l2 (l2)', 'auditory neurons', 'auditory pathway', 
        'auditory pathways', 'avian pallium', 'axon', 'axon collateral', 'axon initial segment (ais)', 
        'axon terminals', 'axonal boutons', 'axonal collaterals', 'axonal pathways', 'axons', 
        'ba brodmann area', 'back muscles', 'barrel cortex', 'basal forebrain', 'basal ganglia', 
        'basal ganglia ( bg )', 'basal ganglia (bg)', 'basal ganglia–thalamic–cortical circuit ( btc )', 
        'basket cell ( bc )', 'basket cells', 'basolateral', 'bergmann glia', 'biceps brachii', 
        'biceps brachii ( bb )', 'brachium conjunctivum ( bc )', 'brain', 'brain anatomy', 
        'brain blood-vessels', 'brain stem', 'brain structure', 'brainstem', 'brainstem burst generator (bbg)', 
        'broca\'s area', 'broca’s area', 'broca’s region', 'brodmann area ( ba )', 'brodmann area (ba)', 
        'c2 second cervical (level of spinal cord)', 'ca3--ca1 synapse', 'ca3–ca1 synapse', 
        'canonical neurons', 'carotid artery', 'caudal ( pnc )', 'caudal auditory cortex ( cac )', 
        'caudal fastigial nucleus (cfn)', 'caudal lateral auditory belt area ( cl )', 
        'caudal medial auditory belt area ( cm )', 'caudal parabelt auditory area ( cpb )', 
        'caudal part of mt ( mtc )', 'caudal superior temporal polysensory region ( cstp )', 
        'caudate', 'caudate nucleus', 'caudate putamen', 'caudate-putamen', 'cb cerebellum', 
        'cc corpus callosum', 'cd caudate nucleus', 'cell anatomy', 'cell membranes', 'cell nuclei', 
        'central amygdala ( cea )', 'central lateral nucleus ( cl )', 'central nervous system', 
        'central nervous system ( cns )', 'central nervous system (cns)', 
        'central nucleus of the amygdala ( ce )', 'centre median nucleus ( cm )', 
        'centrolateral thalamic nucleus ( cl )', 'centromedial thalamic nucleus ( cm )', 
        'cerebellar', 'cerebellar and vestibular nuclei', 'cerebellar circuit', 'cerebellar circuitry', 
        'cerebellar cortex', 'cerebellar cortex (cc)', 'cerebellar efferent projections', 
        'cerebellar hemisphere', 'cerebellar interneurons', 'cerebellar interpositus Nucleus', 
        'cerebellar nuclei', 'cerebellar peduncles', 'cerebellar purkinje cell', 
        'cerebellar purkinje cell layer ( pcl )', 'cerebellar purkinje cells', 'cerebellar purkinje neuron', 
        'cerebellar vermis', 'cerebellar–thalamic–cortical circuit ( cbtc )', 'cerebello-cerebral loop', 
        'cerebello-thalamo-cortical pathway', 'cerebellum', 'cerebellum anatomy', 'cerebellum structure', 
        'cerebral arteries'
    ],
    'B. Neuropharmacology & Biochemistry': [
        # Existing
        'dopamine', 'serotonin', 'glutamate', 'gaba', 'acetylcholine', 'nicotinic', 'muscarinic', 
        'nmda', 'ampa', 'neurotransmitter', 'receptor', 'chemical', 'molecule', 'drug', 'agonist', 
        'antagonist', 'kinase', 'phosphatase', 'enzyme', 'cannabinoid', 'bdnf', 'l-dopa', 'protein', 
        'peptide', 'dna', 'rna', 'gene', 'genetics', 'genomic', 'expression', 'molecular', 'cellular', 
        'intracellular', 'extracellular', 'signaling', 'pathway', 'metabolism', 'metabolic', 
        'mitochondria', 'calcium', 'potassium', 'sodium', 'chloride', 'ion channel', 'pump', 
        'transporter', 'vesicle', 'synaptic', 'plasticity', 'neurotrophin', 'growth factor', 
        'cytokine', 'chemokine', 'hormone', 'steroid', 'estrogen', 'testosterone', 'cortisol', 
        'insulin', 'ghrelin', 'leptin', 'noradrenaline', 'norepinephrine', 'epinephrine', 'adrenaline', 
        'histamine', 'adenosine', 'atp', 'adp', 'camp', 'cgmp', 'second messenger', 'g-protein',
        'opioid', 'endocannabinoid', 'ligand', 'metabotropic', 'ionotropic', 'pharmaco', 'biomarker',
        'oxidative stress', 'antioxidant', 'nootropic', 'botulinum', 'toxin',
        '( r )-(+)-[2,3-dihydro-5-methyl-3-(4-morpholinylmethyl)pyrrolo[1,2,3-de]-1,4-benzoxazin-6-yl]-1-naphthalenylmethanone mesylate', 
        '(1s,3r)-1-aminocyclopentane-1', '(s)-3', '(±)-trans-1-aminocyclopentane-1', '(±)-trans-acpd', 
        '1-ebio', '1-methyl-4-phenyl-1', '11c-raclopride', '2-(5-chloro)tricyclo [3.3.1.13, 2-dioxetane-3, 7]decan}-4-Yl)phenyl phosphate ( cspd )', 
        '2-arachidonyl glycerol', '2-methyl-6-phenylethynyl-pyridinempep', '3-acetylpyridine ( 3-ap )', 
        '3-dicarboxylic acid', '3-dicarboxylic acid1s', '3-dicarboxylic acidt-acpd', '3-dicarboxylic acid±-trans-acpd', 
        '3-dione', '3-dione disodium salt ( dnqx )', '3-dionecnqx', '3-nitropropionic acid', 
        '3-nitropropionic acid ( 3-np )', '3r)-1-aminocyclopentane-1', '3r-acpd', '4-dihydroxyphenylacetic acid', 
        '4-dihydroxyphenylalanine ( l-dopa )', '5-dhpg', '5-dihydroxyphenilglycine', '5-dihydroxyphenylglycine', 
        '5-ht serotonin', '6-cyano-7-nitroquinoxaline-2', '6-hydroxydopamine', '6-hydroxydopamine ( 6-ohda )', 
        '6-tetrahydropyridin ( mptp )', '6-tetrahydropyridine ( mptp )', '7-nitro indazole monosodium salt', 
        '[11c]-raclopride ( rac )', '[11c]raclopride', '[18f]-fluorodeoxyglucose ( fdg )', 
        'a subunit of the gamma-aminobutyric acid receptor ( gabaa )', 'acetylcholine ( ach )', 
        'acetyltransferases', 'ach', 'ach acetylcholine', 'actin', 'activation energy', 'activity-dependent transcription factor', 
        'adeno-associated virus ( aav )', 'adenosine a2a receptor', 'adenosine signaling', 'adenosines', 
        'adenylate cyclase', 'adrenergic receptors', 'all-trans retinoic acid', 'alleles', 'alpha-synuclein', 
        'am251', 'amantadine', 'amines', 'amino acid ( aa )', 'amino acid neurotransmitters', 'amino acid sequence', 
        'amino acids', 'aminobutyric acid', 'ampa receptor', 'ampa receptors', 'ampar', 'amphetamine', 
        'amphetamines', 'amylases', 'anandamide', 'ano2', 'anoctamin-2', 'antagonist coactivation', 
        'anti-glur delta antibody', 'anti-mglur antibody', 'anti-nogoa', 'anti-vgcc antibody', 
        'antibacterial agents', 'antibiotics', 'antibodies ( abs )', 'antibody-toxin conjugates', 
        'antidepressants', 'antigens', 'antineoplastic agents', 'antiparkinsonian agents', 'antipsychotic agents', 
        'ap-5', 'apomorphine', 'apoptosis inducing factor', 'app amyloid precursor protein', 'arachidonic acid', 
        'aspartic acid', 'atp adenosine triphosphate',
        # New Additions
        'aurora kinase', 'autism neuroligin', 'auto-antibodies', 'autophagy', 'axonal glycoproteins', 
        'axonal transport', 'baclofen', 'bacopa monnieri', 'bacoside a', 'bacterial toxins', 'bdnf', 
        'bdnf brain-derived neurotrophic factor', 'bdnf met allele', 'bdnf val66met', 'benzodiazepine', 
        'benzodiazepines', 'beta2 nachr', 'bicuculline methiodide', 'bicuculline methiodide ( bicm )', 
        'biochemical mechanism of action', 'biochemical substrates', 'biochemistry', 'bioinformatics', 
        'biogenic amines', 'bioluminescence resonance energy transfer ( bret )', 'biomacromolecules', 
        'biomarkers', 'biomimetic materials', 'biosynthesis', 'biosynthetic techniques', 'biotechnology', 
        'biotransformation (metabolism)', 'blood lactate', 'blood lactate concentration', 'botulinum a toxins', 
        'botulinum toxin', 'brain chemistry', 'brain-derived neurotrophic factor', 
        'brain-derived neurotrophic factor (bdnf)', 'brain-derived neurotrophic factor gene polymorphisms', 
        'brain-derived neurotrophic factor genotype', 'brain‐derived neurotrophic factor', 'bromazepam', 
        'bromodeoxyuridine (brdu)', 'bungarotoxin', 'bungarotoxin ( btx )', 'butyric acid', 'c-fos', 
        'c-terminal residues', 'c1q', 'c1ql1', 'ca 2+', 'ca2+ signaling', 'ca2+-activated k+ channels', 
        'cacna1d', 'cadherins', 'caffeine', 'calcineurin', 'calcium', 'calcium activity', 'calcium channels', 
        'calcium handling', 'calcium ions', 'calcium-activated chloride channel', 'calcium-activated ion channels', 
        'calcium/calmodulin-dependent protein kinase type iv', 'calretinin', 'camp', 
        'camp cyclic adenosine monophosphate', 'camp response element binding protein', 
        'camp response element binding protein ( creb )', 'camp-dependent protein kinase', 
        'cannabinoid', 'cannabinoid 1 receptor', 'cannabinoid receptor type 1', 'cannabinoid receptors', 
        'cannabinoids', 'cannabis', 'cannabis (genus)', 'capsaicin', 'carbamazepine', 'carbidopa', 
        'carboxyl-terminal ( c-terminal )', 'cardiac glycosides', 'cardiolipin', 'carrier proteins', 
        'catechol-o-methyltransferase', 'catechol-o-methyltransferase genotype', 'catecholamines', 
        'cathepsin b', 'cations', 'cb calbindin', 'cb1 cannabinoid receptor', 'cb1r cannabinoid receptor type 1', 
        'cb2r cannabinoid receptor type 2', 'cdna microarray', 'cell adhesion molecules', 'cell biology', 
        'cell receptors', 'cell signaling', 'cell signal transduction', 'cellular retinoic acid binding protein ( crabp )', 
        'cerebellar inhibition'
    ],
    'C. Neurophysiology & Brain Activity': [
        # Existing
        'eeg', 'meg', 'bold', 'oscillation', 'rhythm', 'alpha', 'beta', 'gamma', 'theta', 'delta', 
        'mu rhythm', 'tau rhythm', 'wave', 'coherence', 'synchronization', 'desynchronization', 
        'entrainment', 'phase', 'coupling', 'cross-frequency', 'evoked potential', 'mep', 'erp', 
        'lfp', 'potential', 'firing', 'burst', 'power', 'resting-state', 'connectivity', 'granger', 
        'spindle', 'ripple', 'sharp-wave', 'slow-wave', 'event-related', 'spectral', 'time-frequency', 
        'electrophysiology', 'activity', 'activation', 'arousal', 'sleep stage', 'rem sleep',
        '%sc percentage signal change', '(amt) active motor threshold', '(i/o curve) input–output curve', 
        '(mep) motor evoked potential', '(mvc) maximal voluntary contraction', '(rmt) rest motor threshold', 
        '(sp) silent period', '1/f noise', '40-hz multi-target stimulation', 'absolute change in gain ( acg )', 
        'action potentials', 'activation', 'active motor threshold ( amt )', 'activity', 'activity-dependence', 
        'after-sensations', 'afterhyperpolarization', 'ahp afterhyperpolarization', 'alpha and beta rhythms', 
        'alpha band', 'alpha desynchronization', 'alpha event-related desynchronization', 'alpha frequency band', 
        'alpha oscillations', 'alpha power', 'alpha rhythm', 'alpha-band', 'alpha–gamma linkage', 
        'amplitude of low-frequency fluctuation', 'anticipatory neuronal activity', 'ap action potential', 
        'ap-epsp coupling', 'arousal (physiology)', 'auditory erp attenuation', 'auditory evoked response',
        # New Additions
        'auditory sources', 'awake state', 'ballistic conduction', 'bereitschaftspotential', 'beta', 
        'beta activity', 'beta oscillations', 'beta rhythm', 'beta rhythms', 'beta synchronization', 
        'beta-band', 'beta-band amplitude envelope envelope correlation', 'beta-band oscillations', 
        'beta-rebound', 'biomagnetism', 'biopotentials (electrophysiology)', 
        'blood oxygen level dependent ( bold )', 'blood oxygenation level dependent ( bold )', 
        'blood-oxygen-level-dependent ( bold )', 'bold', 'bold blood oxygenation level dependent', 
        'bold blood-oxygen-level dependent', 'bp bereitschaftspotential', 'brain activation', 
        'brain activity', 'brain connectivity', 'brain electrophysiology', 'brain functional network', 
        'brain metabolism', 'brain network dynamics', 'brain networks', 'brain oscillations', 
        'brain oscillatory activity', 'brain physiology', 'brain polarization', 'brain state', 
        'brain synchronization networks', 'brain waves', 'burst detection', 'burst firing', 
        'busy waking (bw)', 'central pattern generation', 'central pattern generator', 
        'central pattern generators', 'cerebellar higher‐Order functions', 'cerebellar processing'
    ],
    'D. Brain Stimulation & Intervention': [
        # Existing
        'tms', 'tdcs', 'stimulation', 'microstimulation', 'optogenetic', 'chemogenetic', 
        'electrical stimulation', 'epidural', 'neurostimulation', 'deep brain stimulation', 'dbs', 
        'nibs', 'ct bs', 'tbs', 'tacs', 'trns', 'tfus', 'ultrasound stimulation', 'magnetic stimulation', 
        'anodal', 'cathodal', 'sham', 'theta burst', 'paired-pulse', 'neuromodulation',
        '(tms) transcranial magnetic stimulation', '1-ebio', '40-hz multi-target stimulation', 
        '5-hz rtms', 'a-tdcs anodal transcranial direct current stimulation', 'acoustic stimulation', 
        'acupuncture anesthesia', 'afferent stimulation', 'anodal', 'anodal tdcs', 
        'anodal transcranial direct current stimulation',
        # New Additions
        'auditory stimulation', 'automated external defibrillator', 'automated external defibrillator (aed)', 
        'beta-band stimulation', 'bi-tdcs bilateral transcranial direct current stimulation', 
        'bihemispheric electrical stimulation', 'bilateral transcranial direct current stimulation (bi-tdcs)', 
        'brain stimulation', 'brain state-dependent stimulation', 'c-tdcs cathodal transcranial direct current stimulation', 
        'cathodal', 'cathodal tdcs', 'cathodal transcranial direct current stimulation', 
        'cerebellar stimulation'
    ],
    'E. Motor Skills & Performance': [
        # Existing
        'skill', 'performance', 'expertise', 'athlete', 'sport', 'tennis', 'golf', 'baseball', 
        'basketball', 'soccer', 'swimming', 'dance', 'drawing', 'typing', 'handwriting', 'juggling', 
        'kicking', 'throwing', 'aiming', 'reach', 'grasp', 'dexterity', 'musician', 'pianist', 
        'surgeon', 'surgical skill', 'rowing', 'fencing', 'martial arts', 'suturing', 'volleyball', 
        'football', 'rugby', 'hockey', 'cricket', 'gymnastics', 'running', 'walking', 'cycling', 
        'skiing', 'skating', 'driving', 'piloting', 'gaming', 'esports', 'video game', 'playing', 
        'music', 'instrument', 'violin', 'guitar', 'drumming', 'singing', 'fine motor', 'gross motor', 
        'manual', 'bimanual', 'unimanual', 'prehension', 'locomotion', 'gait', 'balance', 'posture', 
        'climbing', 'darts', 'archery', 'shooting', 'ball', 'racket', 'club', 'bat',
        '*suture techniques', '1rm', 'acrobatic training', 'acting', 'action games', 'action video games', 
        'action video gaming', 'active play', 'activities of daily living', 'activities of daily living (adl)', 
        'activities of daily living (adls)', 'aikido', 'aiming', 'amateur athletes', 'aquatic sports', 
        'archery', 'arremesso de dardo', 'association football', 'athlete', 'athlete development', 
        'athlete motor training', 'athlete training', 'athletes', 'athletic ability', 'athletic performance', 
        'athletics',
        # New Additions
        'australian football', 'australian football players', 'australian rules football', 
        'automobile driving', 'back exercises', 'badminton (game)', 'badminton (game) techniques', 
        'badminton players', 'balance ability', 'balance performance', 'balanced reaching', 
        'ball games', 'ball skills', 'ball throwing', 'ballet', 'ballet dancers', 'ballet dancing', 
        'ballet practice', 'ballistic skill', 'ballistic skills', 'ballroom dance', 'ballroom dancing', 
        'barbells', 'baseball', 'baseball instruction', 'baseball pitching', 'baseball players', 
        'baseball training', 'basic clinical skills', 'basic technical skills', 'basketball', 
        'basketball coaching', 'basketball free throw', 'basketball free throws', 'basketball games', 
        'basketball lay-up shot skill', 'basketball player recruiting', 'basketball players', 
        'basketball shooting', 'basketball teams', 'basketball techniques', 'basketball training', 
        'beam walking', 'bench press', 'bicycle riding', 'bicycling', 'billiards', 'bimanual performance', 
        'bird song', 'birdsong', 'bowlers', 'bowling', 'bowling techniques', 'bowling training', 
        'boxers (sports)', 'boxing', 'breaststroke (swimming)', 'breathing exercises', 'broad jump', 
        'calisthenics', 'capoeira (dance)', 'cavity preparation skills', 'cellists', 'cello', 'cello instruction'
    ],
    'F. Motor Control & Execution': [
        # Existing
        'motor control', 'control', 'kinematics', 'kinetics', 'force', 'torque', 'velocity', 
        'acceleration', 'dynamics', 'trajectory', 'movement', 'posture', 'synergy', 'redundancy', 
        'degrees of freedom', 'df', 'dof', 'inverse model', 'forward model', 'feedback', 'feedforward', 
        'primitives', 'jerk', 'coordination', 'gait', 'balance', 'stability', 'variability', 
        'precision', 'accuracy', 'error', 'deviation', 'correction', 'adjustment', 'execution', 
        'planning', 'preparation', 'initiation', 'termination', 'sequencing', 'timing', 'rhythm', 
        'synchronization', 'manipulation', 'effector', 'limb', 'joint', 'muscle', 'motor unit', 
        'emg', 'electromyography', 'stiffness', 'impedance', 'compliance', 'viscosity', 'inertia', 
        'center of mass', 'center of pressure', 'ground reaction', 'biomechanics',
        '(mvc) maximal voluntary contraction', '2330 motor processes', '3d reaching movements', 
        'abduction', 'abduction (kinesiology)', 'acceleration (mechanics)', 'acoustical kinematics', 
        'action control', 'action generation', 'action perception coupling', 'action planning', 
        'action preparation', 'action program', 'action selection', 'action sequences', 'adaptive motor control', 
        'adaptive movement variability', 'adjustability of grasping force', 'adjustment', 'afferent feedback', 
        'aiming movements', 'ajustements posturaux anticipés', 'akinesia', 'amplitude and position coding', 
        'animal locomotion', 'animal mechanics', 'ankle dorsiflexion', 'ankle dorsiflexion (adf)', 
        'ankle physiology', 'ankle--hip relative phase', 'ankle-hip coordination', 'antagonist coactivation', 
        'anterior–posterior ground reaction force (ap-grf)', 'anticipatory planning', 'anticipatory postural adjustment', 
        'anticipatory postural adjustments', 'arm dynamics', 'arm kinematics', 'arm motor performance', 
        'arm movement', 'arm movements', 'arm muscles', 'arm physiology', 'arm reaching', 'arm reaching movement', 
        'arm weight compensation', 'arm-reaching', 'articulating', 'articulation', 'asymmetric', 
        'audio-motor integration', 'audiomotor resonance',
        # New Additions
        'auditory feedback control', 'auditory movement information', 'auditory- sensory-motor integration', 
        'auditory-motor coupling', 'auditory-motor interactions', 'auditory-motor resonance', 
        'auditory-motor synchronization', 'auditory–motor interaction', 'automatic control', 
        'automatic control systems', 'automatic postural response', 'automobile dynamics', 
        'backdrivability', 'balance', 'balance control', 'balance perturbations', 'balance reaction', 
        'balance recovery', 'balancing task', 'ball velocity', 'ballistic movement', 'ballistic movements', 
        'ballistics', 'bang–bang control', 'bearing angle strategy', 'bi-articular muscle', 'bimanual', 
        'bimanual affordances', 'bimanual control', 'bimanual coordination', 'bimanual force control', 
        'bimanual manipulation', 'bimanual motor coordination', 'bimanual movement', 'bimanual movements', 
        'bimanual tapping', 'bimanual task', 'bimanual unloading', 'bio-inspired motor control', 
        'biological feedback control systems', 'biological locomotion', 'biological motion kinematics', 
        'biological systems control', 'biomimetic motor control', 'body movement', 'body sway', 
        'brake systems', 'breakaway friction', 'catching', 'catching task', 'causal control', 
        'cellular control mechanisms', 'cellular mechanics', 'center of gravity ( cog )', 
        'center of gravity (cog)', 'center of mass', 'center of pressure', 'center of vertical pressure', 
        'center of vertical pressure (cvp)', 'center-of-mass ( com )', 'center-out reaching', 
        'central pattern generation', 'central pattern generator', 'central pattern generators', 
        'centre of gravity', 'centre of mass', 'centre of pressure', 'cerebellar modules'
    ],
    'G. Motor Learning: General/Theory': [
        # Existing
        'motor learning', 'learning', 'skill acquisition', 'acquisition', 'retention', 'transfer', 
        'generalization', 'theory', 'schema', 'consolidation', 'memory', 'savings', 're-learning', 
        'automatization', 'practice', 'training', 'procedural learning', 'adaptation', 'aftereffect', 
        'interference', 'facilitation', 'inhibition', 'plasticity', 'use-dependent', 'experience-dependent', 
        'offline', 'online', 'fast learning', 'slow learning', 'stage', 'phase', 'curve', 'asymptote', 
        'plateau',
        '(incidental) motor learning', '(ml) motor learning', '(mp) motor practice', 'acquirable skill', 
        'acquisition and retention', 'acquisition learning', 'acquisition of motor learning', 
        'acquisition of skilled behavior', 'acquisition phase', 'action-effect-related motor adaptation', 
        'adaptation', 'adaptation model', 'adaptation models', 'adaptational effects', 'adaptive generalization', 
        'adaptive learning', 'after-effect', 'after-effects', 'aftereffect', 'aftereffects', 'analogy learning', 
        'anticipatory recall', 'apprentissage', 'apprentissage des aptitudes motrices', 'aprendizagem', 
        'aprendizagem em labirinto', 'aprendizagem motora', 'arbitrary associative visual motor learning', 
        'arbitrary mapping', 'artificial grammar learning', 'association learning', 'associative learning', 
        'associative motor learning',
        # New Additions
        'auditory learning', 'auditory perceptual learning', 'automatic skill acquisition', 
        'automaticity', 'automaticity (learning process)', 'automatization', 'autonomous learning', 
        'autonomous motor learning', 'balance learning', 'ballistic motor learning', 
        'ballistic training', 'bayesian learning', 'behavioral adaptation', 'behavioral training', 
        'bilateral transfer', 'bimanual learning', 'bimanual sequence learning', 'bimanual transfer', 
        'birdsong learning', 'blended learning', 'broad learning', 'cerebellar adaptation', 
        'cerebellar learning', 'cerebellar motor learning', 'cerebellar reserve'
    ],
    'H. Motor Learning: Mechanisms & Factors': [
        # Existing
        'practice', 'feedback', 'instruction', 'knowledge of results', 'kr', 'knowledge of performance', 
        'kp', 'schedule', 'variability', 'interference', 'contextual', 'dosage', 'error', 'amplification', 
        'difficulty', 'guidance', 'repetition', 'spacing', 'massed', 'yoked', 'augmented', 'terminal', 
        'concurrent', 'bandwidth', 'fading', 'summary', 'average', 'self-controlled', 'dyad', 'observational', 
        'demonstration', 'modeling', 'mental practice', 'imagery', 'part-practice', 'whole-practice',
        '3d feedback', 'acoustic feedback', 'action imitation', 'action observation', 'action observation therapy', 
        'action-effect association', 'action-effect contingency', 'action-observation', 'active exploration', 
        'active exposure', 'active learning', 'active training', 'adaptive schedules', 'adaptive training', 
        'advance-cue usage', 'afferent feedback', 'algorithm-based practice schedule', 'allocentric observation', 
        'altered auditory feedback', 'amount of practice', 'analogy', 'anchoring', 'anchoring strategy', 
        'anchors', 'artificial feedback', 'assisted training', 'association of ideas', 'associative input', 
        'at-home training', 'attention focusing in execution of complex sensorimotor skills', 'attentional anchor', 
        'attentional focus', 'attentional focusing', 'audio-motor training', 'augmented feedback',
        # New Additions
        'auditory feedback', 'auditory feedback perturbation', 'auditory pacing', 'auditory training', 
        'auditory-motor training', 'augmented cues', 'augmented extrinsic feedback', 
        'augmented feed- back', 'augmented feedback', 'augmented feedback processing', 
        'augmented information', 'augmented visual feedback', 'augmented-feedback', 
        'auto-generated augmented feedback', 'automated animal training', 'balance practice', 
        'balance training', 'bandwidth', 'bandwidth knowledge of results', 'bandwidths', 
        'behavioral paradigm', 'behavioral task', 'behavioral tasks', 'bewegunsgvorstellungstraining', 
        'bilateral training', 'bimanual training', 'biofeedback training', 'blocked practice', 
        'blocked-practice', 'catch trials'
    ],
    'I. Implicit vs. Explicit Learning': [
        # Existing
        'implicit', 'explicit', 'awareness', 'conscious', 'procedural', 'declarative', 'unconscious', 
        'non-declarative', 'monitoring', 'controlled processing', 'automatic', 'automaticity', 
        'dual-task', 'secondary task', 'cognitive load', 'working memory load', 'verbalization', 
        'verbal report', 'rule', 'strategy', 'sequence learning', 'serial reaction time', 'srt',
        'action awareness', 'alternating serial reaction time task', 'attention to action', 
        'awareness', 'associative sequence learning',
        # New Additions
        'automatic processing', 'awareness', 'awareness of movement'
    ],
    'J. Sensory & Perceptual Systems': [
        # Existing
        'sensory', 'somatosensory', 'proprioception', 'proprioceptive', 'tactile', 'haptic', 
        'auditory', 'vestibular', 'perception', 'integration', 'recalibration', 'cross-modal', 
        'multisensory', 'senses', 'afferent', 'efferent', 'vision', 'visual', 'ocular', 'eye', 
        'ear', 'skin', 'touch', 'sound', 'noise', 'vibration', 'temperature', 'nociception', 'pain', 
        'gustatory', 'olfactory', 'psychophysics', 'threshold', 'discrimination', 'detection', 
        'illusion', 'hallucination',
        '3d shape perception', 'a audio/auditory', 'absolute pitch', 'acoustic localization', 
        'acoustic signals', 'action perception', 'action sounds', 'active sensing', 'afferent pathways', 
        'after-sensations', 'altered auditory feedback', 'ambulatory electrocardiography', 'amplitude modulation', 
        'animal sounds', 'anterior auditory field ( aaf )', 'anterior ectosylvian auditory area ( faes )', 
        'anterior ectosylvian somatosensory area ( siv )', 'anterior ectosylvian visual area ( aev )', 
        'artificial touch', 'audio', 'audio-somatosensory', 'audio-tactile', 'audio-visual', 
        'audio-visual interaction', 'audiotactile integration', 'audiovisual', 'audiovisual congruency', 
        'audiovisual integration', 'audio–visual', 'audio–visual interaction', 'audition', 'auditory', 
        'auditory ( a )', 'auditory adaptation', 'auditory context', 'auditory cue', 'auditory cueing', 
        'auditory cuing', 'auditory dominance',
        # New Additions
        'auditory feedback', 'auditory localization', 'auditory movement information', 'auditory perception', 
        'auditory perception in children', 'auditory perception testing', 'auditory perceptual threshold', 
        'auditory perturbation', 'auditory rhythm', 'auditory sensory', 'auditory sources', 
        'auditory-somatosensory integration', 'auditory–visual', 'augmented reality', 'av audiovisual', 
        'bilateral', 'biological motion', 'biological motion perception', 'bisensory', 
        'bisensory attention', 'blindness', 'blindsight', 'blindsight (visual perception)', 
        'body image', 'body part coding', 'body representation', 'body representations', 'body schema', 
        'bone conduction'
    ],
    'K. Plasticity & Adaptation': [
        # Existing
        'plasticity', 'adaptation', 'ltp', 'ltd', 'potentiation', 'depression', 'metaplasticity', 
        'reorganization', 're-organization', 'remapping', 'use-dependent', 'homeostatic', 'hebbian', 
        'synaptic plasticity', 'structural plasticity', 'functional plasticity', 'recovery', 'repair', 
        'regeneration', 'sprouting', 'pruning',
        '3-nitropropionic acid-induced long-term potentiation', '3-nitropropionic acid-induced long-term potentiation3-np-ltp', 
        '3-np-ltp', 'aberrant plasticity', 'abnormal reorganization', 'acquisition learning', 
        'activity-dependent plasticity', 'activity‐dependent plasticity', 'adaptation', 'adaptation model', 
        'adaptive plasticity', 'aftereffect', 'associative and non-associative plastic processes', 
        'associative plasticity',
        # New Additions
        'auditory perceptual learning', 'axonal competition', 'axonal swelling', 'axonal swellings', 
        'bacterial adaptation', 'behavioral compensation', 'behavioural tagging', 'bidirectional plasticity', 
        'biological adaptation', 'brain adaptation', 'brain plasticity', 'camkii plasticity', 
        'cerebellar ltd', 'cerebellar plasticity'
    ],
    'L. Cognition & Executive Function': [
        # Existing
        'cognition', 'cognitive', 'attention', 'executive function', 'working memory', 'wm', 
        'processing', 'load', 'task switch', 'mental', 'decision making', 'planning', 'control', 
        'mind', 'reasoning', 'computational psychiatry', 'memory', 'inhibition', 'suppression', 
        'updating', 'shifting', 'flexibility', 'intelligence', 'iq', 'aptitude', 'focus', 
        'concentration', 'vigilance', 'awareness', 'consciousness', 'problem solving', 'creativity', 
        'language', 'speech', 'semantic', 'episodic',
        '2340 cognitive processes', '2343 learning & memory', 'abilities', 'ability', 'ability research', 
        'ability testing', 'ability-related differences', 'abstract structure', 'abstract thought', 
        'academic ability', 'academic achievement', 'academic motivation', 'academic tasks', 'acalculia', 
        'achievement', 'action concepts', 'action memory', 'action prediction', 'action processing', 
        'action representation', 'action representations', 'action understanding', 'action-cognition coupling', 
        'action–cognition coupling', 'activity control task (act)', 'adaptive engagement', 'adaptive shift', 
        'age factors in cognition', 'age factors in memory', 'age-dependence', 'alerting', 'allocation of attention', 
        'ambiguity tolerance', 'analogical reasoning', 'animal cognition', 'animal intelligence', 
        'anticipatory recall', 'apperception', 'aptitudes', 'arithmetic', 'arithmetic problem-solving', 
        'association', 'association of ideas', 'associative memory', 'associative memory (psychology)', 
        'associative processes', 'attention', 'attention (behavior)', 'attention and executive control', 
        'attention control', 'attention demand', 'attention demands', 'attention distraction', 'attention in children', 
        'attention research', 'attention resources', 'attention span', 'attention testing', 'attentional bias', 
        'attentional blink', 'attentional capture', 'attentional control', 'attribute–treatment interaction',
        # New Additions
        'auditory memory', 'auditory selective attention', 'autobiographical memory', 'autodidacticism', 
        'autonomy', 'avoidance', 'awareness', 'behavior', 'behavioural disinhibition', 'belief', 
        'belief & doubt', 'beliefs', 'binding', 'bodily self-consciousness', 'body image', 
        'body image in children', 'body ownership', 'brainwashing', 'c-ic cognitive-inhibitory control', 
        'ca cognitive ability', 'cache memory', 'categorization', 'categorization (psychology)', 
        'central executive', 'cerebellum .working memory. fmri'
    ],
    'M. Computational & Modeling': [
        # Existing
        'model', 'computational', 'algorithm', 'simulation', 'neural network', 'deep learning', 
        'machine learning', 'predictive', 'bayesian', 'dynamical system', 'theory', 'optimization', 
        'prediction', 'manifold', 'complexity', 'artificial intelligence', 'robot control', 
        'classifier', 'decoder', 'encoding', 'decoding', 'dimensionality reduction', 'pca', 'ica', 
        'lda', 'svm', 'regression', 'correlation', 'cluster', 'dynamics', 'attractor', 'bifurcation', 
        'chaos', 'noise', 'stochastic', 'deterministic', 'linear', 'nonlinear', 'parameter', 
        'estimation', 'kalman', 'markov', 'monte carlo',
        '(i/o curve) input–output curve', '1/f noise', '3d model', '3d reconstruction', 'act-r', 
        'action models', 'active inference', 'actor-critic', 'actor–critic Network', 'act‐r', 
        'adaptation model', 'adaptation models', 'adaptive control', 'adaptive control systems', 
        'adaptive dynamic programming', 'adaptive internal model', 'adaptive logics', 'adaptive neural control', 
        'adaptive system', 'adaptive systems', 'adaptive threshold-hunting', 'algorithm-based practice schedule', 
        'algorithms', 'analysis of covariance', 'analyses of variance ( anova )', 'analysis of variance', 
        'analysis of variance ( anova )', 'analysis of variance (anova)', 'apriori algorithm', 
        'arbitrary constants', 'artificial intelligence', 'artificial neural connection', 'artificial neural network', 
        'artificial neural networks', 'artificial spiking neural network', 'association model', 
        'asymptotes', 'attractor dynamics', 'attractors (mathematics)',
        # New Additions
        'auto-associative and hetero-associative networks', 'autocorrelation', 'autoencoder (ae)', 
        'autoencoder networks', 'backpropagation', 'basis function', 'bayes factor', 'bayesian', 
        'bayesian analysis', 'bayesian and biologically inspired models', 'bayesian causal inference', 
        'bayesian field theory', 'bayesian hierarchical models', 'bayesian inference', 'bayesian integration', 
        'bayesian learning', 'bayesian model', 'bayesian model comparison', 'bayesian modeling', 
        'bayesian models', 'bayesian processes', 'bayesian theory', 'biocomputational modeling', 
        'biological models', 'biological neural networks', 'biological system modeling', 
        'biologically inspired computing', 'brain model', 'brain modeling', 'brain models', 'calculus of tensors'
    ],
    'N. Robotics & Technology': [
        # Existing
        'robot', 'virtual reality', 'vr', 'exoskeleton', 'assistive', 'bmi', 'bci', 'wearable', 
        'haptic device', 'kinect', 'mri-compatible', 'technology', 'system design', 'interface', 
        'simulator', 'laparoscopy', 'teleoperation', 'telepresence', 'prosthesis', 'prosthetic', 
        'orthosis', 'orthotic', 'device', 'sensor', 'actuator', 'manipulator', 'controller', 
        'software', 'hardware', 'system', 'machine', 'computer', 'digital', 'engineering', 
        'mechatronics', 'app', 'smartphone', 'tablet', 'camera', 'tracker', 'motion capture', 
        'imu', 'accelerometer', 'gyroscope', 'magnetometer',
        '(hmd) head mounted display', '(vr) virtual reality', '2d laparoscopy', '3d laparoscopy', 
        '3d robotic manipulandum', '3d visualization', 'aac system design', 'accelerator', 'accelerometer', 
        'accelerometers', 'accelerometry', 'acoustic devices', 'acquisition of electronic information resources', 
        'active video game', 'active video games', 'active video gaming', 'activity recognition', 
        'actuators', 'aerospace electronics', 'air cylinders', 'air traffic control', 'animation (cinematography)', 
        'animations', 'ankle-foot-orthosis', 'app automated pellet presentation', 'application software', 
        'artificial arms', 'artificial hands', 'artificial implants', 'artificial limbs', 'artificial muscles', 
        'artificial objects', 'assistance system', 'assistive devices', 'assistive robotics', 'assistive technologies', 
        'assistive technology', 'audio signal processing', 'audiovisual aids in education', 'audiovisual equipment', 
        'audiovisual materials',
        # New Additions
        'augmented reality', 'augmented reality (ar)-biofeedback motion training', 'authoring tools and methods', 
        'automated external defibrillator', 'automated external defibrillator (aed)', 'automated task', 
        'automatic data collection systems', 'automation', 'automobile driving simulators', 'automotive navigation systems', 
        'autonomous robots', 'autopilot', 'avatars (virtual reality)', 'backdrivability', 'bandwith allocation', 
        'bci', 'bci/bmi brain computer/machine interface', 'bio-inspired robotics', 'biodex balance system', 
        'bioengineering', 'biofeedback system', 'biomedical engineering', 'biomedical transducers', 
        'biometric identification', 'biomimetic materials', 'bionics', 'bioprosthesis', 'biorobotics', 
        'biotechnology', 'body-machine interface', 'body-weight supported treadmill training', 
        'brain computer interface', 'brain machine interface', 'brain-computer inefficiency', 
        'brain-computer interface', 'brain-computer interfaces', 'brain-computer interfaces (bcis)', 
        'brain-computer-interface', 'brain-machine interface', 'brain-machine interface (bmi)', 
        'brain-machine interfaces', 'brain-machine interfacing (bmi)', 'brain-robot interface', 
        'brain‐computer interface (bci)', 'brain–computer interface', 'brain–computer interface (bci)', 
        'brain–computer interfaces', 'brain–e interface', 'brain–machine interface', 
        'brain–machine interface (bmi)', 'brain–robot interface'
    ],
    'O. Clinical Conditions & Disease Models': [
        # Existing
        'parkinson', 'dystonia', 'ataxia', 'stroke', 'cerebral palsy', 'autism', 'schizophrenia', 
        'alzheimer', 'dementia', 'adhd', 'epilepsy', 'huntington', 'disease', 'disorder', 'syndrome', 
        'injury', 'lesion', 'hemiparesis', 'tremor', 'multiple sclerosis', 'ms', 'dcd', 'pain', 
        'neuropathy', 'radiculopathy', 'myopathy', 'amyotrophic lateral sclerosis', 'als', 'tumor', 
        'cancer', 'oncology', 'trauma', 'tbi', 'concussion', 'psychiatric', 'depression', 'anxiety', 
        'addiction', 'obesity', 'diabetes', 'cardiovascular', 'aging', 'frailty', 'impairment', 
        'disability', 'handicap', 'pathology', 'diagnosis', 'prognosis', 'etiology', 'epidemiology',
        '(pd) parkinson\'s disease', '(pdp) patients with parkinson\'s disease', '(updrs) unified parkinson disease rating scale', 
        '22q11 deletion syndrome', '3-acetylpyridine ( 3-ap )', '3-acetylpyridine (3-ap)', 
        '3-nitropropionic acid', '3xtg-ad', '5xfad', '5xfad mouse model', '6-hydroxydopamine ( 6-ohda )', 
        '6-ohda-induced lesion', '6-tetrahydropyridin ( mptp )', '6-tetrahydropyridine ( mptp )', 
        'abnormal reflexes', 'acalculia', 'accident prevention', 'accidental falls', 'accidental falls in old age', 
        'acoustic neuroma', 'acquired brain injury', 'acidente vascular cerebral', 'acl injury', 
        'acute cerebellar stroke', 'acute cerebellitis', 'acute diseases', 'acute inflammation', 
        'acute pain', 'acute stroke', 'addiction', 'adhd', 'adverse health care events', 'affective disorders', 
        'age factors in cognition disorders', 'age factors in disease', 'agraphia', 'akinesia', 
        'albinism', 'alcohol drug abuse', 'alcohol-related neurodevelopmental disorders (arnd)', 
        'alpha-synucleinopathy', 'alzheimer', 'alzheimer\'s disease', 'alzheimer\'s patients', 
        'alzheimer’s disease', 'amaurosis fugax', 'amnestic mild cognitive impairment', 'amputation', 
        'amputation complications', 'amputees', 'amyotrophic lateral sclerosis', 'anaerobic infections', 
        'anaesthetic neurotoxicity', 'ankle abnormalities', 'ankle injuries', 'ankle injury', 
        'anterior cruciate ligament (acl) injury', 'anterior cruciate ligament injuries', 'anterior knee pain', 
        'anxiety', 'anxiety disorders', 'anxiety in old age', 'apathy', 'aphasia', 'aphasic persons', 
        'apraxia', 'apraxia of speech', 'apraxic agraphia', 'arm abnormalities', 'arm amputation', 
        'arm paralysis', 'arnold-chiari deformity', 'arthroplasty', 'articulation disorders', 
        'articulation disorders in children', 'asd', 'asperger syndrome', 'asperger\'s syndrome', 
        'asperger\'s syndrome in children', 'asperger’s disorder', 'asperger’s disorder (ad)', 
        'aspiration pneumonia', 'asthenia', 'ataxia', 'ataxin1', 'attention deficit hyperactivity disorder', 
        'attention deficit hyperactivity disorder (adhd)', 'attention deficit-hyperactivity disorder', 
        'attention deficit/hyperactivity disorder ( adhd )', 'attention-deficit disorder in adults', 
        'attention-deficit hyperactivity disorder', 'attention-deficit/hyperactivity disorder', 
        'attention-deficit/hyperactivity disorder (adhd)', 'attention‐deficit/hyperactivity disorder',
        # New Additions
        'aujeszky\'s disease virus', 'autism', 'autism in adolescence', 'autism in children', 
        'autism spectrum condition', 'autism spectrum disorder', 'autism spectrum disorder (asd)', 
        'autism spectrum disorders', 'autism spectrum disorders in children', 'autistic disorder', 
        'autoimmune diseases', 'autosomal dominant diseases', 'avc', 'axonal swelling', 'axonal swellings', 
        'backache', 'balance disorders', 'basal ganglia diseases', 'basal ganglia pathology', 
        'behavior disorders', 'behavioural neurology', 'benign tumors', 'bipolar disorder', 
        'blepharospasm', 'blindness', 'blood circulation disorders', 'body dysmorphic disorder', 
        'brachialgia', 'bradykinesia', 'brain abnormalities', 'brain concussion', 'brain damage', 
        'brain diseases', 'brain infarction', 'brain injuries', 'brain injury', 'brain lesion profiles', 
        'brain lesions', 'brain stem diseases', 'brain tumors', 'brown-sequard syndrome', 'bruxism', 
        'bulbar', 'burke–fahn–marsden movement and disability scale ( bfm )', 'cancer', 'cardiac arrest', 
        'cardiovascular diseases', 'catheterization', 'cellular pathology', 'central nervous system disturbances', 
        'central nervous system injuries', 'cerebellar agenesis', 'cerebellar ataxia', 'cerebellar ataxias', 
        'cerebellar damage', 'cerebellar degeneration', 'cerebellar disease', 'cerebellar dysfunction', 
        'cerebellar lesions', 'cerebellar pathology', 'cerebellar phenotype', 'cerebellar tumor', 
        'cerebellar tumors', 'cerebellum degeneration', 'cerebellum diseases', 'cerebral atrophy'
    ],
    'P. Rehabilitation & Therapy': [
        # Existing
        'rehabilitation', 'therapy', 'treatment', 'intervention', 'clinical', 'physical therapy', 
        'occupational therapy', 'cimt', 'music-supported', 'gait training', 'assistive', 
        'functional recovery', 'neurorehabilitation', 'prehab', 'neurodevelopmental treatment', 
        'physiotherapy', 'training', 'exercise', 'practice', 'regimen', 'protocol', 'telehealth', 
        'telerehab', 'remote', 'home-based', 'community-based', 'inpatient', 'outpatient',
        '(updrs) unified parkinson disease rating scale', 'abdominal surgery', 'accident prevention', 
        'accidental fall prevention', 'acl injury prevention', 'action observation therapy', 
        'action observation treatment', 'activities of daily living training', 'acupuncture anesthesia', 
        'acute exercise', 'advanced life support', 'aerobic', 'aerobic exercise', 'aerobic exercises', 
        'allied health education', 'alternative medicine', 'alternative pedagogy', 'anesthesia', 
        'anesthesiology', 'anesthetics', 'ankle injury', 'ankle weight', 'anterior cruciate ligament injury prevention', 
        'anterior cruciate ligament reconstruction', 'anterior cruciate ligament surgery', 'antineoplastic agents', 
        'apraxia treatment', 'aquatic exercises', 'arm exercises', 'arm surgery', 'art therapy', 
        'arthroplasty', 'arthroscopy', 'artificial limbs', 'assertiveness training', 'assist-as-needed', 
        'assistance', 'assisted training', 'assistive devices', 'assistive technology', 'at-home training',
        # New Additions
        'automated external defibrillator', 'back care', 'back exercises', 'backache prevention', 
        'balance rehabilitation', 'balance therapy', 'basic life support', 'basic life support ( bls )', 
        'basic life support (bls)', 'behavior modification', 'behavior modification for autistic children', 
        'behavior therapy', 'behavioral activation', 'behavioral recovery', 'bilateral assistance', 
        'bilateral movement therapy', 'bilateral movement training', 'bilateral training', 
        'bimanual therapy', 'bimanual training', 'body weight support', 'body weight supported treadmill training', 
        'body-weight supported treadmill training', 'body-weight-supported treadmill training', 
        'brain disease treatment', 'brain injury treatment', 'brain surgery', 'breathing exercises', 
        'bypass', 'bystander cpr', 'cancer chemotherapy', 'cardiopulmonary resuscitation', 
        'cardiopulmonary resuscitation ( cpr )', 'cardiopulmonary resuscitation (cpr)', 
        'cardiopulmonary resuscitation education', 'cardiovascular surgery', 'care of dementia patients', 
        'catheterization'
    ],
    'Q. Psychological Factors & Motivation': [
        # Existing
        'motivation', 'emotion', 'anxiety', 'self-efficacy', 'self-control', 'goal', 'stress', 
        'mindfulness', 'imagery', 'mental practice', 'mental-training', 'attitude', 'expectancy', 
        'psychology', 'social', 'confidence', 'affect', 'mood', 'personality', 'trait', 'state', 
        'resilience', 'coping', 'burnout', 'fatigue', 'arousal', 'reward', 'punishment', 'incentive', 
        'feedback', 'reinforcement',
        'academic motivation', 'acceptability', 'achievement goal theory', 'act psychology', 
        'active imagination', 'active self', 'adaptability (personality)', 'adaptability (personality) in children', 
        'adaptability to others', 'adaptation level (psychology)', 'addiction', 'adlerian psychology', 
        'adolescent psychology', 'aesthetics', 'affect', 'affect (psychology)', 'affect suppression', 
        'affective disorders', 'affective learning', 'affective neuroscience', 'agency', 'agitation (psychology)', 
        'ambiguity tolerance', 'animals', 'anxiety', 'anxiety prevention', 'anxiety-like behavior', 
        'apathy', 'applied cognitive psychology', 'applied psychology', 'approach behavior', 'approach/withdrawal motivation', 
        'approaching', 'archetype (psychology)', 'arcs model of motivational design', 'arousal', 
        'arousal state', 'art therapy', 'assertiveness training', 'association of ideas', 'athletic ability & psychology', 
        'attention (behavior)', 'attitude (psychology)', 'attitudes of medical personnel', 'attitudes toward aging', 
        'attraction', 'attribution (social psychology)',
        # New Additions
        'autonomy', 'autonomy (psychology)', 'autonomy support', 'avoidance', 'avoidance (psychology)', 
        'avoidance conditioning', 'behaviorism (psychology)', 'bird psychology', 'body image', 
        'brainwashing', 'camps', 'camps for children', 'career development', 'career education', 
        'caregivers'
    ],
    'R. Timing & Rhythm': [
        # Existing
        'timing', 'rhythm', 'temporal', 'synchronization', 'metronome', 'interval', 'period', 
        'tempo', 'beat', 'duration', 'speed', 'rate', 'frequency', 'latency', 'reaction time', 
        'response time', 'movement time', 'onset', 'offset', 'asynchrony', 'jitter', 'delay',
        'absolute timing', 'acceleration duration ( ad )', 'acoustic startle', 'acoustic startle reflex ( asr )', 
        'acoustic startle response', 'alternating serial reaction time task', 'anticipatory timing', 
        'arm frequency', 'asynchrony', 'auditory cue', 'auditory cueing', 'auditory cuing',
        # New Additions
        'auditory pacing', 'auditory rhythm', 'autocorrelation', 'beta rhythm', 'biological rhythms', 
        'cadence'
    ],
    'S. Research Methodology & Statistics': [
        # Existing
        'study', 'method', 'trial', 'experiment', 'analysis', 'anova', 'regression', 'statistic', 
        'measurement', 'assessment', 'test', 'scale', 'questionnaire', 'survey', 'reliability', 
        'validity', 'electrophysiology', 'quantitative', 'qualitative', 'bias', 'longitudinal', 
        'cross-sectional', 'head', 'cohort', 'sample', 'population', 'data', 'variable', 'correlation', 
        'causality', 'significance', 'p-value', 'confidence interval', 'effect size', 'power', 
        'meta-analysis', 'review', 'synthesis', 'design', 'protocol', 'procedure', 'task', 
        'paradigm', 'stimulus', 'response',
        '%sc percentage signal change', '(cv) coefficient of variation', '(eg) experimental group', 
        'accuracy index', 'acquisition of data', 'activity control task (act)', 'adaptive evaluation', 
        'aha assisting hand assessment', 'akaike information criterion', 'akaike\'s information criterion (aic)', 
        'ale meta-analysis', 'analyses of variance ( anova )', 'analysis of covariance', 'analysis of variance', 
        'analysis of variance ( anova )', 'analysis of variance (anova)', 'anovas analysis of variance', 
        'anthropological research', 'anthropometry', 'appraisers', 'arbitrary constants', 'assessment', 
        'assessment model', 'auc area under the curve',
        # New Additions
        'autoethnography', 'average error ( ae )', 'axioms', 'bayes factor', 'bayesian analysis', 
        'bayesian statistics', 'behavioral assessment', 'behavioral assessments', 'behavioral paradigm', 
        'behavioral research', 'behavioural testing', 'bender gestalt test', 'bender-gestalt test', 
        'bias', 'bibliographic databases', 'bioassays and physiological analysis', 'biological assay', 
        'biological classification', 'biological research', 'biological variation', 'biostatistics', 
        'blind experiment', 'blinding', 'block test', 'bs 95% ci bias-corrected bootstrapped 95% confidence intervals', 
        'case report', 'case series', 'case studies', 'case study', 'case-control method', 
        'causal inference'
    ],
    'T. Human & Animal Subjects': [
        # Existing
        'human', 'animal', 'subject', 'patient', 'child', 'infant', 'adult', 'elderly', 'older', 
        'adolescent', 'male', 'female', 'mice', 'rat', 'monkey', 'primate', 'songbird', 'athlete', 
        'gamer', 'novice', 'expert', 'td', 'typical', 'population', 'participant', 'volunteer', 
        'student', 'man', 'woman', 'boy', 'girl', 'mouse', 'rodent', 'cat', 'dog', 'fish', 'fly', 
        'worm', 'yeast', 'cell',
        '(pdp) patients with parkinson\'s disease', '10th postnatal day ( p10 )', '<italic>a. florea</italic>', 
        '<italic>a. mellifera</italic>', '<italic>b. terrestris</italic>', 'ability in children', 
        'able-bodied', 'adaptability (personality) in children', 'adolescence', 'adolescent', 
        'adolescents', 'adult', 'adult students', 'adults', 'african american children', 'age groups', 
        'aged', 'aging', 'aging.', 'alzheimer\'s patients', 'amateur athletes', 'americans', 
        'amniotes', 'amputees', 'animal behavior', 'animal cells', 'animal cognition', 'animal courtship', 
        'animal disease models', 'animal genetics', 'animal intelligence', 'animal model', 'animal models', 
        'animal models in epilepsy research', 'animal models in research', 'animal models of inflammation', 
        'animal sexual behavior', 'animal sociality', 'animals', 'aphasic persons', 'archaeological human remains', 
        'articulation disorders in children', 'asians', 'asperger\'s syndrome in children', 'athlete', 
        'athletes', 'athletes with disabilities',
        # New Additions
        'amateur athletes', 'animal cells', 'auditory perception in children', 'australian football players', 
        'autism in adolescence', 'autism in children', 'autism spectrum disorders in children', 
        'autistic children', 'autistic people', 'avian', 'badminton players', 'ballet dancers', 
        'barn owl', 'baseball players', 'basketball players', 'bats', 'behavioral assessment of infants', 
        'beginner', 'bengalese finch', 'bird', 'birds', 'black people', 'boys', 'brachydanio', 
        'brain damaged patients', 'c control subjects', 'c57bl/6 mice', 'cancer patients', 
        'cardiac patients', 'cat', 'cats', 'cats as laboratory animals', 'cell types', 'cells', 
        'cerebellar patients', 'cerebellar patients (cbl)', 'cercopithecidae'
    ],
    'U. Vision & Oculomotor Control': [
        # Existing
        'saccade', 'eye movement', 'gaze', 'ocular', 'oculomotor', 'vor', 'visual tracking', 
        'visual field', 'vision', 'visual', 'pursuit', 'vergence', 'nystagmus', 'pupil', 'retina', 
        'fovea', 'optic', 'blink', 'fixation', 'microsaccade', 'optokinetic',
        '2-(5-chloro)tricyclo [3.3.1.13, 2-dioxetane-3, 7]decan}-4-Yl)phenyl phosphate ( cspd )', 
        '3d shape perception', '6-diamidino-2-phenylindole', 'action perception', 'action perception coupling', 
        'active sensing', 'all-trans retinoic acid', 'amaurosis fugax', 'anterior ectosylvian visual area ( aev )', 
        'anticipatory smooth eye movements', 'area v5/mt', 'audio-visual', 'audio-visual interaction', 
        'audiovisual', 'audiovisual congruency', 'audiovisual integration', 'audio–visual', 'audio–visual interaction',
        # New Additions
        'binocular disparity', 'binocular vision', 'blepharospasm', 'blindness', 'blindsight', 
        'blindsight (visual perception)', 'blink inefficiency', 'blink reflex', 'blinking (physiology)', 
        'blinks', 'blur adaptation'
    ],
    'V. Speech & Language': [
        # Existing
        'speech', 'language', 'vocal', 'stutter', 'phonetics', 'pronunciation', 'grammar', 
        'tongue', 'articulation', 'singing', 'apraxia of speech', 'dysarthria', 'communication', 
        'voice', 'larynx', 'pharynx', 'oral', 'verbal', 'linguistic', 'phonology', 'syntax', 
        'semantic', 'pragmatic', 'reading', 'writing', 'sign language',
        'aac system design', 'action-related language', 'age factors in language acquisition', 
        'alphabet', 'american english language', 'analogical reasoning', 'anomia', 'aphasia', 
        'aphasic persons', 'apraxia', 'apraxia of speech', 'articulating', 'articulation', 
        'articulation (speech)', 'articulation disorders', 'articulation disorders in children', 
        'articulatory gestures', 'artificial languages', 'asymmetry (linguistics)', 'audiovisual aids in education', 
        'audiovisual education', 'audiovisual materials', 'audiovisual presentations',
        # New Additions
        'automatic speech recognition', 'bengali songs', 'bilingualism', 'bird song', 'bird vocalizations', 
        'birdsong', 'birdsongs', 'bird’s own song (bos)', 'body language', 'body language reading', 
        'brain communication'
    ],
    'W. Development & Lifespan': [
        # Existing
        'development', 'aging', 'infancy', 'childhood', 'adolescence', 'postnatal', 'critical period', 
        'life-span', 'developmental coordination disorder', 'dcd', 'maturation', 'onset', 
        'developmental', 'growth', 'age', 'young', 'old', 'senior', 'pediatric', 'geriatric', 
        'birth', 'death', 'epigenetic', 'prenatal', 'neonatal',
        '10th postnatal day ( p10 )', 'accidental falls in old age', 'adolescence', 'adolescent', 
        'adolescent health', 'adolescent psychology', 'adolescents', 'adult', 'adult education', 
        'adult learning', 'age', 'age & intelligence', 'age differences', 'age discrimination', 
        'age distribution', 'age factors in cognition', 'age factors in cognition disorders', 'age factors in disease', 
        'age factors in health behavior', 'age factors in language acquisition', 'age factors in memory', 
        'age factors in sleep', 'age groups', 'age of acquisition', 'age of onset', 'age-dependence', 
        'aged', 'ageing', 'aging', 'aging.', 'alcohol-related neurodevelopmental disorders (arnd)', 
        'anxiety in old age', 'attitudes toward aging',
        # New Additions
        'autism in adolescence', 'autism in children', 'autism spectrum disorders in children', 
        'autistic children', 'birth weight', 'brain aging', 'brain development', 'cell death', 
        'cell differentiation', 'cerebellar development', 'cerebellum development'
    ],
    'X. Imaging & Assessment Techniques': [
        # Existing
        'fmri', 'mri', 'eeg', 'meg', 'pet', 'dti', 'fnirs', 'electromyography', 'emg', 
        'biomechanics', 'posturography', 'kinematics', 'kinetics', 'assessment', 'test', 'scale', 
        'survey', 'imaging', 'spectroscopy', 'microscopy', 'analysis', 'tomography', 'ultrasound', 
        'x-ray', 'ct scan', 'scan', 'recording', 'monitoring', 'measurement', 'evaluation', 
        'screening', 'diagnostic',
        '%sc percentage signal change', '(ehi) edinburgh handedness inventory', '(updrs) unified parkinson disease rating scale', 
        '11c-raclopride', '2d:4d', '3d grase', '3d reconstruction', '3d-mri', '3t 3 tesla', 
        '9-hole box', '[11c]-raclopride ( rac )', '[11c]raclopride', '[18f]-fluorodeoxyglucose ( fdg )', 
        'abdominal examination', 'ability testing', 'academic achievement evaluation', 'accuracy task', 
        'actigraphy', 'activity recognition', 'adaptive evaluation', 'aha assisting hand assessment', 
        'ambulatory electrocardiography', 'amplitude estimation', 'analysis of variance', 'angiogenesis', 
        'animal experimentation', 'anthropometry', 'arterial spin labeling', 'arterial spin-labeling', 
        'assessment', 'assessment model', 'athletic ability testing', 'attention networks test', 
        'attention testing', 'audiometric equipment', 'audiometry',
        # New Additions
        'auditory perception testing', 'automated data collection systems', 'autoradiography', 
        'axial diffusivity ( λ || )', 'barthel index', 'beck hopelessness scale', 
        'behavioral assessment', 'behavioral assessment of infants', 'behavioral assessments', 
        'bess test', 'biodex balance system', 'biofeedback system', 'biomedical measurements', 
        'biopotentials (electrophysiology)', 'blood alcohol concentration ( bac )', 'blood testing', 
        'body mass index', 'bone health', 'brain imaging', 'brain magnetic resonance imaging', 
        'brain map', 'brain mapping', 'brain metabolic mapping', 'brain monitoring', 'brain morphometry', 
        'brain slice', 'brain tomography', 'brain volume', 'brain volumetry', 
        'bruininks–oseretsky test of motor proficiency-two (bot-2)', 'burke–fahn–marsden movement and disability scale ( bfm )', 
        'calcium imaging', 'cardiopulmonary fitness', 'cardiorespiratory fitness', 'cell preservation'
    ],
    'Z. Unclassified': [
        # Existing
        '( R )-(+)-[2,3-dihydro-5-methyl-3-(4-morpholinylmethyl)pyrrolo[1,2,3-de]-1,4-benzoxazin-6-yl]-1-naphthalenylmethanone mesylate',
        '2 S', '2', '212-2 mesylate', '2300', '2320', '2323', '2326', '2330', '2340', '2343', 
        '3-dicarboxylic acid1s', '3-dicarboxylic acidt-acpd', '3-dicarboxylic acid±-trans-acpd', 
        '3-dione', '3-dionecnqx', '3380', '3700', '3720', '3r)-1-aminocyclopentane-1', '4c3hpg', 
        '5-dihydroxyphenilglycine', '7-nina', 'aida', 'ap-v (ap-5)', 'bapta', 
        'bis(2-aminophenoxy)ethane-n', 'chpg', 'cpccoet', 'dag', 'dcg-iv', 
        'dl-amino-5-phosphonopentanoic acid', 'dl-amino-5-phosphonopentanoic acidap-v ap-5', 
        'dnqx 6', 'dopamineda', 'egta', 'entopeduncular nucleusepn', 'epsp', 
        'ethylene glycol bisβ-aminoethyl ether-n', 'excitatory post-synaptic potentialepsp', 
        'g-protein coupled receptorgprc', 'gprc', 'hd', 'hfs', 'i-ltp', 'inositol-3-phosphateip3', 
        'ip3', 'l-2-amino-3-phosphonopropionatel-ap3', 'l-ap3', 'l-ccg-i', 'l-name', 
        'l-serine-o-phosphatel-sop', 'l-sop', 'ltd', 'mcp g', 'mglur', 'mglur1 knock-outmglur1-/-', 
        'mglur1-/-', 'mglur5 knock-outmglur5-/-', 'mglur5-/-', 'mma', 'mpep', 'msop', 'n', 'n′', 
        'o bis(2-aminoethyl)ethyleneglycol-n', 'nac', 'ng-nitro-l-arginine methylesterl-name', 
        'nmda', 'nos', 'nacl', 'protein phosphatase 1pp-1', 'rs-1-aminoindan-1', 
        'rs-2-chloro-5-hydroxyphenylglycinechpg', 's-α-methylserine-o-phosphatemsop', 
        's-4-carboxy-3-hydroxyphenylglycine4c3hpg', 's-4-carboxyphenylglycine4-cpg', 'snap', 
        'sd', 'snc/r', 'stn', 't-acpd', 'tea', 'tetrodotoxinttx', 'tpa', 'ttx', 'vdcc', 
        '±-trans-1-aminocyclopentane-1', 'vdp', 'lavenders', 'flower petals', 'sunflower seeds', 
        'chf swiss francs', 'cardinal numbers', 'autographs', 'plastics', 'startup costs', 
        'wages', 'likes & dislikes', 'non-fungible tokens', 'airplanes', 'helicopters', 'railroads', 
        'ships', 'submarines', 'trucks', 'vans', 'automobiles', 'bicycles', 'tricycles', 
        'skateboards', 'roller skates', 'ice skates', 'skis', 'snowboards', 'sleds', 'phronesis', 
        'monoculars', 'spurious limits', 'likes & dislikes', '2 s', '1s',
        '1889-1976', '1929-2017', '1940-1973', '1956-', '1981-', '1s', '2', '2 s', '212-2 mesylate', 
        '2300', '2320', '2323', '2326', '2330', '2340', '2343', '2′r', '2′s', '3', '3-dicarboxylic acid1s', 
        '3380', '3700', '3720', '6', '<italic>a. florea</italic>', '<italic>a. mellifera</italic>', 
        '<italic>b. terrestris</italic>', 'academic medical centers', 'academic medicine', 'academic support programs', 
        'acceptability', 'access to information', 'acclimatization', 'accreditation', 'acculturation', 
        'acheulean', 'acheulian culture', 'additives', 'aeronautical flights', 'aeronautics', 
        'agriculture', 'agrochemicals', 'air cylinders', 'air guns', 'airplane ditching', 'airplanes', 
        'albus', 'alcohol', 'alcohol drinking', 'american heart association ( aha )', 'american journal of psychology (periodical)', 
        'americans', 'anatomical planes', 'anatomical variation', 'anatomy', 'anatomy and physiology', 
        'anatomy education', 'animation (cinematography)', 'animations', 'arizona', 'arms transfers', 
        'art therapy', 'artificial objects', 'artificial satellite training', 'asians', 'assimilated', 
        'association for computing machinery', 'astral projection', 'athletic clubs', 'athletic equipment', 
        'athletic fields', 'athletic trainers', 'audiences', 'audiovisual presentations',
        # New Additions
        'augmentation', 'augmentative and alternative communication', 'australia', 'authors', 
        'authorship in literature', 'auto-generated augmented feedback', 'autographs', 'autoimmune diseases', 
        'automated teller machines', 'automobile bodies', 'automobile engines', 'automobile speed', 
        'automobile steering gear', 'automobile tires', 'automobiles', 'aviation', 'baccalaureate nursing education', 
        'balance of payments', 'bancom', 'bark', 'bars', 'beer', 'belgium', 'benchmarking (management)', 
        'benefit performances', 'benner', 'bernstein', 'bibliography', 'bicycle equipment', 'bicycles', 
        'bifaces (stone implements)', 'bifactor', 'big data', 'bi-stability', 'blackberry ltd.', 
        'body size', 'body temperature regulation', 'body weight', 'botswana', 'box', 'box trainer', 
        'bruce', 'brunswik', 'building repair', 'built environment', 'business', 'california', 
        'calibration', 'canada', 'candela ( cd )', 'capacity (law)', 'cardinal numbers', 
        'cardiovascular disease related mortality', 'carson (calif.)', 'cartesian coordinates', 
        'cartesian plane', 'cart–pole task', 'cauchy sequences', 'cave paintings', 'cell filling', 
        'cell phone', 'cell phones', 'cell population', 'cell populations', 'cell transformation', 
        'cell transmission model (traffic engineering)', 'cellbio', 'centimeter ( cm )'
    ]
}
# def find_categories_for_keyword(keyword):
#     for category, terms in CATEGORIES.items():
#         if keyword in category:

# Function for multi-label classification
def classify_keyword_multi_label(keyword):
    unknown_words = set([])
    kw_lower = keyword.lower()
    matched_categories = []

    # Check for unclassified first (exact match only for highly specific, fragmented terms)
    # The 'Z. Unclassified' list contains items the user explicitly mentioned or are fragments.
    if kw_lower in [unclassified_term.lower() for unclassified_term in CATEGORIES['Z. Unclassified']]:
        return ['Z. Unclassified']

    # Iterate through all categories and assign ALL matches (multi-label)
    for category, terms in CATEGORIES.items():
        if category == 'Z. Unclassified':
            continue  # Skip checking general keywords against the unclassified list
        # if kw_lower in [term.lower() for term in terms]:
        #     matched_categories.append(category)
        if any(term.lower() in kw_lower for term in terms):
            matched_categories.append(category)
    
    # If no matches found in any category, assign to unclassified (catch-all for new ambiguous terms)
    if not matched_categories:
        # print(f"couldn't find match for {kw_lower}")
        with open("unknown_words.txt", 'a') as f:
            f.write(keyword)
            f.write('\n')
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