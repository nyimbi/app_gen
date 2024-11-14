from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.properties import ObjectProperty, ListProperty


class BaseCRUDScreen(BoxLayout):
    db = ObjectProperty() # Connect the DB engine to your screen via a property
    table_name = ""

    # Initialize the base class with global variables and functions
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.tables = globals_variable_for_your_table_list
        # Set the initial table to read from or create new records in
        self.current_table = self.tables[0]
        self.load_data()

    def load_data(self):
        """
        Retrieve all rows for current table from SQLAlchemy ORM and store them in a list property.
        """
        self.rows = self.db.session.query(self.current_table).all()
        self.ids.record_count.text = str(len(self.rows)) + " Records"

    def prev_record(self):
        """
        Move to the previous record if any.
        """
        if len(self.rows) > 0:
            index = self.current_row - 1 if self.current_row > 0 else len(self.rows) - 1
            self.set_record(index)

    def next_record(self):
        """
        Move to the next record if any.
        """
        if len(self.rows) > 0:
            index = self.current_row + 1 if self.current_row < (len(self.rows) - 1) else 0
            self.set_record(index)

    def search(self, text):
        """
        Search through the current table and display matching results.
        Adjust this function according to your database schema and specific search requirements.
        """
        rows = self.db.session.query(self.current_table).filter(any([getattr(row, f) == text for f
in row.__mapper__.columns])).all()
        self.rows = rows
        self.ids.record_count.text = str(len(self.rows)) + " Records"

    def set_record(self, index):
        """
        Set the current record and update UI accordingly.
        Adjust this function according to your database schema.
        """
        self.current_row = index
        if len(self.rows) > 0:
            self.ids.table_record.data = [row[index] for row in self.rows]
            self.ids.table_record.current = index + 1
        else:
            # No records found, show appropriate message
            print("No record found at this index")

    def create_new(self):
        """
        Create a new row for the current table using SQLAlchemy ORM. Adjust this function according
to your database schema.
        """
        new_row = self.current_table() # Create a new object of current table model class
        self.db.add(new_row)
        self.db.commit()
        self.load_data()

    def update_record(self, row):
        """
        Update the current record using SQLAlchemy ORM. Adjust this function according to your
database schema.
        """
        self.db.session.merge(row)  # Merge changes made in UI to the database object
        self.db.commit()

    def delete_record(self, row):
        """
        Delete the current record using SQLAlchemy ORM. Adjust this function according to your
database schema.
        """
        self.db.session.delete(row)  # Delete the object from DB session
        self.db.commit()
        self.load_data()