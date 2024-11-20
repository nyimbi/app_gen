class CustomSecurityManager(SecurityManager):
    def __init__(self, appbuilder):
        super().__init__(appbuilder)
        self.add_permission_view_menu('can_change_layout', 'MultipleViews')
        self.add_permission_view_menu('can_custom_view', 'MultipleViews')
