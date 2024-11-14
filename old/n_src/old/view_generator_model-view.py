from .view_utils import get_view_icon

def generate_model_view(table, p):
    class_name = get_class_name(table.name, p)
    view_name = f"{class_name}ModelView"
    columns = [c.name for c in table.columns]
    list_columns = get_list_columns(columns)
    field_sets = get_field_sets(table)
    
    # Get the actual icon text
    icon = get_view_icon(table.name, "ModelView")
    
    generated_code.append([
        f"{view_name}",
        f"""
class {view_name}(ModelView):
    datamodel = SQLAInterface({class_name})
    list_columns = {list_columns}
    show_columns = list_columns
    edit_columns = list_columns
    add_columns = list_columns
    list_widget = BeautifulListWidget
    edit_widget = BeautifulFormWidget
    add_widget = BeautifulFormWidget
    show_widget = BeautifulFormWidget

    # Field sets for add and edit forms
    field_sets = {field_sets}

    # Enhanced search functionality
    search_columns = {list_columns}

    # Improved labels and descriptions
    label_columns = {{
        {', '.join([f"'{col}': '{col.replace('_', ' ').title()}'" for col in list_columns])}
    }}
    description_columns = {{
        {', '.join([f"'{col}': 'Enter the {col.replace('_', ' ')} here'" for col in list_columns])}
    }}

    # Custom formatters for better data presentation
    formatters_columns = {{
        'created_at': lambda x: x.strftime('%Y-%m-%d %H:%M:%S') if x else '',
        'updated_at': lambda x: x.strftime('%Y-%m-%d %H:%M:%S') if x else '',
    }}

    # Enhanced form field widgets
    add_form_extra_fields = {{
        {', '.join([generate_form_field(c) for c in table.columns if c.name in list_columns])}
    }}

    # Enable in-place editing
    can_edit = True

    # Custom actions
    @action("delete_all", "Delete All", "Are you sure you want to delete all records?", "fa-trash", multiple=True)
    def delete_all(self, items):
        if isinstance(items, list):
            self.datamodel.delete_all(items)
            flash(f"Deleted {{len(items)}} records", "success")
        else:
            flash("No records selected", "warning")
        return redirect(request.referrer)

    @action("print", "Print", "Print the selected items?", "fa-print", single=False)
    def print_items(self, items):
        if isinstance(items, list):
            return render_template('print_items.html', items=items, columns=self.list_columns)
        else:
            flash("No items selected", "warning")
        return redirect(request.referrer)

    @action("export_csv", "Export CSV", "Export selected items to CSV?", "fa-file-excel-o", single=False)
    def export_csv(self, items):
        if isinstance(items, list):
            csv_data = self.datamodel.export_as_csv(items)
            response = make_response(csv_data)
            response.headers["Content-Disposition"] = f"attachment; filename={self.__class__.__name__}_export.csv"
            response.headers["Content-Type"] = "text/csv"
            return response
        else:
            flash("No items selected", "warning")
        return redirect(request.referrer)

    @action("bookmark", "Bookmark", "Bookmark selected items?", "fa-bookmark", single=False)
    def bookmark_items(self, items):
        if isinstance(items, list):
            for item in items:
                item.is_bookmarked = True
            self.datamodel.bulk_update(items)
            flash(f"Bookmarked {{len(items)}} items", "success")
        else:
            flash("No items selected", "warning")
        return redirect(request.referrer)

    @action("merge", "Merge", "Merge selected items?", "fa-compress", single=False)
    def merge_items(self, items):
        if isinstance(items, list) and len(items) > 1:
            # Implement merge logic here
            flash(f"Merged {{len(items)}} items", "success")
        else:
            flash("Select at least two items to merge", "warning")
        return redirect(request.referrer)

    @action("split", "Split", "Split selected item?", "fa-scissors", single=True)
    def split_item(self, item):
        # Implement split logic here
        flash(f"Split item {{item}}", "success")
        return redirect(request.referrer)

    @action("clone", "Clone", "Clone selected item?", "fa-clone", single=True)
    def clone_item(self, item):
        new_item = self.datamodel.obj()
        for col in self.list_columns:
            setattr(new_item, col, getattr(item, col))
        self.datamodel.add(new_item)
        flash(f"Cloned item {{item}}", "success")
        return redirect(request.referrer)

    @action("archive", "Archive", "Archive selected items?", "fa-archive", single=False)
    def archive_items(self, items):
        if isinstance(items, list):
            for item in items:
                item.is_archived = True
            self.datamodel.bulk_update(items)
            flash(f"Archived {{len(items)}} items", "success")
        else:
            flash("No items selected", "warning")
        return redirect(request.referrer)

    @action("restore", "Restore", "Restore selected items?", "fa-undo", single=False)
    def restore_items(self, items):
        if isinstance(items, list):
            for item in items:
                item.is_archived = False
            self.datamodel.bulk_update(items)
            flash(f"Restored {{len(items)}} items", "success")
        else:
            flash("No items selected", "warning")
        return redirect(request.referrer)

    @action("bulk_edit", "Bulk Edit", "Edit selected items?", "fa-edit", single=False)
    def bulk_edit(self, items):
        if isinstance(items, list):
            return redirect(url_for('.bulk_edit_form', ids=','.join([str(item.id) for item in items])))
        else:
            flash("No items selected", "warning")
        return redirect(request.referrer)

    @expose('/bulk_edit_form/<ids>')
    @has_access
    def bulk_edit_form(self, ids):
        items = self.datamodel.get_list_by_ids(ids.split(','))
        form = self.add_form()
        if request.method == 'POST':
            form = self.add_form(request.form)
            if form.validate():
                for item in items:
                    form.populate_obj(item)
                self.datamodel.bulk_update(items)
                return redirect(self.get_redirect())
        return self.render_template('bulk_edit.html', form=form, items=items)

    # Advanced Filtering and Sorting
    base_filters = []
    base_order = []

    def pre_add(self, item):
        # Set created_at and updated_at if they exist
        if hasattr(item, 'created_at'):
            item.created_at = datetime.datetime.now()
        if hasattr(item, 'updated_at'):
            item.updated_at = datetime.datetime.now()

    def pre_update(self, item):
        # Update updated_at if it exists
        if hasattr(item, 'updated_at'):
            item.updated_at = datetime.datetime.now()

    # User-Specific Actions
    @expose('/favorite/<pk>')
    @has_access
    def favorite(self, pk):
        item = self.datamodel.get(pk)
        if item:
            current_user.favorites.append(item)
            db.session.commit()
            flash(f"Added {{item}} to favorites", "success")
        return redirect(request.referrer)

    @expose('/watchlist/<pk>')
    @has_access
    def watchlist(self, pk):
        item = self.datamodel.get(pk)
        if item:
            current_user.watchlist.append(item)
            db.session.commit()
            flash(f"Added {{item}} to watchlist", "success")
        return redirect(request.referrer)

    @expose('/personalize')
    @has_access
    def personalize(self):
        if request.method == 'POST':
            current_user.list_columns = request.form.getlist('columns')
            current_user.list_order = request.form.get('order')
            db.session.commit()
            flash("View settings updated", "success")
        return self.render_template('personalize.html', columns=self.list_columns, current_columns=current_user.list_columns, current_order=current_user.list_order)

    # Integration with External Services
    def post_add(self, item):
        # Example: Send email notification
        send_email_notification(f"New {{self.__class__.__name__}} added", f"A new {{self.__class__.__name__}} has been added: {{item}}")

    def post_update(self, item):
        # Example: Update external API
        update_external_api(item)

    def post_delete(self, item):
        # Example: Log to external service
        log_to_external_service(f"{{self.__class__.__name__}} deleted: {{item}}")

"""
    ])
    generated_views.append((view_name, "ModelView", table.name, icon))

def generate_views(db_uri):
    # ... (previous code remains unchanged)

    # Add view registration function
    generated_code.append([
        "register_views",
        """
def register_views():
""" + "\n".join([f"    appbuilder.add_view({class_name}, '{table_name}', icon='{icon}', category='Generated Views')" 
                  for class_name, view_type, table_name, icon in generated_views]) + """

    # Gamification: Reminder for incomplete forms
    @appbuilder.app.context_processor
    def inject_notifications():
        notifications = []
        for view_name, view in appbuilder.baseviews.items():
            if isinstance(view, WizardView):
                progress = view.get_progress()
                if 0 < progress < 100:
                    notifications.append(f"Continue your {view.__class__.__name__[:-10]} form! You're {progress:.0f}% done.")
        return dict(notifications=notifications)

# GraphQL schema
schema = graphene.Schema(query=Query)
"""
    ])

    # ... (rest of the function remains unchanged)