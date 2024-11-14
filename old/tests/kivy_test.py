import kivy
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.properties import ObjectProperty
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Database setup
engine = create_engine('sqlite:///mydatabase.db')  # Replace with your database URL
Base = declarative_base()
Session = sessionmaker(bind=engine)
session = Session()

# Define your model
class Entry(Base):
    __tablename__ = 'entries'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    value = Column(String)

Base.metadata.create_all(engine)  # Create the table if it doesn't exist

# Kivy UI setup
class DataEntryApp(App):
    def build(self):
        self.layout = BoxLayout(orientation='vertical')

        # Add text inputs for data entry
        self.name_input = TextInput(hint_text='Enter Name')
        self.value_input = TextInput(hint_text='Enter Value')
        self.layout.add_widget(self.name_input)
        self.layout.add_widget(self.value_input)

        # Add a button to submit data
        submit_button = Button(text='Submit', on_press=self.submit_data)
        self.layout.add_widget(submit_button)

        return self.layout

    def submit_data(self, instance):
        name = self.name_input.text
        value = self.value_input.text

        # Create a new entry and add it to the database
        new_entry = Entry(name=name, value=value)
        session.add(new_entry)
        session.commit()

        # Clear input fields and provide feedback
        self.name_input.text = ''
        self.value_input.text = ''
        print('Data submitted successfully!')

if __name__ == '__main__':
    DataEntryApp().run()

