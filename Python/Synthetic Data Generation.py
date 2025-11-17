import pandas as pd
import numpy as np
from faker import Faker
from datetime import datetime, timedelta
import random

fake = Faker()

# Generate 20 providers across specialties
def generate_providers(n=20):
    specialties = ['Internal Medicine', 'Pediatrics', 'Emergency Medicine', 
                   'Surgery', 'Cardiology', 'Oncology']
    departments = ['Inpatient', 'Outpatient', 'Emergency', 'Surgical']
    
    providers = []
    for i in range(n):
        providers.append({
            'provider_id': f'PROV{i:04d}',
            'name': fake.name(),
            'specialty': random.choice(specialties),
            'department': random.choice(departments),
            'fte': random.choice([0.5, 0.75, 1.0]),
            'hire_date': fake.date_between(start_date='-10y', end_date='-1y'),
            'baseline_capacity': random.randint(12, 25) # patients/day
        })
    return pd.DataFrame(providers)

# Generate 90 days of encounter data with realistic burnout patterns
def generate_encounters(providers_df, days=90):
    encounters = []
    encounter_id = 0
    
    for _, provider in providers_df.iterrows():
        # Simulate burnout buildup over 90 days
        # Week 1-4: Normal load
        # Week 5-8: Increasing load (staff shortage simulation)
        # Week 9-12: Peak stress, then intervention
        
        start_date = datetime.now() - timedelta(days=days)
        
        for day in range(days):
            current_date = start_date + timedelta(days=day)
            
            # Skip weekends
            if current_date.weekday() >= 5:
                continue
            
            # Determine patient load based on burnout phase
            if day < 28:  # Weeks 1-4: Normal
                daily_load = int(provider['baseline_capacity'] * random.uniform(0.7, 0.9))
            elif day < 56:  # Weeks 5-8: Increasing
                daily_load = int(provider['baseline_capacity'] * random.uniform(0.95, 1.3))
            else:  # Weeks 9-12: Peak then intervention
                if day < 70:
                    daily_load = int(provider['baseline_capacity'] * random.uniform(1.2, 1.5))
                else:  # Post-intervention reduction
                    daily_load = int(provider['baseline_capacity'] * random.uniform(0.6, 0.8))
            
            # Generate encounters for the day
            for _ in range(daily_load):
                acuity = random.choices(
                    ['Low', 'Medium', 'High', 'Critical'],
                    weights=[0.4, 0.35, 0.2, 0.05]
                )[0]
                
                # Documentation time correlates with acuity
                doc_time_map = {'Low': (5, 10), 'Medium': (10, 20), 
                                'High': (20, 40), 'Critical': (40, 90)}
                doc_time = random.randint(*doc_time_map[acuity])
                
                encounters.append({
                    'encounter_id': f'ENC{encounter_id:08d}',
                    'provider_id': provider['provider_id'],
                    'patient_id': f'PAT{random.randint(0, 9999):04d}',
                    'encounter_date': current_date.date(),
                    'encounter_time': f'{random.randint(8, 17):02d}:{random.choice([0, 15, 30, 45]):02d}',
                    'duration_minutes': random.randint(15, 60),
                    'acuity_level': acuity,
                    'encounter_type': random.choice(['Office Visit', 'Procedure', 'Consult', 'Follow-up']),
                    'documentation_time_minutes': doc_time
                })
                encounter_id += 1
    
    return pd.DataFrame(encounters)

# Generate workload metrics (aggregated from encounters)
def generate_workload_metrics(encounters_df):
    metrics = []
    
    for (provider_id, date), group in encounters_df.groupby(['provider_id', 'encounter_date']):
        # Calculate daily metrics
        patient_count = len(group)
        clinical_hours = group['duration_minutes'].sum() / 60
        doc_time = group['documentation_time_minutes'].sum()
        
        # After-hours work increases with high patient load
        after_hours = 0
        if patient_count > 20:
            after_hours = random.randint(30, 120)
        elif patient_count > 15:
            after_hours = random.randint(0, 60)
        
        # Missed breaks correlate with patient volume
        missed_breaks = max(0, patient_count - 18) // 3
        
        # Email volume
        email_count = random.randint(15, 50) + (patient_count * 2)
        
        metrics.append({
            'metric_id': f'MET{len(metrics):08d}',
            'provider_id': provider_id,
            'date': date,
            'patient_count': patient_count,
            'total_clinical_hours': round(clinical_hours, 2),
            'documentation_time_minutes': doc_time,
            'after_hours_minutes': after_hours,
            'missed_breaks': missed_breaks,
            'email_count': email_count,
            'inbox_response_time_hours': round(random.uniform(1, 24), 2)
        })
    
    return pd.DataFrame(metrics)

