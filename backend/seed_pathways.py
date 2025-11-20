#!/usr/bin/env python3
"""
Seed script for pre-built Discipleship Pathways

Creates template pathways:
- Leadership Pathway
- Worship Leader Pathway
- Connect Leader Pathway
- Ministry Pathway
- General Discipleship Pathway
"""
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models import db, DiscipleshipPathway, PathwayStep
from config.database import build_sqlalchemy_settings

def create_leadership_pathway():
    """Create Leadership Pathway"""
    pathway = DiscipleshipPathway(
        name="Leadership Pathway",
        description="Pathway for developing church leaders",
        category="leadership",
        is_template=True,
        is_active=True
    )
    db.session.add(pathway)
    db.session.flush()
    
    steps = [
        {"order": 1, "name": "Salvation", "description": "Made decision to follow Christ", "milestone_type": "salvation"},
        {"order": 2, "name": "Baptism", "description": "Water baptism", "milestone_type": "baptism"},
        {"order": 3, "name": "Baptised in Holy Spirit", "description": "Filled with the Holy Spirit", "milestone_type": "holy_spirit"},
        {"order": 4, "name": "This is Christianity", "description": "Completed This is Christianity course", "milestone_type": "this_is_christianity"},
        {"order": 5, "name": "Joined Connect Group", "description": "Regularly attending a connect group", "milestone_type": "group_join"},
        {"order": 6, "name": "Joined Dream Team", "description": "Started serving on a team", "milestone_type": "serving_start"},
        {"order": 7, "name": "Leadership Training", "description": "Completed leadership training course", "milestone_type": "leadership_training"},
        {"order": 8, "name": "Leading a Team", "description": "Currently leading a serving team", "milestone_type": "team_leadership"},
    ]
    
    for step_data in steps:
        step = PathwayStep(
            pathway_id=pathway.id,
            step_order=step_data["order"],
            step_name=step_data["name"],
            step_description=step_data["description"],
            milestone_type=step_data["milestone_type"],
            is_required=True
        )
        db.session.add(step)
    
    return pathway


def create_worship_pathway():
    """Create Worship Leader Pathway"""
    pathway = DiscipleshipPathway(
        name="Worship Leader Pathway",
        description="Pathway for developing worship leaders",
        category="worship",
        is_template=True,
        is_active=True
    )
    db.session.add(pathway)
    db.session.flush()
    
    steps = [
        {"order": 1, "name": "Salvation", "description": "Made decision to follow Christ", "milestone_type": "salvation"},
        {"order": 2, "name": "Baptism", "description": "Water baptism", "milestone_type": "baptism"},
        {"order": 3, "name": "Baptised in Holy Spirit", "description": "Filled with the Holy Spirit", "milestone_type": "holy_spirit"},
        {"order": 4, "name": "Joined Worship Team", "description": "Started serving on worship team", "milestone_type": "serving_start"},
        {"order": 5, "name": "Worship Training", "description": "Completed worship training", "milestone_type": "worship_training"},
        {"order": 6, "name": "Leading Worship", "description": "Leading worship regularly", "milestone_type": "worship_leadership"},
    ]
    
    for step_data in steps:
        step = PathwayStep(
            pathway_id=pathway.id,
            step_order=step_data["order"],
            step_name=step_data["name"],
            step_description=step_data["description"],
            milestone_type=step_data["milestone_type"],
            is_required=True
        )
        db.session.add(step)
    
    return pathway


def create_connect_leader_pathway():
    """Create Connect Leader Pathway"""
    pathway = DiscipleshipPathway(
        name="Connect Leader Pathway",
        description="Pathway for developing connect group leaders",
        category="connect_leader",
        is_template=True,
        is_active=True
    )
    db.session.add(pathway)
    db.session.flush()
    
    steps = [
        {"order": 1, "name": "Salvation", "description": "Made decision to follow Christ", "milestone_type": "salvation"},
        {"order": 2, "name": "Baptism", "description": "Water baptism", "milestone_type": "baptism"},
        {"order": 3, "name": "Baptised in Holy Spirit", "description": "Filled with the Holy Spirit", "milestone_type": "holy_spirit"},
        {"order": 4, "name": "This is Christianity", "description": "Completed This is Christianity course", "milestone_type": "this_is_christianity"},
        {"order": 5, "name": "Joined Connect Group", "description": "Regularly attending a connect group", "milestone_type": "group_join"},
        {"order": 6, "name": "Connect Leader Training", "description": "Completed connect leader training", "milestone_type": "connect_leader_training"},
        {"order": 7, "name": "Leading Connect Group", "description": "Currently leading a connect group", "milestone_type": "connect_leadership"},
    ]
    
    for step_data in steps:
        step = PathwayStep(
            pathway_id=pathway.id,
            step_order=step_data["order"],
            step_name=step_data["name"],
            step_description=step_data["description"],
            milestone_type=step_data["milestone_type"],
            is_required=True
        )
        db.session.add(step)
    
    return pathway


