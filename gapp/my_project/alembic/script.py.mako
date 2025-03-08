from alembic import op
import sqlalchemy as sa

# Revision identifiers, used by Alembic.
revision = "abc123"
down_revision = None
branch_labels = None
depends_on = []

def upgrade():
    # -----------------------------------------------------
    #
    # --- Models ---
    #
    # You can use this section to make changes on models,
    # such as add fields and table relationships (i.e. foreign keys)
    #

# Example:
#
# op.add_column('my_table', sa.Column('new_field_name',
#                                         sa.Integer, nullable=False))

def downgrade():
    # -----------------------------------------------------
    #
    # --- Revert Changes made by upgrade() ---
    #
    # In this section you can reverse the changes done in your
    # previous function. If there is no corresponding action,
    # just leave it empty.
    #

# Example:
#
# op.drop_column('my_table', 'new_field_name')

if __name__ == "__main__":
    upgrade()