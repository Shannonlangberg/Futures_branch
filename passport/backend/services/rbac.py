"""RBAC (Role-Based Access Control) service"""
from sqlmodel import Session, select
from models.rbac import RBACRole, RBACScope
from models.leader import Leader

def check_permission(
    session: Session,
    leader_id: str,
    action: str,
    resource_id: str = None,
    resource_type: str = None
) -> bool:
    """Check if leader has permission for an action"""
    # Get leader
    leader = session.get(Leader, leader_id)
    if not leader:
        return False
    
    # Admin has all permissions
    if leader.role == "admin":
        return True
    
    # Get RBAC roles
    statement = select(RBACRole).where(RBACRole.leader_id == leader_id)
    roles = session.exec(statement).all()
    
    # Check global scope
    global_roles = [r for r in roles if r.scope == RBACScope.GLOBAL]
    if global_roles:
        return True
    
    # Check resource-specific scope
    if resource_type == "campus" and resource_id:
        campus_roles = [r for r in roles if r.scope == RBACScope.CAMPUS and r.scope_id == resource_id]
        if campus_roles:
            return True
    
    if resource_type == "track" and resource_id:
        track_roles = [r for r in roles if r.scope == RBACScope.TRACK and r.scope_id == resource_id]
        if track_roles:
            return True
    
    return False





