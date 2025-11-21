#!/usr/bin/env python3
"""Check for duplicate/legacy discipleship data"""

from app import app
from models import db, Person, PersonPathwayProgress, PersonPathwayStepCompletion, PathwayStep, DiscipleshipPathway

def check_shannon_data():
    with app.app_context():
        person = Person.query.filter(
            db.func.lower(Person.email) == 'shannon.langberg@futures.church',
            Person.is_active == True
        ).first()
        
        if not person:
            print("❌ Person not found")
            return
        
        print("="*80)
        print(f"DATA CHECK FOR: {person.full_name}")
        print("="*80)
        
        # OLD SYSTEM - Person table columns
        print("\n🗂️  OLD SYSTEM (Person table columns):")
        print(f"   - dna_completed: {person.dna_completed}")
        print(f"   - baptised_on: {person.baptised_on}")
        print(f"   - filled_holy_spirit: {person.filled_holy_spirit}")
        print(f"   - rise_attended: {person.rise_attended}")
        print(f"   - first_served_on: {person.first_served_on}")
        
        # NEW SYSTEM - Pathway Progress
        print("\n🎯 NEW SYSTEM (Pathway Progress):")
        
        # Check if there are any pathways
        all_pathways = DiscipleshipPathway.query.filter_by(is_active=True).all()
        print(f"   Total active pathways in system: {len(all_pathways)}")
        for pathway in all_pathways:
            print(f"      - {pathway.name} (ID: {pathway.id})")
        
        # Check person's pathway progress
        progress_records = PersonPathwayProgress.query.filter_by(
            person_id=person.id
        ).all()
        
        print(f"\n   {person.full_name}'s pathway progress records: {len(progress_records)}")
        
        for progress in progress_records:
            pathway = DiscipleshipPathway.query.get(progress.pathway_id)
            pathway_name = pathway.name if pathway else f"Unknown (ID: {progress.pathway_id})"
            
            print(f"\n   📖 Pathway: {pathway_name}")
            print(f"      Status: {progress.status}")
            print(f"      Started: {progress.started_at}")
            print(f"      Completed: {progress.completed_at}")
            print(f"      Progress: {progress.progress_percentage}%")
            
            # Check step completions
            completions = PersonPathwayStepCompletion.query.filter_by(
                pathway_progress_id=progress.id
            ).all()
            
            print(f"      Completed steps: {len(completions)}")
            for completion in completions:
                step = PathwayStep.query.get(completion.pathway_step_id)
                step_name = step.title if step else f"Unknown step {completion.pathway_step_id}"
                print(f"         ✅ {step_name} - {completion.completed_at}")
        
        print("\n" + "="*80)
        print("RECOMMENDATION:")
        print("="*80)
        
        if person.dna_completed or person.baptised_on or person.filled_holy_spirit:
            print("❌ You have data in the OLD SYSTEM (Person table columns)")
            print("   These columns are legacy and should probably be cleared")
            print("   The NEW pathway system should be the single source of truth")
        else:
            print("✅ No legacy data found in Person table columns")
        
        if progress_records:
            print(f"✅ You have {len(progress_records)} pathway progress records in the NEW SYSTEM")
        else:
            print("⚠️  No pathway progress found in the NEW SYSTEM")
            print("   You may need to start/complete pathways to track progress")
        
        print("\n")

if __name__ == '__main__':
    check_shannon_data()