# Generate burnout assessments (weekly for training data)
def generate_burnout_assessments(providers_df, workload_df):
    assessments = []
    assessment_id = 0
    
    for _, provider in providers_df.iterrows():
        provider_workload = workload_df[workload_df['provider_id'] == provider['provider_id']]
        
        # Generate weekly assessments
        for week in range(0, 13):
            week_data = provider_workload[
                (provider_workload['date'] >= datetime.now().date() - timedelta(days=90 - week*7)) &
                (provider_workload['date'] < datetime.now().date() - timedelta(days=90 - (week+1)*7))
            ]
            
            if len(week_data) == 0:
                continue
            
            # Calculate burnout score from workload patterns
            avg_patients = week_data['patient_count'].mean()
            avg_after_hours = week_data['after_hours_minutes'].mean()
            avg_doc_time = week_data['documentation_time_minutes'].mean()
            
            # Burnout formula (0-100)
            burnout_score = min(100, int(
                (avg_patients - provider['baseline_capacity']) * 3 +
                (avg_after_hours / 60) * 10 +
                (avg_doc_time / 60) * 2 +
                random.randint(-10, 10)  # Natural variation
            ))
            burnout_score = max(0, burnout_score)
            
            # Component scores
            emotional_exhaustion = min(100, burnout_score + random.randint(-15, 15))
            depersonalization = min(100, burnout_score + random.randint(-20, 10))
            accomplishment = max(0, 100 - burnout_score + random.randint(-10, 20))
            
            # Categorize
            if burnout_score < 25:
                status = 'Low'
            elif burnout_score < 50:
                status = 'Medium'
            elif burnout_score < 75:
                status = 'High'
            else:
                status = 'Critical'
            
            assessments.append({
                'assessment_id': f'ASMT{assessment_id:08d}',
                'provider_id': provider['provider_id'],
                'assessment_date': (datetime.now() - timedelta(days=90 - week*7)).date(),
                'emotional_exhaustion_score': emotional_exhaustion,
                'depersonalization_score': depersonalization,
                'personal_accomplishment_score': accomplishment,
                'overall_burnout_score': burnout_score,
                'self_reported_status': status
            })
            assessment_id += 1
    
    return pd.DataFrame(assessments)

# Generate task assignments
def generate_tasks(providers_df, days=90):
    tasks = []
    task_types = ['Chart Review', 'Phone Call', 'Prior Authorization', 
                  'Lab Review', 'Imaging Review', 'Prescription Refill']
    
    for _, provider in providers_df.iterrows():
        for day in range(days):
            date = datetime.now() - timedelta(days=90-day)
            
            # Each provider gets 5-15 tasks per day
            num_tasks = random.randint(5, 15)
            
            for _ in range(num_tasks):
                priority = random.choices(
                    ['Routine', 'Urgent', 'STAT'],
                    weights=[0.7, 0.25, 0.05]
                )[0]
                
                task_time_map = {
                    'Chart Review': (10, 30),
                    'Phone Call': (5, 15),
                    'Prior Authorization': (20, 60),
                    'Lab Review': (5, 15),
                    'Imaging Review': (10, 25),
                    'Prescription Refill': (3, 10)
                }
                
                task_type = random.choice(task_types)
                
                tasks.append({
                    'task_id': f'TASK{len(tasks):08d}',
                    'provider_id': provider['provider_id'],
                    'task_type': task_type,
                    'priority': priority,
                    'assigned_date': date,
                    'due_date': date + timedelta(hours=random.randint(4, 48)),
                    'status': random.choice(['Pending', 'In Progress', 'Completed']),
                    'estimated_minutes': random.randint(*task_time_map[task_type]),
                    'reassigned_to': None
                })
    
    return pd.DataFrame(tasks)

# Main data generation
if __name__ == '__main__':
    print("Generating synthetic EPIC/EHR data...")
    
    providers = generate_providers(20)
    print(f"✓ Generated {len(providers)} providers")
    
    encounters = generate_encounters(providers, 90)
    print(f"✓ Generated {len(encounters)} patient encounters")
    
    workload = generate_workload_metrics(encounters)
    print(f"✓ Generated {len(workload)} workload metric records")
    
    assessments = generate_burnout_assessments(providers, workload)
    print(f"✓ Generated {len(assessments)} burnout assessments")
    
    tasks = generate_tasks(providers, 90)
    print(f"✓ Generated {len(tasks)} task assignments")
    
    # Save to CSV
    providers.to_csv('data/providers.csv', index=False)
    encounters.to_csv('data/encounters.csv', index=False)
    workload.to_csv('data/workload_metrics.csv', index=False)
    assessments.to_csv('data/burnout_assessments.csv', index=False)
    tasks.to_csv('data/tasks.csv', index=False)
    
    print("\n✅ All synthetic data generated successfully!")
    print("\nData Summary:")
    print(f"  - 20 providers across 6 specialties")
    print(f"  - 90 days of historical data")
    print(f"  - ~{len(encounters)} total patient encounters")
    print(f"  - {len(assessments)} burnout assessments for ML training")
