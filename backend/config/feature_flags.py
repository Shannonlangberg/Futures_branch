# Feature Flags Configuration
# Controls which features are enabled in the system

class FeatureFlags:
    """Feature flags for controlling system functionality"""
    
    # Devotions Management
    DEVOTIONS_ADMIN_ENABLED = True
    
    # Connect Groups for Staff
    GROUPS_FOR_STAFF_ENABLED = True
    
    # Beacon Management
    BEACON_MGMT_ENABLED = True
    
    # RBAC System
    RBAC_ENABLED = True
    
    # Campus Scoping
    CAMPUS_SCOPING_ENABLED = True
    
    @classmethod
    def get_all_flags(cls):
        """Get all feature flags as a dictionary"""
        return {
            'DEVOTIONS_ADMIN_ENABLED': cls.DEVOTIONS_ADMIN_ENABLED,
            'GROUPS_FOR_STAFF_ENABLED': cls.GROUPS_FOR_STAFF_ENABLED,
            'BEACON_MGMT_ENABLED': cls.BEACON_MGMT_ENABLED,
            'RBAC_ENABLED': cls.RBAC_ENABLED,
            'CAMPUS_SCOPING_ENABLED': cls.CAMPUS_SCOPING_ENABLED
        }
    
    @classmethod
    def is_enabled(cls, flag_name):
        """Check if a specific feature flag is enabled"""
        return getattr(cls, flag_name, False)
