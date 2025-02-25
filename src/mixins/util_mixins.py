class VersionMixin:
    """Mixin class for version models"""
    version = Column(Integer, nullable=False)
    changed_by_id = Column(Integer, ForeignKey('ab_user.id'))
    changed_on = Column(DateTime, default=datetime.now)
    change_type = Column(String(10), nullable=False)
    _changes = Column('changes', JSON)

    @property
    def changes(self) -> dict:
        """Get changes in readable format"""
        return self._changes or {}

class ArchivedVersion(Model):
    """Model for archived versions"""
    __tablename__ = 'archived_versions'

    id = Column(Integer, primary_key=True)
    item_type = Column(String(100), nullable=False)
    item_id = Column(Integer, nullable=False)
    version = Column(Integer, nullable=False)
    data = Column(JSON, nullable=False)
    deleted_at = Column(DateTime, nullable=False)
    deleted_by_id = Column(Integer, ForeignKey('ab_user.id'))

    def __repr__(self) -> str:
        return f"<ArchivedVersion {self.item_type}:{self.item_id} v{self.version}>"