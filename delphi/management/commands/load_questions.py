"""
Delphi Consensus Study - Question Loader
=========================================
DELPHI CONSENSUS RECOMMENDATIONS ON STANDARDIZING POST-ERCP PANCREATITIS 
DEFINITIONS, RESEARCH PRIORITIES - QUESTIONS ROUND 1

This script loads all Round 1 questions exactly as specified in the 
source document (delphi questions.docx).

Principal Investigator: Dr. Venkata S Akshintala
Institution: Johns Hopkins University
"""

import json
from django.core.management.base import BaseCommand
from delphi.models import Study, Round, Item, RoundItem


class Command(BaseCommand):
    help = 'Load all Delphi Round 1 questions for PEP Consensus Study'

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('Starting question import...'))
        
        # Create the Study
        study, created = Study.objects.get_or_create(
            name="DELPHI CONSENSUS RECOMMENDATIONS ON STANDARDIZING POST-ERCP PANCREATITIS DEFINITIONS, RESEARCH PRIORITIES",
            defaults={
                'description': """STUDY AIM:
By harnessing the collective judgment of experts in the field, this study aims to standardize future research and clinical practices related to PEP.

CONSENSUS:
Statements were accepted as having reached consensus if after second-round voting ≥75% of experts disagreed ('definitely disagree' or 'disagree'), or agreed ('definitely agree' or 'agree')"""
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS(f'Created Study: {study.name}'))
        else:
            self.stdout.write(self.style.WARNING(f'Study already exists: {study.name}'))
        
        # Create Round 1
        round1, created = Round.objects.get_or_create(
            study=study,
            number=1,
            defaults={
                'is_open': False,
                'show_feedback_immediately': False
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS('Created Round 1'))
        else:
            self.stdout.write(self.style.WARNING('Round 1 already exists'))
        
        # Define all questions exactly as in the Word document
        questions = self.get_all_questions()
        
        # Create Items and RoundItems
        order = 1
        for q in questions:
            item = Item.objects.create(
                study=study,
                prompt=q['prompt'],
                item_type=q['item_type'],
                option_a=q.get('option_a', ''),
                option_b=q.get('option_b', ''),
                option_c=q.get('option_c', ''),
                option_d=q.get('option_d', ''),
                option_e=q.get('option_e', ''),
                option_f=q.get('option_f', ''),
                matrix_rows=q.get('matrix_rows', ''),
                matrix_columns=q.get('matrix_columns', ''),
            )
            
            self.stdout.write(f'  Created Item {order}: {q["prompt"][:60]}...')
            
            # Link to Round
            RoundItem.objects.create(
                round=round1,
                item=item,
                order=order
            )
            
            order += 1
        
        self.stdout.write(self.style.SUCCESS(f'\nSuccessfully loaded {order-1} questions into Round 1'))
        self.stdout.write(self.style.SUCCESS('Done!'))

    def get_all_questions(self):
        """
        Returns all questions exactly as specified in delphi questions.docx
        """
        
        questions = []
        
        # ================================================================
        # TOPIC: DEFINITION AND DIAGNOSIS POST ERCP PANCREATITIS
        # ================================================================
        
        # Question 1: Post-ERCP pancreatitis definition (MCQ)
        questions.append({
            'prompt': 'Post-ERCP pancreatitis is best defined according to:',
            'item_type': 'multiple',
            'option_a': 'Cotton/Consensus criteria (definition: Abdominal pain suggestive of pancreatitis requiring new hospitalization or extension of hospital stay for 2–3 days and a serum amylase at least three times the upper limit of normal, 24 hours after the procedure)',
            'option_b': 'Atlanta criteria (definition: (1) abdominal pain consistent with acute pancreatitis (acute onset of a persistent, severe, epigastric pain often radiating to the back); (2) serum lipase activity (or amylase activity) at least three times greater than the upper limit of normal; and (3) characteristic findings of acute pancreatitis on contrast-enhanced computed tomography (CECT) and less commonly magnetic resonance imaging (MRI) or transabdominal ultrasonography)',
            'option_c': 'I don\'t know',
            'option_d': 'Other (Free text option to be included)',
        })
        
        # Question 2: Biochemical markers (Checkbox)
        questions.append({
            'prompt': 'What biochemical and surrogate markers of post-ERCP pancreatitis should be monitored:',
            'item_type': 'checkbox',
            'option_a': 'Amylase',
            'option_b': 'Lipase',
            'option_c': 'CRP',
            'option_d': 'I don\'t know',
            'option_e': 'Other (Free text option to be included)',
            'option_f': 'None',
        })
        
        # ================================================================
        # TOPIC: PEP RISK FACTORS
        # ================================================================
        
        # Question 3: Risk stratification description (Likert)
        questions.append({
            'prompt': 'A detailed description of the population and their risk stratification of PEP should be included',
            'item_type': 'likert5',
        })
        
        # Question 4: Patient-related risk factors (Matrix)
        patient_risk_factors = [
            'Female sex (alone)',
            'Age <50 years (alone)',
            'Age <30 years (alone)',
            'Female sex AND age <50 years (as a combined criterion)',
            'Female sex AND age <60 years (as a combined criterion)',
            'Body mass index >30 kg/m²',
            'History of post-ERCP pancreatitis (single episode)',
            'History of post-ERCP pancreatitis (≥2 episodes)',
            'History of recurrent acute pancreatitis (≥2 episodes, any etiology)',
            'History of acute pancreatitis (single episode, any etiology)',
            'Clinical suspicion of sphincter of Oddi dysfunction',
            'Confirmed sphincter of Oddi dysfunction — Type I',
            'Confirmed sphincter of Oddi dysfunction — Type II',
            'Normal serum bilirubin (≤1 mg/dL)',
            'Normal common bile duct diameter (<9 mm)',
            'Non-dilated pancreatic duct',
            'Native papilla (no prior biliary sphincterotomy)',
            'Periampullary diverticulum',
            'Absence of chronic pancreatitis',
            'Cirrhosis / chronic liver disease',
            'End-stage renal disease / dialysis dependence',
        ]
        
        matrix_columns = ['Yes', 'No', 'Major', 'Minor', 'Not a Risk Factor', 'I don\'t know']
        
        questions.append({
            'prompt': 'Which of the following patient-related factors should be considered risk factors for post-ERCP pancreatitis, and how should each be classified?',
            'item_type': 'matrix',
            'matrix_rows': json.dumps(patient_risk_factors),
            'matrix_columns': json.dumps(matrix_columns),
        })
        
        # Question 5: Other patient-related risk factors (Free text)
        questions.append({
            'prompt': 'Other patient-related risk factor(s) not listed above (please specify):',
            'item_type': 'text',
        })
        
        # Question 6: Difficult cannulation definition (MCQ)
        questions.append({
            'prompt': 'Difficult cannulation is best defined as',
            'item_type': 'multiple',
            'option_a': '> 5 cannulation attempts',
            'option_b': '>8 Cannulation attempts',
            'option_c': '>10 Cannulation attempts',
            'option_d': '>10 Minutes of attempts',
            'option_e': 'I don\'t know',
        })
        
        # Question 7: Procedure-related risk factors (Matrix)
        procedure_risk_factors = [
            'Difficult cannulation (as defined by institutional/endoscopist judgment)',
            'Failed cannulation',
            'Pancreatic sphincterotomy',
            'Biliary sphincterotomy',
            'Pre-cut (access) sphincterotomy / needle-knife fistulotomy',
            'Transpancreatic sphincterotomy',
            'Endoscopic papillary balloon dilation of intact biliary sphincter (short duration, ≤1 minute)',
            'Endoscopic papillary balloon dilation of intact biliary sphincter (prolonged duration, >1 minute)',
            'Endoscopic papillary large balloon dilation (after prior sphincterotomy)',
            'Pancreatic duct contrast injection (single injection)',
            'Pancreatic duct contrast injection (2 injections)',
            'Pancreatic duct contrast injection (≥3 injections)',
            'Pancreatic duct contrast injection extending to the tail',
            'At least 3 pancreatic duct injections, with at least 1 injection to the tail',
            'Opacification of pancreatic acini (pancreatic acinarization)',
            'Pancreatic guidewire passage (single passage)',
            'Pancreatic guidewire passage (≥2 passages)',
            'Pancreatic duct instrumentation (brush cytology, biopsy)',
            'More than five accidental pancreatograms',
            'Ampullectomy',
            'Biliary stent placement without prior sphincterotomy',
            'Trainee involvement in cannulation / procedure',
            'Prolonged procedure duration (>30 minutes)',
            'Prolonged procedure duration (>60 minutes)',
            'Therapeutic (vs. diagnostic) ERCP',
            'Cholangioscopy',
            'Pancreatoscopy',
        ]
        
        questions.append({
            'prompt': 'Which of the following procedure-related factors should be considered risk factors for post-ERCP pancreatitis, and how should each be classified?',
            'item_type': 'matrix',
            'matrix_rows': json.dumps(procedure_risk_factors),
            'matrix_columns': json.dumps(matrix_columns),
        })
        
        # Question 8: Other procedure-related risk factors (Free text)
        questions.append({
            'prompt': 'Other patient-related risk factor(s) not listed above (please specify):',
            'item_type': 'text',
        })
        
        # Question 9: Pancreatic Cancer as risk factor (MCQ)
        questions.append({
            'prompt': 'Should Pancreatic Cancer be considered a risk factor in PEP',
            'item_type': 'multiple',
            'option_a': 'Yes',
            'option_b': 'No',
            'option_c': 'I don\'t know',
            'option_d': 'Other (Free text option to be included)',
        })
        
        # Question 10: High risk definition (MCQ)
        questions.append({
            'prompt': 'In PEP High risk should be defined as',
            'item_type': 'multiple',
            'option_a': 'Presence of one definite risk factor or two likely risk factors',
            'option_b': 'Suspected sphincter of Oddi dysfunction / Age 18–50 years / Female / Normal common bile duct [CBD] diameter [<9 mm] / Normal serum bilirubin / Body mass index >30 kg/m2 / Previous acute pancreatitis',
            'option_c': 'Pre-cut sphincterotomy / Endoscopic pancreatic sphincterotomy / Endoscopic papillary balloon dilation of the intact biliary sphincter / Difficult cannulation (more than 10 minutes elapsed for the successful selective cannulation, or in failed cannulation / Injection of contrast agent into the pancreatic duct / Female patient and age <60 years / Clinical suspicion of sphincter of Oddi dysfunction / History of recurrent pancreatitis / History of PEP.',
            'option_d': 'Presence of one major criteria (History of PEP / Pancreatic sphincterotomy / Precut sphincterotomy / Difficult cannulation (>5 attempts/10 min to cannulate) / Failed cannulation / Pneumatic dilation of an intact sphincter / Sphincter of Oddi dysfunction of type I or type II) OR ≥2 minor inclusion criteria (Age <50 and female gender / History of acute pancreatitis (at least 2 episodes) / >2 pancreatic injections (with at least 1 injection in tail) / Pancreatic acinarization / Pancreatic brush cytology)',
            'option_e': '<50 years of age and female sex / History of recurrent pancreatitis / clinical suspicion of sphincter of Oddi dysfunction (SOD) / Normal bilirubin (≤1 mg/dL) / Pancreatic sphincterotomy / Pancreatic duct injection; instrumentation of the pancreatic duct (e.g., brush cytology) / Precut sphincterotomy / Pneumatic dilation of an intact biliary sphincter / Ampullectomy / Difficult cannulation (duration of cannulation attempts >5 minutes, more than five attempts, or more than two pancreatic guidewire passages)',
            'option_f': 'Presence of one major criteria (Clinical suspicion of sphincter of Oddi dysfunction / History of PEP / Pancreatic sphincterotomy / Precut sphincterotomy / ≥8 cannulation attempts / Pneumatic dilatation of an intact biliary sphincter / ampullectomy) OR ≥2 minor inclusion criteria (Women younger than 50 years / History of recurrent pancreatitis (≥2 times) / ≥3 injections of contrast into the pancreatic duct with ≥1 injection to the tail of the pancreas / Opacification of pancreatic acini / Brush cytology performed on the pancreatic duct)',
        })
        
        # Question 11: High risk definition continued (MCQ)
        questions.append({
            'prompt': 'In PEP High risk should be defined as (continued)',
            'item_type': 'multiple',
            'option_a': 'Suspected sphincter of Oddi dysfunction / History of prior post-ERCP pancreatitis / Pancreatic sphincterotomy / Balloon dilatation of the biliary sphincter / Normal bilirubin (<1 mg/dL) / Pancreatic duct injection / Precut sphincterotomy / Young age (<30 y)',
            'option_b': 'More than five accidental pancreatograms / Needle knife precutting',
            'option_c': 'Presence of one major criteria (Clinical suspicion of sphincter of Oddi dysfunction / History of post-ERCP pancreatitis / Pancreatic sphincterotomy / Precut sphincterotomy / More than eight cannulation attempts (as determined by the endoscopist) / Pneumatic dilatation of an intact biliary sphincter / Ampullectomy) OR ≥2 minor inclusion criteria (Age of less than 50 years and female sex / History of recurrent pancreatitis (≥2 episodes) / Three or more injections of contrast agent into the pancreatic duct with at least one injection to the tail of the pancreas / Excessive injection of contrast agent into the pancreatic duct resulting in opacification of pancreatic acini / Acquisition of a cytologic specimen from the pancreatic duct with the use of a brush)',
            'option_d': 'I don\'t know',
            'option_e': 'Other (Free text option to be included)',
        })
        
        # Question 12: Low risk definition (MCQ)
        questions.append({
            'prompt': 'In PEP Low risk should be defined as',
            'item_type': 'multiple',
            'option_a': 'Chronic calcific pancreatitis',
            'option_b': 'Previously undergone ERCP with sphincterotomy',
            'option_c': 'Chronic calcific pancreatitis / Pancreatic-head mass / Undergoing routine biliary-stent exchange',
            'option_d': 'Chronic calcific pancreatitis / Pancreatic-head mass / Undergoing routine biliary-stent exchange/ Previously undergone ERCP with sphincterotomy',
            'option_e': 'I don\'t know',
            'option_f': 'Other (Free text option to be included)',
        })
        
        # Question 13: Average risk definition (MCQ)
        questions.append({
            'prompt': 'In PEP Average risk should be defined as',
            'item_type': 'multiple',
            'option_a': 'Patient meets neither High-risk nor Low-risk criteria',
            'option_b': 'Average-risk is not a useful category',
            'option_c': 'I don\'t know',
            'option_d': 'Other (Free text option to be included)',
        })
        
        # Question 14: Risk stratification in trials (MCQ)
        questions.append({
            'prompt': 'Risk stratification of PEP in trials should be defined as',
            'item_type': 'multiple',
            'option_a': 'High vs average vs low',
            'option_b': 'High + average vs low',
            'option_c': 'No stratification',
            'option_d': 'I don\'t know',
            'option_e': 'Other (free text option to be included)',
        })
        
        # ================================================================
        # TOPIC: RCT DESIGN
        # ================================================================
        
        # Question 15: RCT rationale/design (MCQ)
        questions.append({
            'prompt': 'The rationale / design of a RCT for prevention of PEP should be',
            'item_type': 'multiple',
            'option_a': 'Pragmatic',
            'option_b': 'Explanatory',
            'option_c': 'I don\'t know',
            'option_d': 'Others',
        })
        
        # Question 16: Placebo use (MCQ)
        questions.append({
            'prompt': 'Is it acceptable to use placebo in PEP trials including in all comers',
            'item_type': 'multiple',
            'option_a': 'Yes',
            'option_b': 'No',
            'option_c': 'I don\'t know',
            'option_d': 'Others',
        })
        
        # Question 17: Patient inclusion (MCQ)
        questions.append({
            'prompt': 'Should RCTs include patients who are',
            'item_type': 'multiple',
            'option_a': 'High risk',
            'option_b': 'Average risk',
            'option_c': 'All comers',
        })
        
        # Question 18: Exclusion criteria (MCQ)
        questions.append({
            'prompt': 'Should future PEP trials exclude the use of',
            'item_type': 'multiple',
            'option_a': 'IV Fluids',
            'option_b': 'Rectal NSAIDs',
            'option_c': 'PD stent',
            'option_d': 'Do not exclude any',
            'option_e': 'I don\'t know',
            'option_f': 'Other',
        })
        
        # Question 19: RRR for new agent vs placebo (MCQ)
        questions.append({
            'prompt': 'What should be considered as the maximum relative risk reduction (RRR) for power calculations when comparing a new agent to placebo',
            'item_type': 'multiple',
            'option_a': '1%-20%',
            'option_b': '21%-40%',
            'option_c': '41%-60%',
            'option_d': '61%-80%',
            'option_e': '81%-100%',
            'option_f': 'I don\'t know',
        })
        
        # Question 20: RRR for SOC vs SOC + new agent (MCQ)
        questions.append({
            'prompt': 'What should be considered as the maximum relative risk reduction for power calculations when comparing standard of care to standard of care plus a new agent',
            'item_type': 'multiple',
            'option_a': '1%-20%',
            'option_b': '21%-40%',
            'option_c': '41%-60%',
            'option_d': '61%-80%',
            'option_e': '81%-100%',
            'option_f': 'I don\'t know',
        })
        
        # Question 21: Ideal RRR - new agent vs placebo (Free text)
        questions.append({
            'prompt': 'Ideal maximal relative risk reduction for power calculations when comparing a new agent to placebo.',
            'item_type': 'text',
        })
        
        # Question 22: Ideal RRR - SOC vs SOC + new agent (Free text)
        questions.append({
            'prompt': 'Ideal maximal relative risk reduction for power calculations when comparing standard of care to standard of care plus a new agent',
            'item_type': 'text',
        })
        
        # Question 23: Blinding (MCQ)
        questions.append({
            'prompt': 'Blinding in RCTs PEP prophylaxis is:',
            'item_type': 'multiple',
            'option_a': 'Necessary: preferred double blinding (patients, ERCPist) or single blinding (patients) when prophylaxis is an ERCP-related intervention (PD stent placement).',
            'option_b': 'Preferred like answer option 1. But only implemented when feasible in daily practice (example. Blinding in pragmatic hydration studies is not feasible)',
            'option_c': 'Not necessary or preferred',
            'option_d': 'I don\'t know',
            'option_e': 'Others',
        })
        
        # Question 24: Statisticians (MCQ)
        questions.append({
            'prompt': 'Statisticians involved in RCTs for PEP prophylaxis trials should be',
            'item_type': 'multiple',
            'option_a': 'Independent',
            'option_b': 'Blinded',
            'option_c': 'None of the above',
            'option_d': 'I don\'t know',
            'option_e': 'Other',
        })
        
        # ================================================================
        # TOPIC: ENDOSCOPIST AND LOCATION
        # ================================================================
        
        # Question 25: Expertise importance (Likert)
        questions.append({
            'prompt': 'Defining the expertise of the participating ERCPists/endoscopists is important:',
            'item_type': 'likert5',
        })
        
        # Question 26 (19 in doc): Expert endoscopist definition (MCQ)
        questions.append({
            'prompt': '19. An expert endoscopist can be defined as:',
            'item_type': 'multiple',
            'option_a': 'An ERCP lifetime exposure of more than 200 procedures and / or a current number of more than 40 procedures per year.',
            'option_b': 'An ERCP lifetime exposure of more than 400 procedures and current number of more than 50 procedures per year for the past three years (FLUYT).',
            'option_c': 'An ERCP lifetime exposure of more than 156 procedures.',
            'option_d': 'I don\'t know',
            'option_e': 'Other',
        })
        
        # Question 27 (20 in doc): High volume center (MCQ)
        questions.append({
            'prompt': '20. A high volume center can be defined as:',
            'item_type': 'multiple',
            'option_a': '>150 procedures performed per year',
            'option_b': '>200 procedures performed per year',
            'option_c': '>300 procedures performed per year',
            'option_d': '>400 procedures performed per year',
            'option_e': 'I don\'t know',
            'option_f': 'Other',
        })
        
        # Question 28 (21 in doc): RCT location (MCQ)
        questions.append({
            'prompt': '21. RCTs to post-ERCP pancreatitis prophylaxis should be performed in:',
            'item_type': 'multiple',
            'option_a': 'Academic hospitals',
            'option_b': 'Teaching hospitals',
            'option_c': 'Private',
            'option_d': 'All above combined',
            'option_e': 'Academic AND teaching hospitals',
            'option_f': 'I don\'t know',
        })
        
        # ================================================================
        # TOPIC: DATA HANDLING AND DATA INTERPRETATION
        # ================================================================
        
        # Question 29 (23 in doc): Interim analysis (Likert)
        questions.append({
            'prompt': '23. An interim analysis should be performed and stopping rules should be included',
            'item_type': 'likert5',
        })
        
        # Question 30 (24 in doc): Adverse events predefined (Likert)
        questions.append({
            'prompt': '24. Potential adverse events should be predefined in the trial protocol',
            'item_type': 'likert5',
        })
        
        # Question 31 (25 in doc): SAE reporting (Likert)
        questions.append({
            'prompt': '25. (serious) adverse events should be reported in the main manuscript or supplementary appendix',
            'item_type': 'likert5',
        })
        
        # Question 32 (26 in doc): Database audit trail (Likert)
        questions.append({
            'prompt': '26. A RCT to post-ERCP pancreatitis prophylaxis should have a database with audit trail',
            'item_type': 'likert5',
        })
        
        # Question 33 (27 in doc): Adjudication committee (Likert)
        questions.append({
            'prompt': '27. A RCT to post-ERCP pancreatitis prophylaxis should have a adjudication committee',
            'item_type': 'likert5',
        })
        
        # Question 34 (28 in doc): DSMB (Likert)
        questions.append({
            'prompt': '28. A RCT to post-ERCP pancreatitis prophylaxis should have a Data Safety Monitoring Committee/Board (DSMC or DSMB)',
            'item_type': 'likert5',
        })
        
        # Question 35 (29 in doc): Protocol violations predefined (Likert)
        questions.append({
            'prompt': '29. Protocol violations should be predefined',
            'item_type': 'likert5',
        })
        
        # Question 36 (30 in doc): Sample size correction (Likert)
        questions.append({
            'prompt': '30. The sample size should be corrected for potential protocol violations',
            'item_type': 'likert5',
        })
        
        return questions