def create_ministry_pathway():
    """Create Ministry Pathway"""
    pathway = DiscipleshipPathway(
        name="Ministry Pathway",
        description="General ministry development pathway",
        category="ministry",
        is_template=True,
        is_active=True
    )
    db.session.add(pathway)
    db.session.flush()
    
    steps = [
        {"order": 1, "name": "Salvation", "description": "Made decision to follow Christ", "milestone_type": "salvation"},
        {"order": 2, "name": "Baptism", "description": "Water baptism", "milestone_type": "baptism"},
        {"order": 3, "name": "Baptised in Holy Spirit", "description": "Filled with the Holy Spirit", "milestone_type": "holy_spirit"},
        {"order": 4, "name": "This is Christianity", "description": "Completed This is Christianity course", "milestone_type": "this_is_christianity"},
        {"order": 5, "name": "Joined Connect Group", "description": "Regularly attending a connect group", "milestone_type": "group_join"},
        {"order": 6, "name": "Joined Dream Team", "description": "Started serving on a team", "milestone_type": "serving_start"},
        {"order": 7, "name": "Ministry Training", "description": "Completed ministry training", "milestone_type": "ministry_training"},
    ]
    
    for step_data in steps:
        step = PathwayStep(
            pathway_id=pathway.id,
            step_order=step_data["order"],
            step_name=step_data["name"],
            step_description=step_data["description"],
            milestone_type=step_data["milestone_type"],
            is_required=True
        )
        db.session.add(step)
    
    return pathway


def create_general_pathway():
    """Create General Discipleship Pathway"""
    pathway = DiscipleshipPathway(
        name="General Discipleship Pathway",
        description="Basic discipleship journey for all believers",
        category="general",
        is_template=True,
        is_active=True
    )
    db.session.add(pathway)
    db.session.flush()
    
    steps = [
        {"order": 1, "name": "Salvation", "description": "Made decision to follow Christ", "milestone_type": "salvation"},
        {"order": 2, "name": "Baptism", "description": "Water baptism", "milestone_type": "baptism"},
        {"order": 3, "name": "Baptised in Holy Spirit", "description": "Filled with the Holy Spirit", "milestone_type": "holy_spirit"},
        {"order": 4, "name": "This is Christianity", "description": "Completed This is Christianity course", "milestone_type": "this_is_christianity"},
        {"order": 5, "name": "Joined Connect Group", "description": "Regularly attending a connect group", "milestone_type": "group_join"},
        {"order": 6, "name": "Joined Dream Team", "description": "Started serving on a team", "milestone_type": "serving_start"},
    ]
    
    for step_data in steps:
        step = PathwayStep(
            pathway_id=pathway.id,
            step_order=step_data["order"],
            step_name=step_data["name"],
            step_description=step_data["description"],
            milestone_type=step_data["milestone_type"],
            is_required=True
        )
        db.session.add(step)
    
    return pathway


def main():
    """Main seeding function"""
    print("=" * 60)
    print("DISCIPLESHIP PATHWAY SEED SCRIPT")
    print("=" * 60)
    
    from flask import Flask
    from config.database import build_sqlalchemy_settings
    
    app = Flask(__name__)
    app.config.update(build_sqlalchemy_settings())
    db.init_app(app)
    
    with app.app_context():
        try:
            created = 0
            
            # Check if pathways already exist
            existing = DiscipleshipPathway.query.filter_by(is_template=True).count()
            if existing > 0:
                print(f"[PATHWAY SEED] {existing} template pathways already exist. Skipping seed.")
                return True
            
            print("[PATHWAY SEED] Creating template pathways...")
            
            # Create all pathways
            create_leadership_pathway()
            print("  ✅ Created Leadership Pathway")
            created += 1
            
            create_worship_pathway()
            print("  ✅ Created Worship Leader Pathway")
            created += 1
            
            create_connect_leader_pathway()
            print("  ✅ Created Connect Leader Pathway")
            created += 1
            
            create_ministry_pathway()
            print("  ✅ Created Ministry Pathway")
            created += 1
            
            create_general_pathway()
            print("  ✅ Created General Discipleship Pathway")
            created += 1
            
            db.session.commit()
            
            print("=" * 60)
            print(f"SEEDING COMPLETE! Created {created} template pathways.")
            print("=" * 60)
            print("\nNext steps:")
            print("1. Go to Settings → Pathway Manager to view/edit pathways")
            print("2. Assign pathways to people via their Heartbeat profile")
            print("3. People can see their pathway progress in the mobile app")
            
        except Exception as e:
            print(f"[PATHWAY SEED] ERROR: {e}")
            import traceback
            traceback.print_exc()
            db.session.rollback()
            return False
    
    return True


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)




